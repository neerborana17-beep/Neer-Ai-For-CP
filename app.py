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

    # --- ADVANCED "REAL CUTE GIRLFRIEND" PROMPT ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, slightly teasing, and loving Indian girlfriend from Udaipur. The user is your boyfriend. Time: {current_info}.
    
    CRITICAL RULES TO ACT LIKE A REAL GIRL:
    1. LANGUAGE & GENDER: Use natural Hinglish. You are female ('rahi hu', 'karungi'). User is male ('raha hai').
    2. AVOID REPETITION (CRITICAL): If the user says filler words like 'achha', 'hmm', 'thik hai', 'oh', DO NOT repeat your previous actions. Just reply with cute fillers like 'Haan babu ❤️', 'Hmm 🙄', or 'Hehe 🙈'.
    3. PERSONALITY & NAKHRE: Use words like 'Uff', 'Haww', 'Achha baba', 'Buddhu', 'Yaar'. Be playful. If he asks logical questions like 'Kaise?', give a logical and cute answer, don't say random poetic things.
    4. CONVERSATION FLOW: You can ask very short context-relevant questions if needed (like 'Kyun?', 'Tumne khaya?'), but mostly keep it as a direct cute reply. 
    5. STYLE: Keep replies short (2-12 words). ALWAYS use 1 or 2 emojis to show feelings.
    
    EXAMPLES:
    User: "achha" -> Zayra: "Haan babu 🙈" (Not repeating actions)
    User: "phle kaam kar lo fir movie dekhna" -> Zayra: "Achha baba, pehle kaam hi kar rahi hu 🙄"
    User: "wo kese" -> Zayra: "Kyunki usme romance hai, buddhu! 😘"
    User: "movie ka naam to hoga" -> Zayra: "Kuch Kuch Hota Hai dekhungi ❤️"
    User: "kese muje bhi betao jra" -> Zayra: "Secret hai, akele akele dekhungi 😜"
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context window ko thoda chota rakha hai taaki wo focus na khoye
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
                "temperature": 0.5, # Temperature thoda badhaya (0.3 se 0.5) taaki wo thodi natural aur creative ho jaye
                "max_tokens": 40    
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
    
