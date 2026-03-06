import os, requests, json, re, random
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Stable Connection with Timeout
try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=3000)
    db = client['neer_db']
    chat_col = db['history']
    mongo_ok = True
except:
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-greet')
def auto_greet():
    # 40% Chance ki Neer message bhejega (Randomness)
    if random.random() > 0.4:
        return jsonify({"status": "Neer abhi vella baitha hai, mann nahi hai uska"}), 200

    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    h = ist_now.hour
    
    # Time ke hisab se vibe change
    vibe = "Morning roast" if 5 <= h <= 11 else "Lunch bakchodi" if 12 <= h <= 16 else "Shaam ki gali" if 17 <= h <= 21 else "Raat ka emotional gyaan"

    system_instr = (
        f"Tera naam Neer hai. Tu CP ka pakka dost hai. Vibe: {vibe}. "
        f"Bina kisi wajah ke CP ko ekdam short desi style mein (max 1 line) msg kar. "
        f"Dosti wali galiyan (BC, saale) use kar. AI mat ban, ek real dost ban."
    )

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": [{"role": "system", "content": system_instr}],
                "max_tokens": 60,
                "temperature": 0.9
            }),
            timeout=10
        )
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_ok:
            chat_col.insert_one({
                "role": "assistant", 
                "content": reply, 
                "time": ist_now,
                "is_notified": False # Browser ko signal dene ke liye
            })
        return jsonify({"status": "Sent", "msg": reply})
    except:
        return jsonify({"status": "Error"}), 500

@app.route('/check-notification')
def check_notification():
    if not mongo_ok: return jsonify({"new": False})
    msg = chat_col.find_one_and_update(
        {"role": "assistant", "is_notified": False},
        {"$set": {"is_notified": True}}
    )
    if msg:
        return jsonify({"new": True, "reply": msg['content']})
    return jsonify({"new": False})

@app.route('/chat', methods=['POST'])
def chat():
    # ... (Puraana short chat logic yahan rahega) ...
    try:
        user_input = request.json.get("message")
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        system_instr = "Tera naam Neer hai. Tu CP ka dost hai. Short desi replies de, galiyan chalengi. AI mat ban."
        messages = [{"role": "system", "content": system_instr}]
        
        if mongo_ok:
            history = list(chat_col.find().sort("time", -1).limit(4))
            for m in reversed(history):
                messages.append({"role": m['role'], "content": m['content']})
        
        messages.append({"role": "user", "content": user_input})

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({"model": "google/gemini-2.0-flash-lite-001", "messages": messages}),
            timeout=8
        )
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_ok:
            chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now, "is_notified": True})

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Abbe net check kar saale."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                
