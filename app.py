import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import requests
import json

# Request API URLs
req_api = "http://13.200.198.227:8090/validate/weekly_advisory/"
weather_api = "http://13.200.198.227:8090/gfs-weather/"

# CROPS
RABI_CROPS = ['Paddy','Mustard','Blackgram','Greengram','Potato']
KHARIF_CROPS = ['Paddy','Potato']
SOILTYPES = ['Red Soil','Laterite Soil','Red and Yellow Soil',
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
# Row 1: Season, Soil, Lat, Lon, Elevation
# ----------------------------------
col_a, col_b, col_c, col_d, col_e = st.columns(5)
with col_a:
    season = st.selectbox("Select Season :", ["Rabi", "Kharif"], index=0) # Default Rabi
with col_b:
    soil_type = st.selectbox("Select Soil Type :", SOILTYPES, index=0)
with col_c:
    lat = st.number_input("Latitude :", value=21.44, format="%.4f")
with col_d:
    lon = st.number_input("Longitude :", value=85.15, format="%.4f")
with col_e:
    elev = st.number_input("Elevation (m) :", value=100)

# ----------------------------------
# Row 2: Crop, Land Type, Sowing Date, Advisory Date
# ----------------------------------
col1, col2, col3, col4 = st.columns(4)

if season == "Rabi":
    crops = RABI_CROPS
elif season == "Kharif":
    crops = KHARIF_CROPS
else:
    crops = ["None"]

with col1:
    # Defaulting to Potato (index 4 in RABI_CROPS)
    default_crop_idx = crops.index("Potato") if "Potato" in crops else 0
    crop_selection = st.selectbox("Select Crop :", crops, index=default_crop_idx)

with col2:
    land_selection = st.selectbox("Select Land Type :", LANDTYPE, index=0)

with col3:
    sowing_date = st.date_input("Sowing Date :", value=datetime(2026, 1, 1))

with col4:
    adv_date = st.date_input("Advisory Date :", value=datetime(2026, 3, 16))

# ----------------------------------
# Weather Section
# ----------------------------------
weather_type = st.selectbox("Weather Type: ", ['Manual', 'Forecast'], index=0)

if weather_type == "Forecast":
    st.info("Fetching Niruthi weather forecast for specified location...")
    weather_payload = {
        "lat": lat,
        "lon": lon,
        "date": str(adv_date)
    }
    try:
        wthr_req = requests.post(url=weather_api, json=weather_payload)
        if wthr_req.status_code == 200:
            weather_data = wthr_req.json() # Assuming API returns list of dicts
            st.success("Forecast data retrieved!")
            # Optional: Show a preview of fetched weather
            st.write(weather_data) 
            weather_data = []
            # weather_type = 'forecast'
        else:
            st.error(f"Weather API Error: {wthr_req.status_code}")
            weather_data = [{"Date": str(adv_date), "Rainfall (mm)": 0.0}] # Fallback
    except Exception as e:
        st.error(f"Weather Connection Error: {e}")
        weather_data = []

else:
    st.subheader("7-Day Weather Input :")
    dates = [adv_date + timedelta(days=i) for i in range(7)]
    df_init = pd.DataFrame({
        "Date": dates,
        "Rainfall (mm)": [0.0]*7,
        "Tmin (°C)": [20.0]*7,
        "Tmax (°C)": [30.0]*7,
        "RH_min (%)": [30.0]*7,
        "RH_max (%)": [70.0]*7
    })
    edited_df = st.data_editor(df_init, num_rows="fixed", use_container_width=True)
    edited_df['Date'] = edited_df['Date'].astype(str)
    weather_data = edited_df.to_dict(orient="records")

# ----------------------------------
# Submit Button
# ----------------------------------
if st.button("Submit", type="primary"):
    with st.spinner("Generating Advisory..."):
        
        # Build Internal Dictionary as per your default requirements
        advisory_details = {
            "season": season,
            "crop_name": crop_selection,
            "sowing_date": str(sowing_date),
            "current_date": str(adv_date),
            "weather_json": weather_data,
            "weather_input": weather_type,
            "lat": lat,
            "lon": lon,
            "elevation": elev,
            "weekly_advisory": "True" # Specific string requirement from your request
        }

        # Final Payload: Root level fields + stringified 'weekly_advisory'
        payload = {
            "weekly_advisory": json.dumps(advisory_details),
            **advisory_details 
        }

        try:
            response = requests.post(req_api, json=payload)
            
            if response.status_code == 200:
                st.success("Advisory Generated Successfully!")
                res_data = response.json()
                
                # Dynamic parsing based on response type
                if isinstance(res_data, str):
                    advisory_df = pd.read_json(res_data)
                else:
                    advisory_df = pd.DataFrame(res_data)

                # Formatting results
                display_cols = ['crop_name','crop_stage','cropstage_week_start','cropstage_week_end','advisory_title','advisory_content']
                existing = [c for c in display_cols if c in advisory_df.columns]
                
                final_df = advisory_df[existing].rename(columns={
                    "crop_name":"Crop", "crop_stage":"Stage",
                    "cropstage_week_start":"Week_From", "cropstage_week_end":"Week_To",
                    "advisory_title":"Adv. Title", "advisory_content":"Adv. Content"
                })

                st.table(final_df) # Using table for a clean PRD-like look

            else:
                st.error(f"API Error: {response.status_code}")
                st.json(response.json())

        except Exception as e:
            st.error(f"Connection Error: {str(e)}")