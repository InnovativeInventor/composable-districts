from typing import Iterable, Optional, Set, Tuple

import geopandas
import numpy as np
import pandas
import pydantic
import shapely.geometry
import tqdm
from postal.near_dupe import near_dupe_hashes

# from postal.expand import expand_address as normalize
from postal.normalize import normalize_string as normalize
from postal.parser import parse_address
from pydantic import BaseModel, ValidationError, validator
from pydantic.dataclasses import dataclass
from shapely.validation import make_valid

import geocompose.auxiliary as auxiliary
from geocompose.export import export

# def get_geometry(dataframe: geopandas.GeoDataFrame):
#     for _, x in dataframe.iterrows():
#         yield x["geometry"]

# make_valid = lambda x: x # placeholder


class HashableEdge(pydantic.BaseModel):
    """
    A HashableEdge class is composed of tuples and 
    """

    edge: Tuple[Tuple[int, int], Tuple[int, int]]
    id: int

    def __hash__(self):
        # return hash(((min(self.edge), max(self.edge)), self.id))
        return hash(self.id)
        # return hash((self.edge, self.id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    #     return ((self.edge == other.edge) or (self.edge == tuple(reversed(other.edge)))) and self.id == other.id


class Addresses:
    """
    An Addresses class is composed of two DataFrames:
        - a geopandas DataFrame containing a polygon representation of the region
        - a pandas DataFrame containing the addresses-location pairs.

    The geopandas DataFrame is immediately replaced with a voronoi diagram.
    """

    def __init__(
        self,
        addresses_given: geopandas.GeoDataFrame,
        polygon_given: geopandas.GeoDataFrame,
        generate=True,
    ):
        # self.polygon = geopandas.GeoDataFrame(*args, **kwargs)

        # if addresses:
        #     self.address = geopandas.GeoDataFrame(addresses, columns=["polygon", "name", "location"], geometry="location")
        # else:
        #     self.address = geopandas.GeoDataFrame(columns=["polygon", "name", "location"], geometry="location")

        self.polygon = polygon_given
        self.addresses = addresses_given

        self.polygon_index = polygon_given.sindex
        self.addresses_index = self.addresses.sindex
        self.adjacency_map = {}

        # self.borders = shapely.ops.unary_union([x["geometry"] for _,x in self.polygon.iterrows()])
        # self.union = make_valid(shapely.ops.unary_union(self.polygon["geometry"]))
        self.union = shapely.ops.unary_union(self.polygon["geometry"])
        self.union_index = geopandas.GeoDataFrame(
            self.union, columns=["geometry"]
        ).sindex

        self.border = auxiliary.find_border(self.union)
        self.border_index = self.border.sindex

        if generate:
            # self.border_hull = make_valid(shapely.ops.unary_union(self.polygon["geometry"])).convex_hull
            self.diagram = self.generate_diagram()  # turn off in prod

    def __add__(self, other):
        """
        Currently just concatenates the addresses and the polygon GeoDataFrames.

        TODO: Do smart deduplication using merge_addresses.
        """
        return Addresses(
            auxiliary.concat_gdf(self.addresses, other.addresses),
            auxiliary.concat_gdf(self.polygon, other.polygon),
        )

    def generate_diagram(self):
        """
        Generates a Voronoi diagram.

        TODO: Find speedups
        """
        diagram: shapely.geometry.collection.GeometryCollection = shapely.ops.voronoi_diagram(
            shapely.geometry.MultiPoint(self.addresses["geometry"]), envelope=self.union
        )

        diagram_gdf = geopandas.GeoDataFrame(diagram.geoms, columns=["geometry"])
        self.diagram_unfiltered = diagram_gdf.copy()
        for count, cell in tqdm.tqdm(diagram_gdf.iterrows(), total=len(diagram_gdf)):
            # print(type(cell), len(cell)) # len always one
            for polygon in cell:
                for line in auxiliary.find_polygon_border(polygon):  # tuple
                    reversed_line = tuple(reversed(line))

                    try:
                        self.adjacency_map[line].add(count)  # unique up to .id
                    except KeyError:
                        self.adjacency_map[line] = {count}

                    try:
                        self.adjacency_map[reversed_line].add(count)  # unique up to .id
                    except KeyError:
                        self.adjacency_map[reversed_line] = {count}

                    # self.adjacency_map[line].add(count)
                    # self.adjacency_map[reversed_line].add(count)

                    # edge = HashableEdge(edge=line, id=count)
                    # reversed_edge = HashableEdge(edge=reversed_line, id=count)

                    # if self.adjacency_map.get(line): # could make this symmetric
                    #     self.adjacency_map[line].add(edge) # unique up to .id
                    # else:
                    #     self.adjacency_map[line] = set(edge)

                    # if self.adjacency_map.get(reversed_line):
                    #     self.adjacency_map[reversed_line].add(reversed_edge)
                    # else:
                    #     self.adjacency_map[reversed_line] = set(reversed_edge)

                    # self.adjacency_map[line].add(reversed_edge)
                    # self.adjacency_map[reversed_line].add(edge)

        print("Finding border cells")  # debug
        border_cells = set()
        for count, cell in tqdm.tqdm(diagram_gdf.iterrows(), total=len(diagram_gdf)):
            for polygon in cell:
                for line in auxiliary.find_polygon_border(polygon):  # tuple
                    # print(len(self.adjacency_map.get(line).union(self.adjacency_map.get(reversed_line))))
                    # if len(self.adjacency_map.get(line).union(self.adjacency_map.get(reversed_line)))< 3:
                    if len(self.adjacency_map.get(line)) <= 1:
                        # print(count, self.adjacency_map.get(line).union(self.adjacency_map.get(reversed_line)))
                        border_cells.add(count)
                        # border_cells.union(self.adjacency_map.get(line).union(self.adjacency_map.get(reversed_line)))

        breakpoint()

        print("Finding adjacent cells", len(border_cells))  # debug
        crust = border_cells
        self.already_seen = set()
        for count, cell in tqdm.tqdm(enumerate(border_cells), total=len(border_cells)):
            adjacent_cells = self.find_adjacent_crust(
                cell, diagram_gdf, border_cells.union(crust)
            )
            crust = crust.union(adjacent_cells)
            if count == 100:
                break

        breakpoint()

        # border_cells = border_cells.union(crust)
        print("Cropping border cells", len(border_cells))  # debug
        # border_cells = {x for x in range(13)}
        for each_cell_id in tqdm.tqdm(border_cells, total=len(border_cells)):
            # cropped_cell = make_valid(cell.intersection(self.union))
            cropped_cell = (
                diagram_gdf.iloc[each_cell_id].get("geometry").intersection(self.union)
            )

            # print(cell)
            # cell["geometry"] = make_valid(cropped_cell)
            # print(cell["geometry"])
            # diagram_gdf.iloc[each_cell_id] = cell
            if cropped_cell:  # both are valid
                diagram_gdf.iloc[each_cell_id]["geometry"] = cropped_cell
                # diagram_gdf["geometry"][each_cell_id] = cropped_cell

            # assert diagram_gdf.iloc[each_cell_id]["geometry"] != cell
            # assert diagram_gdf.iloc[each_cell_id]["geometry"] == cropped_cell

        print(diagram_gdf, len(diagram_gdf), print(diagram_gdf["geometry"]))

        self.diagram = diagram_gdf
        return diagram_gdf

    def find_adjacent_crust(self, cell, diagram_gdf, border_cells):
        adjacent = set()

        for line in auxiliary.find_polygon_border(
            diagram_gdf.iloc[cell].get("geometry")
        ):
            #     edge = HashableEdge(edge=line, id=cell)
            for other_cell in self.adjacency_map[line]:
                if not other_cell in self.already_seen:
                    if (
                        other_cell != cell
                        and (not other_cell in border_cells)
                        and self.union.contains(
                            diagram_gdf.iloc[other_cell].get("geometry")
                        )
                    ):
                        # print(other_cell)
                        adjacent.add(other_cell)
                        adjacent.union(
                            self.find_adjacent_crust(
                                other_cell, diagram_gdf, border_cells.union(adjacent)
                            )
                        )
                    else:
                        self.already_seen.add(other_cell)

        # for line in auxiliary.find_polygon_border(diagram_gdf.iloc[cell].get("geometry")):
        #     edge = HashableEdge(edge=line, id=cell)
        #     for adjacent_edge in self.adjacency_map[line]:
        #         # print(adjacent_edge, type(adjacent_edge))
        #         if adjacent_edge.id != edge.id and not adjacent_edge.id in border_cells:
        #             if not self.border.intersects(adjacent_edge):
        #                 adjacent.add(adjacent_edge.id)
        #                 adjacent.union(self.find_adjacent_crust(adjacent_edge.id, diagram_gdf, border_cells.union(adjacent)))

        return adjacent

    def generate_dual(self):
        """
        Generates the Delaunay triangulation (the dual of the Voronoi diagram).
        """
        pass

    def export_dir(
        self,
        dirname: str,
        addresses: str = "addresses",
        polygon: str = "polygon",
        diagram: str = "diagram",
        diagram_unfiltered: str = "diagram_unfiltered",
        border: str = "border",
    ):
        """
        Exports current state to a directory
        """
        if not dirname.endswith("/"):
            dirname += "/"

        for name, each_object in (
            # (addresses, self.addresses),
            (polygon, self.polygon),
            (border, self.border),
            (diagram, self.diagram),
            (diagram_unfiltered, self.diagram_unfiltered),
        ):
            print("Export", name, each_object, len(each_object))  # debug
            try:
                export(each_object.dropna(subset=["geometry"]), dirname + name)
            except RuntimeError as e:
                print("Error", e)
            print("Export done")

    @staticmethod
    def merge_addresses(
        addresses_1: geopandas.GeoDataFrame, addresses_2: geopandas.GeoDataFrame
    ):
        """
        Utilizes libpostal to find and remove duplicates when merging. Currently broken.
        """
        # labels, values = unzip(map(address_map, addresses_1.iterrows()))
        # print(list(labels), list(values))
        # results_1 = near_dupe_hashes(list(labels), list(values), languages=("en"))
        # # results_1 = near_dupe_hashes(labels, values, languages=("en"))

        # labels, values = unzip(map(address_map, addresses_2.iterrows()))
        # results_2 = near_dupe_hashes(list(labels), list(values), languages=("en"))
        # # results_2 = near_dupe_hashes(labels, values, languages=("en"))

        labels_1 = []
        values_1 = []
        labels_2 = []
        values_2 = []

        for address_1, address_2 in zip(addresses_1.iterrows(), addresses_2.iterrows()):
            _, address_1 = address_1
            _, address_2 = address_2

            for count, each_address in enumerate((address_1, address_2)):
                address_dict = each_address.to_dict()
                for key in address_dict:
                    if value := address_dict[key]:
                        eval("labels_" + str(count + 1)).append(key)
                        # print(value)
                        eval("values_" + str(count + 1)).append(key)

        results_1 = near_dupe_hashes(labels_1, values_1, languages=("en"))
        results_2 = near_dupe_hashes(labels_2, values_2, languages=("en"))

        print(results_1, results_2)
        return results_1 + results_2  # placeholder
