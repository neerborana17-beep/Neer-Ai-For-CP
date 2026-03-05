import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Setup (Memory ke liye)
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db = client['neer_db']
chat_col = db['history']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    # 1. MongoDB se purani 10 baatein yaad dilao
    history = list(chat_col.find().sort("_id", -1).limit(10))
    history.reverse()
    formatted_history = [{"role": m['role'], "content": m['content']} for m in history]

    # 2. Neer ki Asli Personality (Swag wapas!)
    system_instr = {
        "role": "system", 
        "content": "Tera naam Neer hai. Tu user ka sabse pakka desi dost hai. Tera nature ekdam natural hai—tu mazaakiya hai, kabhi kabhi roast karta hai, aur hamesha supportive rehta hai. Tu 'Bhai', 'Oye', 'Abe' jaise words use karta hai. Boring AI ki tarah mat bolna. Tu emotional baatein samajhta hai aur internet slangs use karta hai. Abhi 2026 chal raha hai."
    }
    
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [system_instr] + formatted_history + [{"role": "user", "content": user_input}],
        "temperature": 0.9 # Isse wo robotic nahi rahega
    }
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=15
        )
        
        reply = response.json()['choices'][0]['message']['content']
        # Bracket wali faltu cheezein hatane ke liye
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # 3. Baat yaad rakho (Save to MongoDB)
        chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
        chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})

        return jsonify({"reply": reply})
        
    except Exception as e:
        return jsonify({"reply": "Bhai, server thoda load le raha hai, fir se bol!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
