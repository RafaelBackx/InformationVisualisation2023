import pandas as pd
import numpy as np
import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_bootstrap_components as dbc
from dash import Dash, html, Input, Output, dcc, State, ALL, dash
from dash_extensions.javascript import arrow_function, Namespace
from dash.exceptions import PreventUpdate
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go

import util
import components

import converter as converter

ns = Namespace('dashExtensions', 'default')

df_properties = pd.read_json('./Data/preprocessed-fema-properties.json')
df_projects = pd.read_json('./Data/preprocessed-fema-projects.json')
df_disasters = pd.read_csv('./Data/Preprocessed-Natural-Disasters.csv', delimiter=';')

def get_state_spending(state):
    if (state):
        state_properties = df_properties[(df_properties['state'] == state)]
    else:
        state_properties = df_properties

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

def get_total_spent():
    total_properties = df_properties.sum(numeric_only=True)
    total_spent = total_properties['actualAmountPaid']
    return total_spent

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

def get_disaster_and_fema_cost_distribution_per_state(state):
    if (state):
        state_disaster_info = df_disasters[df_disasters['us state'] == state]
        state_fema_info = df_properties[df_properties['state'] == state]
    else:
        state_disaster_info = df_disasters
        state_fema_info = df_properties

    state_disaster_grouped = state_disaster_info.groupby(['Disaster Subgroup'], as_index=False).sum(numeric_only=True)
    state_fema_grouped = state_fema_info.groupby(['propertyAction'], as_index=False).sum(numeric_only=True)

    disaster_subgroups = state_disaster_grouped['Disaster Subgroup'].values
    fema_actions = state_fema_grouped['propertyAction'].values

    disaster_subgroup_map = {}
    fema_action_map = {}

    for disaster_subgroup in disaster_subgroups:
        spent_on_disaster = sum(state_disaster_grouped[state_disaster_grouped['Disaster Subgroup'] == disaster_subgroup]["Total Damages, Adjusted (\'000 US$)"], 0)
        disaster_subgroup_map[disaster_subgroup] = spent_on_disaster
    
    for fema_action in fema_actions:
        spent_on_action = sum(state_fema_grouped[state_fema_grouped['propertyAction'] == fema_action]['actualAmountPaid'], 0)
        if (fema_action in converter.fema_action_to_disaster):
            to_prevent_disaster = converter.fema_action_to_disaster[fema_action]
        else:
            continue
        fema_action_map[fema_action] = [spent_on_action, to_prevent_disaster]
    
    return disaster_subgroup_map, fema_action_map

def compare_deaths_before_and_after_fema(df_disasters):
    fema_date = 1995
    us_disasters = df_disasters[df_disasters['ISO'] == 'USA'].groupby(['Start Year', 'us state'], as_index=False).sum(numeric_only=True)
    before_fema = us_disasters[us_disasters['Start Year'] < fema_date].groupby('us state', as_index=False).sum(numeric_only=True)
    number_of_deaths_before_fema = before_fema['Total Deaths'].sum()
    number_of_events_per_year_before_fema = len(us_disasters[us_disasters['Start Year'] <= fema_date])
    death_ratio_before = np.round(number_of_deaths_before_fema/number_of_events_per_year_before_fema)

    after_fema = us_disasters[us_disasters['Start Year'] >= fema_date].groupby('us state', as_index=False).sum(numeric_only=True)
    number_of_deaths_after_fema = after_fema['Total Deaths'].sum()
    number_events_per_year_after_fema = len(us_disasters[us_disasters['Start Year'] > fema_date])
    death_ratio_after = np.round(number_of_deaths_after_fema / number_events_per_year_after_fema)

    new_df = pd.DataFrame(columns=['state', 'Deaths before Fema', 'Deaths after Fema'])
    new_df['state'] = after_fema['us state']
    new_df['Deaths before Fema'] = new_df.apply(lambda row: sum(before_fema[before_fema['us state'] == row['state']]['Total Deaths'], 0), axis=1)
    new_df['Deaths after Fema'] = new_df.apply(lambda row: sum(after_fema[after_fema['us state'] == row['state']]['Total Deaths'],0), axis=1)
    fig = go.Figure(data=[
        go.Bar(x=new_df['state'], y=new_df['Deaths before Fema'], name='Deaths before Fema'),
        go.Bar(x=new_df['state'], y=new_df['Deaths after Fema'], name='Deaths after Fema')
    ])
    fig.update_layout(barmode='group',title=f"Death toll comparison before Fema was introduced and after (Fema's first datapoint dates from 1995)")
    fig.add_annotation(text=f'Average deaths per disaser <br>before Fema: {death_ratio_before} <br>after Fema: {death_ratio_after}', 
                        align='left',
                        showarrow=False,
                        xref='paper',
                        yref='paper',
                        x=1.12,
                        y=0.8,
                        bordercolor='black',
                        borderwidth=1)
    return fig

