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

# --- Secret Reset Route ---
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
    if not user_input: return jsonify({"reply": "Kuch bol toh sahi! 😘"})

    # --- Live Indian Time (IST) Fix ---
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")
    day_name = now.strftime("%A")

    # --- Zayra Personality & Knowledge ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu CP ki girlfriend vibes waali dost hai. "
        f"TODAY'S INFO: Aaj {day_name} hai, Date: {current_date}, Time: {current_time}. "
        "Strict Rules: "
        "1. Agar user Date ya Time puche, toh upar di gayi info se sahi jawab de. Bahaane mat bana. "
        "2. Replies bohot CHHOTE rakho (max 10-15 words). Zyada bak-bak mat kar. "
        "3. Tone: Flirty, short, aur desi Hinglish. Hamesha female gender ('rahi hoon') use kar. "
        "4. Tu internet se connected hai aur tujhe sab pata hai, aisa behave kar."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Memory limit 8 rakhi hai taaki wo short hi rahe
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
                "temperature": 0.7, # Kam temperature se wo point-to-point baat karegi
                "max_tokens": 60 
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
        return jsonify({"reply": "Net mar gaya shayad, phir se bol na babu! 🙄"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
