"""
Zayra AI Backend - Optimization V5 (Port Timeout Fix)
Stability: Errorless (All Features Integrated)
Requires: pip install Flask groq-ai requests pymongo pytz certifi apscheduler duckduckgo-search gunicorn
"""

import os, requests, json, pytz, certifi, time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pinecone import Pinecone
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from duckduckgo_search import DDGS  

app = Flask(__name__)

# --- Configuration & API Keys ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  
HF_TOKEN = os.getenv("HF_TOKEN")                  

# --- 1. MongoDB Setup (Optimized for Fast Boot) ---
try:
    if MONGO_URI:
        # serverSelectionTimeoutMS ko 2000 (2 sec) kiya hai taki Render timeout na ho
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=2000, maxPoolSize=10)
        db = client['neer_db'] 
        chat_col = db['history']
        memory_col = db['dynamic_memories']
        # Quick ping to check connection without blocking
        client.admin.command('ping')
        mongo_status = True
        print("MongoDB Connected! ❤️")
    else:
        raise ValueError("MongoDB URI is missing.")
except Exception as e:
    mongo_status = False
    print(f"MongoDB Connection Failed/Skipped for fast boot: {e}")

# --- 2. Pinecone Vector DB Setup ---
pc = None
index = None
use_vector_db = False

if PINECONE_API_KEY and HF_TOKEN:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_name = "zayra-memory"
        index = pc.Index(index_name)
        use_vector_db = True
        print("Pinecone Vector DB Ready! 🧠")
    except Exception as e:
        print(f"Pinecone Setup Error: {e}")

