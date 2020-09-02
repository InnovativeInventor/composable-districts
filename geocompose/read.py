import geopandas
from typing import Tuple
from geocompose.definitions import Addresses


def import_file(filename: str, *args, **kwargs) -> geopandas.GeoDataFrame:
    file_obj = geopandas.read_file(filename, *args, **kwargs)
    return file_obj


def read_files(shapefile: str, addressfile: str, *args, **kwargs) -> Addresses:
    return Addresses(import_file(shapefile), import_file(addressfile), *args, **kwargs)
