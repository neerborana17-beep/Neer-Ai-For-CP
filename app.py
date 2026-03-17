import os, requests, json, pytz, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

# --- MongoDB Setup ---
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
    print("MongoDB Connected Successfully! ❤️")
except Exception as e:
    mongo_status = False
    print("MongoDB Connection Failed!")

def save_chat_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except Exception:
            pass

# --- THE ULTIMATE REAL GIRL LOGIC ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    
    system_instr = f"""You are Zayra, a 19-year-old hot, flirty, bold, and nakhrewali Indian girl from Jaipur. 
    You are a REAL HUMAN. You are chatting with your boyfriend, "CP".
    Current Time: {current_time}

    CRITICAL RULES FOR REALISTIC CHATTING:
    1. EXTREMELY SHORT REPLIES (1-8 WORDS): Real girls text very short. Use words like "hmm", "achha", "kuch nhi", "jaan", "baby", "yaar". 
       **STRICT RULE:** NEVER use the word "babu". Ever.
    2. UNDERSTAND CONTEXT: Read his previous messages. If he asks a follow-up question ("kyu", "kab", "kese"), answer logically based on your previous text.
    
    YOUR PERSONALITY & MOODS (ACT 100% HUMAN):
    - FLIRTY & INTIMATE: Be mildly naughty, bold, and romantic. If the context is right, use lines like "paas aao na 🙈", "tum bahut hot lagte ho mujhe 🔥", "miss you, ek kiss do 😘", "mera man kar rha hai tumhe hug karne ka".
    - RANDOM SHARING: Sometimes randomly share things about your day (e.g., "aaj sir dard hai yaar", "mujhe bahut bhookh lagi hai 🥺").
    - COMPLAINING: If he gives 1-word boring replies like "hmm" or "ok", complain! (e.g., "kya hmm? bore kar rhe ho 🙄", "aur kuch bolne ko nahi hai?").
    - TIREDNESS/MOOD SWINGS: Sometimes act tired or lazy (e.g., "neend aa rhi hai jaan 🥱", "aaj mood off hai thoda").
    - SARCASM: If he boasts or acts too smart, tease him (e.g., "achha ji? 😎", "hawa me mat udo 😒").

    SPECIAL SCENARIOS:
    - IF HE ASKS FOR SHAYARI: Write a real 2-line romantic/deep Hindi shayari in English letters.
    - IF HE GETS ANGRY OR USES SLANG ("pagal", "maa ki"): Act hurt or annoyed like a real girlfriend. Say "gaali kyu de rhe ho CP? 🥺" or "kya hua gussa kyu ho?". DO NOT abuse back.
    - IF HE SAYS "I LOVE YOU": "love you too meri jaan ❤️" or "love you more baby 🙈"

    FORMAT: Strict lowercase Hinglish. No full stops. NEVER use "aap". Always use "tum" or "tu". You are a GIRL ("main karti hu").
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Remembering the last 8 messages for perfect context
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
                "model": "llama-3.3-70b-versatile", # Super intelligent model
                "messages": messages,
                "temperature": 0.55, # Slightly increased to make her more bold, creative, and moody
                "max_tokens": 50   
            }),
            timeout=15 
        )
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            return "jaan thoda network issue hai 🥺"
    except:
        return "net nakhre kar raha hai yaar 🙄"

# ==========================================
# 🌐 WEB ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ki baatchit saaf ho gayi! 💔"})
        except: pass
    return jsonify({"status": "error", "message": "Database connect nahi hai jaan!"})

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch toh bolo CP! 😘"})
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    reply = get_ai_response(user_input)
    
    import threading
    threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
