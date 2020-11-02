import geocompose
import time
import os

"""
TODO: move this to tests/
"""

directory = "processed/export-test/" + str(int(time.time()))
os.mkdir(directory)
print(directory)

representation = geocompose.read_files(
    "data/openaddresses/us/ma/statewide-addresses-state.geojson",
    "data/MA-shapefiles/12_16/MA_precincts12_16.shp",
    generate=True,
)

print("Loaded")

# representation.export_dir("../processed/export-example/")
print(directory)
representation.export_dir(directory)
