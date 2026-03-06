import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import pytz # Timezone ke liye

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
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
    if not user_input: return jsonify({"reply": "Bol na bhai!"})

    # --- Live Date & Time Calculation ---
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")

    # --- Strict Close Friend Tone with Live Date ---
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka pakka yaar hai. Aaj ki date hai {current_date} aur waqt hai {current_time}. "
        "Formal mat ho. Seedha point par baat kar. Hinglish use kar. "
        "Agar user date puche toh ekdam sahi batana jo maine upar di hai."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(5))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001", 
                "messages": messages,
                "temperature": 0.9
            }),
            timeout=20
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now(ist)})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now(ist)})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, server down hai shayad, phir try kar! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                
