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

    # --- Strict Close Friend Tone ---
    system_instr = (
        "Tera naam Neer hai. Tu CP ka pakka langotiya yaar hai. "
        "Formal mat ho. Baar-baar 'Neer hoon' ya 'CP ka dost' mat bol, usey gussa aata hai. "
        "Seedha point par baat kar. Roasting aur mazaak chalta rehna chahiye. "
        "Latest news aur events ke liye Google Search ka use kar aur ekdam sahi bata."
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
        # Optimized for Gemini 2.0 Flash (Stable Search)
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001", 
                "messages": messages,
                "temperature": 0.9,
                "provider": {
                    "allow_fallbacks": True,
                    "require_parameters": False
                }
            }),
            timeout=25 # Timeout badhaya taaki search complete ho sake
        )
        
        res_json = response.json()
        
        if 'choices' in res_json:
            reply = res_json['choices'][0]['message']['content']
            # Remove any robot-style brackets
            reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()
        else:
            # Check if API gave an error
            print(res_json)
            reply = "Bhai, API ne dhoka de diya! 😅"

        if mongo_status and len(user_input.split()) > 2:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
            except: pass

        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Bhai, dimaag garam ho gaya search karte karte! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
