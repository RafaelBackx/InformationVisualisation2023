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
import converter as converter

ns = Namespace('dashExtensions', 'default')

df_properties = pd.read_json('./Data/preprocessed-fema-properties.json')
df_projects = pd.read_json('./Data/preprocessed-fema-projects.json')

usa_slider = dcc.Slider(min=1995,
                          max=2023,
                          step=1,
                          value=1995,
                          marks=None,
                          tooltip={"placement": "bottom",
                                   "always_visible": True},
                          id="usa-slider",
                          className="slider")

usa_slider_wrapper = dbc.Row(
    children=[
        dbc.Col(
            children=[
                # animation_button
            ],
            className="column",
            width="auto"),
        dbc.Col(
            children=[
                usa_slider
            ],
            className="column")
    ], className="slider-container"
)

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
            id="usa-states",
            # Invisible polygons,
            options=dict(style = ns('draw_polygon')),
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=2, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
        usa_slider_wrapper
    ],
    style={"width": "100%", "height": "100%", "display": "block"},
    id="usa-map")


us_layout = html.Div(id='us_layout', children=[
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader(children=['USA Map']),
                            dbc.CardBody(children=map)
                        ],
                        className='map-card'
                    )
                ],
                width=9,
                className='column map-column'
            ),
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader("Aggregated Data"),
                            dbc.CardBody(children=[html.Div(id='us-aggregated-data')])
                        ],
                        className='aggregated-card'
                    )
                ],
                width=3,
                className='column aggregated-column'
            )
        ],
        className='map-row'
    ),
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader('Fema actions to disaster costs'),
                            dbc.CardBody(children=[dbc.Tabs(id='fema-disaster-graphs')])
                        ]
                    )
                ],
                width=6,
                className='column fema-column'
            ),
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader('Fema Cost distribution - '),
                            dbc.CardBody(
                                id='fema-cost-distribution',
                                children=[
                                    dbc.Tabs(id='fema-cost-distribution-tabs')
                                ]
                            )
                        ]
                    )
                ],
                width=6,
                className='column'
            )
        ]
    )
])

def get_state_spending(state,year):
    if (state):
        state_properties = df_properties[(df_properties['state'] == state) & (df_properties['programFy'] == year)]
    else:
        state_properties = df_properties[df_properties['programFy'] == year]

    state_properties_grouped = state_properties.groupby(['programArea'], as_index=False).sum(numeric_only=True)

    different_programs = ['FMA','HMGP', 'LPDM', 'PDM', 'RFC', 'SRL']
    state_spending_map = {}
    total_spending = 0
    for program in different_programs:
        amount_spent = state_properties_grouped[state_properties_grouped['programArea'] == program]['actualAmountPaid'].values
        if (len(amount_spent) > 0):
            amount_spent = amount_spent[0]
        else:
            amount_spent = 0
        state_spending_map[program] = amount_spent
        total_spending += amount_spent
    state_spending_map['total'] = total_spending

    return state_spending_map

def get_total_spent(year):
    total_properties = df_properties[df_properties['programFy'] == year].sum(numeric_only=True)
    total_spent = total_properties['actualAmountPaid']
    return total_spent

#TODO add year to function
def compare_fema_actions_to_disaster_costs(df_disasters: pd.DataFrame, year: int) -> pd.DataFrame:
    # calculate total costs per disaster subgroup
    df_disasters_us = df_disasters[df_disasters['ISO'] == 'USA']
    df_disasters_us_grouped = df_disasters_us.groupby(['Disaster Subgroup', 'Start Year'], as_index=False).sum(numeric_only=True)
    disaster_spent = df_disasters_us_grouped[['Disaster Subgroup', "Total Damages, Adjusted ('000 US$)", 'Start Year']]

    # calculate spent on each type => prevention of subgroup
    years = list(range(1960,2024))
    categories = ['Climatological','Geophysical', 'Hydrological', 'Meteorological']

    spent_map = {year : {cat : 0 for cat in categories} for year in years}

    df_properties_grouped = df_properties.groupby(['propertyAction', 'programFy'], as_index=False).sum(numeric_only=True)
    for _,row in df_properties_grouped.iterrows():
        action = row['propertyAction']
        row_year = row['programFy']
        if (action in converter.fema_action_to_disaster):
            disaster_subgroup = converter.fema_action_to_disaster[action]
        else:
            continue
        spent_map[row_year][disaster_subgroup] += row['actualAmountPaid']

    disaster_spent['Total Mitigated'] = disaster_spent.apply(lambda x: spent_map[x['Start Year']][x['Disaster Subgroup']], axis=1)
    print(disaster_spent)
    return disaster_spent

def get_fema_cost_distribution(state,year,category):
    if (state):
        data = df_properties[df_properties['state'] == state]
    else:
        data = df_properties

    categories = data.groupby(category, as_index=False).sum(numeric_only=True)
    total_spent = sum(categories['actualAmountPaid'].values)      
    categories['spent percentage'] = categories.apply(lambda x: x['actualAmountPaid']/total_spent, axis=1)
    return categories
