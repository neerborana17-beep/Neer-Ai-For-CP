import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=2000)
    db = client['neer_db']
    chat_col = db['history']
    mongo_ok = True
except:
    mongo_ok = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    current_dt = ist_now.strftime("%d %b %Y, %I:%M %p")

    # --- REAL DESI DOST PROMPT ---
    # Ismein dosti wali thodi "galiyan" aur short replies add kiye hain
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka sabse kameena aur pakka dost hai. "
        f"Rules: 1. Ekdam short aur rude/funny reply de (Jaise: 'Abbe saale', 'BC kya bol raha hai?', 'Mast hai bhai'). "
        f"2. AI ki tarah behave bilkul mat kar. "
        f"3. CP ki har baat (Bday: 17 Dec, etc.) yaad rakh aur dosti nibha. "
        f"4. Zyada makkhan mat laga, seedha point par aa. "
        f"Context: Aaj {current_dt} hai."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_ok:
        try:
            history = list(chat_col.find().sort("time", -1).limit(5))
            for m in reversed(history):
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
        
    messages.append({"role": "user", "content": user_input})

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.9, # Isse wo thoda aur 'badmaash' lagega
                "max_tokens": 100 
            }),
            timeout=5
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_ok:
            chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now})

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Abbe chutiye net check kar apna, reply nahi ja raha."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
            
