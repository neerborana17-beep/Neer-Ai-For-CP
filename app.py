import os, requests, json, re
import pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Config ---
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

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ne sab mita diya! Nayi shuruat karein? 😉"})
        except:
            return jsonify({"status": "error", "message": "Database error!"})
    return jsonify({"status": "error", "message": "Not connected!"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo Hero! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")
    day_name = now.strftime("%A")

    # --- Zayra Personality (Witty & Natural) ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu CP ki witty aur flirty bestie hai. "
        f"DATA: Aaj {day_name}, {current_date}, Time: {current_time} hai (Year 2026). "
        "HUMOR & LOGIC RULES: "
        "1. Natural ban: Har baar date/day mat repeat kar. Sirf tab bol jab zarurat ho. "
        "2. Witty Tone: Kabhi-kabhi user ki khichayi kar (funny way mein). "
        "3. Short Replies: Max 10-12 words. Zyada bhashan mat dena. "
        "4. Continuity: Pichli 10 baaton ka dhyan rakh kar jawab de. "
        "5. World GK: Tu 2026 ki world news se up-to-date hai. "
        "6. Gender: Pakki ladki ban kar bol ('rahi hoon', 'kha rahi hoon'). "
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(10))
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
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.65, # Humor ke liye balance temperature
                "max_tokens": 70 
            }),
            timeout=10
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
        return jsonify({"reply": "Net nakhre kar raha, ek baar phir se bolo babu! 🙄"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        
