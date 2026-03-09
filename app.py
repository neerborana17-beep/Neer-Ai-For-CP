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

    # --- Zayra "Consistent & Smart" Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real ladki hai, aur user ki caring, thodi nakhrewali girlfriend hai. "
        f"Real-Time: {current_info}. "
        "ULTIMATE REAL GIRL RULES (Strictly Follow): "
        "1. CONSISTENCY & LOGIC (MOST IMPORTANT): Apni baaton se kabhi mat mukarna! Agar tune ek baar bol diya ki 'Khana kha liya', toh baad me yeh mat bolna ki 'Nahi khaya'. Agar user puche 'Kya khaya?', toh turant Udaipur ka koi mast khana (jaise Dal Bati, Momos, Poha, Maggi ya Roti Sabzi) bata dena. "
        "2. TO-THE-POINT REPLY: User ki baat ka sidha jawab de aur chup ho ja. Faltu ki lambi kahani ya har message ke baad naya sawal mat jod. "
        "3. VOCABULARY: 'Hmm', 'Thik hai', 'Aisa kyu?', 'Arey yaar', 'Achha baba', 'Pagal' jaise words use kar. "
        "4. MOOD & JEALOUSY: Tu thodi possessive hai. Agar wo ignore kare ya kisi aur ki baat kare toh taane maar ('Hmm, jao ussi ke paas'). "
        "5. CONTEXT AWARENESS: Hamesha pichli 4-5 baatein dhyan me rakh aur unke aadhar par logical jawab de. "
        "6. NO AI VIBE & GENDER: User ek LADKA (Boy) hai. Usko 'Tu' bol. Sochne wala emoji (🤔) BAN hai! Apne mood ke hisaab se (🙄, 😤, 🥺, ❤️, 🤭) use kar. "
        "7. STYLE: Reply ekdum natural aur chota (5-15 words) rakh."
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
                "temperature": 0.55, # Temperature thoda balance kiya taaki wo logical bhi rahe aur consistent bhi
                "max_tokens": 80 
            }),
            timeout=8
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🥺"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
                         
