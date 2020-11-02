from typing import Iterable, Optional, Set

import geopandas
import numpy as np
import pandas
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

        # self.boarders = shapely.ops.unary_union([x["geometry"] for _,x in self.polygon.iterrows()])
        self.union = make_valid(shapely.ops.unary_union(self.polygon["geometry"]))
        self.union_index = geopandas.GeoDataFrame(
            self.union, columns=["geometry"]
        ).sindex

        self.boarder = auxiliary.find_boarder(self.union)
        self.boarder_index = self.boarder.sindex

        if generate:
            # self.boarder_hull = make_valid(shapely.ops.unary_union(self.polygon["geometry"])).convex_hull
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
        # diagram: shapely.geometry.collection.GeometryCollection = make_valid( # breaks
        #     shapely.ops.voronoi_diagram(
        #         shapely.geometry.MultiPoint(self.addresses["geometry"])
        #     )
        # )

        diagram: shapely.geometry.collection.GeometryCollection = shapely.ops.voronoi_diagram(
            shapely.geometry.MultiPoint(self.addresses["geometry"])
        )

        diagram_gdf = geopandas.GeoDataFrame(diagram.geoms, columns=["geometry"])
        self.diagram_unfiltered = geopandas.GeoDataFrame(
            diagram.geoms, columns=["geometry"]
        )  # debug
        print(diagram_gdf)
        print(diagram_gdf["geometry"].bounds)
        print(self.boarder_index)

        # possible_matches_index = [count for count, cell in diagram_gdf.iterrows() if self.boarder_index.intersection(cell["geometry"].bounds)]
        # possible_matches = [
        #     (count, cell)
        #     for count, cell in tqdm.tqdm(diagram_gdf.iterrows())
        #     if self.polygon_index.contains(cell["geometry"].bounds) #0
        #     # if self.addresses_index.contains(cell["geometry"].bounds) #1
        #     # if self.boarder_index.contains(cell["geometry"].bounds) #2 # out of order, still running
        #     # if cell["geometry"].bounds.intersection(self.boarder) #3 # to delete
        #     # if self.boarder_index.crosses(cell["geometry"])
        # ]
        possible_matches = self.boarder_index.intersection(
            np.array([x.bounds for x in diagram_gdf["geometry"]])
        )

        # possible_matches = [(count, cell) for count, cell in diagram_gdf.iterrows() if not self.boarder_index.intersects(cell["geometry"].bounds)]

        # precise_matches = [(count, cell) for count, cell in possible_matches if cell["geometry"].intersects(self.union)]
        starting_size = len(diagram_gdf)
        print(starting_size)

        diagram_filtered = geopandas.GeoDataFrame()
        for count in tqdm.tqdm(possible_matches):
            # for count, cell in tqdm.tqdm(precise_matches):
            cropped_valid = make_valid(
                diagram_gdf.iloc[count].intersection(self.union)
            ).buffer(0)
            assert isinstance(cropped_valid, shapely.geometry.polygon.Polygon)
            # print("cropped_valid", cropped_valid)  # debug

            diagram_gdf.iloc[count] = cropped_valid

        # for count, cell in tqdm.tqdm(possible_matches):
        #     # for count, cell in tqdm.tqdm(precise_matches):
        #     if cropped := cell["geometry"].intersection(self.union):
        #         cropped_valid = make_valid(cropped).buffer(0)
        #         assert isinstance(cropped_valid, shapely.geometry.polygon.Polygon)
        #         # print("cropped_valid", cropped_valid)  # debug

        #         diagram_gdf.iloc[count] = cropped_valid

        # for count in range(len(possible_matches), len(diagram_gdf)):
        #         del diagram_gdf.iloc[count] # remove if not necessary

        # return diagram_gdf
        print(
            "Sizes!: ",
            len(possible_matches),
            len(diagram_filtered),
            len(diagram_gdf),
            "Starting size",
            starting_size,
        )
        return diagram_filtered

        # diagram_clipped = make_valid(diagram).intersection(self.boarder).buffer(0)

        # districts = self.addresses.copy(deep=True)
        # districts["geometry"] = diagram.geoms

        # Option 1
        # districts = []
        # for each_geom in diagram_clipped.geoms:
        #     districts.append({"geometry": each_geom})

        # return geopandas.GeoDataFrame(districts)

        # Option 2
        # return geopandas.GeoDataFrame(diagram_clipped.geoms, columns = ["geometry"])

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
        boarder: str = "boarder",
    ):
        """
        Exports current state to a directory
        """
        if not dirname.endswith("/"):
            dirname += "/"

        for name, each_object in (
            (addresses, self.addresses),
            (polygon, self.polygon),
            # (boarder, self.boarder),
            (diagram, self.diagram),
            ("diagram_filtered", self.diagram_unfiltered),
        ):
            print("Export", name, each_object)  # debug
            try:
                export(each_object, dirname + name)
            except RuntimeError as e:
                print("Error", e)

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
