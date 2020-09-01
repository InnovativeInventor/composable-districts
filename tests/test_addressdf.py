import geocompose
import pytest


def test_init_cls():
    with pytest.raises(Exception):
        geocompose.Addresses()

    geocompose.read_files(
        "tests/data/city_of_boston-addresses-city.geojson",
        "data/MA-shapefiles/12_16/MA_precincts12_16.shp",
    )
