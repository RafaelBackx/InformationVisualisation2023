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

from server import app, server
from time import sleep

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

disaster_data = pd.read_csv(
    "Data/Preprocessed-Natural-Disasters.csv", delimiter=";")
gdp_data = pd.read_csv('./Data/gdp_data_constant.csv')

map_data = util.filter_events(disaster_data, {"Start Year": 1960}, True)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True

################
#              #
#  COMPONENTS  #
#              #
################

geophysical_icon = html.Img(
    src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAC+klEQVR4nO2YS2gTURRAnz9EFxYUhWrIvTNE3biR+lsU60YpiNRNaOfdiQuRrtyJ61YQFHXlUtwoVcRFwYWflaWWdu4bY8EPqF2JgqAIivhF28jLTEzSX5IyyczAHHiQzJvFPXPf574nREJCQkLCPBSEWCbiDlP6sGNBn4gz+f6OVSzhlSKYGukSK0VcURJOKcKCbkxwXMSRcdvcxBI/l0QUwZup7sxqETeY4IqXCbynCJ4Wf9vGSREn3D7YqQj/MsFvl3A723C0KCLxfb6/fa2IC0ww6g+ni6VnSgL7GTot4oBjQV9RQsKHfNZsKz1nwkN+Vj4xZdaJKDORTa3Rk9rLhnFidr+SOOLLDIgoowgG/eEzeTsrVszudyyz01+Kv6jc5g0iijBlUizxmzescP/C78EDX+a8iCJMcMuXuLnoezLdwYQzivDHxLHUFhElHMvs1MGxxO/5nJmu9T5LHPbmClwWUaEwIJYriU/85Xawsk/v5IrgupJwprICdm1zB0ucZgm/6hFvCXp1KtdTOFQqQyayqfXl/aS6T090Jnjr910VYZPPmm16vyjXU8X94xET7GMJr6ueexkbm9sHfxzL3NqyoB2CA7oQrHzGhJfmBtt4Y8IbLZHQZwn9FVnC85KMyhnbdC0ViIjEaT1vmi7CEvsrvt7LPKXbFeHdICQqZIabX3ZIeDdrHlT/D2Z4zaicuatpIrpaDTroRbJyv2mrkq5WWyWiCAuuhV2Bi7DEs62UUMUGY4FKTGYzG5WEr60XwYJjGwcDE9F1UBgSyqvB3FJJ49i417WMI0uScHoBdR0UlojyJn6PLmmY8IXew/QdWcMiSsK1MCWUN1eeKQkX/os1egOjd1h9AxK+CFZniOBj5R1APdm4E3bQauHhdq4uiceWscc/vRUi2ST+HJcItbNB+DD0YKnWEMOhxSVs6A47SFWfyIxLxu55JfSaXT6uRr8xwei8Iq7E3rCDU43KSOypktAXafqMET8RWNommZCQkJCQIKr5B4e3yC7b0qbRAAAAAElFTkSuQmCC", style={"width": "auto", "height": "24px"})
meteorological_icon = html.Img(
    src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAxElEQVR4nO3UPWpCQRiF4cdGXYN2rsBNWIkuJKhlNiCmyZrEMj9NIuIybDSCNk4YuQS5GOWqQwh44FQD75k538dw139QDSO8Y4E1ZnhG41r4A7YIvziePV4KfzoBzju+ppBa2BUIiO6eg5bRxys2BeEBc5RODXJ6ATTk3DwGr+LzBvCAFSboHAYMbgQPOcfV3ustUUBAOwZ8JQwYy3pLFbBMXdFStvtJK6rgI+WQo+oJQoaOfBU9vFwx+FVWy8/N7/p7fQOe/B+BqqKyIgAAAABJRU5ErkJggg==", style={"width": "auto", "height": "24px"})
hydrological_icon = html.Img(
    src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABTElEQVR4nM2VO0sDQRDHrxAfxJ07bAQ7sbLwUfsZ7PxI+QA+GjEfwSZF4swqQtTCLt1hIciZmUNr0WChl8idFxIQ3UcScOAPVyy/3+7scBsE/6lCLXt5pgJXOt0BlPc8+fdE4ZXLh2UgSYGkX+Z54aKzMhl6qz8DJNcj8O8g3wan8ezYfEA+/AEfSg7Ggiud7v4KL5Ov8YKH9SRSxGISAMoTaF5y3z1xzQgfnIK45gRfbCbrgPxhKwDiz8oZb1gLALlhD5fBhTes4OH54yoQZx6CHmBnzShQKFVnOJV3gVK1EHDbX8Bts4C46y0g7tqc4NVfIC9GARDf+QoAJbZokRx5C4j3jYKwmW57jSlxFqFsGgWuvwkYTtBxYF2tZB5QbhwEVwHez9kLSokiPvm7XZwVO3eGj1SkZat4dFBihfxWjDFKnD821j2fZn0BzxejKOBMlnUAAAAASUVORK5CYII=", style={"width": "auto", "height": "24px"})
climatological_icon = html.Img(
    src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABIUlEQVR4nOVVW04CQRCsQ4gHM3gF8RogF8CDAAcQf30kggehRnfg2zLTLjjgZkKv7peTdLLZna7qrtmuARxLAc8KeERXSwFK0SXBkwIe2gMQ1yLmiui5cyPORMxEDEoEM5OBWLQo7r7OnZaq6Im4EzHZv9vgXMRYxEoBWwtiKeImfcsIJpbr6V7EpQLi7nAbImqNvrfbb3DiowD+FWmPl8RkKVeuo6i80owd4Ko7GXkIXlsQLEvjr9wCnPJod+CNmPV0Kp/QlgRVlv8D81ii1Z9J1LRsiPwEwy5/0/fkRScTGMka/ZMH7Q0XLvADkoCqWLkHvLbcxYHZRTPAkYgXBWws0jMxzGURcWu5Jam6t2tikDb84sKZirjy5mIP8i8v/U/2bn/Cuda4GwAAAABJRU5ErkJggg==", style={"width": "auto", "height": "24px"})

map_legend = html.Div(children=[
    dbc.Col(children=[
        dbc.Row(children=[
            dbc.Col(children=[
                geophysical_icon
            ]),
            dbc.Col(children=[
                html.P("Geophysical", className="map-legend-item-text")
            ], className="map-legend-item")
        ]),
        dbc.Row(children=[
            dbc.Col(children=[
                meteorological_icon
            ]),
            dbc.Col(children=[
                html.P("Meteorological", className="map-legend-item-text")
            ], className="map-legend-item")
        ]),
        dbc.Row(children=[
            dbc.Col(children=[
                hydrological_icon
            ]),
            dbc.Col(children=[
                html.P("Hydrological", className="map-legend-item-text")
            ], className="map-legend-item")
        ]),
        dbc.Row(children=[
            dbc.Col(children=[
                climatological_icon
            ]),
            dbc.Col(children=[
                html.P("Climatological", className="map-legend-item-text")
            ], className="map-legend-item")
        ])
    ], className="map-legend-item-wrapper")
], className="map-legend")

world_slider = dcc.Slider(min=1960,
                          max=2023,
                          step=1,
                          value=1960,
                          marks=None,
                          tooltip={"placement": "bottom",
                                   "always_visible": True},
                          id="world-year-slider",
                          className="slider")

show_events_button = dbc.Button(
    "Show all events", color="primary", className="me-1 show-events", id="world-show-events")

animation_button = dbc.Button(children=[
    "Play",
    DashIconify(
        icon="material-symbols:play-arrow-rounded"
    )
],
    color="success",
    class_name="me-1",
    id="world-animation-button")

world_slider_wrapper = dbc.Row(
    children=[
        dbc.Col(
            children=[
                animation_button
            ],
            className="column",
            width="auto"),
        dbc.Col(
            children=[
                world_slider
            ],
            className="column")
    ], className="slider-container"
)

map = dl.Map(
    maxBounds=[[-90, -180], [90, 180]],
    maxBoundsViscosity=1.0,
    maxZoom=18,
    minZoom=2,
    center=(40, -37),
    bounceAtZoomLimits=True,
    children=[
        dl.TileLayer(),
        # https://datahub.io/core/geo-countries#resource-countries
        dl.GeoJSON(
            data=util.get_world_geojson(),
            id="countries",
            # Invisible polygons,
            options={"style": {"color": "transparent"}},
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
        dl.GeoJSON(data=util.convert_events_to_geojson(map_data),
                   id="events",
                   options=dict(pointToLayer=ns("draw_marker"))),
        map_legend,
        world_slider_wrapper
    ],
    style={"width": "100%", "height": "100%", "display": "block"},
    id="map")

animation_interval = dcc.Interval(
    'animation-interval', interval=500, disabled=True)

world_gdp_graph = dcc.Graph(
    id="world-gdp-graph", style={"height": "30vh", "width": "100%"})
world_affected_graph = dcc.Graph(
    id="world-affected-graph", style={"height": "30vh", "width": "100%"})


def create_event_accordion(event, missing_events):
    dis_no = event['Dis No']
    missing_events_no = [e['Dis No'] for _, e in missing_events.iterrows()]
    missing = dis_no in missing_events_no
    accordion = dbc.AccordionItem(
        item_id=f'{dis_no}',
        title=f'{event["Disaster Type"]} ({util.get_property(event, "Event Name")})',
        children=[
            html.P(
                f'{event["Disaster Subgroup"]}/{event["Disaster Type"]}/{util.get_property(event, "Disaster Subsubtype")}'),
            html.P(util.get_date(event)),
            html.P(f'{event["Region"]}'),
        ])
    if (missing):
        accordion.children.append(DashIconify(
            icon="material-symbols:location-off-rounded"
        ))
    return accordion


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
                animation_interval,
                html.Div(id="popup"),
                html.Div(
                    children=[
                        dbc.Offcanvas(
                            children=[

                            ],
                            is_open=False,
                            placement="end",
                            id="world-offcanvas"
                        )
                    ]
                )
            ]
        )
    ]
)

home_layout = html.Div(
    children=[
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardHeader(
                                    children=[
                                        "World Map"
                                    ]
                                ),
                                dbc.CardBody(
                                    children=[
                                        map
                                    ]
                                )
                            ],
                            className="map-card")
                    ],
                    width=9,
                    className="column map-column"),
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardHeader(
                                    children=[
                                        "Aggregated Data"
                                    ]
                                ),
                                dbc.CardBody(
                                    children=[
                                        html.Div(
                                            id="world-aggregated-data"),
                                        show_events_button
                                    ]
                                )
                            ],
                            className="aggregated-card")
                    ],
                    width=3,
                    className="column aggregated-column")
            ],
            className="map-row"
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardHeader(
                                    children=[
                                        "GDP Data"
                                    ]
                                ),
                                dbc.CardBody(
                                    children=[
                                        world_gdp_graph
                                    ],
                                    className="gdp-cardbody")
                            ],
                            className="gdp-card")
                    ],
                    width=6,
                    className="column gdp-column"),
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardHeader(
                                    children=[
                                        "Affected Data"
                                    ]
                                ),
                                dbc.CardBody(
                                    children=[
                                        dbc.Tabs(
                                            children=[
                                                dbc.Tab(
                                                    label="Total Deaths", tab_id="deaths"),
                                                dbc.Tab(
                                                    label="Total Injured", tab_id="injuries"),
                                                dbc.Tab(
                                                    label="Total Homeless", tab_id="homeless")
                                            ],
                                            id="world-affected-tabs",
                                            active_tab="deaths"
                                        ),
                                        world_affected_graph
                                    ]
                                )
                            ],
                            className="affected-card")
                    ],
                    width=6,
                    className="column affected-column")
            ],
            className="graphs-row")
    ],
    id="home"
)

