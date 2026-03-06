import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Connection setting ko light rakha hai taaki site turant khule
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
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
    try:
        user_input = request.json.get("message")
        if not user_input: return jsonify({"reply": "Bol na bhai!"})

        now_utc = datetime.utcnow()
        ist_now = now_utc + timedelta(hours=5, minutes=30)
        
        system_instr = f"Tera naam Neer hai. Tu CP ka dost hai. Aaj: {ist_now.strftime('%d %b %Y')}. Hinglish bol."
        messages = [{"role": "system", "content": system_instr}]
        
        if mongo_status:
            try:
                history = list(chat_col.find().sort("time", -1).limit(3))
                for m in reversed(history):
                    messages.append({"role": m['role'], "content": m['content']})
            except: pass
            
        messages.append({"role": "user", "content": user_input})
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.7
            }),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now})

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Ek baar refresh kar le bhai, connection slow hai!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
        
