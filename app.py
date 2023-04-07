import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, dcc, State
from dash_extensions.javascript import arrow_function
import random

import util
from server import app, server

disaster_data = pd.read_csv("Data/Preprocessed-Natural-Disasters.csv", delimiter=";")

events_geojson = util.extract_yearly_map_events(disaster_data, 1960)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

################
#              #
#  COMPONENTS  #
#              #
################

map = dl.Map(
        maxBounds=[[-90,-180],[90,180]], 
        maxBoundsViscosity=1.0, 
        maxZoom=18, 
        minZoom=2, 
        bounceAtZoomLimits=True, 
        children=[
            dl.TileLayer(), 
            # https://datahub.io/core/geo-countries#resource-countries
            dl.GeoJSON(
                url="https://pkgstore.datahub.io/core/geo-countries/countries/archive/23f420f929e0e09c39d916b8aaa166fb/countries.geojson", 
                id="countries", 
                options={"style": {"color": "transparent"}}, # Invisible polygons
                hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))), # Gray border on hover (line_thickness, color, line_style)
            dl.GeoJSON(data=events_geojson, id="events"),
            ],
        style={"width": "100%", "height": "700px", "margin": "auto", "display": "block"}, 
        id="map")

world_slider = dcc.Slider(min=1960, 
                          max=2023, 
                          step=1, 
                          value=1960, 
                          marks=None, 
                          tooltip={"placement": "bottom", "always_visible": True},
                          id="world-year-slider")

animation_button = html.Button('play', id='animation-button')
animation_interval = dcc.Interval('animation-interval',interval=1000,disabled=True)

def generate_country_popup(country):
    country_name = country["properties"]["ADMIN"]
    country_iso = country["properties"]["ISO_A3"] # Can be useful to do lookups
    popup = dbc.Modal(
        children=[
            dbc.ModalHeader(dbc.ModalTitle(country_name)),
            dbc.ModalBody("Here should probably be graphs")
        ], 
        id=f"{country}-modal",
        fullscreen=True,
        is_open=True)
    return popup

############
#          #
#  LAYOUT  #
#          #
############

app.layout = html.Div(children=[map, world_slider, animation_button,animation_interval, html.Div(id="popup")])

###############
#             #
#  CALLBACKS  #
#             #
###############

# Open popup when click on country
@app.callback(Output("popup", "children"), [Input("countries", "click_feature")])
def country_click(feature):
    if feature is not None:
       return generate_country_popup(feature)
    
@app.callback(Output('animation-interval', 'disabled'),
              Input('animation-button', 'n_clicks'),
              State('animation-interval','disabled'))
def animate_slider(n_clicks, animation_status):
    print(animation_status)
    return not animation_status

@app.callback(Output('world-year-slider', 'value'),
              Input('animation-interval','n_intervals'),
              State('world-year-slider', 'value'))
def update_slider(_n_clicks, current_slider_value):
    if (current_slider_value < 2023): # fix, add max slider value
        return current_slider_value + 1
    else:
        return current_slider_value

@app.callback(Output('events','data'),
              Input('world-year-slider','value'))
def update_markers(value):
    return util.extract_yearly_map_events(disaster_data,value)
