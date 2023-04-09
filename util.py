import pandas as pd
from pandas_geojson import to_geojson
from shapely.geometry import shape
import geobuf
import json

def filter_map_events(df, filters):
    data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    for filter in filters:
        data = data[data[filter] == filters[filter]]
    geojson = to_geojson(df=data, lat="Latitude", lon="Longitude", properties=["Dis No", "Disaster Subgroup"]) # More things can be included in the properties when it's needed
    return geojson

def __get_geojson_data(filename):
    file = open(f'./Data/GeoJson1/{filename}', encoding='utf-8')
    geojson = json.load(file)
    return geojson

# def __get_geojson_data(filename):
#     file = open(f'./Data/GeoJson/{filename}', 'rb')
#     json = geobuf.decode(file.read())
#     return json


def get_world_geojson():
    return __get_geojson_data('countries.json')
def get_country_data(country_code):
    return __get_geojson_data(f'{country_code}.json')