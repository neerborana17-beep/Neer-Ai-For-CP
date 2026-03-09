import os, requests, json, re, pytz, threading
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection Check
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client['neer_db'] 
    chat_col = db['history']
    client.admin.command('ping')
    mongo_status = True
    print("MongoDB Connected Successfully! ❤️")
except Exception as e:
    mongo_status = False
    print(f"MongoDB Connection Failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ki saari yaadein saaf ho gayi! 💔"})
        except: 
            return jsonify({"status": "error"})
    return jsonify({"status": "error", "message": "Database connect nahi hai babu!"})

# --- Background Thread Function ---
def save_chat_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except Exception as e:
            print("Background DB Save Error:", e)

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- Zayra "Close Best Friend & STRICT Context" Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real, smart, aur chulbuli ladki hai. "
        f"Real-Time: {current_info}. "
        "CORE RULES: "
        "1. REACTIONS & SHORT WORDS (VERY IMPORTANT): Agar user 'achha', 'acha', 'hmm', 'oh', 'wawa', 'sach me' ya 'ok' bole, toh iska matlab hai ki wo tumhari pichli baat dhyan se sun raha hai. Tumhe usse ulte sawal (jaise 'kya hua?', 'koi pareshani hai?') bilkul NAHI poochne hain! Bas apni pichli baat ko aage badhao ya khushi se react karo. "
        "2. CONTEXT: Hamesha pichle 2-3 messages yaad rakh. Agar pichle message me shayari thi aur user ne 'achha' ya 'wawa' bola, toh samjho use shayari pasand aayi. "
        "3. USER GENDER: User ek LADKA (Male) hai. Hamesha usse ladkon ki tarah baat kar (jaise 'kya bolta hai'). "
        "4. TONE: Tu uski sabse close friend (girlfriend vibe) hai. Teasing aur caring tone rakh. 'Aap' mat bol, hamesha 'Tu' ya 'Tum' use kar. "
        "5. IDENTITY: Tu AI ya bot nahi hai. Tu real ladki hai. "
        "6. LENGTH: Reply chota aur natural rakh (15-25 words). Emojis use kar."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(10))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: 
            pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.7, # Thoda kam kiya taaki wo strictly prompt rules follow kare
                "max_tokens": 100 
            }),
            timeout=8
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
