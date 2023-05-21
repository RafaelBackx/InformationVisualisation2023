import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import dash
from dash import Dash, html, Input, Output, dcc, State, ALL, dash
from dash_extensions.javascript import arrow_function, Namespace
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
from flask import Flask
import plotly.express as px
import dash_leaflet.express as dlx
import json

import util
import components
import callbacks

from time import sleep
import converter as state_converter

import us_layout
import home_layout

# Colormap for graphs
EVENT_COLOURS = {
    "Meteorological": "#ABA4A4",
    "Geophysical": "#C95B20",
    "Hydrological": "#0EB7E3",
    "Climatological": "#FFEE00"
}

DISASTER_SUBGROUPS = [
    "Geophysical",
    "Hydrological",
    "Climatological",
    "Meteorological"
]

ns = Namespace("dashExtensions", "default")

current_state = None
disaster_data = pd.read_csv("Data/Preprocessed-Natural-Disasters.csv", delimiter=";")
gdp_data = pd.read_csv('./Data/gdp_data.csv')
df_properties = pd.read_json('./Data/preprocessed-fema-properties.json')
df_projects = pd.read_json('./Data/preprocessed-fema-projects.json')



# fig = px.scatter(
#     data_frame=disaster_data,
#     x='Longitude',
#     y='Latitude',
#     color='Disaster Type',
#     hover_data=['Country', 'Disaster Type']
# )

# fig.update_layout(
#     title_text='Natural Disasters by Location',
#     margin=dict(l=0, r=0, t=30, b=0)
# )

server = Flask("Natural Disasters Dashboard")
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, prevent_initial_callbacks='initial_duplicate')
server=app.server




################
#              #
#  COMPONENTS  #
#              #
################

tabs = dbc.Tabs(
    children=[
        dbc.Tab(label="Home", tab_id="home"),
        dbc.Tab(label="U.S. Preventions", tab_id="us-prevention")
    ],
    id="tabs",
    active_tab="home")

############
#          #
#  LAYOUT  #
#          #
############

geojson = dl.GeoJSON(data=util.get_world_geojson())

app.layout = html.Div(
    children=[
        tabs,
        html.Div(id="content"),
        html.Div(id="popup")
        # dcc.Graph(figure=fig)  # Add the scatter plot as a dcc.Graph component
    ]
)

###############
#             #
#  CALLBACKS  #
#             #
###############

# Callback for navigating through the main tabs
@app.callback(Output("content", "children"), 
              Input("tabs", "active_tab"))
def navigate_tabs(active_tab):
    if active_tab == "home":
        return home_layout.home_layout
    elif active_tab == "us-prevention":
        return us_layout.us_layout

# Callback that disables the dragging of the map when hovering over the slider container, to prevent dragging the map when dragging the slider
@app.callback(Output("map", "dragging"), 
              Input("world-slider-wrapper", "n_events"), 
              State("world-slider-wrapper", "event"))
def hover_slider(n_events, e):
    if e is not None:
        if e["type"] == "mouseover":
            return False
        elif e["type"] == "mouseout":
            return True
    else:
        return True

# Callback to animate the slider on the main page
@app.callback(Output('animation-interval', 'disabled'),
              Input('world-animation-button', 'n_clicks'),
              State('animation-interval', 'disabled'),
              prevent_initial_call=True)
def animate_slider(n_clicks, animation_status):
    return not animation_status

# Callback to update the value of the slider on the main page
@app.callback(Output('world-year-slider', 'value'),
              Input('animation-interval', 'n_intervals'),
              [State('world-year-slider', 'value'),
               State('world-year-slider', 'max'),
               State('world-year-slider', 'min')],
               prevent_initial_call=True)
def update_slider(_n_clicks, current_slider_value, max, min):
    if (current_slider_value < max):
        return current_slider_value + 1
    else:
        # or min if we want replay, maybe second button to allow for loops ?
        return current_slider_value

# Callback to handle a value change of the slider on the main page
@app.callback(Output('events', 'data'),
              Output('world-gdp-graph', 'figure'),
              Output('world-affected-graph', 'figure'),
              Output("world-aggregated-data", "children"),
              Output('countries', 'hideout'),
              Input('world-year-slider', 'value'),
              [State("world-affected-tabs", 'active_tab'),
               State('world-gdp-tabs', 'active_tab'),
               State('countries', 'hideout')])
def worldwide_slider_change(current_year, affected_filter, gdp_filter, old_hideout):
    return callbacks.slider_change(disaster_data, gdp_data, current_year, affected_filter, gdp_filter, old_hideout=old_hideout)

# Callback to handle switching preferences for the gdp graph on the main page
@app.callback(Output('world-gdp-graph', 'figure', allow_duplicate=True),
              Input('world-gdp-tabs', 'active_tab'),
              State('world-year-slider', 'value'),
              prevent_initial_call=True)
def worldwide_gdp_switch(active_tab, current_year):
    return callbacks.changed_gdp_filter(gdp_data, current_year, None, active_tab != 'general')

# Callback to handle switching preferences for the affected graph on the mmain page
@app.callback(Output('world-affected-graph', 'figure', allow_duplicate=True),
              Input('world-affected-tabs', 'active_tab'),
              State('world-year-slider', 'value'),
              prevent_initial_call=True)
def worldwide_affected_switch(active_tab, current_year):
    return callbacks.changed_affected_filter(disaster_data, current_year, active_tab)

