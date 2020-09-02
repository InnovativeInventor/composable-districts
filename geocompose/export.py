import geopandas


def export(dataframe: geopandas.GeoDataFrame, location: str) -> bool:
    """
    Exports a GeoDataFrame to a folder in various formats
    """
    success = True
    try:
        dataframe.to_file(location + ".geojson", driver="GeoJSON")
    except ValueError as e:
        success = False
        print(e)
    except AttributeError as e:
        success = False
        print(e)

    try:
        dataframe.to_file(location + ".shp")
    except ValueError as e:
        success = False
        print(e)
    except AttributeError as e:
        success = False
        print(e)

    try:
        dataframe.to_file(location + ".gpkg", layer="diff", driver="GPKG")
    except ValueError as e:
        success = False
        print(e)
    except AttributeError as e:
        success = False
        print(e)

    return success
