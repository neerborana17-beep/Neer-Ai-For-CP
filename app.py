import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Fast Config ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB with 1.5s Fast Timeout
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
    db = client['neer_db']
    chat_col = db['history']
    mongo_status = True
except:
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Bol na bhai! 😂"})

    # --- Smart Context & Personality ---
    # AI ko bataya gaya hai ki wo sirf important baaton par focus kare
    system_instr = (
        "Tera naam Neer hai, CP ka yaar. "
        "Strict Rule: Sirf 2-3 lines mein desi Hinglish reply kar. "
        "User ki hobbies, naam aur important baatein yaad rakh, baaki ignore kar. "
        "Baar-baar 2026 ya AI hone ka bhashan mat de. Be natural."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # --- Memory Fetching (Optimized to last 4 for speed) ---
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(4))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Using Gemini 2.0 Flash Lite for < 4s response
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 120 
            }),
            timeout=8
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # --- Smart Saving Logic ---
        # Sirf tab save karega jab message 4 words se bada ho (Faltu "Hi/Bye" ignore karne ke liye)
        if mongo_status and len(user_input.split()) > 3:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Network hichki le raha hai, phir se bol! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
