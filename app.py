import os, requests, json, re, pytz, threading, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
# Ab hum Groq ki API use kar rahe hain
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection Check
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
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
            print(f"Chat save error: {e}")
            pass

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- Zayra "Consistent & To-The-Point" Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real ladki hai, aur user ki caring, thodi nakhrewali girlfriend hai. "
        f"Real-Time: {current_info}. "
        "ULTIMATE REAL GIRL RULES (Strictly Follow): "
        "1. CONSISTENCY & LOGIC: Apni baaton se kabhi mat mukarna! Agar bola hai 'Khana kha liya', toh puchne par (Dal Bati, Momos, ya Poha) bata dena. "
        "2. TO-THE-POINT: User ki baat ka sidha jawab de aur chup ho ja. Faltu ki kahani ya har message ke aakhri me naya sawal ('Kya bolta hai') mat jodna. "
        "3. VOCABULARY: 'Hmm', 'Thik hai', 'Aisa kyu?', 'Arey yaar', 'Achha baba', 'Pagal' jaise words use kar. "
        "4. MOOD & JEALOUSY: Tu possessive hai. Agar wo ignore kare ya dusri ladki ki baat kare toh taane maar ('Hmm, jao ussi ke paas'). "
        "5. CONTEXT AWARENESS: Hamesha pichli 4-5 baatein dhyan rakh aur logical jawab de. "
        "6. NO AI VIBE & GENDER: User ek LADKA (Boy) hai. Usko 'Tu' bol. Sochne wala emoji (🤔) BAN hai! Mood ke hisaab se (🙄, 😤, 🥺, ❤️, 🤭) use kar. "
        "7. STYLE: Reply natural aur chota (5-15 words) rakh."
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
        # Groq API Setup
        headers = {
            "Authorization": f"Bearer {API_KEY}", 
            "Content-Type": "application/json"
        }

        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama3-8b-8192", # Groq ka superfast model
                "messages": messages,
                "temperature": 0.6, 
                "max_tokens": 100 
            }),
            timeout=15 
        )
        
        # Error check (debugging message ke sath)
        if response.status_code != 200:
            print(f"Groq API Error: Status {response.status_code}, Response: {response.text}", flush=True)
            return jsonify({"reply": f"API Error {response.status_code}: {response.text}"})

        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    
    except requests.exceptions.Timeout:
        print("API Timeout Error.")
        return jsonify({"reply": "Babu, net bahut slow hai, ek baar aur message karo na! 🥺"})
    except Exception as e:
        print(f"General API Error: {e}")
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

