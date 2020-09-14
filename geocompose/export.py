import geopandas


def export(dataframe: geopandas.GeoDataFrame, location: str) -> bool:
    """
    Exports a GeoDataFrame to a folder in various formats the location of the dir does not have to contain a trailing slash
    """
    # print(location)
    success = True
    try:
        dataframe.to_file(location + ".geojson", driver="GeoJSON")
    except ValueError as e:
        success = False
        print("Warning: ", e)
    except AttributeError as e:
        success = False
        print("Warning: ", e)

    try:
        dataframe.to_file(location + ".shp")
    except ValueError as e:
        success = False
        print("Warning: ", e)
    except AttributeError as e:
        success = False
        print("Warning: ", e)

    try:
        dataframe.to_file(location + ".gpkg", layer="diff", driver="GPKG")
    except ValueError as e:
        success = False
        print("Warning: ", e)
    except AttributeError as e:
        success = False
        print("Warning: ", e)

    return success


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
