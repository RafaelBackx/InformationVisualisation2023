import pandas as pd
from pandas_geojson import to_geojson
from shapely.geometry import shape
import json

def filter_map_events(df, filters):
    data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    for filter in filters:
        data = data[data[filter] == filters[filter]]
    return data

def get_gdp_data(df_gdp : pd.DataFrame,df_disaster : pd.DataFrame,years,country):
    columns = years + ['Country Code']
    columns = [str(c) for c in columns]
    year_data = df_gdp[columns]
    data : pd.DataFrame = year_data[year_data['Country Code'] == country]
    data = data[[str(y) for y in years]]
    data = data.transpose()

    data_by_year = df_disaster.groupby('Start Year', as_index=False).sum(numeric_only=True)

    def calculate_gdp_share(row):
        year = row['Start Year']
        col = data.columns[0]
        gdp = data[col][str(int(year))]
        damages = row['Total Damages, Adjusted (\'000 US$)'] * 1000
        return (damages / gdp) * 100
    
    data_by_year['share'] = data_by_year.apply(calculate_gdp_share,axis=1)
    return data_by_year



def convert_events_to_geojson(df):
    geojson = to_geojson(df=df, lat="Latitude", lon="Longitude", properties=["Dis No", "Disaster Subgroup"]) # More things can be included in the properties when it's needed
    for event in geojson["features"]:
        event["properties"]["tooltip"] = df[df["Dis No"] == event["properties"]["Dis No"]]["Disaster Type"].values[0]
    return geojson

def __get_geojson_data(filename):
    file = open(f'./Data/GeoJson1/{filename}', encoding='utf-8')
    geojson = json.load(file)
    return geojson

def get_world_geojson():
    return __get_geojson_data('countries.json')
def get_country_data(country_code):
    return __get_geojson_data(f'{country_code}.json')