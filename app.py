import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Stable MongoDB Connection
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
db = client['neer_db']
chat_col = db['history']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        messages = [{"role": "system", "content": "Tera naam Neer hai. Tu CP ka jigar ka tukda hai. Hinglish bol."}]
        
        # Get last 3 chats
        try:
            history = list(chat_col.find().sort("time", -1).limit(3))
            for m in reversed(history):
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
        
        messages.append({"role": "user", "content": user_input})

        # API Call with retry
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages
            }),
            timeout=15 # Time badha diya
        )
        
        res_data = response.json()
        reply = res_data['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Save to DB
        chat_col.insert_one({"role": "user", "content": user_input, "time": now_ist})
        chat_col.insert_one({"role": "assistant", "content": reply, "time": now_ist})

        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Bhai thoda network issue hai, par main yahi hoon. Phir se bol?"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
