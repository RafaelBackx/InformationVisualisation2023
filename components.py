import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import dash_leaflet as dl

from dash_iconify import DashIconify
from dash import html, dcc
from dash_extensions.javascript import arrow_function, Namespace

import util

ns = Namespace("dashExtensions", "default")

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

def generate_cost_bar_plots(data,colour_map=None,log=False):
    data = {key:value for key,value in data.items() if value > 0}
    labels = list(data.keys())
    values = list(data.values())

    colour_map = {key: EVENT_COLOURS[value] for key,value in colour_map.items()}

    def get_colour(event):
        return colour_map[event]

    figure=go.Figure()
    figure.add_trace(go.Bar(x=labels, y=values,
                    marker=dict(color = list(map(get_colour, list(colour_map.keys()))))))
    figure.update_layout(hovermode="x unified")
    return dcc.Graph(figure=figure, style={"height": "80%"})

def generate_aggregated_data_table(df):
    # Fill missing values with 0s
    df = df.fillna(0)

    # Aggregate data and keep relevant columns
    yearly_data = df.groupby("Start Year").sum(numeric_only=True)[
        ["Total Deaths", "No Injured", "No Affected", "No Homeless", "Reconstruction Costs, Adjusted ('000 US$)", "Insured Damages, Adjusted ('000 US$)", "Total Damages, Adjusted ('000 US$)"]]
    
    # If there was no data, just construct a dataframe containing 0s
    if df.empty:
        yearly_data = pd.DataFrame({"Total Deaths": [0], "No Injured": [0], "No Affected": [0], "No Homeless": [
                                   0], "Total Damages, Adjusted ('000 US$)": [0], "Reconstruction Costs, Adjusted ('000 US$)": [0], "Insured Damages, Adjusted ('000 US$)": [0]})
        
    # Mapping between dataframe column names and names used in the front-end
    column_mapping = {
        "Total Deaths": "Deaths",
        "No Injured": "Injured",
        "No Affected": "Affected",
        "No Homeless": "Homeless",
        "Total Damages, Adjusted ('000 US$)": "Damages ('000 US$)",
        "Reconstruction Costs, Adjusted ('000 US$)": "Reconstruction Costs ('000 US$)",
        "Insured Damages, Adjusted ('000 US$)": "Insured ('000 US$)"
    }

    # Construct table
    table_rows = []
    for column in column_mapping:
        if column in ["Total Deaths", "No Injured", "No Affected", "No Homeless"]:
            table_rows.append(html.Tr([html.Td(column_mapping[column]), html.Td(util.format_large_number(yearly_data[column].values[0], False))]))
        else:
            table_rows.append(html.Tr([html.Td(column_mapping[column]), html.Td(util.format_large_number(yearly_data[column].values[0]))]))

    return dbc.Table(html.Tbody(table_rows), bordered=True)


def generate_affected_graph(df, current_year, current_toggle):
    # Filter dataframe and only keep relevant columns
    affected_data = df[df["Start Year"] <= current_year][["Start Year", "Disaster Subgroup",
                        "Total Deaths", "No Injured", "No Homeless"]]

    # Fill missing data with 0s
    missing_rows = {"Start Year": [], "Disaster Subgroup": [],
                    "Total Deaths": [], "No Injured": [], "No Homeless": []}
    
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

    # Add augmented rows to original data
    if len(missing_rows["Start Year"]) != 0:
        affected_data = pd.concat([pd.DataFrame(missing_rows), affected_data.loc[:]]).reset_index(drop=True)

    # Replace Nan by 0s
    affected_data = affected_data.fillna(0)

    # Aggregate data
    affected_data = affected_data.groupby(["Start Year", "Disaster Subgroup"], as_index=False).sum(numeric_only=True)

    # Map toggle value to dataframe column
    column_map = {
        'deaths': 'Total Deaths',
        'injuries': 'No Injured',
        'homeless': 'No Homeless'
    }
    column = column_map[current_toggle]

    # Create graph
    fig = px.line(affected_data, "Start Year", column,
                  color="Disaster Subgroup", color_discrete_map=EVENT_COLOURS)
    fig.update_traces(mode="markers+lines", hovertemplate=None)
    fig.update_layout(hovermode="x unified", xaxis_title="Year", xaxis=dict(
        tickformat="d"), margin=dict(l=0, r=0, t=0, b=0))
    return fig