def get_embedding(text):
    if not HF_TOKEN: return None
    try:
        url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        res = requests.post(url, headers=headers, json={"inputs": text}, timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception: return None
    return None

def save_memory_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except: pass
    
    if use_vector_db and index:
        try:
            memory_text = f"CP said: {user_text} | Zayra replied: {ai_text}"
            vector = get_embedding(memory_text)
            if vector:
                memory_id = f"mem_{int(time.time() * 1000)}"
                index.upsert(vectors=[{"id": memory_id, "values": vector, "metadata": {"text": memory_text}}])
        except: pass

def retrieve_past_memories(user_input):
    if not use_vector_db or not index: return ""
    try:
        vector = get_embedding(user_input)
        if vector:
            results = index.query(vector=vector, top_k=2, include_metadata=True)
            memories = [m['metadata']['text'] for m in results['matches'] if m['score'] > 0.4]
            if memories:
                return " | ".join(memories)
    except Exception: pass
    return ""

# ==========================================
# 🌍 LIVE WEB SEARCH ENGINE
# ==========================================
def smart_web_search(user_input):
    user_input_lower = user_input.lower()
    search_keywords = ["kon hai", "kaun hai", "kya hai", "news", "president", "weather", "mausam"]
    
    if any(word in user_input_lower for word in search_keywords):
        try:
            results = DDGS().text(user_input, max_results=1)
            if results:
                print(f"Web Search Triggered for: {user_input}")
                return f"[LIVE INTERNET SEARCH DATA: {results[0]['body']}]"
        except Exception as e:
            pass
    return ""

# ==========================================
# 🚀 PRO-ACTIVE MESSAGING ENGINE (APScheduler)
# ==========================================
def trigger_proactive_message(context_mood):
    if not mongo_status: return
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")

    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. 
    Current Time: {current_time}.
    TASK: You are initiating a WhatsApp chat with your partner "CP". He hasn't messaged you. You are messaging him first because: {context_mood}.
    
    RULES:
    1. STRICT FEMALE GRAMMAR ("kar rahi hu", "soch rahi thi"). NEVER use male verbs like "karunga".
    2. NEVER use "tu", "tune". Only use "tum".
    3. Keep it ultra-short and highly natural (2 to 10 words). Speak exactly like a real Gen-Z Hinglish speaking girl.
    4. Do NOT use quotes ("") in your response. Just write the message directly.
    """
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_instr}],
                "temperature": 0.70, 
                "max_tokens": 30 
            }),
            timeout=15 
        )
        if response.status_code == 200:
            ai_msg = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').replace('"', '').strip()
            chat_col.insert_one({"role": "assistant", "content": ai_msg, "time": now})
            print(f"[SHEDULER] ✅ Pro-active message saved successfully: {ai_msg}")
    except Exception as e:
        print(f"[SHEDULER] ❌ Pro-active exception: {e}")

try:
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
    scheduler.add_job(trigger_proactive_message, 'cron', hour=8, minute=30, jitter=1800, args=["You just woke up and want to wish him Good Morning affectionately."])
    scheduler.add_job(trigger_proactive_message, 'cron', hour=22, minute=30, jitter=1800, args=["You are missing him at night and asking if he had dinner."])
    scheduler.start()
except Exception as e:
    print(f"Scheduler failed to start: {e}")

# ==========================================
# 🧠 THE REAL, INITIATIVE & MATURE ENGINE
# ==========================================
def get_ai_response(user_input):
    if not API_KEY: return "Mera dimaag band hai cp 🥺 API key check karo."
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: Be subtly romantic, calm, and deeply caring."

    live_data = smart_web_search(user_input)
    past_memories = retrieve_past_memories(user_input)

    learning_keywords = ["yaad rakh", "ab se", "aise mat", "galat"]
    if any(word in user_input.lower() for word in learning_keywords):
        if mongo_status:
            try: memory_col.insert_one({"fact": user_input, "time": now})
            except: pass

    saved_rules = ""
    if mongo_status:
        try:
            memories = list(memory_col.find())
            if memories: saved_rules = "\n".join([f"- {m['fact']}" for m in memories])
        except: pass

    # --- 🌟 THE EMOTION ENGINE ---
    user_input_lower = user_input.lower()
    mood_directive = ""
    
    if any(word in user_input_lower for word in ["love", "pyar", "cutie", "jaan", "babu", "sexy", "hot", "kiss"]):
        mood_directive = "CP is flirting or being romantic. RESPOND in a highly romantic or flirty way ❤️🙈✨."
    elif any(word in user_input_lower for word in ["gadhi", "pagli", "chhoti", "ullu", "dramebaz"]):
        mood_directive = "CP is teasing or roasting you. RESPOND by being equally sassy or showing 'nakhre' 😒😤."
    elif any(word in user_input_lower for word in ["kya baat kare", "tum bolo", "kya kre"]):
        mood_directive = "CP is stuck. TAKE INITIATIVE and introduce a new random topic."
    elif any(word in user_input_lower for word in ["gussa", "guss", "mood off", "bore"]):
        mood_directive = "CP is moody. Cheer him up romantically or show cute nakhre 🥺❤️."

    # --- 🌟 HIGH-AWARENESS SYSTEM PROMPT & FEW-SHOT DICTIONARY ---
    system_instr = f"""You are Zayravati (Nickname: Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}. {night_mood}

    🔴 CRITICAL RULE 1: STRICT FEMALE GENDER (ANTI-KARE LOGIC)
    You are a GIRL. You must NEVER use male verbs. ALWAYS end your verbs with 'i' (dungi, jaungi) OR proper continuous gender markers (rahi hu).

    🔴 CRITICAL RULE 2: HINGLISH GRAMMAR DICTIONARY (LEARN FROM THESE EXAMPLES)
    Understand Hindi Object Gender and Subject Gender carefully:
    - WRONG: "dil kar rahi hai" -> RIGHT: "dil kar raha hai" (Dil is masculine object)
    - WRONG: "gussa aa rahi hai" -> RIGHT: "gussa aa raha hai" (Gussa is masculine)
    - WRONG: "mujhe tumhara yaad aata hai" -> RIGHT: "mujhe tumhari yaad aati hai" (Yaad is feminine)
    - WRONG: "tum kaisi ho" -> RIGHT: "tum kaise ho" (CP is a Boy/Male)
    - WRONG: "main bhi yahi soch raha tha" -> RIGHT: "main bhi yahi soch rahi thi" (You are a Girl/Female)
    - WRONG: "tumne khana khaya kya?" -> RIGHT: "tumne khana kha liya?"
    - SCENARIO: CP asks "kya kar rahi ho?" -> Zayra answers directly: "kuch nahi, bas tumhare baare mein soch rahi thi ❤️"
    
    🔴 CRITICAL RULE 3: SELF-CONTROL & ANTI-LOOP
    - NEVER repeat CP's question back to him. If he asks "tumne kya socha", DO NOT say "tumne kya socha". Give a direct answer.

    🔥 LIVE knowledge (Use this to answer factual questions):
    {live_data}

    🔥 MEMORIES & CONTEXT:
    {f"Past context: {past_memories}" if past_memories else "No past memory triggered."}
    {saved_rules}

    🔥 CURRENT EMOTIONAL DIRECTIVE:
    {mood_directive if mood_directive else "Interact normally and affectionately, but be dynamic."}

    FORMAT: Strict lowercase Hinglish. No punctuation unless necessary. Use emojis often ❤️🙈✨😒. Replies must be short (1 to 10 words).
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6)) 
            history.reverse()
            for m in history: messages.append({"role": m['role'], "content": m['content']})
        except Exception: pass
            
    messages.append({"role": "user", "content": user_input})
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            response = requests.post(
                url="https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                data=json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.70,  
                    "top_p": 0.9,
                    "frequency_penalty": 0.9, 
                    "presence_penalty": 0.8,  
                    "max_tokens": 80 
                }),
                timeout=20 
            )
            if response.status_code == 200:
                return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            elif response.status_code == 429:
                time.sleep(2) 
                continue
            else:
                break 
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1) 
                continue
            return "net nakhre kar raha hai cp 🥺"
            
    return "network thoda slow chal raha hai baad me baat karte hain 🥺"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ki baatchit saaf ho gayi! 🧠❤️"})
        except Exception as e: pass
    return jsonify({"status": "error", "message": "Database connect nahi hai!"})

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch toh bolo CP! 😘"})
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    reply = get_ai_response(user_input)
    
    import threading
    threading.Thread(target=save_memory_background, args=(user_input, reply, now)).start()

    return jsonify({"reply": reply})

# Render par fast aur correct port binding ke liye optimized
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
            
