Offline Transaction Recovery System

HOW TO RUN THIS PROJECT

STEP 1: BACKEND
1. Open terminal in backend folder
2. Run these commands:

py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py

STEP 2: FRONTEND
1. Open another terminal in frontend folder
2. Run:

py -m http.server 5500

STEP 3: OPEN IN BROWSER
Open this link:
http://127.0.0.1:5500

IMPORTANT
- Backend runs on http://127.0.0.1:5000
- If database.db already exists, old data will appear
- If you want fresh data, delete database.db before running app.py