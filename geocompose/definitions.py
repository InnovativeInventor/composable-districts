from typing import Set, Iterable, Optional
from pydantic import BaseModel, validator, ValidationError
import shapely.geometry

# from postal.expand import expand_address as normalize
from postal.normalize import normalize_string as normalize
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
    count, address = input_tuple
    return parse_address(address["name"])


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

    def __add__(self, other):
        raise NotImplementedError
        return AddressDataFrame()

    def generate_diagram(self):
        raise NotImplementedError

    @staticmethod
    def merge_addresses(
        addresses_1: geopandas.GeoDataFrame, addresses_2: geopandas.GeoDataFrame
    ):
        labels, values = unzip(map(addresses_1.iterrows(), address_map))
        results_1 = near_dupe_hashes(labels, values, languages=("en"))

        labels, values = unzip(map(addresses_2.iterrows(), address_map))
        results_2 = near_dupe_hashes(labels, values, languages=("en"))
        print(results_1, results_2)
        return results_1 + results_2  # placeholder
