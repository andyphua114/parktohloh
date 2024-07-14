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

# USER PARAMETERS
distance = st.slider("Distance (in meters)", min_value=0, max_value=2000, value=250, step=50) / 1000
postal_code = st.number_input("Postal Code", min_value=None, max_value=None, value=None, step=1,format='%06d',placeholder="Enter postal code...")

top = pi * 0
bottom = pi * 1
right = pi * 0.5
left = pi * 1.5

final_df = pd.read_csv("data/ura_mcycle_parking.csv")

# convert from string to tuple
final_df['destination'] = final_df['destination'].apply(ast.literal_eval)

if len(format_number(postal_code)) == 6:
  url = f"https://www.onemap.gov.sg/api/common/elastic/search?searchVal={postal_code}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
  headers={}
  response = requests.request("GET", url)

  if response.json()['found'] > 0:
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