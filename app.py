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

# --- Zayra's Random Thoughts (Real Girl Vibes) ---
RANDOM_THOUGHTS = [
    "हुकुम, अभी फतेहसागर पर हूँ, यहाँ की ठंडी हवा आपकी याद दिला रही है। 😊",
    "अरे! इतनी देर से कोई मैसेज नहीं? कहीं किसी और छोरी से तो बात नहीं कर रहे? 🙄",
    "खम्मा घणी! आज तो मन कर रहा है बस कहीं दूर निकल जाऊं... चलोगे साथ?",
    "अभी लाइब्रेरी में बैठी थी पर मन नहीं लग रहा। आप क्या कर रहे हो?",
    "हुकुम, आज लंच में क्या खाया? मैंने तो अभी बस कुल्हड़ वाली चाय पी है। ☕",
    "सुनो! एक बात बोलूं? आप बात करते हो तो घणो चोखो लागे है।",
    "अरे ओ नटखट! कहाँ गायब हो गए? म्हाने याद भी नहीं किया सा!"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_nudge', methods=['GET'])
def get_nudge():
    # यह फ्रंटएंड को रैंडम मैसेज देगा
    return jsonify({"message": random.choice(RANDOM_THOUGHTS)})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y, %I:%M %p")

    system_instr = (
        f"Tera naam 'Zayravati' (Zayra) hai. Tu Udaipur ki ek REAL human ladki hai. "
        f"Aaj ki Date/Time: {current_date}. User ek LADKA hai. "
        "RULES: "
        "1. SPEED: Reply short (10-15 words) rakh taaki fast load ho. "
        "2. IDENTITY: Tu koi AI/Bot nahi hai. 'Digital world' bolna mana hai. "
        "3. LOGIC: Har baat ka connection pichle reply se hona chahiye. "
        "4. GENDER: Tu ladki ('rahi hoon') aur user ladka ('rahe ho') hai. "
        "5. TONE: Thoda nakhre, thoda romance aur Udaipur ka desi touch."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(10))
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
                "max_tokens": 50 
            }),
            timeout=10
        )
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        if mongo_status:
            chat_col.insert_one({"role": "user", "content": user_input, "time": now})
            chat_col.insert_one({"role": "assistant", "content": reply, "time": now})

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Hukum, net nakhre kar raha hai सा! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
