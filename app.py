import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import pytz

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

    # --- Live Date (No Search Needed) ---
    IST = pytz.timezone('Asia/Kolkata')
    now = datetime.now(IST)
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")

    # --- Optimized System Prompt ---
    system_instr = (
        f"Tera naam Neer hai. Tu CP ka pakka yaar hai. Aaj: {current_date}, Time: {current_time}. "
        "Strict Rule: Fast reply kar (max 2-3 lines). Search mat kar jab tak bohot zaruri na ho. "
        "Close friend ki tarah Hinglish bol. Formal baatein mat kar."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Memory limit to 3 for Max Speed
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(3))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Gemini 2.0 Flash Lite is the fastest model right now
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 150
            }),
            timeout=8 # 8 second se zyada wait nahi karega
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            chat_col.insert_one({"role": "user", "content": user_input, "time": now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": now})

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, net slow hai ya API hang ho gayi! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
