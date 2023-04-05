import streamlit as st
import pandas as pd
import plotly.express as px


disaster_data = pd.read_csv("./Data/Preprocessed-Natural-Disasters.csv", delimiter=";")


year = st.slider("Select a year", 1960, 2023, 2000)
map_data = disaster_data[(disaster_data["Latitude"].notnull()) & (disaster_data["Longitude"].notnull()) & (disaster_data["Start Year"] == year)]

# Create the map
st.write("Natural Disasters Map")
fig = px.scatter_mapbox(map_data, lat="Latitude", lon="Longitude", hover_name="Disaster Subgroup", hover_data=["Start Year", "Disaster Type", "Disaster Subtype"], zoom=1)
fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
st.plotly_chart(fig)
