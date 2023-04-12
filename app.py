import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, dcc, State
from dash_extensions.javascript import arrow_function, assign, Namespace
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
import plotly.express as px
import util
from server import app, server

EVENT_COLOURS = {
    "Meteorological": "#ABA4A4",
    "Geophysical": "#C95B20",
    "Hydrological": "#0EB7E3",
    "Climatological": "#FFEE00"
}

ns = Namespace("dashExtensions", "default")

disaster_data = pd.read_csv("Data/Preprocessed-Natural-Disasters.csv", delimiter=";")
gdp_data = pd.read_csv('./Data/gdp_data_constant.csv')

map_data = util.filter_map_events(disaster_data, {"Start Year": 1960})

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
                data=util.get_world_geojson(),
                id="countries", 
                options={"style": {"color": "transparent"}}, # Invisible polygons,
                zoomToBounds=True,
                hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))), # Gray border on hover (line_thickness, color, line_style)
            dl.GeoJSON(data=util.convert_events_to_geojson(map_data), 
                       id="events",
                       options=dict(pointToLayer=ns("draw_marker"))),
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

animation_button = dbc.Button(children=[
                                    "Play",
                                    DashIconify(
                                        icon="material-symbols:play-arrow-rounded"
                                    )
                                ], 
                                color="success", 
                                class_name="me-1", 
                                id="animation-button")

animation_interval = dcc.Interval('animation-interval',interval=500,disabled=True)

worldwide_events_distribution = dcc.Graph(id="worldwide-events-dist")
worldwide_affected_graph = dcc.Graph(id="worldwide-affected-graph")
worldwide_toggle_buttons = html.Div(children=[
                                        dbc.RadioItems(
                                        id="worldwide-affected-buttons",
                                        style={"display": "flex", "flex-direction": "column"},
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        options=[
                                            {"label": "Deaths", "value": 'deaths'},
                                            {"label": "Injuries", "value": 'injuries'},
                                            {"label": "Homeless", "value": 'homeless'},
                                        ],
                                        value='deaths'),
                                    ], className="radio-group")

def generate_affected_graph(current_year, current_toggle):
    affected_data = disaster_data[disaster_data["Start Year"] <= current_year]
    affected_data = affected_data.groupby(["Start Year", "Disaster Subgroup"], as_index=False).sum(numeric_only=True)
    column_map = {
        'deaths': 'Total Deaths',
        'injuries': 'No Injured',
        'homeless': 'No Homeless'
    }
    column = column_map[current_toggle]
    return px.line(affected_data, "Start Year", column, color="Disaster Subgroup", color_discrete_map=EVENT_COLOURS)

############
#          #
#  LAYOUT  #
#          #
############

app.layout = html.Div(children=[
    dbc.Row(children=[
        dbc.Col(children=[
            map,
            dbc.Row(children=[
                dbc.Col(children=[
                    animation_button
                ], width="auto"),
                dbc.Col(children=[
                    world_slider
                ]),
            ], className="g-0")
        ])
    ]),
    dbc.Row(children=[
        dbc.Col(children=[
            worldwide_events_distribution
        ], width=6),
        dbc.Col(children=[
            dbc.Row(children=[
                dbc.Col(children=[
                    worldwide_affected_graph
                ], width=9),
                dbc.Col(children=[
                    worldwide_toggle_buttons
                ])
            ], className="g-0")
        ], width=6)
    ]),
    dbc.Row(children=[
        animation_interval,
        html.Div(id="popup")
    ])
])

# app.layout = html.Div(children=[map, world_slider, animation_button, animation_interval, worldwide_events_distribution, worldwide_affected_graph, html.Div(id="popup")])

