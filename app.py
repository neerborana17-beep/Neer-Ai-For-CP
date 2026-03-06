import os, requests, json, re, random, logging
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

# Logging setup taaki Render logs mein error dikhe
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ENV Variables check
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Stable MongoDB Connection
try:
    if not MONGO_URI:
        raise ValueError("MONGO_URI missing in Environment Variables")
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
    db = client['neer_db']
    chat_col = db['history']
    client.admin.command('ping') # Check if connection is alive
    mongo_ok = True
except Exception as e:
    logging.error(f"MongoDB Error: {e}")
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-greet')
def auto_greet():
    try:
        # 40% Chance randomness
        if random.random() > 0.4:
            return jsonify({"status": "Neer is sleeping"}), 200

        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        h = ist_now.hour
        vibe = "Morning roast" if 5 <= h <= 11 else "Lunch bakchodi" if 12 <= h <= 17 else "Shaam ki gali"
        
        system_instr = f"Tera naam Neer hai. Tu CP ka dost hai. Vibe: {vibe}. Short desi message bhej dosti wali galiyon ke saath."

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": [{"role": "system", "content": system_instr}],
                "max_tokens": 50
            }),
            timeout=10
        )
        reply = response.json()['choices'][0]['message']['content'].strip()

        if mongo_ok:
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now, "is_notified": False})
        return jsonify({"status": "Sent", "msg": reply})
    except Exception as e:
        logging.error(f"Auto-greet failed: {e}")
        return jsonify({"status": "Error", "details": str(e)}), 500

@app.route('/check-notification')
def check_notification():
    if not mongo_ok: return jsonify({"new": False})
    try:
        msg = chat_col.find_one_and_update(
            {"role": "assistant", "is_notified": False},
            {"$set": {"is_notified": True}},
            sort=[("time", -1)]
        )
        if msg:
            return jsonify({"new": True, "reply": msg['content']})
    except: pass
    return jsonify({"new": False})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        messages = [{"role": "system", "content": "Tu Neer hai, CP ka dost. Short desi replies de."}]
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
        reply = response.json()['choices'][0]['message']['content'].strip()

        if mongo_ok:
            chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now, "is_notified": True})

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
