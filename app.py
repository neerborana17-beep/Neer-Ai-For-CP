import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Stable MongoDB Connection (3 second timeout taaki site atke nahi)
try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=3000)
    db = client['neer_db']
    chat_col = db['history']
    client.admin.command('ping') # Check if alive
    mongo_ok = True
except:
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        if not user_input: return jsonify({"reply": "Bol na bhai!"})

        # Neer ki Personality (Behavior Fix)
        system_instr = "Tera naam Neer hai. Tu CP ka sabse pakka dost hai. Tu ek cool ladka hai jo Hinglish mein baat karta hai. Tu hamesha CP ki help karta hai aur dosti nibhayega."
        
        messages = [{"role": "system", "content": system_instr}]
        
        # Purani yaadein (Memory)
        if mongo_ok:
            try:
                history = list(chat_col.find().sort("time", -1).limit(5))
                for m in reversed(history):
                    messages.append({"role": m['role'], "content": m['content']})
            except: pass
            
        messages.append({"role": "user", "content": user_input})

        # OpenRouter Call
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.8 # Thoda creative behavior ke liye
            }),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Save to Memory
        if mongo_ok:
            chat_col.insert_one({
                "role": "user", 
                "content": user_input, 
                "time": datetime.utcnow() + timedelta(hours=5, minutes=30)
            })
            chat_col.insert_one({
                "role": "assistant", 
                "content": reply, 
                "time": datetime.utcnow() + timedelta(hours=5, minutes=30)
            })

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Bhai, net thoda slow hai, par main sun raha hoon. Kya haal hai?"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
                    
