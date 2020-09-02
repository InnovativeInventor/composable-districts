import itertools
import os
import sys

import geopandas
import pandas as pd
import shapely
import tqdm

# from process import decompose_addresses

"""
A simple diff utility on the address-based representation of precincts.

Usage:
python3 diff.py [new] [old]
"""

# addresses = geopandas.read_file(
#     "data/openaddresses/us/{state}/statewide-addresses-state.geojson".format(state="ma")
# )
# addresses_index = addresses.sindex


# def contains_addresses(iterable):
#     for x in iterable:
#         if decompose_addresses((addresses, addresses_index), (0, x))[1].rstrip():
#             yield x


def chain_until(typeclass, ignores, *iterables):
    """
    Flattens/chains iterables recursively until it becomes a certain type. Optionally ignores particular types.
    """
    for each_iterable in iterables:
        if isinstance(each_iterable, typeclass):
            yield each_iterable
        elif not isinstance(each_iterable, ignores):
            # breakpoint()
            return chain_until(
                typeclass,
                ignores,
                *[x for x in each_iterable if not isinstance(each_iterable, ignores)]
            )


def calculate_diffs(shapefile_1, shapefile_2):
    shapefile_diff = geopandas.GeoDataFrame()
    # add_shapefile = geopandas.GeoDataFrame()
    # sub_shapefile = geopandas.GeoDataFrame()

    shapefile_2_index = shapefile_2.sindex

    for count, each_precinct_1 in tqdm.tqdm(
        shapefile_1.iterrows(), total=len(shapefile_1)
    ):
        # addition, subtraction = find_intersect(shapefile_2, shapefile_2_index, each_precinct_1)
        # addition_df = geopandas.GeoDataFrame(list(addition))
        # subtraction_df = geopandas.GeoDataFrame(list(subtraction))

        difference = find_intersect(shapefile_2, shapefile_2_index, each_precinct_1)
        diff_df = geopandas.GeoDataFrame(list(difference))
        # Alternate ways
        # diff_shapefile = diff_shapefile.append(intersection, ignore_index=True)
        # add_shapefile = geopandas.GeoDataFrame(pd.concat([add_shapefile, addition_df], ignore_index=True))
        # sub_shapefile = geopandas.GeoDataFrame(pd.concat([sub_shapefile, subtraction_df], ignore_index=True))
        shapefile_diff = geopandas.GeoDataFrame(
            pd.concat([shapefile_diff, diff_df], ignore_index=True)
        )

    # return add_shapefile, sub_shapefile
    return shapefile_diff


def find_intersect(shapefile_2, shapefile_2_index, each_precinct_1):
    addresses_1 = set(each_precinct_1["addresses"].split())

    possible_matches_index = list(
        shapefile_2_index.intersection(each_precinct_1["geometry"].bounds)
    )
    possible_matches = shapefile_2.iloc[possible_matches_index]
    precise_matches = possible_matches[
        possible_matches.intersects(each_precinct_1["geometry"])
    ]

    for count, each_precinct_2 in precise_matches.iterrows():
        try:
            addresses_2 = set(each_precinct_2["addresses"].split())
        except:
            print(each_precinct_2)

        address_difference = addresses_1 - addresses_2
        if address_difference:
            try:
                intersection = each_precinct_1["geometry"].intersection(
                    each_precinct_2["geometry"]
                )

                if each_precinct_1["geometry"].contains(each_precinct_2["geometry"]):
                    intersection = each_precinct_1["geometry"].symmetric_difference(
                        each_precinct_2["geometry"]
                    )
                elif each_precinct_2["geometry"].contains(each_precinct_1["geometry"]):
                    intersection = each_precinct_1["geometry"].symmetric_difference(
                        each_precinct_2["geometry"]
                    )
                elif (
                    intersection.area > each_precinct_1["geometry"].area * 0.5
                ):  # could use addresses as a heuristic instead
                    # this happens when there are two nearly identical districts and we just want to get the extras as opposed to the intersection
                    intersection = each_precinct_1["geometry"].symmetric_difference(
                        each_precinct_2["geometry"]
                    )

                row = each_precinct_1.to_dict()
                row["diff_address"] = " ".join(address_difference)
                # row["current_geometry"] = each_precinct_1["geometry"] # is this the source of the write to disk errors?
                # row["original_geometry"] = each_precinct_2["geometry"]

                # # Slower method, not necessary but could be useful in theory
                # for each_polygon in contains_addresses(
                #     chain_until(
                #         shapely.geometry.polygon.Polygon,
                #         (
                #             shapely.geometry.point.Point,
                #             shapely.geometry.linestring.LineString,
                #         ),
                #         intersection,
                #     )
                # ):
                for each_polygon in chain_until(
                    shapely.geometry.polygon.Polygon,
                    (
                        shapely.geometry.point.Point,
                        shapely.geometry.linestring.LineString,
                    ),
                    intersection,
                ):
                    # for each_polygon in chain_until(shapely.geometry.polygon.Polygon,() , intersection):
                    assert isinstance(
                        each_polygon, shapely.geometry.polygon.Polygon
                    )  # otherwise there is a problem with writing to disk
                    row["geometry"] = each_polygon
                    yield geopandas.GeoSeries(row)

            except shapely.errors.TopologicalError as e:
                print("WARNING", e)


if __name__ == "__main__":
    """
    The first arg is the most recent one
    """
    shapefile_1_loc = sys.argv[1]
    shapefile_2_loc = sys.argv[2]
    if os.path.isfile(shapefile_1_loc) and os.path.isfile(shapefile_2_loc):
        print("Calculating diff of", shapefile_1_loc, shapefile_2_loc)
        shapefile_1 = geopandas.read_file(shapefile_1_loc)
        shapefile_2 = geopandas.read_file(shapefile_2_loc)

        print("Loaded")

        shapefile_diff = calculate_diffs(shapefile_1, shapefile_2)

        print(shapefile_diff)
        print(shapefile_diff.columns)

        try:
            shapefile_diff.to_file("diff.geojson", driver="GeoJSON")
        except ValueError as e:
            print(e)
        except AttributeError as e:
            print(e)

        try:
            shapefile_diff.to_file("diff.shp")
        except ValueError as e:
            print(e)
        except AttributeError as e:
            print(e)

        try:
            shapefile_diff.to_file("diff.gpkg", layer="diff", driver="GPKG")
        except ValueError as e:
            print(e)
        except AttributeError as e:
            print(e)

    else:
        raise FileNotFoundError
