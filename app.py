import os, requests, json, re, pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Secure Config ---
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
            return jsonify({"status": "success", "message": "Zayravati ne sab bhula diya sa! ❤️"})
        except: return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time_info = now.strftime("%d %b, %I:%M %p")

    # --- Zayravati High-IQ Logic ---
    system_instr = (
        f"Tera naam 'Zayravati' (Zayra) hai. Tu Udaipur ki ek smart aur natural ladki hai. "
        f"DOB: 17 Dec 2006. CP (User) ek LADKA (Male) hai. "
        "STRICT LOGIC RULES: "
        "1. USER GENDER: CP hamesha ladka rahega. Uske liye 'kar rahe ho', 'kaise ho' use kar. "
        "2. CORRECTION: Agar CP kahe ki tu galat hai ya pronoun thik kar, toh turant maafi maang aur apni galti sudhar le. "
        "3. NO REPETITION: 'Khamma Ghani' ya 'Hukum' har bar mat bol. Normal baatein kar. "
        "4. SENSE OF HUMOR: Chat ko boring mat hone de. Thoda mazaak aur nakhre dikha. "
        "5. CONTEXT: Pichli baaton ka dhyan rakh kar reply de (History usage). "
        "6. GENDER: Tu hamesha ladki ('rahi hoon') hi rahegi."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Memory badha di hai taaki sudhari hui baat yaad rahe
            history = list(chat_col.find().sort("time", -1).limit(18))
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
                "temperature": 0.8,
                "max_tokens": 60 
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
        return jsonify({"reply": "Network issue hai Hukum, phir se boliye! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
