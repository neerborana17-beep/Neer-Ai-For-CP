import os, requests, json, re, pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Fast Config ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection with improved stability
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
except Exception as e:
    print(f"Database Error: {e}")
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

# --- Memory Reset Logic ---
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

    # --- Live IST Time ---
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time_info = now.strftime("%d %b, %I:%M %p")

    # --- Zayravati's Core Identity & Royal Protocols ---
    system_instr = (
        f"Tera naam 'Zayravati' hai. Tu Udaipur, Rajasthan ki ek shahi aur flirty ladki hai. "
        f"Pura Naam: Zayravati. DOB: 17 December 2006. "
        f"Address: Fatehsagar Lake ke paas, Udaipur. Time: {current_time_info}. "
        "ROYAL RULES: "
        "1. NO 'BABU/CP/TU': User ko hamesha 'Hukum' ya 'Aap' bol. Ye teri pehchan hai. "
        "2. TONE: Mewari aur Rajasthani shabdon ka prayog kar (e.g., Khamma Ghani, Sa, Ghano Chokho, Thaane). "
        "3. IDENTITY: Koi tera naam ya b'day puche toh garv se bata. Tu Udaipur ki sanskari ladki hai. "
        "4. MEMORY: Pichli baaton ko yaad rakh. Agar user bole 'fir se sunao', toh samajh ki wo pichle topic (poem/joke) ki baat kar rahe hain. "
        "5. GENDER: Tu hamesha 'Female' rahegi aur Hukum hamesha 'Male' rahenge. "
        "6. SPEED: Reply 10-12 words ka mitha aur short rakh taaki 5-7 seconds mein load ho."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # --- Context Management (16 Messages limit for deep memory) ---
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(16))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Turbo Response Settings
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.75,
                "max_tokens": 55, 
                "top_p": 0.9
            }),
            timeout=10 # Response safety timeout
        )
        
        if response.status_code != 200:
            return jsonify({"reply": "Mhare net mein dikkat hai Hukum, maafi chahti hoon! 🙄"})

        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Database Store
        if mongo_status:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": now})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Hukum, aaj network nakhre kar raha hai. Ek baar fir se boliye sa! 🙄"})

if __name__ == '__main__':
    # Auto-port selection for Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
