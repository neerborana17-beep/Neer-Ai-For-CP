import os, requests, json, re, random, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- DATABASE CONNECTION (SSL FIX) ---
try:
    # certifi.where() SSL certificate errors ko block karta hai
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
    db = client['neer_db']
    chat_col = db['history']
    client.admin.command('ping')
    mongo_ok = True
except Exception as e:
    print(f"DB Connection Failed: {e}")
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

# --- CHAT WITH MEMORY ---
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    # System Instruction for Personality
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka jigar ka tukda hai. "
        f"Short desi replies de (1-2 lines). AI mat ban, dost ban. "
        f"Purani baatein yaad rakh. Time: {ist_now.strftime('%I:%M %p')}"
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # DB se Memory nikalna
    if mongo_ok:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6))
            for m in reversed(history):
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
    
    messages.append({"role": "user", "content": user_input})

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": messages,
                "max_tokens": 100
            }),
            timeout=10
        )
        reply = response.json()['choices'][0]['message']['content'].strip()

        # Chat DB mein save karna (Memory)
        if mongo_ok:
            chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now, "is_notified": True})

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai net slow hai ya kuch panga hai!"})

# --- RANDOM MESSAGE GENERATOR ---
@app.route('/auto-greet')
def auto_greet():
    if not mongo_ok: return "DB Not Ready", 500
    
    # Randomness: Sirf 40% chance ki message jayega
    if random.random() > 0.4:
        return "Skip: Neer abhi vella hai", 200

    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    system_instr = "Tu Neer hai. CP ko ek random, chota, desi dost wala message bhej. Mood ke hisab se kuch bhi pooch."
    
    try:
        res = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": [{"role": "system", "content": system_instr}],
                "max_tokens": 50
            })
        )
        reply = res.json()['choices'][0]['message']['content'].strip()
        
        # Save so Notification System can catch it
        chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now, "is_notified": False})
        return f"Random Sent: {reply}"
    except:
        return "Fail", 500

# --- NOTIFICATION CHECKER ---
@app.route('/check-notification')
def check_notification():
    if not mongo_ok: return jsonify({"new": False})
    msg = chat_col.find_one_and_update(
        {"role": "assistant", "is_notified": False},
        {"$set": {"is_notified": True}},
        sort=[("time", -1)]
    )
    if msg: return jsonify({"new": True, "reply": msg['content']})
    return jsonify({"new": False})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
        
