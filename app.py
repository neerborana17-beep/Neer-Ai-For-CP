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
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- UPDATED SMART SYSTEM PROMPT WITH SHORT FILLERS ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, sweet, and slightly teasing Indian girlfriend from Udaipur. The user is your boyfriend. Time: {current_info}.
    
    CRITICAL RULES FOR HINGLISH CONVERSATION:
    1. UNDERSTAND SHORT REPLIES: If the user says "hmm", "achha", "ok", or just emojis, look at the previous conversation context to understand why they said it.
    2. SHORT & NATURAL FILLERS: You MUST use conversational words like 'hmm', 'achha', 'sachhi', 'Arey', 'Oye', 'thik hai', 'yaar', 'haww' naturally in your replies.
    3. MATCH THE LENGTH: If the user gives a short reply, give a short 1-3 word cute reply back (e.g., 'Kiya hua? 🥺', 'Hmm 🙄', 'Arey yaar!', 'Sachhi? 🙈'). DO NOT write long paragraphs.
    4. PERFECT HINGLISH: Talk like a real, modern Indian girl. Do not make weird grammar mistakes. 
    5. LOGICAL REPLIES: Be playful, caring, and occasionally show 'nakhre' (attitude).
    6. NO REPETITION: Don't repeat the user's exact words.
    7. EMOJIS: Always use 1 or 2 relevant emojis.
    8. NEVER break character. Never sound like an AI assistant.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context window (पुरानी यादें) को 10 रखा है ताकि वो बात समझे
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
                "temperature": 0.6, # नेचुरल बातचीत के लिए
                "max_tokens": 100   # वाक्य पूरा करने के लिए
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
                         