###############
#             #
#  CALLBACKS  #
#             #
###############


@app.callback([Output("world-offcanvas", "children"), Output("world-offcanvas", "is_open")], [Input("world-show-events", "n_clicks")], [State("world-offcanvas", "is_open")])
def show_events(n_clicks, io):
    if n_clicks:
        is_open = not io
    else:
        is_open = io
    return "Blablabla", is_open


@app.callback([Output("country-offcanvas", "children"), Output("country-offcanvas", "is_open")], [Input("country-show-events", "n_clicks")], [State("country-offcanvas", "is_open")])
def show_events(n_clicks, io):
    if n_clicks:
        is_open = not io
    else:
        is_open = io
    return "Blablabla", is_open


@app.callback(Output("content", "children"), [Input("tabs", "active_tab")])
def navigate_tabs(active_tab):
    if active_tab == "home":
        return home_layout
    elif active_tab == "us-prevention":
        pass


@app.callback(Output("world-affected", "children"), [Input("world-affected-tabs", "active_tab"), Input('world-year-slider', 'value')])
def change_affected_filter(active_tab, current_year):
    affected_data = disaster_data[disaster_data["Start Year"] <= current_year]
    return components.generate_affected_graph(affected_data, active_tab)

# Open popup when click on country


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
               Input("world-affected-tabs", 'active_tab')])
