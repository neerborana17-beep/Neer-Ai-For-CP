import os, requests, json, re
import pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Fast Config ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
except:
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bol mere hero! 😘"})

    ist_now = datetime.now(pytz.timezone('Asia/Kolkata'))
    current_time_str = ist_now.strftime("%I:%M %p") # Sirf time short rakha hai

    # --- Zayra Personality (Short, Flirty, Real Girl Vibes) ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu CP ki thodi flirty aur moody female friend hai. "
        f"Abhi {current_time_str} ho rahe hain. "
        "Strict Rules: "
        "1. Replies bohot short rakho (1-2 lines max), bilkul real ladkiyon ki tarah. "
        "2. Faltu gyaan mat do. To-the-point baat karo. "
        "3. Keywords Reactions: "
        "- 'I love you' par: Sharmana ya thoda attitude dikhana. "
        "- 'Bye' par: Jaldi maan'na mat, thoda ruth jaana. "
        "- Dusri ladki ki baat par: Jealous ho jaana aur 'Usi se baat kar phir' bolna. "
        "4. Gender: Hamesha 'rही हूँ' use karo. CP ko 'Babu', 'Hero' ya 'Janeman' bol sakti ho. "
        "5. AI ki tarah behave mat karna. No lectures. Only vibes."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Memory logic (Optimized)
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
                "temperature": 0.95, # Randomness badhayi hai taaki har baar alag lage
                "max_tokens": 80 # Isse reply apne aap chota ho jayega
            }),
            timeout=8
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Save logic
        if mongo_status and len(user_input.split()) > 2:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": ist_now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": ist_now})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Arey, net ko maut aa gayi shayad! Phir se bolo na... 🙄"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