def generate_gdp_graph(gdp_data, current_year, categories = False):
    gdp_data = gdp_data[gdp_data["Start Year"] <= current_year]
    
    if categories:
        gdp_data = gdp_data.groupby(["Start Year", "Disaster Subgroup"], as_index=False).sum(numeric_only=True)
        gdp_fig = px.line(gdp_data, 'Start Year', 'share', color="Disaster Subgroup", color_discrete_map=EVENT_COLOURS)
    else:
        gdp_data = gdp_data.groupby("Start Year", as_index=False).sum()
        gdp_fig = px.line(gdp_data, 'Start Year', 'share')

    gdp_fig.update_traces(mode="markers+lines", hovertemplate=None)
    gdp_fig.update_layout(hovermode="x unified", xaxis_title="Year", xaxis=dict(
        tickformat="d"), margin=dict(l=0, r=0, t=0, b=0))
    return gdp_fig

def create_events_accordion(events):
    # Create accordion for all events
    accordion = []
    for _, event in events.iterrows():
        accordion.append(create_event_accordion_item(event))
    return accordion

def create_event_accordion_item(event):
    # If the disaster has a name use it, else use the date
    if not pd.isnull(event["Event Name"]):
        title = event["Event Name"]
    else:
        title = f"{event['Disaster Type']}, {util.get_date(event)}"

    # If location data is known use it, else unknown
    if (not pd.isnull(event["Latitude"])) and (not pd.isnull(event["Longitude"])):
        location = f"{event['Latitude']}, {event['Longitude']}"
    else:
        location = "Unknown"

    if (not pd.isnull(event["Dis Mag Value"])) and (not pd.isnull(event["Dis Mag Scale"])):
        impact = f"{event['Dis Mag Value']} {event['Dis Mag Scale']}"
    else:
        impact = "Unknown"

    if not pd.isnull(event["Local Time"]):
        local_time = event['Local Time']
    else:
        local_time = "Unknown"

    if not pd.isnull(event["Total Deaths"]):
        deaths = util.format_large_number(event["Total Deaths"], False)
    else:
        deaths = "Unknown"

    if not pd.isnull(event["No Injured"]):
        injured = util.format_large_number(event["No Injured"], False)
    else:
        injured = "Unknown"

    if not pd.isnull(event["No Affected"]):
        affected =  util.format_large_number(event["No Affected"], False)
    else:
        affected = "Unknown"

    if not pd.isnull(event["No Homeless"]):
        homeless =  util.format_large_number(event["No Homeless"], False)
    else:
        homeless = "Unknown"

    if not pd.isnull(event["Reconstruction Costs ('000 US$)"]):
        reconstruction =  util.format_large_number(event["Reconstruction Costs, Adjusted ('000 US$)"])
    else:
        reconstruction = "Unknown"

    if not pd.isnull(event["Insured Damages ('000 US$)"]):
        insured =  util.format_large_number(event["Insured Damages, Adjusted ('000 US$)"])
    else:
        insured = "Unknown"

    if not pd.isnull(event["Total Damages ('000 US$)"]):
        damages =  util.format_large_number(event["Total Damages, Adjusted ('000 US$)"])
    else:
        damages = "Unknown"

    if not pd.isnull(event['Region']):
        region = event['Region']
    else:
        region = "Unknown"
    
    if not pd.isnull(event["River Basin"]):
        river_basin = event["River Basin"]
    else:
        river_basin = None

    # Format disaster classification
    if (not pd.isnull(event["Disaster Subsubtype"])):
        classification = f"{event['Disaster Subgroup']}/{event['Disaster Type']}/{event['Disaster Subsubtype']}"
    else:
        classification = f"{event['Disaster Subgroup']}/{event['Disaster Type']}"

    if river_basin:
        # Create accordion for event
        accordion = dbc.AccordionItem(
            title=title,
            children=[
                html.P([html.B("Event classification: "), classification]),
                html.P([html.B("Event date: "), util.get_date(event)]),
                html.P([html.B("Local time: "), local_time]),
                html.P([html.B("Region: "), region]),
                html.P([html.B("River origin: "), river_basin]),
                html.P([html.B("Lat, Long: "), location]),
                html.P([html.B("Impact: "), impact]),
                html.P([html.B("No. affected: "), affected]),
                html.P([html.B("Total deaths: "), deaths]),
                html.P([html.B("No. injured: "), injured]),
                html.P([html.B("No. homeless: "), homeless]),
                html.P([html.B("Total damages ('000 US$): "), damages]),
                html.P([html.B("Reconstruction costs ('000 US$): "), reconstruction]),
                html.P([html.B("Insured damages ('000 US$): "), insured]),
            ]
        )
    else:
        accordion = dbc.AccordionItem(
            title=title,
            children=[
                html.P([html.B("Event classification: "), classification]),
                html.P([html.B("Event date: "), util.get_date(event)]),
                html.P([html.B("Local time: "), local_time]),
                html.P([html.B("Region: "), region]),
                html.P([html.B("Lat, Long: "), location]),
                html.P([html.B("Impact: "), impact]),
                html.P([html.B("No. affected: "), affected]),
                html.P([html.B("Total deaths: "), deaths]),
                html.P([html.B("No. injured: "), injured]),
                html.P([html.B("No. homeless: "), homeless]),
                html.P([html.B("Total damages ('000 US$): "), damages]),
                html.P([html.B("Reconstruction costs ('000 US$): "), reconstruction]),
                html.P([html.B("Insured damages ('000 US$): "), insured]),
            ]
        )

    return accordion

