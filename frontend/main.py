import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import requests
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Rice Disease Detector", page_icon="🌾", layout="wide")

# --- 1. LOAD MODEL DIRECTLY (Fixes 'Connection Refused' Error) ---
@st.cache_resource
def load_model():
    try:
        # Ensure 'rice_model.h5' is in the SAME folder as this file
        model = tf.keras.models.load_model('rice_model.h5')
        return model
    except Exception as e:
        return None

model = load_model()

# --- 2. MAP FUNCTIONS (Real Data) ---
def get_coordinates(city_name):
    """Converts City Name to Latitude/Longitude using OpenStreetMap"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {'q': city_name, 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'RiceDoctorApp/1.0'}
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
        return None, None
    except:
        return None, None

def get_real_shops(lat, lon, radius=5000):
    """Finds real shops using Overpass API"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["shop"~"fertilizer|agrarian|garden_centre|florist"](around:{radius},{lat},{lon});
      way["shop"~"fertilizer|agrarian|garden_centre|florist"](around:{radius},{lat},{lon});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()
        shops = []
        for element in data['elements']:
            shop_data = {
                'lat': element.get('lat') or element.get('center', {}).get('lat'),
                'lon': element.get('lon') or element.get('center', {}).get('lon'),
                'name': element.get('tags', {}).get('name', 'General Agri-Store'),
                'type': element.get('tags', {}).get('shop', 'Agriculture')
            }
            shops.append(shop_data)
        return pd.DataFrame(shops)
    except:
        return pd.DataFrame()

# --- UI STARTS HERE ---

st.title("🌾 Rice Disease Detector")

# --- PART 1: DISEASE DETECTION ---
st.header("1. Scan Crop")
uploaded_file = st.file_uploader("Upload a rice leaf photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display Image
    image = Image.open(uploaded_file)
    st.image(image, caption="Scanned Image", width=300)
    
    if st.button("Analyze Infection"):
        if model is None:
            st.error("❌ Model not found! Upload 'rice_model.h5' to your folder.")
        else:
            with st.spinner("Scanning for pathogens..."):
                # Pre-process Image
                size = (224, 224)
                image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
                img_array = np.asarray(image)
                normalized_image_array = (img_array.astype(np.float32) / 127.5) - 1
                data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
                data[0] = normalized_image_array
                
                # Predict
                prediction = model.predict(data)
                index = np.argmax(prediction)
                
                # ⚠️ UPDATE LABELS TO MATCH YOUR TRAINING
                class_names = ["Brown Spot", "Bacterial Blight", "Healthy"] 
                diagnosis = class_names[index]
                confidence = float(prediction[0][index])
                
                # Save Diagnosis for later use
                st.session_state['last_diagnosis'] = diagnosis
                
                # Show Result
                st.success(f"**Diagnosis:** {diagnosis}")
                st.info(f"**Confidence:** {confidence:.2%}")

# --- PART 2: MAP SEARCH (No Defaults) ---
st.divider()
st.header("2. Find Medicine & Shops")

# Starts EMPTY. User MUST type something.
city_input = st.text_input("Enter your Town/City Name")

if st.button("Search Nearby Shops"):
    if not city_input:
        st.warning("⚠️ Please enter a city name first.")
    else:
        with st.spinner(f"Locating shops in {city_input}..."):
            # 1. Get Lat/Lon
            lat, lon = get_coordinates(city_input)
            
            if lat is not None:
                st.success(f"📍 Found Location: {city_input}")
                
                # 2. Fetch Shops
                df_shops = get_real_shops(lat, lon)
                
                if not df_shops.empty:
                    # Show Map
                    st.map(df_shops)
                    
                    # Show Details with Google Maps Links
                    st.write(f"**Found {len(df_shops)} verified stores:**")
                    for index, row in df_shops.iterrows():
                        with st.expander(f"🛒 {row['name']} ({row['type']})"):
                            # The Google Maps Direction Link
                            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={row['lat']},{row['lon']}"
                            st.markdown(f"[➡️ **Get Directions**]({google_maps_link})")
                else:
                    st.warning("No specific agricultural shops found in this area.")
            else:
                st.error("❌ Could not find that city. Please check the spelling.")