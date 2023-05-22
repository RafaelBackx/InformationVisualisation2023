import pandas as pd
import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash_extensions.javascript import arrow_function, Namespace

import util

import converter as converter
import components

ns = Namespace('dashExtensions', 'default')

df_properties = pd.read_json('./Data/preprocessed-fema-properties.json')
df_projects = pd.read_json('./Data/preprocessed-fema-projects.json')
df_disasters = pd.read_csv('./Data/Preprocessed-Natural-Disasters.csv', delimiter=';')

death_graph = dcc.Graph(id='death_graph', figure=components.generate_average_death_comparison_bar_plot(df_disasters))

usa_states_data = util.get_country_data('USA')

classes = [0,5,10,15,20,25]
colorscale = ['#ffffb2', '#fed976', '#feb24c', '#fd8d3c', '#f03b20', '#bd0026']
style = dict(weight=2, opacity=1, color='black', dashArray='', fillOpacity=0.7)
ctg = ["{}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{}+".format(classes[-1])]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=300, height=30, position="bottomleft")

state_info = html.Div(id="info", className="map-info", style={"position": "absolute", "top": "10px", "right": "10px", "zIndex": "1000"})
state_damages_info = html.Div(id="damages_info", className="map-info", style={"position": "absolute", "top": "10px", "right": "10px", "zIndex": "1000"})

map1 = dl.Map(
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
            data=usa_states_data,
            id="usa-states-1",
            hideout=dict(colorscale=colorscale,classes=classes,style=style,active_state='',ratio_map=util.generate_states_spent_ratio(usa_states_data,df_properties)),
            # Invisible polygons,
            options=dict(style = ns('draw_polygon')),
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=2, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
        colorbar,
        state_info
    ],
    style={"width": "100%", "height": "100%", "display": "block"},
    id="usa-map-1")

map2 = dl.Map(
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
            data=usa_states_data,
            id="usa-states-2",
            hideout=dict(colorscale=colorscale,classes=classes,style=style,active_state='',ratio_map=util.generate_states_damages_ratio(usa_states_data,df_disasters)),
            # Invisible polygons,
            options=dict(style = ns('draw_polygon')),
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=2, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
        colorbar,
        state_damages_info
    ],
    style={"width": "100%", "height": "100%", "display": "block"},
    id="usa-map-2")


us_layout = html.Div(id='us_layout', children=[
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader(children=["USA Map - Mitigation ratio's"]),
                            dbc.CardBody(children=map1)
                        ],
                        className='map-card'
                    )
                ],
                width=6,
                className="column us-map-column gdp-column mit-map"
            ),
            dbc.Col(children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader(children=["USA Map - Damage ratio's"]),
                            dbc.CardBody(children=map2)
                        ],
                        className='map-card'
                    )
                ],
                width=6,
                className="column us-map-column affected-column"
            ),
        ],
        className="map-row us-map-row",
    ),
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader("Disaster cost distribution over subgroups U.S.", id="us-cost-distribution-subgroups-header"),
                            dbc.CardBody(children=[html.Div(id="us-cost-distribution-subgroups")])
                        ]
                    )
                ],
                className="column gdp-column",
                width=6
            ),
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader("Disaster cost distribution over mitigations U.S.", id="us-cost-distribution-mitigations-header"),
                            dbc.CardBody(children=[html.Div(id="us-cost-distribution-mitigations")])
                        ]
                    )
                ],
                className="column affected-column",
                width=6
            )
        ],
        className="graphs-row us-graphs-row"
    ),
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader('Comparison of deaths before and after Fema intervention'),
                            dbc.CardBody(children=[death_graph])
                        ]
                    )       
                ],
                width=12,
                className='column fema-column'
            )
        ],
        className="graphs-row us-graphs-row")
])