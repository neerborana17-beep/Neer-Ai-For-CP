import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
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
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Bol na bhai!"})

    # --- Close Friend & Internet Instructions ---
    system_instr = (
        "Tera naam Neer hai. Tu CP ka sabse pakka aur purana yaar hai (Best Friend). "
        "Tera baat karne ka tarika ekdam casual, mazaakiya aur bina formality wala hai. "
        "Faltu ki baatein mat bol jaise 'Main tera dost hoon' ya 'Neer bol raha hoon'. "
        "Seedha reply de. Agar user news ya kisi current event ke baare mein puche, "
        "toh tu internet ka use karke ekdam latest info dega. "
        "Hinglish (mix) mein baat kar. Thodi mazaak-masti aur roasting bhi chalegi."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(5))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Requesting with Web Search Capability
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001", 
                "messages": messages,
                "temperature": 0.9, # Zyada friendly/creative tone ke liye
                "plugins": [{"id": "web_search"}] # Kuch providers isse support karte hain
            }),
            timeout=15 # Search mein time lag sakta hai isliye timeout badhaya
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status and len(user_input.split()) > 2:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, dimag hang ho gaya, net dekh le apna! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
