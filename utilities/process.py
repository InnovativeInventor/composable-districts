import geopandas
import multiprocessing
import tqdm
import functools
import shapely
import itertools
import glob


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

    Credit: R-tree code modified from https://geoffboeing.com/2016/10/r-tree-spatial-index-python/
    """
    addresses_df, addresses_index = addresses
    count, region = input_tuple

    # print("Input", input_tuple)
    # contains = []
    # for point_index, each_point in tqdm.tqdm(
    #     addresses.iterrows(), total=len(addresses)
    # ):
    #     if region["geometry"].contains(each_point["geometry"]):
    #         contains.append(each_point)

    # return count, contains

    if isinstance(region, shapely.geometry.polygon.Polygon):
        geometry = region
    else:
        geometry = region["geometry"]

    possible_matches_index = list(addresses_index.intersection(geometry.bounds))
    possible_matches = addresses_df.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(geometry)]

    return count, " ".join(precise_matches["hash"].tolist())


def fold(shapefile, input_tuple):
    """
    Left fold for shapefile addresses
    """
    count, contains = input_tuple

    print(contains)
    shapefile.at[count, "addresses"] = contains

    return shapefile


unchain = itertools.chain.from_iterable

if __name__ == "__main__":

    states = glob.glob("*-shapefiles/")
    for each_state in states:
        shapefiles = glob.glob(each_state + "*/*.shp")
        state = each_state.split("-")[0].lower()
        for each_shapefile in shapefiles:
            print("Using", each_shapefile)

            addresses = geopandas.read_file(
                "data/openaddresses/us/{state}/statewide-addresses-state.geojson".format(
                    state=state
                )
            )
            shapefile = geopandas.read_file(each_shapefile)
            shapefile["addresses"] = [[]] * len(shapefile)

            decompose_addresses_state = functools.partial(
                decompose_addresses, (addresses, addresses.sindex)
            )

            # print(shapefile)
            print("Loaded", each_shapefile)

            # No multiprocessing
            for count, each_district in tqdm.tqdm(
                shapefile.iterrows(), total=len(shapefile)
            ):
                each_district["addresses"] = []

                count, contains = decompose_addresses_state((count, each_district))
                shapefile.at[count, "addresses"] = contains

            filename = each_shapefile.split("/")[-1].split(".")[0]
            try:
                shapefile.to_file(
                    "processed/{state}/{filename}.geojson".format(
                        filename=filename, state=state
                    ),
                    driver="GeoJSON",
                )
            except ValueError as e:
                print(e)

            try:
                shapefile.to_file(
                    "processed/{state}/{filename}.shp".format(
                        filename=filename, state=state
                    )
                )
            except ValueError as e:
                print(e)

            try:
                shapefile.to_file(
                    "processed/{state}/{filename}.gpkg".format(
                        filename=filename, state=state
                    ),
                    layer="districts",
                    driver="GPKG",
                )
            except ValueError as e:
                print(e)

            # print("Starting multiprocessing with", process_count, "processes")

            # with multiprocessing.Pool(process_count) as p:
            #     shapefile = functools.reduce(
            #         fold,
            #         tqdm.tqdm(
            #             p.map(
            #                 decompose_addresses_ma,
            #                 tqdm.tqdm(ma_shapefile.iterrows(), total=len(ma_shapefile)),
            #                 # 10,
            #             ),
            #         ),
            #         # tqdm.tqdm(
            #         #     p.imap(decompose_addresses_ma, ma_shapefile.iterrows()),
            #         #     total=len(ma_shapefile),
            #         # ),
            #         ma_shapefile,
            #     )

            #     print(shapefile)

            # shapefile.to_file("shapefile.geojson", driver='GeoJSON')
