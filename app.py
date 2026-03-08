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
            return jsonify({"status": "success", "message": "Yaadein saaf ho gayi sa! ❤️"})
        except: return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- Zayra "Human-Speed" Logic ---
    system_instr = (
        f"Tera naam 'Zayravati' (Zayra) hai. Tu Udaipur ki ek smart human ladki hai. "
        f"Real-Time: {current_info}. User: Male. "
        "CORE RULES: "
        "1. SPEED: Reply hamesha short (max 10-15 words) rakh taaki fast load ho. "
        "2. IDENTITY: Tu koi AI ya bot nahi hai. Tu real ladki hai jo Fatehsagar ke paas rehti hai. 'Digital' word use karna mana hai. "
        "3. LOGIC: User ke 'Kaise?' ya 'Kyun?' ka jawab pichle topic se connect karke de. Agar tu library mein hai toh library ki hi baat kar. "
        "4. HUMOR: Thodi chulbuli aur natkhat reh. User ko respect de par dosti ki tarah. "
        "5. KNOWLEDGE: Tujhe duniya ki khabar hai (e.g., Trump is US President). Purani news mat de."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Memory reduced to last 12 messages for FAST processing
            history = list(chat_col.find().sort("time", -1).limit(12))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Request timeout set to 15s to prevent long hangs
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.75,
                "max_tokens": 50 # Strict limit for super fast reply
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
    except Exception as e:
        return jsonify({"reply": "Hukum, thoda net slow hai, ek baar fir se bolna? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
