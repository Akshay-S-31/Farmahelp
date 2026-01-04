import streamlit as st
import requests
import io

st.set_page_config(page_title="Rice Disease Detector", page_icon="🌾")

st.header("🌾 Rice Disease Detector")
uploaded_file = st.file_uploader("Upload a rice leaf photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Display image
    st.image(uploaded_file, caption="Scanned Image", width=300)
    
    if st.button("Analyze Infection"):
        with st.spinner("Scanning for pathogens..."):
            try:
                # Send to FastAPI
                files = {"file": uploaded_file.getvalue()}
                response = requests.post("http://localhost:8000/detect-disease", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # UI Presentation
                    st.success(f"**Diagnosis:** {data['diagnosis']}")
                    st.info(f"**Confidence:** {data['confidence']}")
                    st.warning(f"**Recommended Cure:** {data['cure']}")
                    
                    # Optional: Play the cure as audio (Voice Assistance)
                    # You can reuse your TTS logic here if you have time
                else:
                    st.error("Server error. Please try again.")
            except Exception as e:
                st.error(f"Connection failed: {e}")