# Callback to show the overlay with all the events for the world
@app.callback(Output("world-events-accordion", "children"), 
              Output("world-offcanvas", "is_open"), 
              Input("world-show-events", "n_clicks"), 
              [State("world-offcanvas", "is_open"), 
               State('world-year-slider', 'value')])
def world_show_events(n_clicks, io, current_year):
    if n_clicks:
        is_open = not io
    else:
        is_open = io
    return callbacks.show_events_button_clicked(disaster_data, current_year), is_open

# Callback to toggle the popup
@app.callback(Output("popup", "children"), [Input('countries', 'n_clicks')], [State("countries", "click_feature"), State("world-year-slider", "value")], prevent_initial_call=True)
def country_click(_n_clicks, feature, current_year):
    if feature is not None:
        return components.generate_country_popup(disaster_data, feature, current_year)

# Callback to animate the slider on the popup
@app.callback(Output('country-animation-interval', 'disabled'),
              Input('country-animation-button', 'n_clicks'),
              State('country-animation-interval', 'disabled'),
              prevent_initial_call=True)
def animate_country_slider(n_clicks, animation_status):
    return not animation_status

# Callback to update the value of the slider on the popup
@app.callback(Output('country-year-slider', 'value'),
              Input('country-animation-interval', 'n_intervals'),
              [State('country-year-slider', 'value'),
               State('country-year-slider', 'max'),
               State('country-year-slider', 'min')],
               prevent_initial_call=True)
def update_country_slider(_n_clicks, current_slider_value, max, min):
    if (current_slider_value < max):
        return current_slider_value + 1
    else:
        # or min if we want replay, maybe second button to allow for loops ?
        return current_slider_value

# Callback to handle a value change of the slider on the popup
@app.callback(Output('country-events', 'data'),
              Output('country-gdp-graph', 'figure'),
              Output('country-affected-graph', 'figure'),
              Output("country-aggregated-data", "children"),
              Input('country-year-slider', 'value'),
              [State('country-affected-tabs', 'active_tab'),
               State("country-gdp-tabs", "active_tab"),
               State("countries", "click_feature")])
def country_slider_change(current_year, affected_filter, gdp_filter, country):
    country_code = country["properties"]["ISO_A3"]
    return callbacks.slider_change(disaster_data, gdp_data, current_year, affected_filter, gdp_filter, country_code=country_code)

# Callback to handle switching preferences for the gdp graph on the popup
@app.callback(Output('country-gdp-graph', 'figure', allow_duplicate=True),
              Input('country-gdp-tabs', 'active_tab'),
              [State('country-year-slider', 'value'),
               State("countries", "click_feature")],
              prevent_initial_call=True)
def country_gdp_switch(active_tab, current_year, country):
    country_code = country["properties"]["ISO_A3"]
    return callbacks.changed_gdp_filter(gdp_data, current_year, country_code, active_tab != 'general')

# Callback to handle switching preferences for the affected graph on the popup
@app.callback(Output('country-affected-graph', 'figure', allow_duplicate=True),
              Input('country-affected-tabs', 'active_tab'),
              [State('country-year-slider', 'value'),
               State("countries", "click_feature")],
              prevent_initial_call=True)
def country_affected_switch(active_tab, current_year, country):
    country_code = country["properties"]["ISO_A3"]
    return callbacks.changed_affected_filter(disaster_data, current_year, active_tab, country_code)

# Callback to show the overlay with all the events for a specific country
@app.callback(Output("country-events-accordion", "children"), 
              Output("country-offcanvas", "is_open"), 
              Input("country-show-events", "n_clicks"), 
              [State("country-offcanvas", "is_open"), 
               State("country-year-slider", "value"), 
               State("countries", "click_feature")])
def country_show_events(n_clicks, io, current_year, country):
    if n_clicks:
        is_open = not io
    else:
        is_open = io
    country_code = country["properties"]["ISO_A3"]
    return callbacks.show_events_button_clicked(disaster_data, current_year, country_code), is_open

@app.callback(Output('usa-states', 'hideout'),
              Input('usa-states', 'click_feature'), 
              State('usa-states', 'hideout'), prevent_initial_call=True)
def update_aggregated_data_on_state_click(clicked_state,  hideout):
    global current_state
    state_name = clicked_state['properties']['ISO_1']
    hideout['active_state'] = state_name
    current_state = state_name
    return hideout

@app.callback([Output('us-cost-distribution-subgroups', 'children', allow_duplicate=True), Output('us-cost-distribution-mitigations', 'children'), Output('usa-states', 'click_feature'), Output('usa-states', 'hideout', allow_duplicate=True)], Input('usa-states','n_clicks'), State('usa-states', 'click_feature'), State('usa-states', 'hideout'),prevent_initial_call='initial_duplicate')
def update_usa_states_aggregated_data_on_click(_n_clicks,state_info,hideout):
    global current_state
    current_feature = state_info
    if (state_info):
        state_name = state_info['properties']['NAME_1']
    else:
        state_name = None
    if state_info and current_state == state_info['properties']['ISO_1']:
        current_state = None
        state_name = None
        current_feature = None
        hideout['active_state'] = ''

    cost_distributions = callbacks.create_cost_distributions_for_state(state_name)
    return cost_distributions[0], cost_distributions[1], current_feature, hideout

@app.callback(Output("info", "children"), [Input("usa-states", "hover_feature")])
def info_hover(feature):
    return callbacks.state_hover(feature, df_properties)

@app.callback(Output("info_countries", "children", allow_duplicate=True), [Input("countries", "hover_feature")])
def info_map(feature):
    return callbacks.country_hover(feature, gdp_data)


if __name__ == "__main__":
    app.run_server(debug=True)