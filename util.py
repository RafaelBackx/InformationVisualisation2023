import pandas as pd
from pandas_geojson import to_geojson
from shapely.geometry import shape
import geopandas
import json

def extract_yearly_map_events(df, year):
    data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    data = data[data["Start Year"] == year]
    geojson = to_geojson(df=data, lat="Latitude", lon="Longitude", properties=["Dis No"]) # More things can be included in the properties when it's needed
    return geojson

def __get_geojson_data(filename):
    file = open(f'./Data/GeoJson/{filename}', encoding='utf-8')
    geojson = json.load(file)
    return geojson


def get_world_geojson():
    return __get_geojson_data('countries.json')
def get_country_data(country_code):
    return __get_geojson_data(f'{country_code}.json')