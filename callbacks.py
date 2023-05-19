import plotly.express as px
from dash import dcc
import dash_bootstrap_components as dbc
import pandas as pd

import components
import converter as state_converter
import us_layout
import util
import locale

locale.setlocale(locale.LC_ALL, '')

from dash import html

def update_map_on_slider_increment(clicked_state,data):
    colour_map = us_layout.generate_states_colours(data)
    print({'active_state': clicked_state, 'colour_map': colour_map})
    return {'active_state': clicked_state, 'colour_map': colour_map}


def create_cost_distributions_for_state(state):
    disaster_cost_distribution, fema_cost_distribution = us_layout.get_disaster_and_fema_cost_distribution_per_state(state)
    fema_disaster_map = {key: value[1] for key,value in fema_cost_distribution.items()}
    fema_cost_distribution = {key: value[0] for key,value in fema_cost_distribution.items()}
    disaster_map = {key:key for key,_ in disaster_cost_distribution.items()}
    disaster_bar_plot = components.generate_cost_bar_plots(disaster_cost_distribution, disaster_map)
    fema_bar_plot = components.generate_cost_bar_plots(fema_cost_distribution, fema_disaster_map)
    return disaster_bar_plot, fema_bar_plot

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

def changed_affected_filter(events, current_year, current_filter, country_code = None):
    # If a country code is given filter events using the code
    if country_code:
        events = util.filter_events(events, {'ISO': country_code})

    # Filter events to go up until current year
    events = events[events["Start Year"] <= current_year]

    # Generate the updated graph
    return components.generate_affected_graph(events, current_year, current_filter)

def changed_gdp_filter(gdp_data, current_year, country_code = None, specific = False):
    # If a country code is given filter events using the code
    if country_code:
        gdp_data = util.filter_events(gdp_data, {'ISO': country_code})
    else:
        gdp_data = gdp_data.groupby(["Start Year", "Disaster Subgroup", "Disaster Type"], as_index=False).sum(numeric_only=True)

    # Generate the updated graph
    return components.generate_gdp_graph(gdp_data, current_year, specific)

def show_events_button_clicked(events, current_year, country_code = None):
    # If a country code is given filter events using the code
    if country_code:
        events = util.filter_events(events, {'ISO': country_code})

    # Filter the events by the current year
    events = util.filter_events(events, {"Start Year": current_year})

    # Return the updated component
    return components.create_events_accordion(events)

def slider_change(events, gdp_data, current_year, affected_filter, gdp_filter, country_code = None):
    # If a country code is given filter events using the code
    if country_code:
        events = util.filter_events(events, {'ISO': country_code})
        gdp_data = util.filter_events(gdp_data, {'ISO': country_code})
    else:
        gdp_data = gdp_data.groupby(["Start Year", "Disaster Subgroup"], as_index=False).sum(numeric_only=True)

    # Filter the events that contain location data for the map
    map_data = util.filter_events(events, {"Start Year": current_year}, True)

    # Filter the events by year
    yearly_data = util.filter_events(events, {"Start Year": current_year})

    # Convert events to geojson for the map
    events_geojson = util.convert_events_to_geojson(map_data)

    # Generate the gdp figure
    gdp_fig = components.generate_gdp_graph(gdp_data, current_year, gdp_filter != "general")

    # Generate the affected figure
    affected_fig = components.generate_affected_graph(events, current_year, affected_filter)

    # Generate the aggregated data component
    aggregated_data = components.generate_aggregated_data_table(yearly_data)

    return events_geojson, gdp_fig, affected_fig, aggregated_data