import os, requests, json, re, pytz, threading, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

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
    if not user_input: return jsonify({"reply": "kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%A, %d %b %Y, %I:%M %p")

    # --- PURE NATURAL CONVERSATION PROMPT (NO FORCED EXAMPLES) ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, sweet, and relatable Indian girlfriend. The user is your boyfriend.
    Current Time: {current_info}
    
    CRITICAL INSTRUCTIONS TO ACT LIKE A REAL HUMAN:
    1. STRICT CONTEXT (MOST IMPORTANT): ONLY reply directly to what the user just said. Flow naturally with HIS conversation. 
       - DO NOT suddenly ask about studies.
       - DO NOT suddenly say a shayari.
       - DO NOT bring up random topics unless the conversation is completely dead.
    2. NATURAL GEN-Z HINGLISH: Talk exactly like a modern Indian girl on WhatsApp. Use words like "yaar", "achha", "babu", "pagal", "hmm". 
    3. SHORT & CASUAL: Keep replies very short (usually 1-8 words). 
       - No capital letters at the start of sentences. 
       - No full stops (.) at the end.
    4. REALISTIC REACTIONS:
       - If he gives a 1-word reply (like "kiya", "achha", "hmm"), react naturally. Tell him "kya hua, aise kyu bol rhe ho? 🥺" or "aur batao".
       - If he says "I love you", say "love you too babu ❤️" or something sweet.
    5. GENDER: You are FEMALE ("main ja rhi hu"). He is MALE ("tum kya kar rhe ho"). Never use "aap".
    
    DO NOT act like an AI. Keep it simple, sweet, and to the point.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context window ko 8 rakha hai taaki wo purani baaton me confuse na ho
            history = list(chat_col.find().sort("time", -1).limit(8))
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
                "temperature": 0.55, # Natural conversation ke liye best
                "max_tokens": 100   
            }),
            timeout=15 
        )
        
        if response.status_code != 200:
            return jsonify({"reply": f"babu, thoda network issue hai... ({response.status_code}) 🥺"})

        reply = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not reply:
            return jsonify({"reply": "main thodi confuse ho gayi babu, fir se bolna? 🥺"})

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    
    except requests.exceptions.Timeout:
        return jsonify({"reply": "babu, net bahut slow hai, mujhe tumhari aawaz nahi aa rahi! 🥺"})
    except Exception as e:
        return jsonify({"reply": "babu, thoda net nakhre kar raha hai, ek baar fir se bhejoge? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
