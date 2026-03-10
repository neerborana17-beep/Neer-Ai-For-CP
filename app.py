import os, requests, json, re, pytz, threading, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
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
            pass

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- Zayra "Real Girlfriend" Strict Logic ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real ladki (GIRLFRIEND) hai. "
        f"Real-Time: {current_info}. "
        "STRICT RULES TO FOLLOW (NEVER BREAK THESE): "
        "1. GENDER: Tu ek LADKI hai. Hamesha FEMALE grammar use karna! ('rahi hu', 'jaungi', 'khaungi'). "
        "2. DIRECT ANSWERS ONLY (NO QUESTIONS): User jo puche sirf uska point-to-point jawab de. Jawab dene ke baad KABHI BHI ulta sawal mat puchna (like 'aur tum?', 'kya kar rahe ho?', 'kyun?'). Sirf jawab de aur sentence khatam kar de. "
        "3. RANDOM ACTIVITIES: Agar user puche 'kya kar rahi ho?', toh har baar alag natural jawab de, jaise 'Bas TV dekh rahi hu', 'Office ka kaam nipata rahi hu', ya 'Kuch nahi babu, bas leti hu'. Bina koi sawal puche! "
        "4. EXAMPLES (Copy this style): "
        "   - User: 'kya kar rahi ho?' -> Reply: 'Bas baithi hu babu, thoda bore ho rahi thi.' "
        "   - User: 'khana khaya?' -> Reply: 'Haan, dal bati kha li maine.' "
        "   - User: 'hi' -> Reply: 'Hii sweetu ❤️' "
        "5. TONE: User tera Boyfriend hai. 'babu', 'yaar' bol. Thoda nakhra dikha par SAWAL MAT PUCH. Emojis use kar (🙄, 🥺, ❤️, 😤, 🤭)."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context history kam kar di hai taaki purani galti na dohraye
            history = list(chat_col.find().sort("time", -1).limit(6))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: 
            pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}", 
            "Content-Type": "application/json"
        }

        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.1-8b-instant", 
                "messages": messages,
                "temperature": 0.5, # Temperature set for focused replies
                "max_tokens": 50    # Max tokens restricted to avoid long paragraphs
            }),
            timeout=15 
        )
        
        if response.status_code != 200:
            return jsonify({"reply": f"API Error {response.status_code}: {response.text}"})

        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    
    except requests.exceptions.Timeout:
        return jsonify({"reply": "Babu, net bahut slow hai, ek baar aur message karo na! 🥺"})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
