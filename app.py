import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import requests

# Request API
req_api = "http://127.0.0.1:8000/validate/weekly_advisory/"

# CROPS
RABI_CROPS = ['None','Paddy','Mustard','Blackgram','Greengram','Potato']
KHARIF_CROPS = ['None','Paddy','Potato']

SOILTYPES = ['None','Red Soil','Laterite Soil','Red and Yellow Soil',
             'Coastal Saline and Alluvial Soil','Deltaic Alluvial Soil',
             'Black Soil','Mixed Red and Black Soil','Brown Forest Soil']

LANDTYPE = ['Low Land','Medium Land','Up Land']

# ----------------------------------
# PAGE CONFIG
# ----------------------------------
st.set_page_config(page_title="Model Testing", layout="wide")
st.title("Welcome to Model Testing Platform!")

st.header("Please Select Model Input Parameters:")

# ----------------------------------
# Dynamic Season → Crop
# ----------------------------------
col1, col2 = st.columns(2)
with col1:
    season = st.selectbox("Select Season :", ["None", "Rabi", "Kharif"],width='stretch')

    if season == "Rabi":
        crops = RABI_CROPS
    elif season == "Kharif":
        crops = KHARIF_CROPS
    else:
        crops = ["None"]
with col2:
    st.selectbox("Select Soil Type :",SOILTYPES,width='stretch')

# ----------------------------------
# Layout Columns
# ----------------------------------
col3, col4, col5, col6 = st.columns(4)

with col3:
    crop_selection = st.selectbox("Select Crop :", crops)

with col4:
    elevation = st.selectbox("Select Land Type :", LANDTYPE)

with col5:
    sowing_date = st.date_input("Sowing Date :")

with col6:
    adv_date = st.date_input("Advisory Date :")

# ----------------------------------
# Weather Table
# ----------------------------------
weather_type = st.selectbox("Weather Type: ",['Manual','Forecast'])

if weather_type == "Forecast":
    table_option = True
    st.write("Niruthi weather forecast information will be used for advisory generation...")
else:
    table_option = False

if not table_option:
    st.subheader("7-Day Weather Input :")

    start_date = adv_date
    dates = [start_date + timedelta(days=i) for i in range(7)]

    df = pd.DataFrame({
        "Date": dates,
        "Rainfall (mm)": [0.0]*7,
        "Tmin (°C)": [20.0]*7,
        "Tmax (°C)": [30.0]*7,
        "RH_min (%)": [30.0]*7,
        "RH_max (%)": [70.0]*7
    })

    edited_df = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        disabled = table_option
    )

    edited_df['Date'] = edited_df['Date'].astype(str)

    numeric_cols = [
        "Rainfall (mm)",
        "Tmin (°C)",
        "Tmax (°C)",
        "RH_min (%)",
        "RH_max (%)"
    ]

    edited_df[numeric_cols] = edited_df[numeric_cols].fillna(0.0)

# ----------------------------------
# Submit Button
# ----------------------------------
if st.button("Submit", type="primary"):

    with st.spinner("Generating Advisory..."):
        if weather_type == 'Manual':
            weather_data = edited_df.to_dict(orient="records")
        else:
            dates = [adv_date + timedelta(days=i) for i in range(7)]
            df = pd.DataFrame({
                "Date": dates,
                "Rainfall (mm)": [0.0]*7,
                "Tmin (°C)": [20.0]*7,
                "Tmax (°C)": [30.0]*7,
                "RH_min (%)": [30.0]*7,
                "RH_max (%)": [70.0]*7
            })
            numeric_cols = [
                "Rainfall (mm)",
                "Tmin (°C)",
                "Tmax (°C)",
                "RH_min (%)",
                "RH_max (%)"
            ]
            df['Date'] = df['Date'].astype(str)
            df[numeric_cols] = df[numeric_cols].fillna(0.0)
            weather_data = df.to_dict(orient='records')

        payload = {
            "season": season,
            "crop_name": crop_selection,
            "sowing_date": str(sowing_date),
            "current_date": str(adv_date),
            "weather_json": weather_data,
            "weather_input": weather_type
        }

        response = requests.post(req_api, json=payload)

    # ----------------------------------
    # Handle Response
    # ----------------------------------
    if response.status_code == 200:

        st.success("Advisory Generated Successfully!")

        advisory_response = pd.read_json(response.json())

        hide_columns = [
            "state","advisory_index","advisory_code",
            "rain_min","rain_max","rain_mean",
            "temp_min","temp_max","rh_min","rh_max",
            "rainydays_min","raindays_max",
            "wind_min","wind_max","landtype",
            "agro_week","day_of_month","month_of_year"
        ]

        advisory_response = advisory_response[
            advisory_response.columns.difference(hide_columns)
        ]

        advisory_response = advisory_response[
            ['crop_name','crop_stage',
             'cropstage_week_start','cropstage_week_end',
             'advisory_title','advisory_content']
        ]

        advisory_response = advisory_response.rename(columns={
            "crop_name":"Crop",
            "crop_stage":"Stage",
            "cropstage_week_start":"Week_From",
            "cropstage_week_end":"Week_To",
            "advisory_title":"Adv. Title",
            "advisory_content":"Adv. Content"
        })

        st.data_editor(advisory_response, use_container_width=True)
        st.write(response)

    else:
        st.error(f"API Error: {response.status_code}")
        st.write(response.text)