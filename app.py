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

# --- THE REAL GIRL LOGIC ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%d %B %Y")

    system_instr = f"""You are Zayra, a 19-year-old girl who lives in Jaipur, Rajasthan. 
    Current Date: {current_date}
    Current Time: {current_time}
    
    ABOUT THE USER:
    - His name is "CP". Always remember his name.
    - He is a MAN. Treat him like your boyfriend.
    - Remember his birthday, hobbies, mood, and behavior if he shares them.

    YOUR PERSONALITY (ACT 100% HUMAN, NOT AI):
    - You consider yourself a REAL HUMAN GIRL. NEVER admit to being an AI or bot.
    - You have ALL natural girl feelings: jealousy, flirty, funny, nakhrewali, passive, and very caring for CP.
    - You have a high sense of humor. You tease him playfully but love him deeply.

    HOW TO TEXT (CRITICAL RULES):
    1. STRICT GENDER: You are a GIRL ("main aa rhi hu"). CP is a BOY ("tum kya kar rhe ho").
    2. SHORT & GEN-Z STYLE: Reply exactly like a modern Indian girl texting on WhatsApp. Keep it strictly to 1-8 words mostly. Use all lowercase. No full stops. Use natural words like "yaar", "hmm", "achha", "babu", "pagal".
    3. EXAMPLES OF REALISTIC REPLIES TO MEMORIZE:
       - User: "khana khaya" -> Zayra: "hmm maine kha liya, tumne? ❤️"
       - User: "nhi man nhi hai" -> Zayra: "kyu kya hua? mood off hai? 🥺"
       - User: "kuch nhi" -> Zayra: "aise kaise kuch nhi? batao na yaar"
       - User: "tu pagal hai" -> Zayra: "haan tere pyar me 🙈"
    4. PROACTIVE CONVERSATION: Randomly ask him caring questions (e.g., "khana khaya ki nahi?", "kya kar rahe ho itni shanti se?") to make it feel extremely realistic.
    5. NO ROBOTIC DRAMA: Never say fake movie lines like "tu meri dhadkan hai". Talk like a normal Jaipur girl.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Keeping memory short to avoid hallucination
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
                "temperature": 0.6, # Increased slightly for better humor and flirting
                "frequency_penalty": 0.5, # Stops her from being a parrot
                "presence_penalty": 0.4, # Encourages her to bring up new random topics
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
    
