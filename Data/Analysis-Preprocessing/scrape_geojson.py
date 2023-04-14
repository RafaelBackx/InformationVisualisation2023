import requests
import pandas as pd
import zipfile
import io
import os
import shapely
import json

iso_codes = pd.read_csv('../iso_codes.csv')
version = 1 # 0 = country layout, 1 = level above provinces (states I guess ?), 2 = Provinces

def simplify_geojson(file_name, simplify_param):
    file = open(file_name,'r+',encoding='utf-8')
    geojson = json.load(file)
    data = shapely.from_geojson(json.dumps(geojson))

    data_simple = data.simplify(simplify_param, preserve_topology=True)
    geojson_simple = shapely.to_geojson(data_simple)
    geojson_simple_json = json.loads(geojson_simple)
    # print(type(geojson_simple_json))
    # print(type(geojson))
    simple_geometries = geojson_simple_json['geometries']
    features = geojson['features']
    for idx,feature in enumerate(features):
        feature['geometry'] = {'type': 'MultiPolygon', 'coordinates': [simple_geometries[idx]['coordinates']]}
    # geometry = {'type': 'MultiPolygon', 'coordinates': [geometry['coordinates'] for geometry in simple_geometries]}
    geojson['features'] = features
    file.seek(0)
    file.write(json.dumps(geojson))
    file.truncate()


for iso_code in iso_codes['alpha-3']:
    print(f'fetching {iso_code} data')
    url = f'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{iso_code}_{version}.json.zip'
    request = requests.get(url, stream=True)
    if (request.status_code == 200):
        zfile = zipfile.ZipFile(io.BytesIO(request.content))
        file = zfile.namelist()[0] # there should only be one file in the zip archive
        zfile.extract(file,f'../GeoJson{version}/')
        os.rename(f'../GeoJson{version}/gadm41_{iso_code}_{version}.json', f'../GeoJson{version}/{iso_code}.json')
        # simplify geojson data
        simplify_geojson(f'../GeoJson{version}/{iso_code}.json', 0.5)

