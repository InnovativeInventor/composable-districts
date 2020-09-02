from typing import Set, Iterable, Optional
from pydantic import BaseModel, validator, ValidationError
import shapely.geometry

# from postal.expand import expand_address as normalize
from postal.normalize import normalize_string as normalize
from geocompose.export import export
from postal.parser import parse_address
from pydantic.dataclasses import dataclass
import geopandas
import pandas
from postal.near_dupe import near_dupe_hashes


def unzip(tuple_iterable):
    """
    Inverse of the Python builtin zip function
    """

    def fst(tuple_iterable):
        for x, _ in tuple_iterable:
            yield x

    def snd(tuple_iterable):
        for _, y in tuple_iterable:
            yield y

    return fst(tuple_iterable), snd(tuple_iterable)


def address_map(input_tuple):
    """
    TODO: Convert to using pandas-native operations and avoid casting to dict
    """
    count, address = input_tuple
    address_dict = address.to_dict()
    del address_dict["hash"]
    del address_dict["geometry"]

    keys = []
    values = []

    for key in address_dict:
        if value := address_dict[key]:
            keys.append(key)
            # print(value)
            values.append(value)

    return keys, values
    # return (address_dict.keys(), address_dict.values())


def concat_gdf(*args):
    """
    Concatenates an arbitrary number of GeoDataFrames
    """
    return geopandas.GeoDataFrame(pandas.concat([*args], ignore_index=True))


def get_geometry(dataframe: geopandas.GeoDataFrame):
    for _, x in dataframe.iterrows():
        yield x["geometry"]


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
    ):
        # self.polygon = geopandas.GeoDataFrame(*args, **kwargs)

        # if addresses:
        #     self.address = geopandas.GeoDataFrame(addresses, columns=["polygon", "name", "location"], geometry="location")
        # else:
        #     self.address = geopandas.GeoDataFrame(columns=["polygon", "name", "location"], geometry="location")

        self.polygon = polygon_given
        self.addresses = addresses_given

        # self.boarders = shapely.ops.unary_union([x["geometry"] for _,x in self.polygon.iterrows()])
        self.boarder = shapely.ops.unary_union(list(get_geometry(self.polygon)))

        self.diagram = self.generate_diagram()

    def __add__(self, other):
        """
        Currently just concatenates the addresses and the polygon GeoDataFrames.
        TODO: Do smart deduplication using merge_addresses.
        """
        return Addresses(
            concat_gdf(self.addresses, other.addresses),
            concat_gdf(self.polygon, other.polygon),
        )

    def generate_diagram(self):
        # return shapely.ops.voronoi_diagram(shapely.geometry.asMultiPoint(list(get_geometry(self.addresses))), envelope=self.boarder)
        return shapely.ops.voronoi_diagram(
            shapely.geometry.MultiPoint(list(get_geometry(self.addresses))),
            envelope=self.boarder,
        )

    def export_dir(self, dirname: str, addresses="addresses", polygon="polygon"):
        """
        Exports current state to a directory
        """
        for name, each_object in ((addresses, self.addresses), (polygon, self.polygon)):
            export(each_object, dirname + name)

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
