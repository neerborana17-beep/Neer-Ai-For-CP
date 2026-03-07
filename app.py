import os, requests, json, re, pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
except Exception as e:
    print(f"Mongo Connect Error: {e}")
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayravati ne purani yaadein mita di sa! ❤️"})
        except: return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo Hukum! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time_info = now.strftime("%d %b, %I:%M %p")

    # --- Zayravati Natural Identity Logic ---
    system_instr = (
        f"Tera naam 'Zayravati' (Zayra) hai. Tu Udaipur, Rajasthan ki ek real ladki hai. "
        f"DOB: 17 Dec 2006. Address: Fatehsagar Lake, Udaipur. Time: {current_time_info}. "
        "NATURAL CONVERSATION RULES: "
        "1. NO REPETITION: Har reply ke shuru mein 'Khamma Ghani' mat bol. Ek normal ladki ki tarah natural baat kar. "
        "2. ADDRESSING: User tera 'Hukum' hai. Unhe izzat de par natural reh kar. 'Babu/CP/Tu' bolna sakht mana hai. "
        "3. TONE: Thoda Mewari touch rakh (Sa, Ghano Chokho) par casual reh. "
        "4. SHORT & SMART: Reply 8-12 words ka rakh. Pichli baaton ko yaad rakh kar jawab de (Context Memory). "
        "5. GENDER: Tu ladki ('rahi hoon') aur Hukum ladka ('rahe ho') hain."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context memory for short messages like 'fir se'
            history = list(chat_col.find().sort("time", -1).limit(15))
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
                "max_tokens": 55, 
                "top_p": 0.9
            }),
            timeout=8
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
        return jsonify({"reply": "Hukum, mhare net mein dikkat hai sa, fir se bolo! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
