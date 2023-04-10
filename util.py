import pandas as pd
from pandas_geojson import to_geojson
from shapely.geometry import shape
import json

def filter_map_events(df, filters):
    data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    for filter in filters:
        data = data[data[filter] == filters[filter]]
    return data

def get_gdp_data(df,years,country):
    columns = years + ['Country Code']
    columns = [str(c) for c in columns]
    year_data = df[columns]
    data : pd.DataFrame = year_data[year_data['Country Code'] == country]
    data = data[[str(y) for y in years]]
    return data.transpose().values.flatten()


def convert_events_to_geojson(df):
    geojson = to_geojson(df=df, lat="Latitude", lon="Longitude", properties=["Dis No", "Disaster Subgroup"]) # More things can be included in the properties when it's needed
    return geojson

def __get_geojson_data(filename):
    file = open(f'./Data/GeoJson1/{filename}', encoding='utf-8')
    geojson = json.load(file)
    return geojson

def get_world_geojson():
    return __get_geojson_data('countries.json')
def get_country_data(country_code):
    return __get_geojson_data(f'{country_code}.json')