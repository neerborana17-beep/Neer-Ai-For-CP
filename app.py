import os, requests, json, re, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- STABLE DATABASE CONNECTION ---
try:
    client = MongoClient(
        MONGO_URI, 
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    db = client['neer_db']
    chat_col = db['history']
    client.admin.command('ping')
    mongo_ok = True
except Exception as e:
    print(f"DB Error: {e}")
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        if not user_input: return jsonify({"reply": "Bol na bhai!"})

        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        # System Prompt (Simple & Friendly)
        system_instr = (
            f"Tera naam Neer hai. Tu CP ka pakka dost hai. "
            f"Hinglish mein short replies de. Purani baatein yaad rakh. "
            f"Current Time: {ist_now.strftime('%I:%M %p, %d %b')}"
        )
        
        messages = [{"role": "system", "content": system_instr}]
        
        # Memory Load Karna (Last 6 Messages)
        if mongo_ok:
            try:
                history = list(chat_col.find().sort("time", -1).limit(6))
                for m in reversed(history):
                    messages.append({"role": m['role'], "content": m['content']})
            except: pass
        
        messages.append({"role": "user", "content": user_input})

        # API Call
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "max_tokens": 150
            }),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content'].strip()
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply)

        # Memory Save Karna
        if mongo_ok:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now})
            except: pass

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Bhai, server thoda busy hai. Ek baar refresh kar!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
