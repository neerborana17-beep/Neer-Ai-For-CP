import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Fast connection (Sirf 3 second wait karega, atkeyga nahi)
try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=3000)
    db = client['neer_db']
    chat_col = db['history']
    # Check connection
    client.admin.command('ping')
    mongo_ok = True
except:
    mongo_ok = False
    print("MongoDB skip kiya speed ke liye")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        messages = [{"role": "system", "content": "Tera naam Neer hai. Tu CP ka dost hai. Desi Hinglish bol."}]
        
        # History fetch with safety
        if mongo_ok:
            try:
                history = list(chat_col.find().sort("time", -1).limit(3))
                for m in reversed(history):
                    messages.append({"role": m['role'], "content": m['content']})
            except: pass
            
        messages.append({"role": "user", "content": user_input})

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({"model": "google/gemini-2.0-flash-lite-001", "messages": messages}),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_ok:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.utcnow()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.utcnow()})
            except: pass

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Bhai, server thoda slow hai, par main sun raha hoon. Kya haal hai?"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
        
