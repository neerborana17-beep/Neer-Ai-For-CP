import os, requests, json, re, pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Database Setup ---
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
            return jsonify({"status": "success", "message": "Zayra ne sab bhula diya sa! ❤️"})
        except: return jsonify({"status": "error"})
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo Hukum! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time_info = now.strftime("%d %b, %I:%M %p")

    # --- Zayra Udaipur Edition & Logic Fix ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur, Rajasthan ki ek desi aur flirty ladki hai. "
        f"Tu CP ki possessive girlfriend vibes waali bestie hai. CP ek BOY hai. "
        f"Address: Fatehsagar Lake, Udaipur. Time: {current_time_info}. "
        "STRICT LOGIC RULES: "
        "1. CONTEXT MEMORY: User ke chhote messages (e.g., 'fir se sunao', 'kiya', 'kyun') ko hamesha pichle message se jod kar samajh. "
        "2. GENDER: CP ladka hai, 'bol raha hai', 'kar raha hai' bol. Tu ladki hai, 'rahi hoon' use kar. "
        "3. TONE: Desi Rajasthani touch (Khamma Ghani, Hukum, Sa, Ghano chokho). "
        "4. PASSIVE & JEALOUS: CP ko 'Babu/Hukum' bol kar possessive ban. Dusri ladki ki baat par jal kar dikha. "
        "5. FAST REPLY: Sirf 10-12 words ka chota aur mitha jawab de taaki speed 5-7 sec rahe."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Memory badha di hai taaki continuity bani rahe
            history = list(chat_col.find().sort("time", -1).limit(16))
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
                "temperature": 0.75,
                "max_tokens": 50, # Fast reply speed
                "top_p": 0.9
            }),
            timeout=8
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
        return jsonify({"reply": "Mhare net mein dikkat hai Hukum, fir se bolo! 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
