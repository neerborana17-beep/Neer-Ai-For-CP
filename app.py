import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- Safe MongoDB Setup ---
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client['neer_db']
    chat_col = db['history']
    # Check connection
    client.admin.command('ping')
    mongo_status = True
except:
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    # Personality Instruction (Tera Swag Wapas!)
    system_instr = {
        "role": "system", 
        "content": "Tera naam Neer hai. Tu user ka sabse pakka desi dost hai. Tera nature mazaakiya, raw aur supportive hai. Tu 'Bhai', 'Oye', 'Abe' use karta hai. Boring robotic AI mat ban. 2026 chal raha hai."
    }
    
    messages = [system_instr]
    
    # Agar Mongo chal raha hai toh history lo
    if mongo_status:
        history = list(chat_col.find().sort("_id", -1).limit(5))
        history.reverse()
        for m in history:
            messages.append({"role": m['role'], "content": m['content']})
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "temperature": 0.8
            }),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, dimaag garam ho gaya hai mera, thoda ruk ke bol! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                     
