import os, requests, json, re, random, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- CONNECTION FIX ---
try:
    # tlsAllowInvalidCertificates=True aur certifi dono laga diye hain
    client = MongoClient(
        MONGO_URI, 
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True, 
        serverSelectionTimeoutMS=5000
    )
    db = client['neer_db']
    chat_col = db['history']
    # Sirf check karne ke liye ki connection zinda hai
    client.admin.command('ping')
    mongo_ok = True
except Exception as e:
    print(f"Connection Error: {e}")
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

# ... baki ka chat aur auto-greet logic same rahega ...
