# Streamlit live coding script
import streamlit as st
import pandas as pd
#import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy


# Load data helpers
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

@st.cache_data
def load_json(path):
    with open(path) as response:
        json_ = json.load(response)
    return json_


# load actual data
df_raw = load_data(path="./data/renewable_power_plants_CH.csv")
df = deepcopy(df_raw)
geojson = load_json(path="./data/georef-switzerland-kanton.geojson")


# Add title and header
st.title("Renewable Energy Production in Switzerland")
st.header("Exploration of open source data (2016)")

url = "https://data.open-power-system-data.org/renewable_power_plants/2020-08-25"
st.write("Data Source:", url)


# Prepare DF

cantons_dict = {
'TG':'Thurgau', 
'GR':'Graubünden', 
'LU':'Luzern', 
'BE':'Bern', 
'VS':'Valais',                
'BL':'Basel-Landschaft', 
'SO':'Solothurn', 
'VD':'Vaud', 
'SH':'Schaffhausen', 
'ZH':'Zürich', 
'AG':'Aargau', 
'UR':'Uri', 
'NE':'Neuchâtel', 
'TI':'Ticino', 
'SG':'St. Gallen', 
'GE':'Genève',
'GL':'Glarus', 
'JU':'Jura', 
'ZG':'Zug', 
'OW':'Obwalden', 
'FR':'Fribourg', 
'SZ':'Schwyz', 
'AR':'Appenzell Ausserrhoden', 
'AI':'Appenzell Innerrhoden', 
'NW':'Nidwalden', 
'BS':'Basel-Stadt'}

df['canton_long'] = df['canton'].apply(lambda x: cantons_dict[x])
df.drop(columns=['data_source','nuts_1_region','nuts_2_region','nuts_3_region','postcode',
                 'address','municipality_code','contract_period_end'], inplace=True)


########## Energy production per Kanton / per Datasource section

st.header("Renewable energy production per Kanton")

# Prepare df
df_grouped = df.groupby(['canton_long','energy_source_level_2']).agg(production = ('production','sum')).reset_index()
sources = df.energy_source_level_2.unique()

# Setting up columns
left_column, right_column = st.columns([2, 1])

# Widgets: selectbox
sources = ["All"]+sorted(sources)
source = left_column.selectbox("Choose an energy source", sources)

# Widgets: radio buttons
show_plants = right_column.radio(
    label='Show biggest power plants', options=['No', 'Yes'])

# Flow control and plotting
if source == "All":
    df_reduced = df_grouped.groupby(['canton_long'], ).agg(production = ('production','sum')).reset_index()
    df_top10 = df.sort_values(by='production', ascending=False).iloc[0:10]
else:
    df_reduced = df_grouped[df_grouped["energy_source_level_2"] == source]
    df_top10 = df[df['energy_source_level_2'] == source].sort_values(by='production', ascending=False).iloc[0:10]

# Plot Chloropleth
fig1 = go.Figure(go.Choroplethmapbox(
    geojson=geojson, 
    locations=df_reduced.canton_long, 
    z=df_reduced.production, 
    featureidkey="properties.kan_name",       
    colorscale="Viridis",
    marker_opacity=0.8, 
    marker_line_width=1,
    text=df_reduced.canton_long,
    hovertemplate="<b>%{text}</b><br><br>" +
            "Production: %{z:.2f} MWh<br>" +
            "<extra></extra>"
))

fig1.update_layout(
    margin={"r":0,"t":70,"l":0,"b":0},
    height=500, 
    width=650,
    mapbox_center = {"lat": 46.78, "lon": 8.2},
    mapbox_style="carto-positron",
    mapbox_zoom=6.3,
    title={"text": "Renewable Energy Production in Switzerland", "font": {"size": 24}},
    yaxis={"title": {"text": "production in MWh", "font": {"size": 16}}}
)

# Plot Powerplants
if show_plants == "Yes":
    fig1.add_trace(go.Scattermapbox(
        lon = df_top10['lon'],
        lat = df_top10['lat'],
        text = df_top10['project_name'],
        marker = dict(
            size = df_top10['production']/80,
            sizemode = 'area',
            color = 'orange',
            opacity = 0.7,
        ),
        hovertemplate="<b>%{text}</b><br><br>" +
            "%{marker.size:.2f} MWh<br>" +
            "<extra></extra>"
    ))

st.plotly_chart(fig1)


########## Private solar producers section

st.header("")
st.header("Solar Energy Production by Private Households")

# Prepare df
df_private = df[(df.company == 'Natural person') & (df.energy_source_level_2 == 'Solar') & (df.production >= 0)]
df_private_solar = df_private.groupby('canton_long').agg(production = ('production', 'sum'))
df_solar_mun = df_private[df.energy_source_level_2 == 'Solar'].groupby(['municipality','lat','lon']).agg(production = ('production','sum'), tariff = ('tariff','sum')).reset_index()

# Setting up columns
left_column2, right_column2 = st.columns([2, 1])

# Widgets: radio buttons
show_muns = left_column2.radio(
    label='Show municipalities', options=['No', 'Yes'])

# Flow control and plotting

# Plot Chloropleth
fig2 = go.Figure(go.Choroplethmapbox(
    geojson=geojson, 
    locations=df_private_solar.index, 
    z=df_private_solar.production, 
    featureidkey="properties.kan_name",       
    colorscale="Viridis",
    marker_opacity=0.8, 
    marker_line_width=1,
    text=df_private_solar.index,
    hovertemplate="<b>%{text}</b><br><br>" +
            "Production: %{z:.0f} MWh<br>" +
            "<extra></extra>"
))
fig2.update_layout(
    margin={"r":0,"t":70,"l":0,"b":0},
    height=500, 
    width=650,
    mapbox_center = {"lat": 46.78, "lon": 8.2},
    mapbox_style="carto-positron",
    mapbox_zoom=6.3,
    title={"text": "Private Solar Production", "font": {"size": 24}}
)

# Show municipalities


if show_muns == "Yes":
    fig2.add_trace(go.Scattermapbox(
        lon = df_solar_mun['lon'],
        lat = df_solar_mun['lat'],
        text = df_solar_mun['municipality'],
        marker = dict(
            size = df_solar_mun['tariff']/300,
            sizemode = 'area',
            color = 'orange',
            opacity = 0.4,
        ),
        hovertemplate="<b>%{text}</b><br><br>" +
            "%{marker.size:.2f} MWh<br>" +
            "<extra></extra>"
    ))

st.plotly_chart(fig2)