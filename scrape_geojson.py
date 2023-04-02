import requests
import pandas as pd
import zipfile
import io
import os

iso_codes = pd.read_csv('./Data/iso_codes.csv')

for iso_code in iso_codes['alpha-3']:
    # iso_code = "BEL"
    print(f'fetching {iso_code} data')
    url = f'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{iso_code}_2.json.zip'
    request = requests.get(url, stream=True)
    if (request.status_code == 200):
        zfile = zipfile.ZipFile(io.BytesIO(request.content))
        file = zfile.namelist()[0] # there should only be one file in the zip archive
        zfile.extract(file,f'./Data/GeoJson/')
        os.rename(f'./Data/GeoJson/gadm41_{iso_code}_2.json', f'./Data/GeoJson/{iso_code}.json')