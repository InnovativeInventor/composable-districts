import geocompose
import pytest


def test_init_cls():
    with pytest.raises(Exception):
        precinct = geocompose.Addresses()

    geocompose.read_files(
        "tests/data/city_of_boston-addresses-city.geojson",
        "data/MA-shapefiles/12_16/MA_precincts_12_16.shp",
    )
