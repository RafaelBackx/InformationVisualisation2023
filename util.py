import pandas as pd
from pandas_geojson import to_geojson
from shapely.geometry import shape
import shapely
import json
from geopy.geocoders import Nominatim
import zipcodes
from data import abbrev_to_us_state, us_state_to_abbrev

geolocator = Nominatim(user_agent='geoapiExercises')

def filter_map_events(df, filters):
    data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    for filter in filters:
        data = data[data[filter] == filters[filter]]
    return data


def get_events_without_location(df: pd.DataFrame):
    data = df[df['Latitude'].isnull() & df['Longitude'].isnull()]
    return data


def get_gdp_data(df_gdp: pd.DataFrame, df_disaster: pd.DataFrame, years, country):
    columns = years + ['Country Code']
    columns = [str(c) for c in columns]
    year_data = df_gdp[columns]
    data: pd.DataFrame = year_data[year_data['Country Code'] == country]
    data = data[[str(y) for y in years]]
    data = data.transpose()

    data_by_year = df_disaster.groupby(
        'Start Year', as_index=False).sum(numeric_only=True)

    def calculate_gdp_share(row):
        year = row['Start Year']
        col = data.columns[0]
        gdp = data[col][str(int(year))]
        damages = row['Total Damages, Adjusted (\'000 US$)'] * 1000
        return (damages / gdp) * 100

    if (data_by_year.empty):
        data_by_year["share"] = 0
        return data_by_year
    else:
        data_by_year['share'] = data_by_year.apply(calculate_gdp_share, axis=1)
        return data_by_year


def convert_events_to_geojson(df):
    geojson = to_geojson(df=df, lat="Latitude", lon="Longitude", properties=[
                         "Dis No", "Disaster Subgroup"])  # More things can be included in the properties when it's needed
    for event in geojson["features"]:
        event["properties"]["tooltip"] = df[df["Dis No"] ==
                                            event["properties"]["Dis No"]]["Disaster Type"].values[0]
    return geojson


def __get_geojson_data(filename):
    file = open(f'./Data/GeoJson1/{filename}', encoding='utf-8')
    geojson = json.load(file)
    return geojson


def get_world_geojson():
    return __get_geojson_data('countries.json')


def get_country_data(country_code):
    return __get_geojson_data(f'{country_code}.json_opt.json')


def get_property(event, property):
    name = event[property]
    return name if pd.notna(name) else ''


def get_date(event):
    year = event["Start Year"]
    month = event["Start Month"]
    day = event["Start Day"]
    if (pd.isna(month)):
        return f'{int(year)}'
    if (pd.isna(day)):
        return f'{int(year)}-{int(month)}'
    return f'{int(year)}-{int(month)}-{int(day)}'


def get_event(df: pd.DataFrame, event_id):
    event = df[df['Dis No'] == event_id].iloc[0]
    print(f'event: {event}')
    lat = event['Latitude']
    long = event['Longitude']
    if (pd.isna(lat) or pd.isna(long)):
        return event, None
    else:
        return event, [lat, long]


def calculate_center(data):
    shapely_geos = shapely.from_geojson(json.dumps(data))
    center = shapely_geos.centroid
    return center

def lat_long_to_state(lat,long):
    try:
        location = geolocator.reverse(f'{lat}, {long}')
    except:
        return None
    if (not location):
        return None
    address = location.raw['address']
    zip_code = address.get('postcode')
    state = address.get('state')
    if (state):
        return state
    if (not zip_code):
        return None
    abrev = zipcodes.matching(f'{zip_code}')[0]['state']
    return abbrev_to_us_state[abrev]
