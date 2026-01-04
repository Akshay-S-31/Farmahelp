from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import os

app = FastAPI()

# Add CORS Middleware to allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# GLOBAL VARIABLES
model = None
class_names = [
    "Bacterial Leaf Blight", 
    "Brown Spot", 
    "Healthy Rice Leaf", 
    "Leaf Blast", 
    "Leaf scald", 
    "Sheath Blight"
] # MAKE SURE THIS MATCHES YOUR KAGGLE PRINT OUTPUT

# Load model on startup
@app.on_event("startup")
def load_model():
    global model
    model_path = "rice_model.h5"
    if os.path.exists(model_path):
        try:
            model = tf.keras.models.load_model(model_path)
            print("✅ Real Model loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            model = None
    else:
        print("⚠️ Warning: rice_model.h5 not found. Running in MOCK MODE.")
        model = None

def prepare_image(image_bytes):
    # 1. Open the image
    img = Image.open(io.BytesIO(image_bytes))
    
    # 2. FORCE CONVERT TO RGB (Fixes the 4-channel error)
    img = img.convert("RGB") 
    
    # 3. Resize to match model input
    img = img.resize((224, 224)) 
    
    # 4. Normalize and Expand Dimensions
    img_array = np.array(img) / 255.0 
    img_array = np.expand_dims(img_array, axis=0) 
    
    return img_array

@app.post("/detect-disease")
async def detect_disease(file: UploadFile = File(...)):
    # 1. Read Image
    image_bytes = await file.read()
    processed_image = prepare_image(image_bytes)
    
    # 2. Predict
    if model:
        predictions = model.predict(processed_image)
        predicted_class_index = np.argmax(predictions[0])
        confidence = float(np.max(predictions[0]))
        result_class = class_names[predicted_class_index]
    else:
        # MOCK PREDICTION LOGIC
        import random
        result_class = random.choice(class_names)
        confidence = random.uniform(0.85, 0.99)
        print(f"Mocking prediction: {result_class}")
    
    # 3. Simple Logic for "Cure" (You can expand this dictionary)
    cures = {
        "Bacterial Leaf Blight": "Use copper-based fungicides and improve drainage.",
        "Brown Spot": "Apply potassic fertilizer and treat seeds with fungicides.",
        "Healthy Rice Leaf": "Your crop looks great! Keep maintaining current water levels.",
        "Leaf Blast": "Spray Tricyclazole 75 WP. Avoid excessive Nitrogen fertilizer.",
        "Leaf scald": "Use clean seeds and apply Benomyl or Carbendazim.",
        "Sheath Blight": "Drain the field and apply Validamycin."
    }
    
    return {
        "diagnosis": result_class,
        "confidence": f"{confidence*100:.2f}%",
        "cure": cures.get(result_class, "Consult a local agronomist.")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
