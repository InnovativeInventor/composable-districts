import geocompose


def test_merging_simple():
    r_1 = geocompose.read_files(
        "tests/data/city_of_boston-addresses-city.geojson",
        "data/MA-shapefiles/12_16/MA_precincts12_16.shp",
    )
    r_2 = geocompose.read_files(
        "tests/data/city_of_boston-addresses-city.geojson",
        "data/MA-shapefiles/12_16/MA_precincts12_16.shp",
    )
    assert r_1 + r_2
