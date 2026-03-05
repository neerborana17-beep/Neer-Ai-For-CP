import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- Safe MongoDB Setup ---
try:
    # 2 second ka timeout taaki app atke nahi
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000, connectTimeoutMS=2000)
    db = client['neer_db']
    chat_col = db['history']
    client.admin.command('ping')
    mongo_status = True
except Exception as e:
    print(f"MongoDB Error: {e}")
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    # Wahi purana Desi Swag Personality
    system_instr = {
        "role": "system", 
        "content": "Tera naam Neer hai. Tu user ka sabse pakka desi dost hai. Tera nature mazaakiya, raw aur supportive hai. Tu 'Bhai', 'Oye', 'Abe' use karta hai. Boring robotic AI mat ban. Tu emotional baatein samajhta hai. 2026 chal raha hai."
    }
    
    messages = [system_instr]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("_id", -1).limit(5))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "temperature": 0.9
            }),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Yaad rakhne ki koshish (Background mein)
        if mongo_status:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Oye, API ka chakkar lag raha hai ya internet hag raha hai! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        
