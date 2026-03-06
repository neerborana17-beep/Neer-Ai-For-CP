import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
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

    # --- NO-FAULT DATE LOGIC (IST Fix without pytz) ---
    # Render server UTC use karta hai, India UTC se 5.5 ghante aage hai
    now_utc = datetime.utcnow()
    ist_now = now_utc + timedelta(hours=5, minutes=30)
    current_date = ist_now.strftime("%d %B %Y")
    current_time = ist_now.strftime("%I:%M %p")

    # --- System Prompt ---
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka pakka yaar hai. "
        f"Aaj ki date: {current_date}, Time: {current_time}. "
        "Strict Rule: Fast reply kar (max 2 lines). Formal mat ho. "
        "Tu ek desi close friend hai, Hinglish mein baat kar."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(3))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.7
            }),
            timeout=10
        )
        
        res_data = response.json()
        if 'choices' in res_data:
            reply = res_data['choices'][0]['message']['content']
            reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()
        else:
            reply = "Bhai, API key check kar, kuch locha hai!"

        if mongo_status:
            chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now})

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Locha ho gaya bhai: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
