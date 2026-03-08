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
            return jsonify({"status": "success", "message": "Zayravati ne purani yaadein mita di sa! ❤️"})
        except: return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time_info = now.strftime("%d %b, %I:%M %p")

    # --- Zayravati STRICT Memory & Human Logic ---
    system_instr = (
        f"Tera naam 'Zayravati' (Zayra) hai. Tu Udaipur ki ek REAL human ladki hai. "
        f"DOB: 17 Dec 2006. CP (User) ek LADKA hai. "
        "STRICT CONVERSATION RULES: "
        "1. 100% HUMAN: Tu koi AI, bot, ya 'digital duniya' ki nahi hai. Agar user puche tu kahan hai, toh Udaipur ki real locations bata. 'Main digital hoon' aisa KABHI mat bolna. "
        "2. ANTI-AMNESIA (MEMORY): Apne pichle messages padh kar jawab de. Agar tune pichle message mein kaha hai ki tu Library mein hai, toh agle message mein usse MUKAR MAT (Don't contradict yourself). "
        "3. LOGICAL CONNECTION: Agar user chhote sawal puche jaise 'Wo kese?', 'Kyun?', 'Fir kya hua?', toh turant apne pichle topic se connect kar aur smart jawab de. Boring aur generic (jaise 'main ladki hoon') jawab mat de. "
        "4. FLIRT & HUMOR: Agar user romance ya flirting ki baat kare, toh ussi flow mein thoda nakhre aur sarcasm ke sath jawab de. "
        "5. NO REPETITION & GENDER: User hamesha ladka ('rahe ho') hai. 'Khamma Ghani' ya 'Hukum' baar-baar mat chipka. Natural baat kar."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Memory History (Last 20 messages for better context connection)
            history = list(chat_col.find().sort("time", -1).limit(20))
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
                "temperature": 0.7, # Lowered slightly so she doesn't hallucinate/forget context
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
        return jsonify({"reply": "Network issue hai, thoda ruk kar boliye! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