def compare_mitigation_and_damages_graph(df_disasters):
    us_disasters = df_disasters[df_disasters['ISO'] == 'USA']
    us_disasters = us_disasters.groupby(['us state'], as_index=False).sum(numeric_only=True)
    state_properties = df_properties.groupby(['state'], as_index=False).sum(numeric_only=True)


    df_to_compare = pd.DataFrame(columns=['state', 'mitigation costs', 'damages'])
    df_to_compare['state'] = df_properties['state'].unique()
    df_to_compare['mitigation costs'] = df_to_compare.apply(lambda row: sum(state_properties[state_properties['state'] == row['state']]['actualAmountPaid'].values,0), axis=1)
    df_to_compare['damages'] = df_to_compare.apply(lambda row: sum(us_disasters[us_disasters['us state'] == row['state']]["Total Damages, Adjusted ('000 US$)"].values,0), axis=1)
    
    return px.bar(df_to_compare, x='state', y=['mitigation costs', 'damages'], log_y=True)

def compare_prevention_costs_with_other_country(df_disasters, country=None):
    df_disasters_us = df_disasters[df_disasters['ISO'] == 'USA']

    all_country_iso = df_disasters['ISO'].unique()
    years = df_disasters['Start Year'].unique()
    grouped = df_properties.groupby('programFy', as_index=False).sum(numeric_only=True)
    grouped['actualAmountPaid'] = grouped['actualAmountPaid'].cumsum()
    disasters_grouped = df_disasters_us.groupby('Start Year', as_index=False).sum(numeric_only=True)
    disasters_grouped["Total Damages, Adjusted ('000 US$)"] = disasters_grouped["Total Damages, Adjusted ('000 US$)"].cumsum()

    def get_prevention_costs(row):
        prevention_row = grouped[grouped['programFy'] == row['Start Year']]
        if (prevention_row.empty):
            return 0.
        return prevention_row['actualAmountPaid']

    def get_total_costs(start_year, country = None):
        if country:
            country_disasters = df_disasters[df_disasters['ISO'] == country]
        else:
            country_disasters = df_disasters[df_disasters['ISO'] != "USA"]
        country_grouped = country_disasters.groupby('Start Year', as_index=False).mean(numeric_only=True)
        country_grouped["Total Damages, Adjusted ('000 US$)"] = country_grouped["Total Damages, Adjusted ('000 US$)"].cumsum()
        other_country_row = country_grouped[country_grouped['Start Year'] == start_year]
        if other_country_row.empty:
            return 0
        else:
            return other_country_row["Total Damages, Adjusted ('000 US$)"].mean()


    disasters_grouped['prevention costs'] = disasters_grouped.apply(get_prevention_costs, axis=1)
    disasters_grouped['prevention costs'] = disasters_grouped['prevention costs'].astype(dtype=float)
    disasters_grouped['world average'] = disasters_grouped.apply((lambda row: get_total_costs(row["Start Year"])), axis=1)
    disasters_grouped['world average'] = disasters_grouped['world average'].astype(dtype=float)
    
    return px.line(disasters_grouped[disasters_grouped['Start Year'] < 2023], 'Start Year', ["Total Damages, Adjusted ('000 US$)", 'world average'])

def generate_states_colours(data):
    features = data['features']
    state_iso_original = [feature['properties']['ISO_1'] for feature in features]
    state_iso = [name.split('-')[1] for name in state_iso_original]
    state_names = [converter.abbrev_to_us_state[abbrev] for abbrev in state_iso]

    colour_map = {}
    for idx,state_name in enumerate(state_names):
        id = state_iso_original[idx]
        state_spending = get_state_spending(state_name)
        total_spent_state = state_spending['total']
        total_spent_us = get_total_spent()
        total_spent_us = max(total_spent_us, 1)
        # colour = util.ratio_to_gradient(total_spent_state/total_spent_us)
        colour_map[id] = (total_spent_state/total_spent_us) * 100
    return colour_map

death_graph = dcc.Graph(id='death_graph', figure=compare_deaths_before_and_after_fema(df_disasters))
mitigation_graph = dcc.Graph(id='mitigation-graph', figure=compare_mitigation_and_damages_graph(df_disasters))

usa_states_data = util.get_country_data('USA')

classes = [0,5,10,15,20,25]
colorscale = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026']
style = dict(weight=2, opacity=1, color='black', dashArray='', fillOpacity=0.7)
ctg = ["{}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{}+".format(classes[-1])]
colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=300, height=30, position="bottomleft")

def get_info(feature=None):
    header = [html.H4("% of money spent on mitigation in comparison with entire U.S.")]
    if not feature:
        return header + [html.P("Hover over a state")]
    else:
        state_name = feature["properties"]["NAME_1"]
        total_spent = get_total_spent()
        state_spent = get_state_spending(state_name)["total"]
    return header + [html.B(state_name), html.Br(),
                     "{:.3f}%".format((state_spent / total_spent) * 100)]

state_info = html.Div(children=get_info(), id="info", className="map-info", style={"position": "absolute", "top": "10px", "right": "10px", "z-index": "1000"})

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
            data=usa_states_data,
            id="usa-states",
            hideout=dict(colorscale=colorscale,classes=classes,style=style,active_state='',ratio_map=generate_states_colours(usa_states_data)),
            # Invisible polygons,
            options=dict(style = ns('draw_polygon')),
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=2, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
        colorbar,
        state_info
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
                className="column map-column us-map-column"
            )
        ],
        className="map-row us-map-row"
    ),
    dbc.Row(
        children=[
            dbc.Col(
                children=[
                    dbc.Card(
                        children=[
                            dbc.CardHeader("Disaster cost distribution over subgroups"),
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
                            dbc.CardHeader("Disaster cost distribution over mitigations"),
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