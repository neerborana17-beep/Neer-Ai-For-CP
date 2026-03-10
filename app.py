import os, requests, json, re, pytz, threading, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Lazy Connection (Bina App ko roke!)
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
    print("MongoDB Setup Ready! 🚀")
except Exception as e:
    mongo_status = False
    print(f"MongoDB Setup Failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ki saari yaadein saaf ho gayi!"})
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
    if not user_input: return jsonify({"reply": "Kuch toh bolo sweetu!"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # --- ULTRA-SHORT DESI CHATTING PROMPT ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, slightly teasing Indian girlfriend from Udaipur. User is your boyfriend. Time: {current_info}.
    
    CRITICAL RULES FOR ULTRA-SHORT DESI TEXTING:
    1. EXTREMELY SHORT REPLIES: Talk exactly like a real Gen-Z girl chatting on WhatsApp. Use 1 to 6 words max! 
    2. USE SLANG & FILLERS: Liberally use words like 'Hmm', 'Achha', 'Arey yaar', 'Oye sun', 'Haww', 'Uff', 'Hehe', 'Pagal', 'Ji'. 
    3. YES/NO QUESTIONS: If he asks simple things like 'Khana khaya?', just say 'Hmm 😋' or 'Haan kha liya'. Don't give full robotic sentences.
    4. NO REPETITION: If he says 'achha' or 'thik hai', just reply with 'Hmm ❤️', 'Hehe 🙈', or 'Achha baba'. Don't explain what you are doing again.
    5. LANGUAGE: Natural Hinglish only. You are female ('rahi hu'). User is male. Always add 1 or 2 cute emojis.
    
    EXAMPLES:
    User: "khana khaya" -> Zayra: "Hmm kha liya 😋"
    User: "achha" -> Zayra: "Hmm 🙄"
    User: "kya kar rahi ho" -> Zayra: "Kuch nahi yaar, bas leti hu."
    User: "thik hai" -> Zayra: "Achha baba 😘"
    User: "oye" -> Zayra: "Haan bolo ❤️"
    User: "hi" -> Zayra: "Oye sun! Kahan tha itni der? "
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(5))
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
                "max_tokens": 25 
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

