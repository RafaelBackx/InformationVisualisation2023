import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

APP_TITLE = 'Distribution of natural disasters'
APP_SUB_TITLE = 'sub title'

def display_informations(df, year, country, disaster_type):
    df = df[(df['Year'] == year) & (df['Disaster Type'] == disaster_type)]
    if country:
        df = df[(df['Country'] == country)]

def display_map(df, year, country):
    df = df[(df['Year'] == year) & (df['Country'] == country)]

    map = folium.Map()
    st_map = st_folium(map, width = 700, height = 450)

    st.write(df.shape)
    st.write(df.head())
    st.write(df.columns)

def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)

    #Load data
    df = pd.read_csv('../Data/Natural-Disasters.csv', sep=';')

    year = 1912
    country = 'Turkey'
    disaster_type = 'Earthquake'

    display_informations(df, year, country, disaster_type)

    #Display filter and map

    display_map(df, year, country)

    

    


if __name__ == '__main__':
    main()
