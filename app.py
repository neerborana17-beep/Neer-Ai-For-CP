import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Fast DB Connection
try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=2000)
    db = client['neer_db']
    chat_col = db['history']
    mongo_ok = True
except:
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    # --- REAL-TIME DATA ---
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_date = ist_now.strftime("%d %B %Y")
    current_time = ist_now.strftime("%I:%M %p")
    current_day = ist_now.strftime("%A")

    # Neer's Brain with Real-time Context
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka jigar ka tukda hai. "
        f"Aaj ki Date: {current_date}, Time: {current_time}, Day: {current_day}. "
        f"Tu hamesha sahi date/time batayega. Ekdam dosti wali Hinglish bol."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_ok:
        try:
            history = list(chat_col.find().sort("time", -1).limit(2))
            for m in reversed(history):
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
        
    messages.append({"role": "user", "content": user_input})

    try:
        # Speed Optimization: Gemini 2.0 Flash Lite use kar rahe hain jo <2 sec mein reply deta hai
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 200 # Short & Fast replies
            }),
            timeout=5 # 5 second ka hard limit
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_ok:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, net thoda slow hai, par main sun raha hoon!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