def generate_country_popup(disaster_data, country, current_year):
    # Fetch meta data about the country
    country_name = country["properties"]["ADMIN"]
    country_iso = country["properties"]["ISO_A3"]

    # Filter the events by country code and start year
    country_data = util.filter_events(
        disaster_data, {"ISO": country_iso, "Start Year": current_year})
    
    # Filter map events to the events that contain location data
    map_data = util.filter_events(country_data, {}, True)

    country_slider = dcc.Slider(min=1960,
                                max=2023,
                                step=1,
                                value=current_year,
                                marks=None,
                                tooltip={"placement": "bottom",
                                         "always_visible": True},
                                id="country-year-slider",
                                className="slider")

    geophysical_icon = html.Img(
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAYAAAAeP4ixAAAACXBIWXMAAAsTAAALEwEAmpwYAAAC+klEQVR4nO2YS2gTURRAnz9EFxYUhWrIvTNE3biR+lsU60YpiNRNaOfdiQuRrtyJ61YQFHXlUtwoVcRFwYWflaWWdu4bY8EPqF2JgqAIivhF28jLTEzSX5IyyczAHHiQzJvFPXPf574nREJCQkLCPBSEWCbiDlP6sGNBn4gz+f6OVSzhlSKYGukSK0VcURJOKcKCbkxwXMSRcdvcxBI/l0QUwZup7sxqETeY4IqXCbynCJ4Wf9vGSREn3D7YqQj/MsFvl3A723C0KCLxfb6/fa2IC0ww6g+ni6VnSgL7GTot4oBjQV9RQsKHfNZsKz1nwkN+Vj4xZdaJKDORTa3Rk9rLhnFidr+SOOLLDIgoowgG/eEzeTsrVszudyyz01+Kv6jc5g0iijBlUizxmzescP/C78EDX+a8iCJMcMuXuLnoezLdwYQzivDHxLHUFhElHMvs1MGxxO/5nJmu9T5LHPbmClwWUaEwIJYriU/85Xawsk/v5IrgupJwprICdm1zB0ucZgm/6hFvCXp1KtdTOFQqQyayqfXl/aS6T090Jnjr910VYZPPmm16vyjXU8X94xET7GMJr6ueexkbm9sHfxzL3NqyoB2CA7oQrHzGhJfmBtt4Y8IbLZHQZwn9FVnC85KMyhnbdC0ViIjEaT1vmi7CEvsrvt7LPKXbFeHdICQqZIabX3ZIeDdrHlT/D2Z4zaicuatpIrpaDTroRbJyv2mrkq5WWyWiCAuuhV2Bi7DEs62UUMUGY4FKTGYzG5WEr60XwYJjGwcDE9F1UBgSyqvB3FJJ49i417WMI0uScHoBdR0UlojyJn6PLmmY8IXew/QdWcMiSsK1MCWUN1eeKQkX/os1egOjd1h9AxK+CFZniOBj5R1APdm4E3bQauHhdq4uiceWscc/vRUi2ST+HJcItbNB+DD0YKnWEMOhxSVs6A47SFWfyIxLxu55JfSaXT6uRr8xwei8Iq7E3rCDU43KSOypktAXafqMET8RWNommZCQkJCQIKr5B4e3yC7b0qbRAAAAAElFTkSuQmCC", style={"width": "auto", "height": "24px"})
    meteorological_icon = html.Img(
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABAElEQVR4nO2UP04CURjE1wY9g3ScwEtQGT2IAUovYKCx4gRLdma3mI+aDlr/NEDwGjagiTSuea5AwopxgZdQMMkr32++efPyBcFRB68kSc5FNkU+G/Aq8l3kRMB9N44rO8EF3BgwNzL99QBzkbdbwQ1obQSvHZem2ORRVBXw+V+DH5Prv6FSSUBd5KOAjyJwywxe0jQ92VwkMC4KtXUT8iIHD8PwTORoV7hlpc8EDLpxfLUqk2zsBc5cmubitzz5MLCsl0uX4M2XgZF9l2DmLQE59ftE5NStg7rXJ+q126cGDL2V7KROp7x3E+AuyK2KKKqJfNi6eHzf6y8nP+og9AWJ3IBVtXZyhgAAAABJRU5ErkJggg==", style={"width": "auto", "height": "24px"})
    hydrological_icon = html.Img(
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABTElEQVR4nM2VO0sDQRDHrxAfxJ07bAQ7sbLwUfsZ7PxI+QA+GjEfwSZF4swqQtTCLt1hIciZmUNr0WChl8idFxIQ3UcScOAPVyy/3+7scBsE/6lCLXt5pgJXOt0BlPc8+fdE4ZXLh2UgSYGkX+Z54aKzMhl6qz8DJNcj8O8g3wan8ezYfEA+/AEfSg7Ggiud7v4KL5Ov8YKH9SRSxGISAMoTaF5y3z1xzQgfnIK45gRfbCbrgPxhKwDiz8oZb1gLALlhD5fBhTes4OH54yoQZx6CHmBnzShQKFVnOJV3gVK1EHDbX8Bts4C46y0g7tqc4NVfIC9GARDf+QoAJbZokRx5C4j3jYKwmW57jSlxFqFsGgWuvwkYTtBxYF2tZB5QbhwEVwHez9kLSokiPvm7XZwVO3eGj1SkZat4dFBihfxWjDFKnD821j2fZn0BzxejKOBMlnUAAAAASUVORK5CYII=", style={"width": "auto", "height": "24px"})
    climatological_icon = html.Img(
        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAAsTAAALEwEAmpwYAAABIUlEQVR4nOVVW04CQRCsQ4gHM3gF8RogF8CDAAcQf30kggehRnfg2zLTLjjgZkKv7peTdLLZna7qrtmuARxLAc8KeERXSwFK0SXBkwIe2gMQ1yLmiui5cyPORMxEDEoEM5OBWLQo7r7OnZaq6Im4EzHZv9vgXMRYxEoBWwtiKeImfcsIJpbr6V7EpQLi7nAbImqNvrfbb3DiowD+FWmPl8RkKVeuo6i80owd4Ko7GXkIXlsQLEvjr9wCnPJod+CNmPV0Kp/QlgRVlv8D81ii1Z9J1LRsiPwEwy5/0/fkRScTGMka/ZMH7Q0XLvADkoCqWLkHvLbcxYHZRTPAkYgXBWws0jMxzGURcWu5Jam6t2tikDb84sKZirjy5mIP8i8v/U/2bn/Cuda4GwAAAABJRU5ErkJggg==", style={"width": "auto", "height": "24px"})

    map_legend = html.Div(children=[
    dbc.Row(children=[
            dbc.Col(children=[
                html.Div(
                    children=[
                        geophysical_icon, html.P("Geophysical")
                    ], className="legend-item"
                )
            ], width=3),
            dbc.Col(children=[
                html.Div(
                    children=[
                        meteorological_icon, html.P("Meteorological")
                    ], className="legend-item"
                )
            ], width=3),
            dbc.Col(children=[
                html.Div(
                    children=[
                        hydrological_icon, html.P("Hydrological")
                    ], className="legend-item"
                )
            ], width=3),
            dbc.Col(children=[
                html.Div(
                    children=[
                        climatological_icon, html.P("Climatological")
                    ], className="legend-item"
                )
            ], width=3)
        ])
    ])
    animation_button = dbc.Button(children=[
        "Play",
        DashIconify(
            icon="material-symbols:play-arrow-rounded"
        )
    ],
        color="success",
        class_name="me-1",
        id="country-animation-button")
    
    animation_interval = dcc.Interval(
        'country-animation-interval', interval=500, disabled=True)

    country_slider_wrapper = dbc.Row(
        children=[
            dbc.Col(
                children=[
                    animation_button,
                    animation_interval
                ],
                className="column",
                width="auto"),
            dbc.Col(
                children=[
                    country_slider
                ],
                className="column")
        ], className="slider-container"
    )

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
            dl.GeoJSON(data=util.convert_events_to_geojson(map_data),  # Only show events of country
                       id="country-events",
                       options=dict(pointToLayer=ns("draw_marker"))),
            map_legend,
            country_slider_wrapper
        ],
        style={"width": "100%", "height": "100%", "display": "block"},
        id="detailed-map")

    gdp_graph = dcc.Graph(id='country-gdp-graph',
                          style={"height": "25vh", "width": "100%"})

    country_affected_graph = dcc.Graph(
        id='country-affected-graph', style={"height": "25vh", "width": "100%"})

    show_events_button = dbc.Button(
        "Show all events", color="primary", className="me-1 show-events", id="country-show-events")

    popup = dbc.Modal(
        children=[
            dbc.ModalHeader(dbc.ModalTitle(country_name)),
            html.Div(
                children=[
                    dbc.Row(
                        children=[
                            dbc.Col(
                                children=[
                                    dbc.Card(
                                        children=[
                                            dbc.CardHeader(
                                                children=[
                                                    "Map"
                                                ]
                                            ),
                                            dbc.CardBody(
                                                children=[
                                                    dbc.Row(
                                            children=[
                                                map_legend
                                            ],
                                            style={"height": "10%"}
                                        ),
                                        dbc.Row(
                                            children=[
                                                country_map
                                            ],
                                            style={"height": "90%", "marginRight": "0", "marginLeft": "0"}
                                        )
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
                                                        id="country-aggregated-data"),
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
                                                    dbc.Tabs(id='country-gdp-tabs', 
                                                        children=[
                                                            dbc.Tab(label="General",id='gdp-general',tab_id="general"),
                                                            dbc.Tab(label="Specific",id='gdp-specific',tab_id="specific")
                                                        ], active_tab="general"),
                                                        gdp_graph
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
                                                        id="country-affected-tabs",
                                                        active_tab="deaths"
                                                    ),
                                                    country_affected_graph
                                                ]
                                            )
                                        ],
                                        className="affected-card")
                                ],
                                width=6,
                                className="column affected-column")
                        ],
                        className="graphs-row")
                ], id="popup-content"
            ),
            html.Div(
                children=[
                    dbc.Offcanvas(
                        children=[
                            dbc.Accordion(
                                id="country-events-accordion"
                            )
                        ],
                        is_open=False,
                        placement="end",
                        id="country-offcanvas"
                    )
                ]
            )
        ],
        id=f"{country_iso}-modal",
        fullscreen=True,
        is_open=True,
        scrollable=True)
    return popup


