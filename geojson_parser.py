import pandas as pd
import json
from bs4 import BeautifulSoup

def combine_coord(df):
    return (df['x'],df['y'])

def geojson_parser():
    with open("URAParkingLotGEOJSON.geojson") as f:
        data = json.load(f)

    data_features = data['features']

    # Parse the HTML
    soup = BeautifulSoup(data_features[0]['properties']['Description'], 'lxml')

    # Extract the required values
    type_value = soup.find('th', string='TYPE').find_next('td').text
    parking_pl_value = soup.find('th', string='PARKING_PL').find_next('td').text
    lot_value = soup.find('th', string='LOT_NO').find_next('td').text
    pp_code = soup.find('th', string='PP_CODE').find_next('td').text

    # print("TYPE:", type_value)
    # print("PARKING_PL:", parking_pl_value)
    # print("LOT_NO:", lot_value)
    # print("PP_CODE:", pp_code)

    feature_list = []
    for f in data_features:
        features = {}
        coordinates = f['geometry']['coordinates'][0][0][0:2]
        x = coordinates[1]
        y = coordinates[0]
        
        html = f['properties']['Description']

        # Parse the HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract the required values
        type_value = soup.find('th', string='TYPE').find_next('td').text
        parking_pl_value = soup.find('th', string='PARKING_PL').find_next('td').text.strip()
        lot_value = soup.find('th', string='LOT_NO').find_next('td').text
        pp_code = soup.find('th', string='PP_CODE').find_next('td').text

        features = {'type_value':type_value, 'pp_code':pp_code, 'parking_pl_value':parking_pl_value,'lot_value':lot_value, 'x':x, 'y':y}
        feature_list.append(features)

    df = pd.DataFrame(feature_list)

    # combine the lat/lon coord into one tuple
    df['destination'] = df.apply(combine_coord, axis = 1)

    # only keep the mcycle parking lot; TBC future expand to car
    mc_df = df[df['type_value'] == 'MYCYCLE LOTS'].copy()

    # get the numer of parking lots per location
    mc_df_cnt = mc_df.groupby(['pp_code','parking_pl_value'])['lot_value'].agg('count').reset_index().rename({'lot_value':'no_of_lots'}, axis = 1)

    # since lat/lon is for each and every parking lot, we just take the one wiht min coord as reference
    min_x_mc_df = mc_df.groupby(['pp_code','parking_pl_value'])['x'].agg('min').reset_index()

    temp_df = mc_df.merge(min_x_mc_df, how='inner', on=['pp_code','parking_pl_value', 'x'])

    final_df = temp_df.merge(mc_df_cnt, how='inner', on=['pp_code','parking_pl_value']).drop(['lot_value'], axis = 1)

    final_df.to_csv("ura_mcycle_parking.csv", index=False)

if __name__ == "__main__":
    geojson_parser()