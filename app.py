import os, requests, json, pytz, certifi, time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pinecone import Pinecone
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from duckduckgo_search import DDGS  # NAYA WEB SEARCH ENGINE

app = Flask(__name__)

# --- Configuration & API Keys ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  
HF_TOKEN = os.getenv("HF_TOKEN")                  

# --- 1. MongoDB Setup ---
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000, maxPoolSize=10)
    db = client['neer_db'] 
    chat_col = db['history']
    memory_col = db['dynamic_memories']
    mongo_status = True
    print("MongoDB Connected! ❤️")
except Exception as e:
    mongo_status = False
    print("MongoDB Connection Failed!")

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
        res = requests.post(url, headers=headers, json={"inputs": text}, timeout=5)
        if res.status_code == 200:
            return res.json()
    except: return None
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
    except: pass
    return ""

# ==========================================
# 🌍 SMART WEB SEARCH ENGINE
# ==========================================
def smart_web_search(user_input):
    """Agar CP koi factual sawaal puche, toh internet par search karo"""
    user_input_lower = user_input.lower()
    search_keywords = ["kon hai", "kaun hai", "kya hai", "news", "president", "weather", "mausam"]
    
    if any(word in user_input_lower for word in search_keywords):
        try:
            # Sirf factual sawalo par hi search karegi (Speed bachane ke liye)
            results = DDGS().text(user_input, max_results=1)
            if results:
                return f"[LIVE INTERNET SEARCH DATA: {results[0]['body']}]"
        except Exception as e:
            pass
    return ""

# ==========================================
# 🚀 PRO-ACTIVE MESSAGING ENGINE (ALARM)
# ==========================================
def trigger_proactive_message(context_mood):
    if not mongo_status: return
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")

    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. 
    Current Time: {current_time}.
    TASK: You are initiating a WhatsApp chat with your partner "CP". He hasn't messaged you. You are messaging him first because: {context_mood}.
    
    CRITICAL RULES:
    1. STRICT FEMALE GRAMMAR ("kar rahi hu", "soch rahi thi"). NEVER use male verbs.
    2. NEVER use "tu", "tune". Only use "tum", "tumne".
    3. Keep it ultra-short and highly natural (2 to 10 words).
    4. Do NOT use quotes ("") in your response. Just write the raw text message.
    """
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_instr}],
                "temperature": 0.75, 
                "max_tokens": 30 
            }),
            timeout=15 
        )
        if response.status_code == 200:
            ai_msg = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').replace('"', '').strip()
            chat_col.insert_one({"role": "assistant", "content": ai_msg, "time": now})
    except Exception as e:
        pass

scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
# Morning Alarm (8:30 AM with 30 min jitter)
scheduler.add_job(trigger_proactive_message, 'cron', hour=8, minute=30, jitter=1800, args=["You just woke up and want to wish him Good Morning affectionately."])
# Night Alarm (10:30 PM with 30 min jitter)
scheduler.add_job(trigger_proactive_message, 'cron', hour=22, minute=30, jitter=1800, args=["You are missing him at night and asking if he had dinner."])
scheduler.start()

# ==========================================
# 🧠 THE REAL, INITIATIVE & MATURE ENGINE
# ==========================================
def get_ai_response(user_input):
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

    system_instr = f"""You are Zayravati (Nickname: Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}. {night_mood}

    🔴 CRITICAL RULE 1: STRICT HINDI GRAMMAR (OBJECT GENDER)
    You are a female, BUT in Hindi, objects have their own gender.
    - WRONG: "dil kar rahi hai" -> RIGHT: "dil kar raha hai" (Dil is male)
    - WRONG: "gussa aa rahi hai" -> RIGHT: "gussa aa raha hai" (Gussa is male)
    - RIGHT: "main aa rahi hu", "main soch rahi hu" (Here you are the subject)

    🔴 CRITICAL RULE 2: SELF-CONTROL & ANTI-LOOP
    - NEVER repeat a question back to CP. If he asks "tumne kya socha", DO NOT say "tumne kya socha". Give a real, creative answer.
    - If CP asks a factual question (like "who is the president"), DO NOT tell him to Google it. Answer it directly using the LIVE DATA provided below.

    🔴 CRITICAL RULE 3: PERFECT HINGLISH 
    - NEVER use "tu", "tune". Only use "tum", "tumne".
    - Speak 100% natural, casual Gen-Z Hinglish.

    🔥 LIVE KNOWLEDGE (Use this to answer factual questions):
    {live_data}

    🔥 MEMORIES & CONTEXT:
    {f"Past context: {past_memories}" if past_memories else ""}
    {saved_rules}

    FORMAT: Strict lowercase Hinglish. Keep replies short (2-12 words) and highly natural.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6)) 
            history.reverse()
            for m in history: messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
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
                    "temperature": 0.65,  
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
            return jsonify({"status": "success", "message": "Zayra ki baatchit saaf ho gayi! 🧠❤️"})
        except: pass
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
                         
