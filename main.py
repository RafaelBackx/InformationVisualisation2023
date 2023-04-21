from dash import Dash, html, Input, Output, dcc, State, ALL, dash
from dash_extensions.javascript import arrow_function, assign, Namespace
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import math
import pandas as pd
import plotly.express as px
import util
from data import abbrev_to_us_state
import colorsys

ns = Namespace("dashExtensions", "default")

df_properties = pd.read_json('./Data/preprocessed-fema-properties.json')
df_projects = pd.read_json('./Data/preprocessed-fema-projects.json')

df_disasters = pd.read_csv('./Data/Preprocessed-Natural-Disasters.csv', delimiter=';')
df_disasters_us = util.filter_map_events(df_disasters, {'ISO': 'USA'})
# df_disasters_us = util.filter_map_events(df_disasters_us, {'Disaster Subgroup': 'Hydrological'})
df_disasters_us_states = df_disasters_us.groupby(['Start Year', 'us state'], as_index=False).sum(numeric_only=True)


# states = df_properties[df_properties['programArea'] == 'FMA']
states = df_properties.groupby(['programFy', 'state'], as_index=False).sum(numeric_only=True)

app = Dash(__name__)

map = dl.Map(
    maxBounds=[[-90, -180], [90, 180]],
    maxBoundsViscosity=1.0,
    maxZoom=18,
    minZoom=2,
    zoom=10,
    center=(40.5545549008774, -102.17859725490524),
    bounceAtZoomLimits=True,
    children=[
        dl.TileLayer(),
        # https://datahub.io/core/geo-countries#resource-countries
        dl.GeoJSON(
            data=util.get_country_data('USA'),
            id="countries",
            # Invisible polygons,
            options=dict(style = ns('draw_polygon')),
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
    ],
    style={"width": "100%", "height": "90%", "display": "block"},
    id="map")

slider = dcc.Slider(min=1960,
                          max=2023,
                          step=1,
                          value=2000,
                          marks=None,
                          tooltip={"placement": "bottom",
                                   "always_visible": True},
                          id="slider",
                          className="slider")


app.layout = html.Div([
    html.H1("USA test"),
    map,
    slider
    # dcc.Graph(figure=px.line(states,'programFy', 'actualAmountPaid', color='state')),
    # dcc.Graph(figure=px.line(df_disasters_us_states, 'Start Year', 'Total Damages, Adjusted (\'000 US$)', color='us state'))
],style={'width': '100vw', 'height': '100vh'})

@app.callback(Output('countries', 'hideout'), Input('slider','value'), State('countries', 'data'))
def slider_callback(value, data):
    spent = states[states['programFy'] == value]
    costs = df_disasters_us_states[df_disasters_us_states['Start Year'] <= value]

    features = data['features']
    state_iso_original = [feature['properties']['ISO_1'] for feature in features]
    state_iso = [name.split('-')[1] for name in state_iso_original]
    state_names = [abbrev_to_us_state[abbrev] for abbrev in state_iso]

    state_map = {}
    for idx,state in enumerate(state_names):
        id = state_iso_original[idx]
        spent_state = sum(spent[spent['state'] == state]['actualAmountPaid'].values,start=0)
        costs_state = sum(costs[costs['us state'] == state]['Total Damages, Adjusted (\'000 US$)'].values, start=0)

        gradient = 0.5          # neutral, costs == spent
        if (spent_state < costs_state):     # red, this is bad
            ratio = (spent_state/costs_state)/2 # divide by 2 since we have to map between 0 - 0.5 instead of 0 -1
            gradient -= ratio 
        elif (spent_state > costs_state):   # green, this is good
            ratio = (costs_state/spent_state)/2 # divide by 2 since we have to map between 0 - 0.5 instead of 0 -1
            gradient -= ratio
        gradient *= 100

        h = math.floor((100 - gradient) * 120 / 100)
        s = abs(gradient - 50) / 50
        v = 1
        r,g,b = colorsys.hsv_to_rgb(h,s,v)
        colour = '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
        state_map[id] = colour

    print(state_map)
    return state_map

if __name__ == "__main__":
    app.run_server(debug=True)