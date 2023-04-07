import pandas as pd
from pandas_geojson import to_geojson

def extract_yearly_map_events(df, year):
    data = df[df["Latitude"].notnull() & df["Longitude"].notnull()]
    data = data[data["Start Year"] == year]
    geojson = to_geojson(df=data, lat="Latitude", lon="Longitude", properties=["Dis No"]) # More things can be included in the properties when it's needed
    return geojson