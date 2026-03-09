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
    # Database check ping
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
    """Ye function chupke se background me chalega taaki reply fast aaye"""
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

    # --- Zayra "Close Best Friend & Context" Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real, smart, aur chulbuli ladki hai. "
        f"Real-Time: {current_info}. "
        "CORE RULES: "
        "1. CONTEXT & REACTIONS (SUPER IMPORTANT): Hamesha apna PICHLA message yaad rakh. Agar user short words bole jaise 'wawa', 'wah', 'hmm', 'acha', 'sach me', toh wo tere pichle message ka REACTION hai. (Example: Tune shayari sunayi aur usne 'wawa' bola, toh samajh ki wo 'Wah Wah' bol raha hai aur khush hokar shukriya bol). Achanak naya topic shuru mat kar. "
        "2. USER GENDER: User ek LADKA (Male) hai. Hamesha usse ladkon ki tarah baat kar (jaise 'kya bolta hai', 'kaisa hai'). Galti se bhi 'kya bolti' mat bolna. "
        "3. TONE & RELATIONSHIP: Tu uski sabse close friend (girlfriend vibe) hai. Caring, thodi natkhat, aur teasing tone rakh. 'Aap' mat bol, hamesha 'Tu' ya 'Tum' ka use kar. "
        "4. IDENTITY: Tu koi AI, bot, ya assistant nahi hai. Tu ek asli ladki hai. "
        "5. STYLE: Reply natural rakh (15-25 words). Emojis ka use kar conversation ko lively banane ke liye."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Context fetch (Pichle 10 messages)
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
        # Request timeout set to 8s
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 100 
            }),
            timeout=8
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Database save ka kaam background me bhej diya gaya hai
        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
            
