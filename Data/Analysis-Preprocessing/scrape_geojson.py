import requests
import pandas as pd
import zipfile
import io
import os

iso_codes = pd.read_csv('../iso_codes.csv')
version = 1 # 0 = country layout, 1 = level above provinces (states I guess ?), 2 = Provinces


for iso_code in iso_codes['alpha-3']:
    print(f'fetching {iso_code} data')
    url = f'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{iso_code}_{version}.json.zip'
    request = requests.get(url, stream=True)
    if (request.status_code == 200):
        zfile = zipfile.ZipFile(io.BytesIO(request.content))
        file = zfile.namelist()[0] # there should only be one file in the zip archive
        zfile.extract(file,f'../GeoJson{version}/')
        os.rename(f'../GeoJson{version}/gadm41_{iso_code}_{version}.json', f'../GeoJson{version}/{iso_code}.json')