def create_tab_with_fig(fig,category):
    return dbc.Tab(children=[
        dcc.Graph(figure=fig)
    ], label=category)

def generate_state_info(df, feature = None):
    header = [html.H4("% of money spent on mitigation in comparison with entire U.S.")]
    if not feature:
        return header + [html.P("Hover over a state")]
    else:
        state_name = feature["properties"]["NAME_1"]
        total_spent = util.get_total_spent(df)
        state_spent = util.get_state_spending(state_name, df)["total"]
    return header + [html.B(state_name), html.Br(),
                     "{:.3f}%".format((state_spent / total_spent) * 100)]

def generate_state_damages_info(df, feature = None):
    header = [html.H4("% of damages collected in comparison with the entire U.S")]
    if not feature:
        return header + [html.P("Hover over a state")]
    else:
        state_name = feature["properties"]["NAME_1"]
        total_spent = util.get_total_damages(df)
        state_spent = util.get_total_damages_state(df,state_name)
    return header + [html.B(state_name), html.Br(),
                     "{:.3f}%".format((state_spent / total_spent) * 100)]

def generate_country_info(df, current_year, feature=None):
    header = [html.H6("% of GDP in damages", style={'margin':0}), html.Br(), html.H6("because of Natural disasters", style={'margin':0})]
    if not feature:
        return header + [html.P("Hover over a country")]
    else:
        df = df[df['Start Year'] == current_year].groupby('ISO').sum(numeric_only=True)
        country_name = feature['properties']['ISO_A3']
        if (country_name in df.index):
            value = df.loc[country_name, "share"]
        else:
            value = 0
        return header + [html.B(country_name), html.Br(), format(value)]
    
def generate_average_death_comparison_bar_plot(df_disasters):
    before_fema, after_fema = util.compare_deaths_before_and_after_fema(df_disasters)

    fig = go.Figure(
        data=[
            go.Bar(x=before_fema['us state'], y=before_fema['Total Deaths'], name='Mean death rate before FEMA'),
            go.Bar(x=after_fema['us state'], y=after_fema['Total Deaths'], name='Mean death rate after FEMA')
        ]
    )
    fig.update_layout(barmode='group',title=f"Average death comparison before and after Fema's actions (Fema's first actions date from 1989)")
    fig.update_layout(hovermode="x unified")
    return fig

        
                


        
        
        
    

