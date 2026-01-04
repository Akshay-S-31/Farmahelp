import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import requests
import pandas as pd
import os

# --- CONFIGURATION ---
# This must be the first Streamlit command
st.set_page_config(page_title="നെല്ല് രോഗനിർണയം", page_icon="🌾", layout="wide")

# --- DEBUGGING PATHS (Logs to Console) ---
print("--- DEBUGGING PATHS ---")
print(f"Current Working Directory: {os.getcwd()}")
print("Files in current root:", os.listdir())
print("-----------------------")

# --- 1. ROBUST MODEL LOADER (The Fix) ---
@st.cache_resource
def load_model():
    model_filename = 'rice_model.h5'
    
    # Strategy: Walk through all folders to find the file dynamically
    found_model_path = None
    for root, dirs, files in os.walk("."):
        if model_filename in files:
            found_model_path = os.path.join(root, model_filename)
            break # Stop looking once found
            
    if found_model_path:
        try:
            # Load the model from the path we found
            model = tf.keras.models.load_model(found_model_path)
            return model
        except Exception as e:
            st.error(f"❌ Found file at {found_model_path} but failed to load: {e}")
            return None
    else:
        # If we truly can't find it, show an error on the screen
        st.error(f"❌ Critical: '{model_filename}' not found on server.")
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

st.title("🌾 നെല്ല് രോഗനിർണയം")

# --- PART 1: DISEASE DETECTION ---
st.header("1. ക്രോപ്പ് സ്കാൻ ചെയ്യുക")
uploaded_file = st.file_uploader("നെല്ലിന്റെ ഒരു ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display Image
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Scanned Image", width=300)
    
    if st.button("അണുബാധ വിശകലനം ചെയ്യുക"):
        if model is None:
            st.error("❌ Model not found! Upload 'rice_model.h5' to your folder.")
        else:
            with st.spinner("രോഗാണുക്കൾക്കായി സ്കാൻ ചെയ്യുന്നു..."):
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

               # ... inside the Analyze Infection button logic ...

                class_names = ["Brown Spot", "Bacterial Blight", "Healthy"] 
                diagnosis = class_names[index]
                confidence = float(prediction[0][index])
                
                # 2. DEFINE CURES (Keys = English, Values = Malayalam)
                cures = {
                    "Brown Spot": "പ്രോപികൊണസോൾ (ടിൽറ്റ്) അല്ലെങ്കിൽ മാങ്കോസെബ് പോലുള്ള കുമിൾനാശിനികൾ ഉപയോഗിക്കുക. മണ്ണിലെ പോഷകങ്ങൾ മെച്ചപ്പെടുത്തുക.",
                    "Bacterial Blight": "കോപ്പർ ഓക്സിക്ലോറൈഡ് + സ്ട്രെപ്റ്റോസൈക്ലിൻ തളിക്കുക. നൈട്രജൻ ഉപയോഗം കുറയ്ക്കുക.",
                    "Healthy": "കീടനാശിനികൾ ആവശ്യമില്ല. ജലനിരപ്പ് നിലനിർത്തുന്നത് തുടരുക.."
                }
                
                # Get the cure
                recommended_cure = cures.get(diagnosis, "ഒരു വിദഗ്ദ്ധനെ സമീപിക്കുക.")
                
                # Optional: Translate the Diagnosis name itself for display
                diagnosis_malayalam = {
                    "Brown Spot": "ബ്രൗൺ സ്പോട്ട്",
                    "Bacterial Blight": "ബാക്ടീരിയൽ ബ്ലൈറ്റ്",
                    "Healthy": "ആരോഗ്യമുള്ള"
                }
                display_name = diagnosis_malayalam.get(diagnosis, diagnosis)

                # Save to session
                st.session_state['last_diagnosis'] = display_name
                st.session_state['last_cure'] = recommended_cure
                
                # 3. DISPLAY RESULTS
                st.success(f"**രോഗനിർണ്ണയം:** {display_name}")  # Diagnosis in Malayalam
                st.info(f"**Confidence:** {confidence:.2%}")
                st.warning(f"**പ്രതിവിധി:** {recommended_cure}") # Cure in Malayalam
# --- PART 2: MAP SEARCH ---
st.divider()
st.header("2. വളം കടകൾ കണ്ടെത്തുക")

# Starts EMPTY. User MUST type something.
city_input = st.text_input("നിങ്ങളുടെ പട്ടണത്തിന്റെയോ നഗരത്തിന്റെയോ പേര് നൽകുക")

if st.button("സമീപത്തുള്ള കടകൾ തിരയുക"):
    if not city_input:
        st.warning("⚠️ ആദ്യം ഒരു നഗരത്തിന്റെ പേര് നൽകുക..")
    else:
        with st.spinner(f"Locating shops in {city_input}..."):
            # 1. Get Lat/Lon
            lat, lon = get_coordinates(city_input)
            
            if lat is not None:
                st.success(f"📍 ലൊക്കേഷൻ കണ്ടെത്തി: {city_input}")
                
                # 2. Fetch Shops
                df_shops = get_real_shops(lat, lon)
                
                if not df_shops.empty:
                    # Show Map
                    st.map(df_shops)
                    
                    # Show Details with Google Maps Links
                    st.write(f"**Found {len(df_shops)} verified stores:**")
                    for index, row in df_shops.iterrows():
                        with st.expander(f"🛒 {row['name']} ({row['type']})"):
                            # Fixed the Google Maps link format for you
                            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={row['lat']},{row['lon']}"
                            st.markdown(f"[➡️ **ദിശകൾ നേടുക**]({google_maps_link})")
                else:
                    st.warning("ഈ പ്രദേശത്ത്  കാർഷിക കടകളൊന്നും കണ്ടെത്തിയില്ല..")
            else:
                st.error("❌ആ നഗരം കണ്ടെത്താൻ കഴിഞ്ഞില്ല. ദയവായി അക്ഷരത്തെറ്റ് പരിശോധിക്കുക.")