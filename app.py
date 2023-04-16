import pandas as pd
import dash_leaflet as dl
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, dcc, State, ALL, dash
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

map_data = util.filter_map_events(disaster_data, {"Start Year": 1960})

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
        map_legend
    ],
    style={"width": "100%", "height": "90%", "display": "block"},
    id="map")

world_slider = dcc.Slider(min=1960,
                          max=2023,
                          step=1,
                          value=1960,
                          marks=None,
                          tooltip={"placement": "bottom",
                                   "always_visible": True},
                          id="world-year-slider",
                          className="slider")

animation_button = dbc.Button(children=[
    "Play",
    DashIconify(
        icon="material-symbols:play-arrow-rounded"
    )
],
    color="success",
    class_name="me-1",
    id="animation-button")

animation_interval = dcc.Interval(
    'animation-interval', interval=500, disabled=True)

worldwide_events_distribution = dcc.Graph(
    id="worldwide-events-dist", className="main-graphs")
worldwide_affected_graph = dcc.Graph(
    id="worldwide-affected-graph", className="main-graphs")
worldwide_toggle_buttons = html.Div(children=[
    dbc.RadioItems(
        id="worldwide-affected-buttons",
        style={"display": "flex", "flexDirection": "column"},
        className="btn-group",
        inputClassName="btn-check",
        labelClassName="btn btn-outline-primary",
        labelCheckedClassName="active",
        options=[
            {"label": "Deaths", "value": 'deaths'},
            {"label": "Injuries",
             "value": 'injuries'},
            {"label": "Homeless",
             "value": 'homeless'},
        ],
        value='deaths'),
], className="radio-group")


def generate_affected_graph(df, current_year, current_toggle):
    affected_data = df[df["Start Year"] <= current_year][["Start Year", "Disaster Subgroup", "Total Deaths", "No Injured", "No Homeless"]]

    missing_rows = {"Start Year": [], "Disaster Subgroup": [], "Total Deaths": [], "No Injured": [], "No Homeless": []}

    for year in range(1960, current_year+1):
        if year not in affected_data["Start Year"].values:
            for dis_group in DISASTER_SUBGROUPS:
                missing_rows["Start Year"].append(year)
                missing_rows["Disaster Subgroup"].append(dis_group)
                missing_rows["Total Deaths"].append(None)
                missing_rows["No Injured"].append(None)
                missing_rows["No Homeless"].append(None)
        else:
            for dis_group in DISASTER_SUBGROUPS:
                if dis_group not in affected_data[affected_data["Start Year"] == year]["Disaster Subgroup"].values:
                    missing_rows["Start Year"].append(year)
                    missing_rows["Disaster Subgroup"].append(dis_group)
                    missing_rows["Total Deaths"].append(None)
                    missing_rows["No Injured"].append(None)
                    missing_rows["No Homeless"].append(None)

    if len(missing_rows["Start Year"]) != 0:
        affected_data = pd.concat([pd.DataFrame(missing_rows), affected_data.loc[:]]).reset_index(drop=True)

    affected_data = affected_data.groupby(
        ["Start Year", "Disaster Subgroup"], as_index=False).sum(numeric_only=True)

    column_map = {
        'deaths': 'Total Deaths',
        'injuries': 'No Injured',
        'homeless': 'No Homeless'
    }
    column = column_map[current_toggle]
    fig = px.line(affected_data, "Start Year", column,
                  color="Disaster Subgroup", color_discrete_map=EVENT_COLOURS)
    fig.update_traces(mode="markers+lines", hovertemplate=None)
    fig.update_layout(hovermode="x unified", xaxis_title="Year", xaxis=dict(tickformat="d"))
    return fig


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
            ], className="g-0 slider-row")
        ], className="map-column", width=9),
        dbc.Col(children=[
            html.Div(children=[
                "Replace this with events accordion"
            ])
        ], className="events-column", width=3)
    ], className="map-row"),
    dbc.Row(children=[
        dbc.Col(children=[
            worldwide_events_distribution
        ], className="graphs-column"),
        dbc.Col(children=[
            dbc.Row(children=[
                dbc.Col(children=[
                    worldwide_affected_graph
                ], width=9),
                dbc.Col(children=[
                    worldwide_toggle_buttons
                ])
            ], className="g-0 graphs-row")
        ], className="graphs-column")
    ], className="graphs-row"),
    dbc.Row(children=[
        animation_interval,
        html.Div(id="popup")
    ])
], className="main-container")

