import pandas as pd
from pandas_geojson import to_geojson
from shapely.geometry import shape
import shapely
import json
from geopy.geocoders import Nominatim
import zipcodes
from converter import abbrev_to_us_state, us_state_to_abbrev
import matplotlib as mpl

geolocator = Nominatim(user_agent='geoapiExercises')
gdp_disaster_data = pd.read_csv("Data/gdp_data.csv")

def generate_countries_colours():
    years = list(range(1960,2023))
    colour_map = {}
    for year in years:
        df = gdp_disaster_data[gdp_disaster_data['Start Year'] == year].groupby('ISO').sum(numeric_only=True)
        country_names = df.index
        colour_countries = {}
        for country_name in country_names:
            value = df.loc[country_name, "share"]
            colour_countries[country_name] = value
        colour_map[year] = colour_countries        
    return colour_map

def filter_events(df, filters, location_important = False):
    data = df
    if location_important:
        data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    for filter in filters:
        data = data[data[filter] == filters[filter]]
    return data

def get_events_without_location(df: pd.DataFrame):
    data = df[df['Latitude'].isnull() & df['Longitude'].isnull()]
    return data

def get_gdp_data(df_gdp: pd.DataFrame, df_disaster: pd.DataFrame, years, country = None, categories = False):
    columns = years + ['Country Code']
    columns = [str(c) for c in columns]
    gdp_data_filtered = df_gdp[columns]
    if (country):
        gdp_data_reduced = gdp_data_filtered[gdp_data_filtered['Country Code'] == country]
        disaster_columns = ['Start Year', 'ISO']
        if (categories): disaster_columns += ['Disaster Subgroup']
        disaster_data_by_year = df_disaster.groupby(disaster_columns, as_index=False).sum(numeric_only=True)
        disaster_data_by_year = disaster_data_by_year[disaster_data_by_year['ISO'] == country] 
    else:
        disaster_columns = ['Start Year']
        if (categories): disaster_columns += ['Disaster Subgroup']
        gdp_data_reduced = pd.DataFrame([gdp_data_filtered.mean(numeric_only=True)], columns=[str(y) for y in years])
        disaster_data_by_year = df_disaster.groupby(disaster_columns, as_index=False).sum(numeric_only=True)
        disaster_data_by_year['ISO'] = 'WORLD'

    def calculate_gdp_share(row):
        year = str(int(row['Start Year']))
        if (not (year in gdp_data_reduced.columns)):
            return 0
        gdp = gdp_data_reduced[year]
        damages = row["Total Damages, Adjusted ('000 US$)"] * 1000
        return (damages / gdp) * 100

    columns_to_fill = ['Start Year', 'ISO', 'Disaster Subgroup']

    if (disaster_data_by_year.empty):
        disaster_data_by_year["share"] = 0
    else:
        disaster_data_by_year['share'] = disaster_data_by_year.apply(calculate_gdp_share, axis=1)
    
    if categories:
        filled_df = fill_missing_columns_with_default(disaster_data_by_year,columns_to_fill,["Total Damages, Adjusted (\'000 US$)", 'share'],[0,0])
        return filled_df
    return disaster_data_by_year

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
        return f'{int(month)}/{int(year)}'
    return f'{int(day)}/{int(month)}/{int(year)}'

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

def ratio_to_gradient(ratio):
    colour_map = mpl.colormaps['YlOrRd'].resampled(8)
    colour = colour_map(1-ratio)
    colour = [c * 255 for c in colour]
    r,g,b,_ = colour
    colour = '#%02x%02x%02x' % (int(r), int(g), int(b))
    return colour

def fill_missing_columns_with_default(df, columns, columns_to_fill, values):
    copy_df = df.copy()
    unique_columns = [copy_df[col].unique() for col in columns]
    index = pd.MultiIndex.from_product(unique_columns,names=columns)
    new_df = pd.DataFrame(index=index, columns=['count'])
    merged_df = pd.merge(copy_df, new_df, how='right', left_on=columns, right_index=True)
    for idx,col in enumerate(columns_to_fill):
        merged_df[col] = merged_df[col].fillna(values[idx])
    return merged_df

def format_large_number(number, float = True):
    if float:
        return f"{number:,}"
    else:
        return f"{number:,.0f}"
    

def get_state_spending(state, df_properties):
    if (state):
        state_properties = df_properties[(df_properties['state'] == state)]
    else:
        state_properties = df_properties

    state_properties_grouped = state_properties.groupby(['programArea'], as_index=False).sum(numeric_only=True)

    different_programs = ['FMA','HMGP', 'LPDM', 'PDM', 'RFC', 'SRL']
    state_spending_map = {}
    total_spending = 0
    for program in different_programs:
        amount_spent = state_properties_grouped[state_properties_grouped['programArea'] == program]['actualAmountPaid'].values
        if (len(amount_spent) > 0):
            amount_spent = amount_spent[0]
        else:
            amount_spent = 0
        state_spending_map[program] = amount_spent
        total_spending += amount_spent
    state_spending_map['total'] = total_spending

    return state_spending_map

def get_total_spent(df_properties):
    total_properties = df_properties.sum(numeric_only=True)
    total_spent = total_properties['actualAmountPaid']
    return total_spent

def get_total_damages(df_disasters):
    return df_disasters[(df_disasters['ISO'] == 'USA') & (df_disasters['us state'].notna())].sum(numeric_only=True)["Total Damages, Adjusted ('000 US$)"]

def get_total_damages_state(df_disasters, state_name):
    return df_disasters[(df_disasters['ISO'] == 'USA') & (df_disasters['us state'] == state_name)].sum(numeric_only=True)["Total Damages, Adjusted ('000 US$)"]


    
    
   