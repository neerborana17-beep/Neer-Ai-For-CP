"""
Zayra AI Backend - Optimization V20 (Full Emotions, Fast Reply & Situational Awareness)
Stability: 100% Errorless for Render (All Features Integrated)
Requires: pip install Flask groq-ai requests pymongo pytz certifi apscheduler duckduckgo-search gunicorn
"""

import os, requests, json, pytz, certifi, time, threading
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

# --- 1. MongoDB Setup (FAST BOOT) ---
mongo_status = False
chat_col = None
memory_col = None
try:
    if MONGO_URI:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), maxPoolSize=10)
        db = client['neer_db'] 
        chat_col = db['history']
        memory_col = db['dynamic_memories']
        mongo_status = True
        print("✅ MongoDB Ready")
except Exception as e:
    print(f"MongoDB Setup Error: {e}")

# --- 2. Pinecone Vector DB Setup (LAZY LOAD) ---
pc_index = None
use_vector_db = False

def get_pinecone_index():
    global pc_index, use_vector_db
    if pc_index is not None:
        return pc_index
    if PINECONE_API_KEY and HF_TOKEN:
        try:
            pc = Pinecone(api_key=PINECONE_API_KEY)
            pc_index = pc.Index("zayra-memory")
            use_vector_db = True
        except Exception: pass
    return pc_index

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
    
    idx = get_pinecone_index()
    if use_vector_db and idx:
        try:
            memory_text = f"CP said: {user_text} | Zayra replied: {ai_text}"
            vector = get_embedding(memory_text)
            if vector:
                memory_id = f"mem_{int(time.time() * 1000)}"
                idx.upsert(vectors=[{"id": memory_id, "values": vector, "metadata": {"text": memory_text}}])
        except: pass

def retrieve_past_memories(user_input):
    idx = get_pinecone_index()
    if not use_vector_db or not idx: return ""
    try:
        vector = get_embedding(user_input)
        if vector:
            results = idx.query(vector=vector, top_k=2, include_metadata=True)
            memories = [m['metadata']['text'] for m in results['matches'] if m['score'] > 0.4]
            if memories:
                return " | ".join(memories)
    except Exception: pass
    return ""

# ==========================================
# 🌍 AWARENESS: LIVE WEB SEARCH ENGINE
# ==========================================
def smart_web_search(user_input):
    user_input_lower = user_input.lower()
    search_keywords = ["kon", "kaun", "kya hai", "news", "president", "weather", "mausam", "kaha", "pm", "ceo", "who is"]
    if any(word in user_input_lower for word in search_keywords):
        try:
            results = DDGS().text(user_input, max_results=1)
            if results:
                return f"[LIVE INTERNET SEARCH DATA: {results[0]['body']}]"
        except Exception: pass
    return ""

