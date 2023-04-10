import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, dcc, State
from dash_extensions.javascript import arrow_function, assign, Namespace
from dash.exceptions import PreventUpdate
import plotly.express as px
import util
from server import app, server

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
                # zoomToBoundsOnClick=True,
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

animation_button = html.Button('play', id='animation-button')
animation_interval = dcc.Interval('animation-interval',interval=500,disabled=True)

############
#          #
#  LAYOUT  #
#          #
############

app.layout = html.Div(children=[map, world_slider, animation_button,animation_interval, html.Div(id="popup")])

def generate_country_popup(country,df):
    country_name = country["properties"]["ADMIN"]
    country_iso = country["properties"]["ISO_A3"] # Can be useful to do lookups
    country_data = util.filter_map_events(df, {"ISO": country_iso})
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
                dcc.Slider(min=1960, max=2023, step=1, value=2021, marks=None,tooltip={'placement': 'bottom', 'always_visible': True}, id='country-year-slider'),
                html.Div(children=[
                    dcc.Graph(id='gdp-graph',figure=px.line(df,x='Start Year', y="Reconstruction Costs, Adjusted ('000 US$)")),
                    html.Div(children= [
                        dcc.Graph(id='affected-graph',figure=px.line(df,x='Start Year', y="Reconstruction Costs, Adjusted ('000 US$)")),
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
@app.callback(Output("popup", "children"), [Input("countries", "click_feature")])
def country_click(feature):
    if feature is not None:
       return generate_country_popup(feature, map_data) # disable the interval because otherwise it draws on the other map
    
@app.callback(Output('animation-interval', 'disabled'),
              Input('animation-button', 'n_clicks'),
              State('animation-interval','disabled'),prevent_initial_call=True)
def animate_slider(n_clicks, animation_status):
    print(animation_status)
    return not animation_status

@app.callback(Output('world-year-slider', 'value'),
              Input('animation-interval','n_intervals'),
              State('world-year-slider', 'value'),
              State('world-year-slider', 'max'),
              State('world-year-slider', 'min'))
def update_slider(_n_clicks, current_slider_value, max, min):
    if (current_slider_value < max):
        return current_slider_value + 1
    else:
        return current_slider_value # or min if we want replay, maybe second button to allow for loops ?

@app.callback(Output('events','data'),
              Input('world-year-slider','value'))
def update_markers(value):
    map_data = util.filter_map_events(disaster_data, {"Start Year": value})
    return util.convert_events_to_geojson(map_data)

@app.callback([Output('gdp-graph','figure'), Output('affected-graph','figure')],[Input('country-year-slider','value'),Input('graph-toggle-buttons','value')], State("countries", "click_feature"))
def country_slider_change(value,toggle_value,country):
    country_code = country["properties"]["ISO_A3"]
    # update graphs gpd graph
    years = list(range(1960,value+1))
    country_gdp_data = util.get_gdp_data(gdp_data,years,country_code)
    gdp_fig = px.line(None,years,country_gdp_data)

    #update injuries graph
    column_map = {
        'deaths': 'Total Deaths',
        'injuries': 'No Injured',
        'homeless': 'No Homeless'
    }
    column = column_map[toggle_value]
    data = disaster_data[disaster_data['ISO'] == country_code]
    data = data.groupby(['Start Year', 'Disaster Subgroup'], as_index=False).sum(numeric_only=True)
    affected_fig = px.line(data[data['Start Year'] <= value],'Start Year',column,color='Disaster Subgroup', log_y=True)
    return gdp_fig, affected_fig
