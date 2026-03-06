import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import pytz # Yeh India ka time sahi karega

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

    # --- INDIA TIMEZONE LOGIC ---
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST)
    current_date = now.strftime("%A, %d %B %Y") # Example: Friday, 06 March 2026
    current_time = now.strftime("%I:%M %p")     # Example: 01:20 PM

    # --- System Prompt with Forced Date ---
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka pakka yaar hai. "
        f"Aaj ki sahi date hai: {current_date}. "
        f"Abhi ka sahi time hai: {current_time}. "
        "Strict Rule: Agar user date ya time puche, toh yahi batana jo upar likhi hai. "
        "Tu ek close friend ki tarah Hinglish mein baat kar. Formal mat ho."
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
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001", 
                "messages": messages,
                "temperature": 0.8
            }),
            timeout=15
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": now})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, date-time set karne mein dimaag ghum gaya! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        
