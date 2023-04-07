import plotly.express as px
import pandas as pd
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash import Dash, html, dcc, Input, Output
from pandas_geojson import to_geojson

disaster_data = pd.read_csv("../Data/Preprocessed-Natural-Disasters.csv", delimiter=";")
map_data = disaster_data[disaster_data["Latitude"].notnull() & disaster_data["Longitude"].notnull()]
map_data = map_data[disaster_data["Start Year"] == 2000]
events_geojson = to_geojson(df=map_data, lat="Latitude", lon="Longitude", properties=["Dis No"])

app = Dash(__name__)

map = dl.Map(maxBounds=[[-90,-180],[90,180]], maxBoundsViscosity=1.0, maxZoom=18, minZoom=2, bounceAtZoomLimits=True, children=[
    dl.TileLayer(), 
    # https://datahub.io/core/geo-countries#resource-countries
    dl.GeoJSON(url="https://pkgstore.datahub.io/core/geo-countries/countries/archive/23f420f929e0e09c39d916b8aaa166fb/countries.geojson", id="countries", options={"style": {"color": "transparent"}}),
    dl.GeoJSON(data=events_geojson, id="events")],
    style={"width": "100%", "height": "700px", "margin": "auto", "display": "block"}, id="map")

app.layout = html.Div([map, html.Div(id="country"), html.Div(id="event")])

@app.callback(Output("country", "children"), [Input("countries", "click_feature")])
def country_click(feature):
    if feature is not None:
       return feature["properties"]["ADMIN"]
    
@app.callback(Output("event", "children"), [Input("events", "click_feature")])
def country_click(feature):
    if feature is not None:
       event = map_data[map_data["Dis No"] == feature["properties"]["Dis No"]]
       return event.to_string()

if __name__ == "__main__":
    app.run_server(debug=True)