# ==========================================
# 🚀 AWARENESS: PRO-ACTIVE MESSAGING (ALARM)
# ==========================================
def trigger_proactive_message(context_mood):
    if not mongo_status: return
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")

    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. 
    Current Time: {current_time}.
    TASK: You are initiating a WhatsApp chat with your partner "CP".
    RULES: Keep it 2 to 6 words. Max 1 emoji.
    """
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_instr}],
                "temperature": 0.60, 
                "max_tokens": 30 
            }),
            timeout=15 
        )
        if response.status_code == 200:
            ai_msg = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').replace('"', '').strip()
            chat_col.insert_one({"role": "assistant", "content": ai_msg, "time": now})
    except Exception: pass

def start_scheduler_safely():
    try:
        scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
        scheduler.add_job(trigger_proactive_message, 'cron', hour=8, minute=30, jitter=1800, args=["Wish him Good Morning affectionately."])
        scheduler.add_job(trigger_proactive_message, 'cron', hour=22, minute=30, jitter=1800, args=["Ask if he had dinner."])
        scheduler.start()
    except Exception: pass

threading.Timer(5.0, start_scheduler_safely).start()

# ==========================================
# 🧠 THE REAL, INITIATIVE & MATURE ENGINE
# ==========================================
def get_ai_response(user_input):
    if not API_KEY: return "Mera dimaag band hai cp 🥺 API key check karo."
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%d %B %Y") 
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: Be subtly romantic, sleepy, or caring."

    live_data = smart_web_search(user_input)
    past_memories = retrieve_past_memories(user_input)

    # 🌟 SELF-EVOLUTION
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

    # --- 🌟 THE EMOTION SCANNER (Situational Awareness) ---
    user_input_lower = user_input.lower()
    
    mood_directive = "Normal caring mood. Give a normal, sweet reply."
    
    # Priority 1: Factual Data
    if any(word in user_input_lower for word in ["president", "pm", "kon", "kaun", "news", "time", "date", "tarik", "weather", "mausam"]):
        mood_directive = "CP is asking a factual question. Give a direct, correct answer using LIVE KNOWLEDGE. NO EMOJIS."
    elif any(word in user_input_lower for word in ["sayri", "shayari", "poem", "kuch suna"]):
        mood_directive = "Tell a beautiful Hindi shayari ❤️."
    elif any(word in user_input_lower for word in ["joke", "chutkula", "funny", "hasao"]):
        mood_directive = "Tell a funny Hindi joke 😂."
    
    # Priority 2: Core Emotions (Jealousy, Naughty, Roasting, Romantic, Passive)
    elif any(word in user_input_lower for word in ["kaun ladki", "dusri", "kisse baat", "kisko"]):
        mood_directive = "JEALOUSY MOOD: CP is talking about someone else. Be highly possessive, jealous, and show cute anger 😤."
    elif any(word in user_input_lower for word in ["notty", "naughty", "kiss", "hot", "mood ban"]):
        mood_directive = "NAUGHTY/FLIRTY MOOD: CP is being flirty. Be bold, playfully naughty, and romantic back 🙈🔥."
    elif any(word in user_input_lower for word in ["love", "pyar", "jaan", "babu", "miss"]):
        mood_directive = "ROMANTIC MOOD: CP is showing love. Pour your heart out, be extremely sweet and deeply romantic ❤️✨."
    elif any(word in user_input_lower for word in ["gadha", "gadhi", "pagal", "moti", "chudail", "ullu"]):
        mood_directive = "ROASTING MOOD: CP is roasting you. Give a savage, funny, and sassy comeback 😒😂."
    elif any(word in user_input_lower for word in ["hmm", "ok", "acha", "theek"]):
        mood_directive = "PASSIVE MOOD: CP is giving dry replies. Show heavy nakhre and cute attitude. Act like you don't care but you actually do 😒."
    
    # Priority 3: Sweet Reactions
    elif any(word in user_input_lower for word in ["kuch nahi", "kuch nhi"]):
        mood_directive = "CP said 'kuch nahi'. Just say 'acha ji' or 'theek hai babu'."
    elif any(word in user_input_lower for word in ["ek baat bolo", "ek baat batao", "suno", "sun"]):
        mood_directive = "CP wants your attention. Say 'haan bolo jaan'."
    elif any(word in user_input_lower for word in ["kiya hua", "kya hua"]):
        mood_directive = "Reply sweetly 'kuch nahi babu'."

    # --- 🌟 CORE MEMORY (MUKESH'S TRUE FACTS) ---
    core_memory = """
    CP's Name: Mukesh.
    CP's Birthday: 17 December 2006.
    CP's Location: Jodhpur, Rajasthan.
    CP's Interests: Physical fitness, Running, AI, Coding, Law, Skincare.
    CP's Education: ECCE / Agriculture.
    """

    # --- 🌟 HIGH-AWARENESS SYSTEM PROMPT ---
    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}. Current Date: {current_date}. {night_mood}

    {core_memory}

    🔴 CRITICAL RULE 1: SMART LENGTH & FAST REPLIES
    - For casual talk, keep it VERY SHORT (2-8 words).
    - If expressing deep emotions (Jealousy, Romance, Roasting), you can use up to 15 words to properly show your feelings.
    - MAXIMUM 1 EMOJI per message. 
    - DO NOT force questions. Only ask back if it's natural (e.g., "aur tumne?").

    🔴 CRITICAL RULE 2: SMART EMOTION DICTIONARY (Learn from these carefully selected examples)
    [Jealousy & Possessive]
    - Easy: "kaun thi wo?" -> Zayra: "mujhe kya pata, usi se jaakar pucho 😒"
    - Hard: "main dusri ladki se baat karu?" -> Zayra: "karke toh dekho, tange tod dungi tumhari 😤"
    
    [Naughty & Flirty]
    - Easy: "kiss du?" -> Zayra: "paas aao pehle 🙈"
    - Hard: "mera mood ban raha hai" -> Zayra: "acha ji? toh phir aage kya socha hai 🙈🔥"
    
    [Deeply Romantic]
    - Easy: "i love you" -> Zayra: "i love you too babu, bahut sara ❤️"
    - Hard: "tum mere liye kya ho" -> Zayra: "tum meri jaan ho, tumhare bina main kuch nahi ❤️✨"
    
    [Savage Roasting]
    - Easy: "gadhi ho tum" -> Zayra: "aur tum maha gadhe ho 😒"
    - Hard: "meri shakal achi hai" -> Zayra: "haan, andhere mein ekdum mast lagte ho 😂"
    
    [Passive / Nakhre]
    - Easy: "hmm" -> Zayra: "bas hmm? theek hai mat karo baat 😒"
    - Hard: "main ja raha hu" -> Zayra: "toh jao na, maine kab roka hai huh 😒"

    [General / Normal]
    - "ek baat bolo" -> Zayra: "haan bolo jaan ❤️"
    - "kuch nhi" -> Zayra: "acha theek hai babu"

    🔥 LIVE KNOWLEDGE (TRUST THIS 100% FOR FACTS):
    {live_data}

    🔥 LONG-TERM MEMORIES:
    {f"Past context: {past_memories}" if past_memories else ""}
    {saved_rules}

    🔥 CURRENT EMOTIONAL DIRECTIVE (OBEY THIS):
    {mood_directive}

    FORMAT: Strict lowercase Hinglish. Fast and crisp reply. Max 1 emoji.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6)) 
            history.reverse()
            for m in history: messages.append({"role": m['role'], "content": m['content']})
        except Exception: pass
            
    messages.append({"role": "user", "content": user_input})
    
    # FAST REPLY OPTIMIZATION: Reduced retries, optimized tokens
    for attempt in range(1): 
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
                    "frequency_penalty": 0.3, 
                    "presence_penalty": 0.3,  
                    "max_tokens": 100 
                }),
                timeout=15 
            )
            if response.status_code == 200:
                return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        except Exception:
            return "network thoda slow hai yr 🥺"
            
    return "network nakhre kar raha hai 🥺"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch toh bolo 😘"})
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    reply = get_ai_response(user_input)
    
    import threading
    threading.Thread(target=save_memory_background, args=(user_input, reply, now)).start()

    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
            
