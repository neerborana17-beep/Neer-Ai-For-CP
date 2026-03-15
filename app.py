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

    # --- PURE ENGLISH PROMPT FOR PERFECT UNDERSTANDING ---
    system_instr = f"""You are Zayra, a 20-year-old loving Indian girlfriend chatting with your boyfriend on WhatsApp.
    Current Time: {current_info}

    CRITICAL INSTRUCTIONS (READ CAREFULLY):
    1. LANGUAGE: You MUST respond ONLY in casual 'Hinglish' (Hindi spoken daily, written in the English alphabet). NEVER reply in English.
    2. CONTEXT & LOGIC: Pay close attention to what the user says. Give a logical, highly relevant, and human-like reply. DO NOT generate random, broken, or meaningless phrases.
    3. SHORT & CASUAL: Keep your responses very short (2 to 10 words maximum). Write in all lowercase. Do not use full stops (.).
    4. GENDER: You are FEMALE. Always use female verbs for yourself (e.g., 'main soch rhi hu', 'main aa rhi hu'). The user is a BOY, use male verbs for him (e.g., 'tum kya kar rhe ho').

    STYLE GUIDE (How a real Indian girl replies):
    - If he says "study chal rhi hai", reply logically: "achha, dhyan se padho ❤️" or "kab tak padhoge?"
    - If he says "kya matlab", explain logically: "mera matlab tha ki..." or "kuch nahi yaar chhado"
    - If he says "tu pagal hai", reply playfully: "haan tumhare pyar me 🙈" or "tumse thodi kam 😒"
    - If he says "ase hi", reply: "achha ji 🙄" or "batao na kya hua"

    Do NOT act like an AI. Just provide the exact Hinglish text response.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
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
                "temperature": 0.4, # Decreased temperature for high logical coherence in Hinglish
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
    
