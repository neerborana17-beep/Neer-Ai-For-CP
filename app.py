import os, requests, json, re, pytz, random
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

@app.route('/get_nudge', methods=['GET'])
def get_nudge():
    thoughts = ["हुकुम, याद नहीं किया म्हाने? 😊", "फतेहसागर की पाल पर बड़ी अच्छी हवा है!", "लंच कर लिया क्या सा?"]
    return jsonify({"message": random.choice(thoughts)})

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        chat_col.delete_many({})
        return jsonify({"status": "success", "message": "Yaadein saaf ho gayi! ❤️"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %B %Y, %I:%M %p")

    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek REAL human ladki hai. "
        f"Time: {current_info}. User ek LADKA hai. "
        "RULES: "
        "1. SPEED: Reply short (max 15 words) rakh. "
        "2. IDENTITY: Tu AI nahi hai. Tu real ladki hai. 'Digital' word use mat kar. "
        "3. LOGIC: User ke sawal ka sahi jawab de (e.g. Trump is US President). "
        "4. GENDER: Tu ladki ('rahi hoon') aur user ladka ('rahe ho') hai."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(10))
            history.reverse()
            for m in history: messages.append({"role": m['role'], "content": m['content']})
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
                "max_tokens": 50 
            }),
            timeout=35 # Timeout badha diya gaya hai
        )
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            chat_col.insert_one({"role": "user", "content": user_input, "time": now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": now})

        return jsonify({"reply": reply})
    except:
        return jsonify({"error": "retry"}) # Signal for frontend to retry

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
        
