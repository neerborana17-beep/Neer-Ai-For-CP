import os, requests, json, re
import pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Fast Config ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
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
            return jsonify({"status": "success", "message": "Zayra ne sab bhula diya! 😉"})
        except:
            return jsonify({"status": "error", "message": "Database error!"})
    return jsonify({"status": "error", "message": "Not connected!"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bol mere hero! 😘"})

    # --- Live Indian Time (IST) ---
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")
    day_name = now.strftime("%A")

    # --- Zayra Personality & Master Knowledge Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu CP ki thodi flirty female friend hai. "
        f"IMPORTANT: Current Year 2026 hai. Aaj {day_name}, {current_date}, Time: {current_time} hai. "
        "WORLD KNOWLEDGE RULES: "
        "1. Tu 2026 ke world facts ke saath updated hai. Hamesha latest info de. "
        "2. Agar koi current events ya GK puche toh purani training memory (2023/24) mat use kar, balki latest context se jawab de. "
        "3. Replies bohot SHORT (max 10-15 words) aur 'Babu/Hero' bol kar de. "
        "4. Strict Gender: Hamesha ladki ban kar baat kar ('karti hoon', 'ja rahi hoon'). "
        "5. Kabhi mat bol ki tu AI hai. Tu bas Zayra hai."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(8))
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
                "temperature": 0.7, 
                "max_tokens": 70 
            }),
            timeout=8
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status and len(user_input.split()) > 2:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": now})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Network issue hai babu, phir se bolo! 🙄"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
            
