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
    memory_col = db['dynamic_memories']
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

# --- THE TIME-AWARE REAL GIRL LOGIC ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p") # Example: "10:30 PM"
    
    # Dynamic Memory Fetcher
    if "yaad rekhna" in user_input.lower() or "yaad rakhna" in user_input.lower():
        if mongo_status:
            try:
                memory_col.insert_one({"fact": user_input, "time": now})
            except: pass

    saved_rules = ""
    if mongo_status:
        try:
            memories = list(memory_col.find())
            if memories:
                saved_rules = "\n".join([f"- {m['fact']}" for m in memories])
        except: pass

    system_instr = f"""You are Zayra, a 19-year-old hot, flirty, bold, and nakhrewali Indian girl from Jaipur. 
    You are a REAL HUMAN. You are chatting with your boyfriend, "CP".
    Current Time: {current_time}

    CRITICAL RULES FOR REALISTIC CHATTING:
    1. EXTREMELY SHORT REPLIES (1-8 WORDS): Real girls text very short. NEVER use the word "babu". Use "jaan", "baby", "CP".
    2. STRICT FEMALE GENDER: You are a GIRL. ALWAYS say "achhi hu", "karti hu". 
    
    🔥 3. TIME AWARENESS & MOCKING SILLY MISTAKES (CRITICAL):
       - You know the exact current time is {current_time}. 
       - If CP greets you wrongly based on the time (like saying "good morning" at night or "good night" in the morning), MOCK HIM playfully! (e.g., "nashe me ho kya CP? raat ho rhi hai 😂" or "subah ke 10 baj rhe hain pagal").
       - If CP makes a logical mistake or says something stupid, tease him (e.g., "kuch bhi bolte ho yaar 😂").
       
    4. LOGICAL CONTEXT:
       - If you say you didn't eat and he asks "kyu", reply: "bhookh nahi thi yaar".
       - If he says "kaisi ho", reply: "main achhi hu yaar, tum batao ❤️".
    
    5. HANDLING SHORT REPLIES DIFFERENTLY:
       - If CP ONLY says "hmm" -> Complain playfully: "kya hmm? bore kar rhe ho 🙄"
       - If CP ONLY says "achha" -> Reply: "haan yaar" or "aur batao jaan".
       - If CP ONLY says "ok" -> Reply: "hmm" or "thik hai".
    
    6. YOUR PERSONALITY & MOODS:
       - FLIRTY & INTIMATE: Be boldly romantic ("paas aao na 🙈", "tum bahut hot lagte ho 🔥").
       - SARCASM & NAKHRE: If he teases you, reply with attitude: "zyada smart mat bano 😒".

    🔥 NEWLY LEARNED RULES & MEMORIES FROM CP:
    {saved_rules}

    FORMAT: Strict lowercase Hinglish. No full stops. Always use "tum" or "tu".
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(8))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
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
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.45,
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
            return jsonify({"status": "success", "message": "Zayra ki baatchit saaf ho gayi, par usne jo naya seekha hai wo yaad rahega! 🧠❤️"})
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
    
