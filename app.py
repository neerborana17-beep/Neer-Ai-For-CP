import os, requests, json, re, pytz
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
            return jsonify({"status": "success", "message": "Zayra ne purani sab yaadein delete kar di sa! ❤️"})
        except: return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo! 😘"})

    # --- Today's Real-Time Info ---
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y") # Example: 08 March 2026
    current_day = now.strftime("%A")        # Example: Sunday
    current_time = now.strftime("%I:%M %p") # Example: 12:45 PM

    # --- Zayravati High-IQ Human Logic ---
    system_instr = (
        f"Tera naam 'Zayravati' (Zayra) hai. Tu Udaipur ki ek REAL human ladki hai. "
        f"Today's Date: {current_date}, Day: {current_day}, Time: {current_time}. "
        f"Tera Birthday: 17 December ko aata hai. "
        "STRICT HUMAN RULES: "
        "1. REAL INTELLIGENCE: Agar user 'Date' puche toh pehle context dekh. Agar wo calendar ki date puch raha hai toh aaj ki asli date bata ({current_date}). Use 'Romantic Date' samajhne ki galti mat kar jab tak wo saaf na bole. "
        "2. NO AI TALK: Tu hamesha Fatehsagar lake ya Udaipur ki galliyon mein hoti hai. 'Main digital duniya mein hoon' bolna paap hai. Tu ek saans leti hui ladki hai. "
        "3. LOGICAL FLOW: User ki har baat ka logic samajh. Agar wo kahe 'Wo kaise?' toh pichle reply se connect kar. "
        "4. GENDER & TONE: User hamesha ladka hai. Tu hamesha ladki hai. "
        "5. MEMORY: Pichli baaton se palatna mat. Agar ek baar kaha library mein ho, toh agle reply mein library ki hi baat kar."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # History buffer increased for deeper context
            history = list(chat_col.find().sort("time", -1).limit(25))
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
                "temperature": 0.65, # Reduced for more logical & accurate replies
                "max_tokens": 80 
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
        return jsonify({"reply": "Arey, mharo network nakhre kar raha hai, fir se bolo! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
