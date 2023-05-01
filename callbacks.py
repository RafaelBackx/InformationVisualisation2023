import plotly.express as px
from dash import dcc
import dash_bootstrap_components as dbc

import components
import converter as state_converter
import us_layout
import util
import locale

locale.setlocale(locale.LC_ALL, '')

from dash import html

def update_map_on_slider_increment(slider_value,  data):
    print(slider_value)
    features = data['features']
    state_iso_original = [feature['properties']['ISO_1'] for feature in features]
    state_iso = [name.split('-')[1] for name in state_iso_original]
    state_names = [state_converter.abbrev_to_us_state[abbrev] for abbrev in state_iso]

    colour_map = {}

    for idx,state_name in enumerate(state_names):
        id = state_iso_original[idx]
        state_spending = us_layout.get_state_spending(state_name,slider_value)
        total_spent_state = state_spending['total']
        total_spent_us = us_layout.get_total_spent(slider_value)
        total_spent_us = max(total_spent_us, 1)
        colour = util.ratio_to_gradient(total_spent_state/total_spent_us)
        colour_map[id] = colour
    return colour_map

def update_aggregated_data_on_slider_increment(slider_value, df_properties):
    spending = us_layout.get_state_spending(state=None,year=slider_value)
    spending = dict(sorted(spending.items(),key= lambda x:x[1], reverse=True))
    #TODO move total to the end
    return [html.P(f'{program} - {locale.currency(spent, grouping=True)}') for program,spent in spending.items()]

def create_fema_disaster_graph(df_disasters, year):
    df = us_layout.compare_fema_actions_to_disaster_costs(df_disasters, year)
    categories = df['Disaster Subgroup'].unique()
    tabs = []
    for category in categories:
        fig = px.line(df[df['Disaster Subgroup'] == category],'Start Year', ["Total Damages, Adjusted ('000 US$)", 'Total Mitigated'], log_y=False)
        tab = components.create_tab_with_fig(fig,category)
        tabs.append(tab)
    return tabs

def create_fema_cost_distribution(year,categories):
    children = []
    for category in categories:
        data = us_layout.get_fema_cost_distribution(None,year,category)
        fig = px.bar(data,category,'spent percentage')
        child = dbc.Tab(dcc.Graph(figure=fig), label=category)
        children.append(child)
    return children



