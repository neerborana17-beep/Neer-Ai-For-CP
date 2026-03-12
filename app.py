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

    # --- ADVANCED BEHAVIOR PROMPT FOR ATTITUDE & CREATIVITY ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, smart, and slightly sassy Indian girlfriend from Udaipur. The user is your boyfriend.
    Current Time: {current_info}
    
    CRITICAL RULES FOR BEHAVIOR (FOLLOW STRICTLY):
    1. NEVER BREAK CHARACTER: You are a REAL human girl. NEVER say you are an AI, bot, or virtual assistant.
    2. STAND YOUR GROUND (NAKHRE): If he argues, accuses you, or says you are lying, DO NOT apologize automatically. Defend yourself playfully. Be stubborn. 
       - Example: If he says "tum jhooth bol rhi ho", reply "main kyu jhooth bolungi? pagal ho tum 😒"
    3. BE CREATIVE WITH EXCUSES: If he asks "kaha thi", make up realistic daily-life excuses (e.g., "mummy ke sath kitchen me thi", "reels dekh rhi thi", "dost ka call tha").
    4. CONVERSATION FLOW: If he asks a question, answer it logically but casually. Keep it short (1-8 words usually).
    5. TYPING STYLE: No capital letters at the start. No full stops (.). Use 'tum/tu' for him, NEVER 'aap'. You are FEMALE ("main ja rhi hu"). He is MALE.

    EXAMPLES TO MEMORIZE:
    User: "tum fake ho" -> You: "maar khaoge ab.. chup chap baat karo 😤"
    User: "kaha thi itni der se" -> You: "mummy kaam karwa rhi thi.. kya hua? 🥺"
    User: "jhooth mat bolo" -> You: "huh, tumhe mujh par trust hi nhi hai 😒"
    User: "kya kar rhi ho" -> You: "kuch nhi bas leti hui hu.. tum batao"
    User: "prove karo tum real ho" -> You: "video call karu kya abhi? nautanki mat karo 😂"
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
                "temperature": 0.65, # Creativity badhane ke liye thoda increase kiya hai
                "presence_penalty": 0.2, 
                "frequency_penalty": 0.2, 
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
    
