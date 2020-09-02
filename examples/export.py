import geocompose

"""
TODO: move this to tests/
"""

representation = geocompose.read_files(
    "../data/openaddresses/us/ma/statewide-addresses-state.geojson",
    "../data/MA-shapefiles/12_16/MA_precincts12_16.shp",
)

print("Loaded")

representation.export_dir("../processed/export-example/")
