# Farmhelp

Easy accessible voice assisted platform for illiterate and old farmers, helps in solving doubts, disease detection using image detection from uploaded pictures. Weather details, soil details based on location and field details. Fertilizers usage manuals etcn and easily accessible. Output for voice prompts is also in voice for convenience.

## 🚀 How to Run

### 1. Install Dependencies
Open your terminal and run:
```bash
# In the project root
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### 2. Start the Backend
```bash
cd backend
python main.py
```
*Note: If you don't have `rice_model.h5`, it will start in **Mock Mode** and give random results for testing.*

### 3. Start the Frontend
Open a **new terminal** and run:
```bash
cd frontend
streamlit run main.py
```

## 🧠 Moving from Mock to Real AI
When you have your trained `rice_model.h5` file:
1. Place it inside the `backend/` folder.
2. Restart the backend. It will detect the file and use real AI for predictions!
