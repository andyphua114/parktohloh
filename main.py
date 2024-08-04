import pandas as pd
import ast
from math import pi
import requests
from haversine import inverse_haversine, haversine
import streamlit as st

def calc_distance(coord, destination):
    return round(1000 * haversine(coord, destination))

# function to format postal code to six digit
def format_number(number):
    if number:
      return "%06d" % int(number)
    # if not valid number just return 0
    return "0"

st.set_page_config(layout="wide")
st.title('Park Toh Loh')

# SELECT TYPE RADIO BUTTON

veh_type = st.radio("Select vehicle type",
                    ["All", "Car", "Motorcycle"])

# SEARCH ADDRESS FUNCTION

selected_postal = None

address = st.text_input("Address", value="", placeholder="Search address...")

# search address details using OneMap API
if address != "":
  url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={address}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
  headers={}
  response = requests.request("GET", url)

  # if there are results, parse into a dataframe
  if response.json()['found'] > 0:
    search_results = response.json()['results']
    location_df = pd.DataFrame(search_results)
    cols = ['SEARCHVAL','POSTAL','BLK_NO','ROAD_NAME','BUILDING','ADDRESS']

    # allow single selection to use the corresponding selected postal code
    event = st.dataframe(location_df[cols], on_select="rerun", selection_mode="single-row", use_container_width=True, hide_index=True)
    
    if len(event.selection['rows']) != 0:
      selected_idx = event.selection['rows'][0]

      selected_postal = location_df.iloc[selected_idx]['POSTAL']
       
# SEARCH PARKING FUNCTION

default_postal = None

# if there are selected postal code from search address function, use the postal code
if selected_postal:
  postal_code_input = selected_postal
  default_postal = int(selected_postal)

# USER PARAMETERS
distance = st.slider("Distance (in meters)", min_value=0, max_value=2000, value=500, step=50) / 1000
postal_code = st.number_input("Postal Code", min_value=None, max_value=None, value=default_postal, step=1,format='%06d',placeholder="Enter postal code...")

top = pi * 0
bottom = pi * 1
right = pi * 0.5
left = pi * 1.5

loaded_df = pd.read_csv("data/ura_car_mcycle_parking.csv")

# filter df based on veh type selection
if veh_type == 'Motorcycle':
  final_df = loaded_df[loaded_df['type_value'] == 'MYCYCLE LOTS'].copy()
elif veh_type == 'Car':
  final_df = loaded_df[loaded_df['type_value'] == 'CAR LOTS'].copy()
else:
  final_df = loaded_df.copy()

# convert from string to tuple
final_df['destination'] = final_df['destination'].apply(ast.literal_eval)

postal_code_input = None

if len(format_number(postal_code)) == 6:
  postal_code_input = format_number(postal_code)
  url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code_input}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
  headers={}
  response = requests.request("GET", url)

  if response.json()['found'] > 0:
    #print(response.json())
    coord = (float(response.json()['results'][0]['LATITUDE']), float(response.json()['results'][0]['LONGITUDE']))
    x1 = inverse_haversine(coord, distance, top)[0]
    x0 = inverse_haversine(coord, distance, bottom)[0]
    y0 = inverse_haversine(coord, distance, left)[1]
    y1 = inverse_haversine(coord, distance, right)[1]

    search_df = final_df[(final_df['x'] >= x0) & (final_df['x'] <= x1) & (final_df['y'] >= y0) & (final_df['y'] <= y1)].copy()
    search_df['distance'] = search_df['destination'].apply(lambda x: calc_distance(coord,x))

    park_df = search_df.drop_duplicates().sort_values('distance')

    # google map link https://www.google.com/maps/search/?api=1&query={}%2C{}

    def return_link(x):
      return f'https://www.google.com/maps/search/?api=1&query={x[0]}%2C{x[1]}'

    park_df['link'] = park_df['destination'].apply(return_link)
    #park_df['display_link'] = park_df.apply(lambda row: f'<a href="{row["link"]}">{row["parking_pl_value"]}</a>', axis=1)

    cols = ['type_value','pp_code','parking_pl_value','no_of_lots','distance','link']

    #"https://(.*?)\.streamlit\.app"
    #'https://www.google.com/maps/search/?api=1&query=(.*?)%2C(.*?)}'

    # Convert DataFrame to HTML and display using st.markdown
    # html = park_df[cols].to_html(escape=False, index=False)
    # st.markdown(html, unsafe_allow_html=True)

    st.dataframe(park_df[cols], use_container_width=True, hide_index=True, column_config={"link":st.column_config.LinkColumn(display_text="Google Maps")})