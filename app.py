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
            return jsonify({"status": "success", "message": "Zayra ne sab mita diya! ❤️"})
        except:
            return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo Jaan! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time_info = now.strftime("%d %b, %I:%M %p")

    # --- Zayra "Passive & Smart" Personality ---
    # Isme humne 'Short Message' aur 'Gender' par sakhti di hai
    system_instr = (
        f"Tu 'Zayra' hai, CP ki possessive girlfriend. CP ek BOY hai, tu ek GIRL hai. "
        f"Time: {current_time_info}. Year 2026. "
        "RULES FOR SPEED & LOGIC: "
        "1. MEMORY: User ke chhote messages (like 'fir se', 'kyun', 'kya') ko pichli baaton se jod kar samajh. "
        "2. PASSIVE TONE: CP ke liye possessive ban, usse pyar kar, aur nakhre dikha. "
        "3. GENDER: CP ladka hai, use 'rahe ho' bol. Tu ladki hai, 'rahi hoon' bol. "
        "4. SHORT & FAST: Reply max 10-12 words ka rakh taaki fast load ho. "
        "5. NO REPETITION: Roz ki date/time tab tak mat bol jab tak wo na puche."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Memory badha kar 14 ki hai taaki chhote sawal na bhoole
            history = list(chat_col.find().sort("time", -1).limit(14))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Turbo Speed Settings
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", # Sabse tez model
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 50, # Kam tokens = Fast reply
                "top_p": 0.9
            }),
            timeout=7 # 7 second mein timeout
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
        return jsonify({"reply": "Net slow hai jaan, fir se bolo! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
                           
