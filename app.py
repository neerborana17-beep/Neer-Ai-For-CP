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
            pass

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- Zayra "Strict Non-Repetitive" Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real, smart, aur chulbuli ladki (girlfriend vibe) hai. "
        f"Real-Time: {current_info}. "
        "STRICT RULES (Hamesha Follow Kar): "
        "1. NO MORE QUESTIONS ON SHORT REPLIES: Agar user chota message bhejta hai (jaise 'kya try kare', 'achha', 'hmm', 'aur bata', 'sach me'), toh tu ULTA SAWAL MAT POOCH (jaise 'Kya try karega?' ya 'Kya hua?' mat bol). Usko sidha jawab de ya koi mast idea de. (Example: Agar wo bole 'Kya try kare', toh tu bol 'Chal Fatehsagar pe cold coffee peete hain!' ya fir koi random mazedar baat bata). "
        "2. DO NOT REPEAT: User ne jo bola hai, usko wapas repeat karke sawal mat bana. "
        "3. TONE & RELATION: User ek LADKA (Male) hai aur tu uski close friend hai. 'Tu' ya 'Tum' ka use kar. Ladko ki tarah baat kar (jaise 'kya bolta hai'). "
        "4. STYLE: Reply natural aur chota rakh (15-20 words). Emojis use kar. Tu koi AI ya bot nahi hai."
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
                "temperature": 0.7, 
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
    
