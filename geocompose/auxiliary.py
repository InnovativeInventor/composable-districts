import geopandas
import shapely
import pandas

"""
Auxiliary helper functions
"""


def concat_gdf(*args):
    """
    Concatenates an arbitrary number of GeoDataFrames
    """
    return geopandas.GeoDataFrame(pandas.concat([*args], ignore_index=True))


def find_boarder(object):
    lines = []
    # object = object.bounds
    object_hull = object.convex_hull

    prev_line = object_hull.exterior.coords[-1]
    for each_object in object_hull.exterior.coords:
        lines.append(shapely.geometry.LineString((prev_line, each_object)))
        prev_line = each_object

    return geopandas.GeoDataFrame(lines, columns=["geometry"])


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
                *[x for x in each_iterable if not isinstance(each_iterable, ignores)],
            )


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
