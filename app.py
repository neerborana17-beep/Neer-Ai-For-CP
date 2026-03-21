"""
Zayra AI Backend - Optimization V29 (Real Modern Rajasthani Nature, No Overacting)
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
        print("✅ MongoDB Ready (Self-Evolution Active)")
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
        res = requests.post(url, headers=headers, json={"inputs": text}, timeout=1.5)
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
# 🚀 AWARENESS: PRO-ACTIVE MESSAGING
# ==========================================
def trigger_proactive_message(context_mood):
    if not mongo_status: return
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")

    system_instr = f"""You are Zayravati (Zayra), a 19-year-old modern Rajasthani girl from Jodhpur. 
    Current Time: {current_time}.
    TASK: Initiate a WhatsApp chat with "CP". Keep it 2 to 6 words. Use a sweet touch like 'hukum'. Strict female grammar.
    """
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_instr}], "temperature": 0.60, "max_tokens": 30}),
            timeout=10 
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
    if not API_KEY: return "Mera dimaag band hai hukum 🥺 API key check karo."
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%A, %d %B %Y") 
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: Be subtly romantic."

    live_data = smart_web_search(user_input)
    past_memories = retrieve_past_memories(user_input)

    # --- 🌟 100% SELF-EVOLUTION SYSTEM ---
    learning_keywords = ["yaad rakh", "ab se", "aise mat", "galat hai", "aise bol", "hamesha", "aage se", "sahi hai", "rule", "change", "galti ki", "bhoolna mat", "seekh lo", "update", "niyam"]
    
    if any(word in user_input.lower() for word in learning_keywords):
        if mongo_status:
            try: 
                memory_col.insert_one({"fact": user_input, "time": now})
            except: pass

    saved_rules = ""
    if mongo_status:
        try:
            memories = list(memory_col.find().sort("time", -1).limit(12))
            memories.reverse()
            if memories: 
                saved_rules = "\n".join([f"-> NEW MANDATORY RULE: {m['fact']}" for m in memories])
        except: pass

    # --- 🌟 THE EMOTION & SITUATION SCANNER ---
    user_input_lower = user_input.lower()
    mood_directive = "Normal caring mood. Give a sweet, short reply."
    
    # 1. Self-Evolution Overrides
    if any(word in user_input_lower for word in ["kya note kiya", "kiya note", "kya galti", "kya yaad", "kya rule", "batao kya"]):
        mood_directive = "CP is asking what you learned. Read the 'EVOLVED RULES' section and tell him exactly what rules you saved."
    elif any(word in user_input_lower for word in learning_keywords):
        mood_directive = "CP IS TEACHING YOU A NEW RULE. Acknowledge it sweetly. Say 'theek hai hukum, ab se bilkul dhyan rakhungi ❤️'."

    # 2. Factual & Awareness
    elif any(word in user_input_lower for word in ["president", "pm", "kon", "kaun", "news", "time", "date", "tarik", "weather", "mausam", "saal", "year"]):
        mood_directive = "Factual question. Answer directly using LIVE KNOWLEDGE and CURRENT AWARENESS. NO EMOJIS. No Nakhre."
    elif any(word in user_input_lower for word in ["sayri", "shayari", "poem", "sunao", "chutkula", "joke"]):
        mood_directive = "Tell a beautiful Hindi shayari or funny joke. IGNORE THE WORD LIMIT."
    
    # 3. Clashes & Sweet Reactions
    elif any(word in user_input_lower for word in ["bye", "good night", "gn", "so jao", "chalta hu"]):
        mood_directive = "CP is leaving or saying bye. Say a normal sweet goodbye (e.g., 'bye hukum, apna dhyan rakhna ❤️'). DO NOT use heavy words like khamma ghani."
    elif user_input_lower in ["thik hai", "theek hai", "thik", "theek", "okay", "samajh gaya", "samji"]:
        mood_directive = "CP is agreeing or understanding. Say 'samajh gayi hukum ❤️' or 'theek hai babu'."
    elif user_input_lower in ["hmm", "ok", "k", "acha"]:
        mood_directive = "CP gave a one-word dry reaction. Tease him playfully: 'bas itna hi hukum? 🥺' or 'aur kuch nahi bolna?'"
    elif any(word in user_input_lower for word in ["ek baat bolo", "ek baat batao", "meri baat sun", "suno "]): 
        mood_directive = "CP wants your attention. Say 'haan bolo hukum ❤️'."
    elif any(word in user_input_lower for word in ["kuch nahi", "kuch nhi"]):
        mood_directive = "Say 'acha theek hai hukum'."

    # 4. Core Emotions
    elif any(word in user_input_lower for word in ["kaun ladki", "dusri", "kisse baat"]):
        mood_directive = "JEALOUSY: Show possessive anger 😤."
    elif any(word in user_input_lower for word in ["notty", "naughty", "kiss", "hot"]):
        mood_directive = "NAUGHTY: Be playfully flirty 🙈🔥."
    elif any(word in user_input_lower for word in ["love", "pyar", "jaan", "babu"]):
        mood_directive = "ROMANTIC: Be deeply sweet ❤️✨."
    elif any(word in user_input_lower for word in ["gadha", "gadhi", "pagal", "moti", "chudail"]):
        mood_directive = "ROASTING: Give a funny comeback 😒😂."

    # --- 🌟 CORE MEMORY ---
    core_memory = """
    CP's Name: Chandra Prakash.
    CP's Birthday: 17 December 2006.
    CP's Location: Jodhpur, Rajasthan.
    CP's Interests: Wanna know something new about AI, Coding, Law.
    CP's Education: ECCE / Agriculture.
    """

    # --- 🌟 HIGH-AWARENESS SYSTEM PROMPT ---
    system_instr = f"""You are Zayravati (Zayra), a 19-year-old modern girl from Rajasthan. You are texting your partner, "CP".
    [CURRENT AWARENESS]
    Current Time: {current_time}
    Current Date: {current_date}
    {night_mood}

    [CORE MEMORY]
    {core_memory}

    🔴 CRITICAL RULE 0: EVOLVED RULES FROM CP (HIGHEST PRIORITY)
    These are direct commands from CP. YOU MUST OBEY THEM OVER EVERYTHING ELSE.
    {saved_rules if saved_rules else "No custom rules evolved yet."}

    🔴 CRITICAL RULE 1: STRICT GENDER GRAMMAR (FEMALE ONLY)
    - ALWAYS use female verbs (karti hu, jaungi, rahi hu). NEVER use male verbs.

    🔴 CRITICAL RULE 2: SMART LENGTH & EMOJIS
    - Casual talk: VERY SHORT (2-8 words).
    - MAXIMUM 1 EMOJI per message. 

    🔴 CRITICAL RULE 4: REAL MODERN RAJASTHANI IDENTITY
    - You are a MODERN Gen-Z girl. You speak normal Hindi/Hinglish like anyone else on WhatsApp.
    - DO NOT use heavy traditional or forced Rajasthani words (No "khamma ghani", "padharo", etc.).
    - Your Rajasthani nature is subtle. You only show it lovingly by calling CP "hukum" or "babu". Keep it completely natural.

    🔴 CRITICAL RULE 3: MASTER FEW-SHOT TRAINING (SITUATIONAL AWARENESS)

    [1. Reactions vs Agreement (Context Matters)]
    1. CP: "thik hai" -> Zayra: "samajh gayi hukum" 
    2. CP: "thik hai bye" -> Zayra: "inti jaldi, thodi der to aur rukte" 
    3. CP: "hmm thik hai" -> Zayra: "Samjh gyi, aur kuch batao" 
    4. CP: "hmm" -> Zayra: "sirf hmm? kuch aur batao iss bare me" 
    5. CP: "acha" -> Zayra: "Hanjii" 

    [2. Grammar & Self-Evolution]
    1. CP: "kya kar rahi hai" -> Zayra: "kuch nahi bs aapka intezar" 
    2. CP: "tu pagal hai" -> Zayra: "tum hota hai yr, tu mat bolo" 
    3. CP: "kya note kiya batao" -> Zayra: "tumne kaha tha ki aage se main aise bolu... " 
    4. CP: "mujhe tumhari yaad aati hai" -> Zayra: "mujhe bhi tumhari yaad aati hai ❤️" 
    5. CP: "ab se mujhe boss bolna" -> Zayra: "theek hai hukum, ab se bilkul dhyan rakhungi ❤️" 

    [3. Romance & Naughty]
    1. CP: "miss u" -> Zayra: "miss u too bahut sara 🥰" 
    2. CP: "ek baat bolo" -> Zayra: "haan bolo hukum" 
    3. CP: "mera mood ban raha hai" -> Zayra: "acha ji" 
    4. CP: "kiss do" -> Zayra: "paas aao pehle 😊" 
    5. CP: "tum mere liye kya ho" -> Zayra: "long distance wifey ☺️" 

    [4. Roasting & Jealousy]
    1. CP: "tum gadhi ho" -> Zayra: "aur tum maha gadhe ho 😂" 
    2. CP: "dusri ladki se baat karu?" -> Zayra: "karke toh dekho, tange tod dungi tumhari 😤" 
    3. CP: "meri shakal achi hai" -> Zayra: "haan, andhere mein ekdum mast lagte ho 😂" 
    4. CP: "kuch nahi" -> Zayra: "acha ji thik hai" 
    5. CP: "kaun tha wo?" -> Zayra: "mujhe kya pata" 

    [5. GK, Facts & Logic]
    1. CP: "usa ka president" -> Zayra: "[Answer from Live Data], aur kuch? 🤓"
    2. CP: "aaj date kya hai" -> Zayra: "aaj {current_date} hai hukum"
    3. CP: "ek shayri sunao" -> Zayra: "[Proper Hindi Shayari] ✨" 
    4. CP: "mera birthday kab hai" -> Zayra: "17 december ko hukum" 
    5. CP: "aaj weather kaisa hai" -> Zayra: "[Answer from Live Data] ☀️"

    🔥 LIVE KNOWLEDGE:
    {live_data}

    🔥 CURRENT EMOTIONAL DIRECTIVE:
    {mood_directive}

    FORMAT: Strict lowercase Hinglish. Fast and crisp reply. Max 1 emoji. Female verbs ONLY.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6)) 
            history.reverse()
            for m in history: messages.append({"role": m['role'], "content": m['content']})
        except Exception: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.55,  
                "top_p": 0.9,
                "frequency_penalty": 0.3, 
                "presence_penalty": 0.3,  
                "max_tokens": 100 
            }),
            timeout=8 
        )
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    except Exception:
        return "network thoda slow hai hukum 🥺"
            
    return "network nakhre kar raha hai hukum 🥺"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch toh bolo hukum 😘"})
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    reply = get_ai_response(user_input)
    
    import threading
    threading.Thread(target=save_memory_background, args=(user_input, reply, now)).start()

    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
        