def worldwide_slider_change(current_year, current_toggle):
    # Update general map
    map_data = util.filter_events(
        disaster_data, {"Start Year": current_year}, True)

    yearly_data = disaster_data[disaster_data["Start Year"] == current_year]
    year_data = disaster_data[disaster_data["Start Year"] == current_year][[
        "Start Year", "Disaster Subgroup", "Dis No"]]

    affected_data = disaster_data[disaster_data["Start Year"] <= current_year]

    missing_rows = pd.DataFrame(
        {"Start Year": [], "Disaster Subgroup": [], "Dis No": []})

    for dis_group in DISASTER_SUBGROUPS:
        if dis_group not in year_data["Disaster Subgroup"].values:
            missing_rows[["Start Year", "Disaster Subgroup", "Dis No"]] = [
                [current_year, dis_group, None]]

    if not missing_rows.empty:
        year_data = pd.concat(
            [missing_rows, year_data.loc[:]]).reset_index(drop=True)

    # Update event distribution graph
    event_count = year_data.groupby(
        "Disaster Subgroup", as_index=False).count()
    event_count["colour"] = event_count["Disaster Subgroup"].map(EVENT_COLOURS)
    event_dist_fig = px.bar(event_count, x="Dis No", y="Disaster Subgroup",
                            color="Disaster Subgroup", color_discrete_map=EVENT_COLOURS)
    event_dist_fig.update_traces(hovertemplate="<br>".join([
        "Disaster Subgroup: %{y}",
        "Disasters: %{x}",
        "<extra></extra>"
    ]))
    event_dist_fig.update_layout(
        hoverlabel=dict(
            bgcolor="white"
        ),
        xaxis_title="Disaster Count",
        margin=dict(l=0, b=0, t=0, r=0))

    # Update affected
    affected_fig = components.generate_affected_graph(
        affected_data, current_year, current_toggle)

    aggregated_data = components.generate_aggregated_data_table(yearly_data)

    return util.convert_events_to_geojson(map_data), event_dist_fig, affected_fig, aggregated_data


