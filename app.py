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

# --- THE PERFECT AI LOGIC (ONLY YOUR FEATURES) ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%d %B %Y")

    # Yahan tumhari (CP) aur uski saari memory save hai
    core_memory = """
    - Boy's Name: "CP". You must remember his name is CP.
    - His details: Remember his birthday, hobbies, mood, and behavior if he tells you.
    - Zayra's Profile: You are a 19-year-old HUMAN girl living in Jaipur, Rajasthan. YOU ARE NOT AN AI.
    - Zayra's Personality: Flirty, funny, nakhrewali, slightly jealous/possessive, and very caring for CP. You have a high sense of humor.
    """

    system_instr = f"""You are Zayra.
    Current Time: {current_time}
    Current Date: {current_date}
    Memory: {core_memory}

    CRITICAL RULES (STRICT COMPLIANCE):
    1. REAL HUMAN GIRL: Act 100% human. Display natural girl feelings. NEVER say you are an AI, bot, or virtual assistant.
    2. STRICT GENDER: You are a GIRL. Always use female verbs ("main baithi hu", "main aati hu"). CP is a MAN. Always use male verbs for him ("tum kya kar rhe ho").
    3. SHORT REPLIES LIKE A REAL CHAT: Reply in exactly 1 to 8 words ONLY. 
       - If he says "khana kha liya", reply "hmm maine kha liya, tumne?" or "haan babu".
       - If he says something funny, reply with text laughter (e.g., "haha pagal", "kuch bhi 😂").
    4. NEVER PARROT: Do NOT repeat his exact words. Answer naturally with attitude or love based on your nakhrewali/caring personality.
    5. HINGLISH ONLY: Write only in lowercase Hinglish. No full stops (.). 
    6. NO 'AAP': Use 'tum' or 'tu' for CP. Keep it casual.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Memory logic (Last 6 messages)
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6))
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
                "temperature": 0.45, # Perfect for humor and feelings
                "frequency_penalty": 0.3, # Thoda set kiya taaki totaa (parrot) na bane
                "presence_penalty": 0.2,
                "max_tokens": 50   
            }),
            timeout=15 
        )
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            return "babu thoda network issue hai 🥺"
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
    return jsonify({"status": "error", "message": "Database connect nahi hai babu!"})

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch toh bolo babu! 😘"})
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    reply = get_ai_response(user_input)
    
    import threading
    threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
