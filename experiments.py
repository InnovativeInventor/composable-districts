import geopandas
import multiprocessing
import tqdm
import functools
import itertools


def load():
    """
    Loads MA shapefile and address database
    """
    ma_addresses = geopandas.read_file(
        "data/openaddresses/us/ma/statewide-addresses-state.geojson"
    )
    ma_shapefile = geopandas.read_file("MA-shapefiles/12_16/MA_precincts_12_16.shp")
    return ma_addresses, ma_shapefile


def decompose_addresses(addresses, input_tuple):
    """
    Decomposes a geographical region into a list of addresses
    TODO: Maybe turn this into an iterable?
    """
    count, region = input_tuple
    print("Input", input_tuple)

    contains = []
    for point_index, each_point in tqdm.tqdm(
        addresses.iterrows(), total=len(addresses)
    ):
        if region["geometry"].contains(each_point["geometry"]):
            contains.append(each_point)

    return count, contains


def fold(shapefile, input_tuple):
    """
    Left fold for shapefile addresses
    """
    count, contains = input_tuple
    shapefile.set_value(count, "addresses", contains)

    return shapefile


unchain = itertools.chain.from_iterable

if __name__ == "__main__":
    process_count = 6

    ma_addresses = geopandas.read_file(
        "data/openaddresses/us/ma/statewide-addresses-state.geojson"
    )
    ma_shapefile = geopandas.read_file("MA-shapefiles/12_16/MA_precincts_12_16.shp")

    decompose_addresses_ma = functools.partial(decompose_addresses, ma_addresses)

    print(ma_shapefile)
    print("Loaded")

    print("Starting multiprocessing with", process_count, "processes")

    with multiprocessing.Pool(process_count) as p:
        shapefile = functools.reduce(
            fold,
            # p.map(decompose_addresses_ma,
            #        tqdm.tqdm(ma_shapefile.iterrows(), total=len(ma_shapefile))),
            tqdm.tqdm(
                p.imap(decompose_addresses_ma, ma_shapefile.iterrows()),
                total=len(ma_shapefile),
            ),
            ma_shapefile,
        )

    print(shapefile)

    # for district_index, each_district in tqdm.tqdm(ma_shapefile.iterrows(), total=len(ma_shapefile)):
    #     each_district["addresses"] = []

    #     # drop_points = [] # points to drop
    #     for point_index, each_point in tqdm.tqdm(ma_addresses.iterrows(), total=len(ma_addresses)):
    #         # print(each_district)
    #         if each_district["geometry"].contains(each_point["geometry"]):
    #             print("True")
    #             each_district["addresses"].append(each_point)
    #             # drop_points.append(point_index)
    #     # ma = ma.drop(labels=drop_points)
    #     # assert len(ma) < size