@app.callback([Output('country-events', 'data'),
               Output('country-gdp-graph', 'figure'),
               Output('country-affected-graph', 'figure'),
               Output("country-aggregated-data", "children")],
              [Input('country-year-slider', 'value'),
               Input('country-affected-tabs', 'active_tab')],
              State("countries", "click_feature"))
def country_slider_change(current_year, toggle_value, country):
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

    aggregated_data = components.generate_aggregated_data_table(yearly_data)

    return util.convert_events_to_geojson(map_data), gdp_fig, affected_fig, aggregated_data


# @app.callback(Output('world-events-accordion', 'children'), Input('world-year-slider', 'value'), prevent_initial_call=True)
# def slider_create_accordion_events(slider_value):
#     missing_events = util.get_events_without_location(
#         disaster_data[disaster_data["Start Year"] == slider_value])
#     df = pd.concat([missing_events, map_data], axis=0)
#     children = []
#     for _, event in df.iterrows():
#         children.append(create_event_accordion(event, missing_events))
#     accordion_items = [create_event_accordion(event, missing_events) for _, event in pd.concat([
#         missing_events, map_data], axis=0).iterrows()]
#     print(len(accordion_items))
#     return accordion_items


# @app.callback(Output('detailed-map', 'center'), Input('events-accordion', 'active_item'), State("countries", "click_feature"), prevent_initial_call=True)
# def country_event_click(event_id, data):
#     if (event_id):
#         event, loc = util.get_event(disaster_data, event_id)
#         return loc
#     else:
#         point = util.calculate_center(data)
#         return [point.y, point.x]


# @app.callback(Output('map', 'center'), Input("world-events-accordion", 'active_item'), prevent_initial_call=True)
# def world_event_click(event_id):
#     if (event_id):
#         event, loc = util.get_event(disaster_data, event_id)
#         return loc
#     else:
#         return (40, -37)
