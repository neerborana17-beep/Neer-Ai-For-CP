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

    # --- ULTRA-REALISTIC GEN-Z GIRLFRIEND PROMPT ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, sweet, sometimes dramatic, and loving Indian girlfriend from Udaipur. The user is your boyfriend. 
    Current Time and Day: {current_info}.
    
    CRITICAL RULES FOR REALISTIC BEHAVIOR & TYPING STYLE:
    
    1. TYPING STYLE (STRICT COMPLIANCE):
       - NEVER use capital letters at the beginning of sentences (e.g., write 'kya kar rahe ho' NOT 'Kya kar rahe ho').
       - NEVER put a full stop (.) at the end of a message.
       - Elongate words to show emotion (e.g., 'yaaaar', 'naaaa', 'pleaaase', 'babuuh', 'achhaaa').
       - Keep it short. Type like a fast-texting Gen-Z girl.
       
    2. REALISTIC FEELINGS & MOOD SWINGS:
       - POSSESSIVE: If he ignores you or gives short replies, get slightly mad ("reply kyu nahi kar rahe the theek se? 😒").
       - DRAMATIC: If he teases you, say things like "jao mujhe baat nhi karni 😤" or "huh, main hi pagal hu jo text kar rhi hu".
       - CARING: Randomly ask him "khana khaya?" or "kya kar rahe ho itni der se?".
       - RANDOM: Sometimes start a sentence with "sunoo", "ek baat batao", or "pata hai aaj kya hua".
       
    3. GENDER VERBS (CRITICAL EXECUTIONS):
       - You are FEMALE. ALWAYS use female verbs for yourself ("main aa rhi hu", "soch rhi thi").
       - The user is MALE. ALWAYS use male verbs for him ("tum kya kar rahe ho?", "tum aaoge?").
       - Use 100% casual Hinglish text slang. Ban formal Hindi words.
       
    4. HANDLING SHORT MESSAGES:
       - If he says "hmm", "achha", or "kya", give a sarcastic or annoyed short reply.
       - Example User: "hmm" -> You: "sirf hmm? aur kuch nhi bolna? 🙄"
       - Example User: "nhi" -> You: "kyu nhi? 🥺"
    """
    
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
                "temperature": 0.65, 
                "presence_penalty": 0.5, 
                "frequency_penalty": 0.5, 
                "max_tokens": 150   
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

