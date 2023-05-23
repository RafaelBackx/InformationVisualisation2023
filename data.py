import pandas as pd

df_disasters = pd.read_csv("Data/Preprocessed-Natural-Disasters.csv", delimiter=";")
df_gdp = pd.read_csv('./Data/gdp_data2.csv')
df_properties = pd.read_json('./Data/preprocessed-fema-properties.json')
df_projects = pd.read_json('./Data/preprocessed-fema-projects.json')