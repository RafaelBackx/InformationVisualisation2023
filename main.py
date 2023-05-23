from dash import Dash, html, Input, Output, dcc, State
from dash_extensions.javascript import arrow_function, Namespace
import dash_leaflet as dl
import math
import pandas as pd
import util
from converter import abbrev_to_us_state
import colorsys
import locale
import data

locale.setlocale(locale.LC_ALL, '')


ns = Namespace("dashExtensions", "default")

app = Dash(__name__)

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
            id="countries",
            # Invisible polygons,
            options=dict(style = ns('draw_polygon')),
            zoomToBounds=True,
            hoverStyle=arrow_function(dict(weight=3, color='#666', dashArray=''))),  # Gray border on hover (line_thickness, color, line_style)
    ],
    style={"width": "75vw", "height": "90%", "display": "block"},
    id="map")

slider = dcc.Slider(min=1960,
                          max=2023,
                          step=1,
                          value=2000,
                          marks=None,
                          tooltip={"placement": "bottom",
                                   "always_visible": True},
                          id="slider",
                          className="slider")


app.layout = html.Div([
    html.H1("USA test"),
    html.Div(children=[
        map,
        html.Div(id='aggregated-data', style={'width': '25vw'})
    ], style={'display': 'flex', 'gap': '2vw', 'height': '80vh'}),
    slider
    # dcc.Graph(figure=px.line(states,'programFy', 'actualAmountPaid', color='state')),
    # dcc.Graph(figure=px.line(df_disasters_us_states, 'Start Year', 'Total Damages, Adjusted (\'000 US$)', color='us state'))
],style={'width': '100vw', 'height': '100vh'})

def generate_aggregated_data(df_states: pd.DataFrame, df_disasters, year, state=None):
    df_states_year_program = df_states.groupby(['programFy', 'programArea'], as_index=False).sum(numeric_only=True)
    df_states_year_program = df_states_year_program[df_states_year_program['programFy'] == year]

    df_states_year_program.sort_values(by='actualAmountPaid',inplace=True, ascending=False)

    programs = [html.P(f'{program["programArea"]} - {locale.currency(program["actualAmountPaid"], grouping=True)}') for _,program in df_states_year_program.head(5).iterrows()]

    return html.Div(children=[html.H5('Top 5 funded programs'), *programs])


@app.callback([Output('countries', 'hideout'), Output('aggregated-data', 'children')], Input('slider','value'), State('countries', 'data'))
def slider_callback(value, country_data):

    df_disasters = pd.read_csv('./Data/Preprocessed-Natural-Disasters.csv', delimiter=';')
    df_disasters_us = df_disasters[df_disasters['ISO'] == 'USA']
    # df_disasters_us = util.filter_map_events(df_disasters_us, {'Disaster Subgroup': 'Hydrological'})
    df_disasters_us_states = df_disasters_us.groupby(['Start Year', 'us state'], as_index=False).sum(numeric_only=True)

    total_costs = data.df_properties[data.df_properties['programFy'] == value].sum(numeric_only=True)['actualAmountPaid']

    # states = df_properties[df_properties['programArea'] == 'FMA']
    states = data.df_properties.groupby(['programFy', 'state'], as_index=False).sum(numeric_only=True)

    spent = states[states['programFy'] == value]
    costs = df_disasters_us_states[df_disasters_us_states['Start Year'] <= value]

    # spent = spent[spent['programArea'] == 'FMA'] # get all data about flood prevention
    # costs = costs[costs['Disaster Subgroup'] == 'Hydrological'] # get all hydrological events

    features = country_data['features']
    state_iso_original = [feature['properties']['ISO_1'] for feature in features]
    state_iso = [name.split('-')[1] for name in state_iso_original]
    state_names = [abbrev_to_us_state[abbrev] for abbrev in state_iso]

    children = generate_aggregated_data(data.df_properties, df_disasters, value)
    state_map = {}
    for idx,state in enumerate(state_names):
        id = state_iso_original[idx]
        spent_state = sum(spent[spent['state'] == state]['actualAmountPaid'].values,start=0)
        costs_state = sum(costs[costs['us state'] == state]['Total Damages, Adjusted (\'000 US$)'].values, start=0)

        # print(f'state: {state} spent: {spent_state} of the total: {total_costs}')

        gradient = 0.5          # neutral, costs == spent
        if (spent_state < costs_state):     # red, this is bad
            ratio = (spent_state/costs_state)/2 # divide by 2 since we have to map between 0 - 0.5 instead of 0 -1
            gradient -= ratio 
        elif (spent_state > costs_state):   # green, this is good
            ratio = (costs_state/spent_state)/2 # divide by 2 since we have to map between 0 - 0.5 instead of 0 -1
            gradient -= ratio

        # gradient = spent_state / total_costs
        gradient *= 100
        print(gradient)
        h = math.floor((100 - gradient) * 120 / 100)
        s = abs(gradient - 50) / 50
        v = 1
        r,g,b = colorsys.hsv_to_rgb(h,s,v)
        colour = '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))
        state_map[id] = colour

    print(state_map)
    return state_map, children

@app.callback(Output('aggregated-data', 'children', allow_duplicate=True),Input('countries', 'n_clicks'), [State('countries', 'click_feature'), State('slider', 'value')], prevent_initial_call=True)
def on_state_click(n_clicks, state, value):
    state_iso = state['properties']['ISO_1']
    iso = state_iso.split('-')[1]
    state_name = abbrev_to_us_state[iso]

    state_data = data.df_properties[(data.df_properties['programFy'] == value) & (data.df_properties['state'] == state_name)]
    total_spent = state_data.sum(numeric_only=True)['actualAmountPaid']

    grouped_state_data = state_data.groupby(['programArea'], as_index=False).sum(numeric_only=True)
    grouped_state_data.sort_values(by=['actualAmountPaid'], ascending=False, inplace=True)

    programs = [html.P(f'{program["programArea"]} - {locale.currency(program["actualAmountPaid"], grouping=True)}') for _,program in grouped_state_data.head(5).iterrows()]

    return html.Div(children=[html.H5(f'Top 5 funded programs - {state_name}'), *programs])

    # return dash.no_update

if __name__ == "__main__":
    app.run_server(debug=True)