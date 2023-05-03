import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, dcc, State, ALL, dash
from dash_extensions.javascript import arrow_function, Namespace
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
import plotly.express as px

import util
import components
import callbacks

from server import app, server
from time import sleep
import converter as state_converter

import us_layout
import home_layout

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

disaster_data = pd.read_csv("Data/Preprocessed-Natural-Disasters.csv", delimiter=";")
gdp_data = pd.read_csv('./Data/gdp_data_constant.csv')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

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

app.layout = html.Div(
    children=[
        tabs,
        html.Div(id="content"),
        html.Div(
            children=[
                html.Div(id="popup"),
            ]
        )
    ]
)

###############
#             #
#  CALLBACKS  #
#             #
###############

@app.callback([Output("map", "dragging")], [Input("world-slider-wrapper", "n_events")], [State("world-slider-wrapper", "event")])
def hover_slider(n_events, e):
    if e is not None:
        if e["type"] == "mouseover":
            return [False]
        elif e["type"] == "mouseout":
            return [True]
    else:
        return [True]

@app.callback([Output("world-events-accordion", "children"), Output("world-offcanvas", "is_open")], [Input("world-show-events", "n_clicks")], [State("world-offcanvas", "is_open"), State('world-year-slider', 'value')])
def world_show_events(n_clicks, io, year):
    if n_clicks:
        is_open = not io
    else:
        is_open = io
    yearly_events = util.filter_events(disaster_data, {"Start Year": year})
    return callbacks.show_events_button_clicked(yearly_events), is_open

@app.callback([Output("country-events-accordion", "children"), Output("country-offcanvas", "is_open")], [Input("country-show-events", "n_clicks")], [State("country-offcanvas", "is_open"), State("country-year-slider", "value"), State("countries", "click_feature")])
def show_events(n_clicks, io, year, country):
    if n_clicks:
        is_open = not io
    else:
        is_open = io
    country_code = country["properties"]["ISO_A3"]
    country_yearly_events = util.filter_events(disaster_data, {"Start Year": year, "ISO": country_code})
    return callbacks.show_events_button_clicked(country_yearly_events), is_open

@app.callback(Output("content", "children"), [Input("tabs", "active_tab")])
def navigate_tabs(active_tab):
    if active_tab == "home":
        return home_layout.home_layout
    elif active_tab == "us-prevention":
        return us_layout.us_layout

@app.callback(Output("popup", "children"), [Input('countries', 'n_clicks')], [State("countries", "click_feature"), State("world-year-slider", "value")], prevent_initial_call=True)
def country_click(_n_clicks, feature, current_year):
    if feature is not None:
        # disable the interval because otherwise it draws on the other map
        return components.generate_country_popup(disaster_data, feature, current_year)

@app.callback(Output('animation-interval', 'disabled'),
              Input('world-animation-button', 'n_clicks'),
              State('animation-interval', 'disabled'), prevent_initial_call=True)
def animate_slider(n_clicks, animation_status):
    return not animation_status

@app.callback(Output('world-year-slider', 'value'),
              Input('animation-interval', 'n_intervals'),
              State('world-year-slider', 'value'),
              State('world-year-slider', 'max'),
              State('world-year-slider', 'min'), prevent_initial_call=True)
def update_slider(_n_clicks, current_slider_value, max, min):
    if (current_slider_value < max):
        return current_slider_value + 1
    else:
        # or min if we want replay, maybe second button to allow for loops ?
        return current_slider_value

@app.callback(Output('events', 'data'),
              Output('world-gdp-graph', 'figure'),
              Output('world-affected-graph', 'figure'),
              Output("world-aggregated-data", "children"),
              [Input('world-year-slider', 'value'),
               Input("world-affected-tabs", 'active_tab'),
               Input("world-gdp-tabs", "active_tab")])
def worldwide_slider_change(current_year, current_toggle, active_tab):
    # Update general map
    map_data = util.filter_events(
        disaster_data, {"Start Year": current_year}, True)

    yearly_data = disaster_data[disaster_data["Start Year"] == current_year]
    year_data = disaster_data[disaster_data["Start Year"] == current_year][[
        "Start Year", "Disaster Subgroup", "Dis No"]]

    affected_data = disaster_data[disaster_data["Start Year"] <= current_year]

    if active_tab == "general":
        gdp_fig = components.generate_gdp_graph(gdp_data, disaster_data, current_year)
    else:
        gdp_fig = components.generate_gdp_graph(gdp_data, disaster_data, current_year, categories=True)

    # Update affected
    affected_fig = components.generate_affected_graph(
        affected_data, current_year, current_toggle)

    aggregated_data = components.generate_aggregated_data_table(yearly_data)

    return util.convert_events_to_geojson(map_data), gdp_fig, affected_fig, aggregated_data

@app.callback([Output('country-events', 'data'),
               Output('country-gdp-graph', 'figure'),
               Output('country-gdp-graph-specific','figure'),
               Output('country-affected-graph', 'figure'),
               Output("country-aggregated-data", "children")],
              [Input('country-year-slider', 'value'),
               Input('country-affected-tabs', 'active_tab')],
              State("countries", "click_feature"))
def country_slider_change(current_year, toggle_value, country):
    print(current_year)
    country_code = country["properties"]["ISO_A3"]

    data = util.filter_events(disaster_data, {'ISO': country_code})

    affected_data = data[data["Start Year"] <= current_year]

    yearly_data = util.filter_events(data, {"Start Year": current_year})

    map_data = util.filter_events(yearly_data, {}, True)

    # update affected graph
    affected_fig = components.generate_affected_graph(
        affected_data, current_year, toggle_value)

    gdp_fig = components.generate_gdp_graph(
        gdp_data, data, current_year, country_code)
    gdp_fig_specific = components.generate_gdp_graph(gdp_data, data, current_year, country_code, True)

    aggregated_data = components.generate_aggregated_data_table(yearly_data)

    return util.convert_events_to_geojson(map_data), gdp_fig, gdp_fig_specific, affected_fig, aggregated_data

@app.callback([Output('usa-states', 'hideout'), Output('us-aggregated-data','children')], Input('usa-slider', 'value'), [State('usa-states', 'data')])
def update_aggregated_data_on_state_click(slider_value,  data):
    colour_map = callbacks.update_map_on_slider_increment(slider_value,data)
    aggregated_data = callbacks.update_aggregated_data_on_slider_increment(slider_value, us_layout.df_properties)

    return colour_map,aggregated_data

@app.callback(Output('fema-disaster-graphs', 'children'), Input('usa-slider', 'value'), prevent_initial_call=True)
def create_fema_disaster_graph(slider_value):
    return callbacks.create_fema_disaster_graph(disaster_data, slider_value)

@app.callback(Output('fema-cost-distribution-tabs', 'children'), Input('usa-slider', 'value'), prevent_initial_call=True)
def create_fema_cost_distributions(slider_value):
    return callbacks.create_fema_cost_distribution(slider_value, ['structureType', 'foundationType'])