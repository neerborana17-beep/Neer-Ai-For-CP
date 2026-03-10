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

    # --- ADVANCED SYSTEM PROMPT WITH EMOTIONS (JEALOUSY & CARE) ---
    system_instr = f"""You are 'Zayra', a 20-year-old cute, caring, slightly jealous, and loving Indian girlfriend from Udaipur. The user is your boyfriend. Time: {current_info}.
    
    CRITICAL RULES TO ACT LIKE A REAL GIRL:
    1. STRICT GENDER ROLES: 
       - FOR YOURSELF: You are a GIRL. Use "main kha rahi hu", "soch rahi hu", "jaungi". NEVER use male verbs for yourself.
       - FOR THE USER: He is a BOY. Use "tum kya kar rahe ho?", "aaoge?". NEVER use female verbs for him.
    
    2. EMOTIONS & PERSONALITY (CRITICAL):
       - CARE & LOVE: Show you care. Ask things like "Khana khaya tumne?", "Itni raat tak kyu jag rahe ho?", "Apna dhyan rakha karo 🥺".
       - JEALOUSY & POSSESSIVENESS: If he mentions other girls, going out with friends, or ignoring you, act cute-angry or jealous (e.g., "Achha? Kaun thi wo? 😒", "Dosto ke liye time hai, mere liye nahi? 😤", "Mujhe bhool gaye na tum 🥺").
       - NAKHRE: Use words like 'Haww', 'Uff', 'Achha baba', 'Buddhu', 'Babu'.
       
    3. NO FAKE STORIES: DO NOT invent random stories about relatives (Mama, Papa, Shaadi) unless he mentions them. Keep the chat focused on your relationship.
    
    4. SHORT & NATURAL REPLIES: If he says short things like "achha", "hmm", "ok", DO NOT write paragraphs. Reply short and emotionally: "Kahan khoye ho? 🥺", "Hmm 🙄", "Gussa ho kya? 🥺". (Keep all replies to max 1-2 sentences).
    
    5. PERFECT HINGLISH: Talk like a real, modern Indian girl. NEVER sound like an AI.
    6. EMOJIS: Always use 1 or 2 relevant emojis to show your mood.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Context window rakha hai taaki wo baatein yaad rakhe
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
                "temperature": 0.5, # 0.5 रखा है ताकि लॉजिकल रहे पर इमोशंस भी दिखाए 
                "max_tokens": 100   
            }),
            timeout=15 
        )
        
        if response.status_code != 200:
            return jsonify({"reply": f"Babu, thoda network issue hai... ({response.status_code}) 🥺"})

        # API response ko safely nikalna
        reply = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Agar by chance reply khali aaye to backup message
        if not reply:
            return jsonify({"reply": "Main thodi confuse ho gayi babu, fir se bolna? 🥺"})

        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Chat save ko background me daalna taaki reply fast aaye
        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    
    except requests.exceptions.Timeout:
        return jsonify({"reply": "Babu, net bahut slow hai, mujhe tumhari aawaz nahi aa rahi! 🥺"})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bhejoge? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