def generate_country_popup(country, current_year):
    country_name = country["properties"]["ADMIN"]
    country_iso = country["properties"]["ISO_A3"] # Can be useful to do lookups
    country_data = util.filter_map_events(disaster_data, {"ISO": country_iso, "Start Year": current_year})
    popup = dbc.Modal(
        children=[
            dbc.ModalHeader(dbc.ModalTitle(country_name)),
            dl.Map(
                dragging=False,
                scrollWheelZoom=False,
                zoomControl=False,
                children=[
                    dl.TileLayer(), 
                    # https://datahub.io/core/geo-countries#resource-countries
                    dl.GeoJSON(
                        data=util.get_country_data(country_iso),
                        id="country", 
                        options={"style": {"color": "#123456"}}, # Invisible polygons,
                        zoomToBounds=True,
                        hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))), # Gray border on hover (line_thickness, color, line_style)
                    dl.GeoJSON(data=util.convert_events_to_geojson(country_data), # Only show events of country
                               id="country-events",
                               options=dict(pointToLayer=ns("draw_marker"))),
                    ],
                style={"width": "100%", "height": "50vh", "margin": "auto", "display": "block"}, 
                id="detailed-map"),
                dcc.Slider(min=1960, max=2023, step=1, value=current_year, marks=None,tooltip={'placement': 'bottom', 'always_visible': True}, id='country-year-slider'),
                html.Div(children=[
                    dcc.Graph(id='gdp-graph',figure=px.line(map_data,x='Start Year', y="Reconstruction Costs, Adjusted ('000 US$)")),
                    html.Div(children= [
                        dcc.Graph(id='affected-graph',figure=px.line(map_data,x='Start Year', y="Reconstruction Costs, Adjusted ('000 US$)")),
                        html.Div(
                                [
                                    dbc.RadioItems(
                                        id="graph-toggle-buttons",
                                        className="btn-group",
                                        inputClassName="btn-check",
                                        labelClassName="btn btn-outline-primary",
                                        labelCheckedClassName="active",
                                        options=[
                                            {"label": "Deaths", "value": 'deaths'},
                                            {"label": "Injuries", "value": 'injuries'},
                                            {"label": "Homeless", "value": 'homeless'},
                                        ],
                                        value='deaths',
                                    ),
                                ],
                                className="radio-group",
                            )
                    ],
                    style={'display': 'flex'})
                ],
                style={'display': 'flex', 'height': '50vh'})
        ], 
        id=f"{country_iso}-modal",
        fullscreen=True,
        is_open=True)
    return popup

###############
#             #
#  CALLBACKS  #
#             #
###############

# Open popup when click on country
@app.callback(Output("popup", "children"),[Input('countries', 'n_clicks')], [State("countries", "click_feature"), State("world-year-slider", "value")], prevent_initial_call=True)
def country_click(_n_clicks, feature, current_year):
    if feature is not None:
       return generate_country_popup(feature, current_year) # disable the interval because otherwise it draws on the other map
    
@app.callback(Output('animation-interval', 'disabled'),
              Input('animation-button', 'n_clicks'),
              State('animation-interval','disabled'), prevent_initial_call=True)
def animate_slider(n_clicks, animation_status):
    return not animation_status

@app.callback(Output('world-year-slider', 'value'),
              Input('animation-interval','n_intervals'),
              State('world-year-slider', 'value'),
              State('world-year-slider', 'max'),
              State('world-year-slider', 'min'), prevent_initial_call=True)
def update_slider(_n_clicks, current_slider_value, max, min):
    if (current_slider_value < max):
        return current_slider_value + 1
    else:
        return current_slider_value # or min if we want replay, maybe second button to allow for loops ?

@app.callback(Output('events','data'),
              Output('worldwide-events-dist', 'figure'),
              Output('worldwide-affected-graph', 'figure'),
              [Input('world-year-slider','value'),
               Input('worldwide-affected-buttons', 'value')])
def worldwide_slider_change(current_year, current_toggle):
    # Update general map
    map_data = util.filter_map_events(disaster_data, {"Start Year": current_year})

    # Update event distribution graph
    event_count = map_data.groupby("Disaster Subgroup").count().reset_index()
    event_count["colour"] = event_count["Disaster Subgroup"].map(EVENT_COLOURS)
    event_dist_fig = px.bar(event_count, x="Dis No", y="Disaster Subgroup", color="Disaster Subgroup", color_discrete_map=EVENT_COLOURS)

    # Update affected
    affected_fig = generate_affected_graph(current_year, current_toggle)
    
    return util.convert_events_to_geojson(map_data), event_dist_fig, affected_fig

@app.callback([Output('country-events', 'data'),
               Output('gdp-graph','figure'), 
               Output('affected-graph','figure')],
               [Input('country-year-slider','value'),
                Input('graph-toggle-buttons','value')], 
                State("countries", "click_feature"))
def country_slider_change(current_year,toggle_value,country):
    country_code = country["properties"]["ISO_A3"]
    data = util.filter_map_events(disaster_data, {'ISO': country_code})
    # Update map
    map_data = util.filter_map_events(data, {"Start Year": current_year})
    # update graphs gpd graph
    years = list(range(1960,current_year+1))
    country_gdp_data = util.get_gdp_data(gdp_data,data[data["Start Year"] <= current_year],years,country_code)
    gdp_fig = px.line(country_gdp_data, 'Start Year', 'share')

    # update affected graph
    affected_fig = generate_affected_graph(current_year, toggle_value)

    return util.convert_events_to_geojson(map_data), gdp_fig, affected_fig
