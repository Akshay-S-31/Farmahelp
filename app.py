import streamlit as st
import http.client
import json
import os
import io
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from gtts import gTTS
from googletrans import Translator
import math

# Setup
load_dotenv()
api_key = os.getenv("AMBEE_KEY")
geolocator = Nominatim(user_agent="farmahelp_app")
translator = Translator()

def get_weather(lat, lng):
    conn = http.client.HTTPSConnection("api.ambeedata.com")
    headers = {'x-api-key': api_key, 'Content-type': "application/json"}
    url = f"/weather/latest/by-lat-lng?lat={lat}&lng={lng}"
    conn.request("GET", url, headers=headers)
    res = conn.getresponse()
    return json.loads(res.read().decode("utf-8"))

# Streamlit UI
st.set_page_config(page_title="Weather Malayalam", page_icon="🌤️")
st.title("🌤️ കാലാവസ്ഥാ വിവരങ്ങൾ (Weather Info)")

city_name = st.text_input("നഗരത്തിന്റെ പേര് നൽകുക (Enter City Name)", "")

if st.button('കാലാവസ്ഥ അറിയുക (Get Weather)'):
    if not city_name:
        st.warning("ദയവായി ഒരു നഗരത്തിന്റെ പേര് നൽകുക.")
    else:
        with st.spinner('വിവരങ്ങൾ ശേഖരിക്കുന്നു...'):
            location = geolocator.geocode(city_name)
            if location:
                lat, lng = location.latitude, location.longitude
                result = get_weather(lat, lng)
                
                if result.get("message") == "success":
                    data = result["data"]
                    
                    # 1. Translate English Summary to Malayalam
                    eng_summary = data['summary']
                    try:
                        translated = translator.translate(eng_summary, dest='ml')
                        ml_summary = translated.text
                    except:
                        ml_summary = eng_summary # Fallback if translation fails

                    # 2. Build the Malayalam Voice Script
                    # We translate "The weather is" and "Temperature is" manually for natural flow
                    weather_report = (
                        f"{city_name} ലെ കാലാവസ്ഥ ഇപ്പോൾ {ml_summary} ആണ്. "
                        f"ഇപ്പോഴത്തെ താപനില {round((data['temperature']-32)*(5/9),2)} ഡിഗ്രി സെൽഷ്യസ് ആണ്. "
                        f"വായുവിൽ ഈർപ്പം {data['humidity']} ശതമാനം ആണ്."
                    )

                    # 3. Generate Malayalam Audio
                    tts = gTTS(text=weather_report, lang='ml')
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    
                    # 4. Display Results
                    st.success(f"📍 {location.address}")
                    st.info(f"**വിവരണം:** {ml_summary}")
                    st.audio(audio_fp, format='audio/mp3')
                    
                    col1, col2 = st.columns(2)
                    col1.metric("താപനില (Temp)", f"{round((data['temperature']-32)*(5/9),2)}°C")
                    col2.metric("ഈർപ്പം (Humidity)", f"{data['humidity']}%")
                else:
                    st.error("API Error.")
            else:
                st.error("നഗരം കണ്ടെത്താൻ കഴിഞ്ഞില്ല.")