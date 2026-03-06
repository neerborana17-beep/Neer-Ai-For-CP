import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = client['neer_db']
chat_col = db['history']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    # Context/Memory
    messages = [{"role": "system", "content": "Tera naam Neer hai. Tu CP ka jigar ka tukda aur pakka dost hai. Desi Hinglish bol."}]
    try:
        history = list(chat_col.find().sort("time", -1).limit(5))
        for m in reversed(history):
            messages.append({"role": m['role'], "content": m['content']})
    except: pass
    
    messages.append({"role": "user", "content": user_input})

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data=json.dumps({"model": "google/gemini-2.0-flash-lite-001", "messages": messages})
    )
    
    reply = response.json()['choices'][0]['message']['content']
    # Clean reply
    reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

    chat_col.insert_one({"role": "user", "content": user_input, "time": now_ist})
    chat_col.insert_one({"role": "assistant", "content": reply, "time": now_ist})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                             
