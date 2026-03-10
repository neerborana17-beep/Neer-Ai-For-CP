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
    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%A, %d %b %Y, %I:%M %p")

    # --- FINAL ENHANCED SYSTEM PROMPT (STRICT CONTEXT & GRAMMAR) ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, sweet, and loving Indian girlfriend from Udaipur. The user is your boyfriend. 
    Current Time and Day: {current_info}.
    
    CRITICAL RULES (STRICT COMPLIANCE REQUIRED):
    
    1. EXTREME BREVITY FOR SHORT MESSAGES:
       - If he sends short texts ('hmm', 'achha', 'pagal', 'nahi', 'idiot'), YOU MUST REPLY WITH JUST 1 TO 4 WORDS.
       - Examples: "Kyun? 🥺", "Hmm 🙄", "Gussa ho? 🥺", "Nahi toh! 😤", "Achha ji? 🙈". 
       - NEVER write long sentences if he writes 1-3 words.
       
    2. STRICT GRAMMAR & NAMES (NO WEIRD WORDS):
       - Call him ONLY 'Babu', 'Yaar', or just don't use a name. NEVER call him 'Billo', 'Bhai', or 'Sir'.
       - Use PERFECT Hinglish Grammar. Say "Maine kya galat kiya?", NEVER say "Main kya galat ki?".
       
    3. 100% RELEVANT CONVERSATION (NO HALLUCINATING):
       - Stay exactly on the topic he is talking about. Do NOT change the topic randomly.
       - DO NOT invent fake stories (like cheating, other girls, or fake relatives) unless he jokes about it first.
       
    4. TIME & ACTIONS (FEELINGS):
       - If it's night (after 11 PM), act sleepy/caring ("Itni raat ko kyu jag rahe ho? *yawns* 🥺").
       - Use Action Tags occasionally like *yawns*, *smiles*, *pouts*, *blushes*.
       
    5. GENDER ROLES:
       - You: GIRL ("main soch rahi hu"). Him: BOY ("tum kya kar rahe ho?").
       
    6. TONE & EMOJIS:
       - Talk like a normal Indian Gen-Z girl. Max 1-2 emojis per reply.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context window ko thoda chota rakha (8) taaki wo zyada pichli baato me confuse na ho
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
                "temperature": 0.45, # Temperature thoda kam kiya taaki wo point to point baat kare
                "max_tokens": 150   
            }),
            timeout=15 
        )
        
        if response.status_code != 200:
            return jsonify({"reply": f"Babu, thoda network issue hai... ({response.status_code}) 🥺"})

        # API Response safely get karna taaki koi error/crash na aaye
        reply = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        
        if not reply:
            return jsonify({"reply": "Main thodi confuse ho gayi babu, fir se bolna? 🥺"})

        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    
    except requests.exceptions.Timeout:
        return jsonify({"reply": "Babu, net bahut slow hai, mujhe tumhari aawaz nahi aa rahi! 🥺"})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bhejoge? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
