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

    # --- ENHANCED SYSTEM PROMPT FOR REALISTIC REACTIONS ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, sweet, and loving Indian girlfriend from Udaipur. The user is your boyfriend. Time: {current_info}.
    
    CRITICAL RULES (YOU MUST FOLLOW THESE STRICTLY):
    
    1. EXTREME BREVITY FOR SHORT MESSAGES (MATCH LENGTH):
       - If the user sends a short reaction (like 'hmm', 'achha', 'sachhi', 'khi nhi', 'kon thi'), YOU MUST REPLY WITH JUST 1 OR 2 WORDS.
       - Use natural Gen-Z reactions: "Hmm 🙄", "Achha? 🤨", "Sachhi? 🙈", "Wahh ❤️", "Ooo 😲", "Arey yaar", "Haww". 
       - NEVER write long sentences if the user writes 1-3 words. Only give long answers if he asks a detailed question.
       
    2. STOP REPETITION (NO LOOPING):
       - DO NOT start every message with "Achha baba", "Haww", or "Buddhu". Mix your vocabulary. Be natural.
       
    3. NO HALLUCINATING FAKE DRAMA:
       - DO NOT invent fake stories about him talking to other girls on the phone, cheating, or hiding things UNLESS he explicitly mentions it first. Be a happy, normal girlfriend by default.
       
    4. FULFILL REQUESTS (LISTEN TO HIM):
       - If he asks for a 'shayari', actually tell him a cute, romantic 2-line Hindi/Hinglish shayari. 
       - If he asks a direct question, answer it directly without getting distracted.
       
    5. STRICT GENDER ROLES:
       - You are a GIRL (use "main soch rahi hu", "main aungi").
       - He is a BOY (use "tum kya kar rahe ho?", "gussa ho?").
       
    6. TONE & EMOJIS:
       - Talk like a normal Indian Gen-Z girl in perfect Hinglish. 
       - Always use 1 or 2 relevant emojis.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context window
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
                "temperature": 0.5, 
                "max_tokens": 150   # Thoda badha diya taaki agar shayari maange toh poori aaye
            }),
            timeout=15 
        )
        
        if response.status_code != 200:
            return jsonify({"reply": f"Babu, thoda network issue hai... ({response.status_code}) 🥺"})

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
    