# app.layout = html.Div(children=[map, world_slider, animation_button, animation_interval, worldwide_events_distribution, worldwide_affected_graph, html.Div(id="popup")])


def generate_country_popup(country, current_year):
    country_name = country["properties"]["ADMIN"]
    # Can be useful to do lookups
    country_iso = country["properties"]["ISO_A3"]
    country_data = util.filter_map_events(
        disaster_data, {"ISO": country_iso, "Start Year": current_year})
    missing_events = util.get_events_without_location(country_data)
    country_map = dl.Map(
        dragging=False,
        scrollWheelZoom=False,
        zoomControl=False,
        preferCanvas=True,
        children=[
            dl.TileLayer(),
            # https://datahub.io/core/geo-countries#resource-countries
            dl.GeoJSON(
                data=util.get_country_data(country_iso),
                id="country",
                # Invisible polygons,
                options={"style": {"color": "#123456"}},
                zoomToBounds=True,
                hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
            dl.GeoJSON(data=util.convert_events_to_geojson(country_data),  # Only show events of country
                       id="country-events",
                       options=dict(pointToLayer=ns("draw_marker"))),
            map_legend
        ],
        style={"width": "100%", "height": "90%", "display": "block"},
        id="detailed-map")

    events_accordion = dbc.Accordion(id='events-accordion', children=[create_event_accordion(
        event, missing_events) for _, event in missing_events.iterrows()])

    aggregated_country_data_card = dbc.Card(
        children=[
            dbc.CardHeader(children=["Aggregated data"]),
            dbc.CardBody(children=[
                html.Div(id='country-agg-data')
            ])
        ]
    )

    country_slider = dcc.Slider(min=1960, max=2023, step=1, value=current_year, marks=None, tooltip={
                                'placement': 'bottom', 'always_visible': True}, id='country-year-slider', className="slider")

    gdp_graph = dcc.Graph(id='gdp-graph')

    country_affected_graph = dcc.Graph(id='affected-graph')

    country_toggle_buttons = html.Div(children=[
        dbc.RadioItems(
            id="graph-toggle-buttons",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-primary",
            style={"display": "flex",
                   "flexDirection": "column"},
            labelCheckedClassName="active",
            options=[
                {"label": "Deaths", "value": 'deaths'},
                {"label": "Injuries",
                 "value": 'injuries'},
                {"label": "Homeless",
                 "value": 'homeless'},
            ],
            value='deaths',
        ),
    ],
        className="radio-group",
    )

    popup = dbc.Modal(children=[
        dbc.ModalHeader(dbc.ModalTitle(country_name)),
        dbc.Row(children=[
                dbc.Col(children=[
                    country_map,
                    dbc.Row(children=[
                        # dbc.Col(children=[
                        #     animation_button
                        # ], width="auto"),
                        dbc.Col(children=[
                            country_slider
                        ]),
                    ], className="g-0 slider-row")
                ], className="map-column map-column-popup", width=9),
                dbc.Col(children=[
                    dbc.Row(children=[
                        aggregated_country_data_card
                    ], className="aggregated-data"),
                    dbc.Row(children=[
                        events_accordion
                    ], className="events-accordion"),
                ], className="events-column events-column-popup", width=3)
                ], className="map-row popup-map-row"),
        dbc.Row(children=[
                dbc.Col(children=[
                    gdp_graph
                ], className="graphs-column popup-graphs"),
                dbc.Col(children=[
                    dbc.Row(children=[
                        dbc.Col(children=[
                            country_affected_graph
                        ], width=9),
                        dbc.Col(children=[
                            country_toggle_buttons
                        ])
                    ], className="g-0 graphs-row")
                ], className="graphs-column popup-graphs")
                ], className="graphs-row")
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


@app.callback(Output("popup", "children"), [Input('countries', 'n_clicks')], [State("countries", "click_feature"), State("world-year-slider", "value")], prevent_initial_call=True)
def country_click(_n_clicks, feature, current_year):
    if feature is not None:
       # disable the interval because otherwise it draws on the other map
       return generate_country_popup(feature, current_year)


@app.callback(Output('animation-interval', 'disabled'),
              Input('animation-button', 'n_clicks'),
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
              Output('worldwide-events-dist', 'figure'),
              Output('worldwide-affected-graph', 'figure'),
              [Input('world-year-slider', 'value'),
               Input('worldwide-affected-buttons', 'value')])
def worldwide_slider_change(current_year, current_toggle):
    # Update general map
    map_data = util.filter_map_events(
        disaster_data, {"Start Year": current_year})

    year_data = disaster_data[disaster_data["Start Year"] == current_year][["Start Year", "Disaster Subgroup", "Dis No"]]

    missing_rows = pd.DataFrame({"Start Year": [], "Disaster Subgroup": [], "Dis No": []})

    for dis_group in DISASTER_SUBGROUPS:
        if dis_group not in year_data["Disaster Subgroup"].values:
            missing_rows[["Start Year", "Disaster Subgroup", "Dis No"]] = [[current_year, dis_group, None]]

    if not missing_rows.empty:
        year_data = pd.concat([missing_rows, year_data.loc[:]]).reset_index(drop=True)

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
        xaxis_title="Disaster Count")

    # Update affected
    affected_fig = generate_affected_graph(disaster_data, current_year, current_toggle)

    return util.convert_events_to_geojson(map_data), event_dist_fig, affected_fig


@app.callback([Output('country-events', 'data'),
               Output('gdp-graph', 'figure'),
               Output('affected-graph', 'figure'),
               Output('events-accordion', 'children'),
               Output('country-agg-data', 'children')],
              [Input('country-year-slider', 'value'),
               Input('graph-toggle-buttons', 'value')],
              State("countries", "click_feature"))
def country_slider_change(current_year, toggle_value, country):
    country_code = country["properties"]["ISO_A3"]
    data = util.filter_map_events(disaster_data, {'ISO': country_code})

    # update affected graph
    affected_fig = generate_affected_graph(disaster_data[disaster_data["ISO"] == country_code], current_year, toggle_value)

    # Update map
    map_data = util.filter_map_events(data, {"Start Year": current_year})

    # update graphs gpd graph
    years = list(range(1960, current_year+1))
    country_gdp_data = util.get_gdp_data(
        gdp_data, data[data["Start Year"] <= current_year], years, country_code)
    gdp_fig = px.line(country_gdp_data, 'Start Year', 'share')
    gdp_fig.update_traces(mode="markers+lines", hovertemplate=None)
    gdp_fig.update_layout(hovermode="x unified", xaxis_title="Year", xaxis=dict(tickformat="d"))

    missing_events = util.get_events_without_location(disaster_data[(
        disaster_data["Start Year"] == current_year) & (disaster_data["ISO"] == country_code)])
    accordion_items = [create_event_accordion(event, missing_events) for _, event in pd.concat([
        missing_events, map_data], axis=0).iterrows()]

    # aggregate data
    number_of_deaths = map_data['Total Deaths'].sum()
    number_of_injured = map_data['No Injured'].sum()
    number_of_homeless = map_data['No Homeless'].sum()

    aggr_data = [f'Number of deaths: {number_of_deaths}',
                 f'Number of injured: {number_of_injured}', f'Number of homeless: {number_of_homeless}']
    aggr_data_html = [html.P(value) for value in aggr_data]

    return util.convert_events_to_geojson(map_data), gdp_fig, affected_fig, accordion_items, aggr_data_html


@app.callback(Output('detailed-map', 'center'), Input('events-accordion', 'active_item'), State("countries", "click_feature"), prevent_initial_call=True)
def event_click(event_id, data):
    if (event_id):
        event, loc = util.get_event(disaster_data, event_id)
        return loc
    else:
        point = util.calculate_center(data)
        return [point.y, point.x]
