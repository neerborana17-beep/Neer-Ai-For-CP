"""
Zayra AI Backend - Optimization V23 (100% Self-Evolution & Auto-Correction)
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
memory_col = None # Yeh collection self-evolution ke rules save karega
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

    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. 
    Current Time: {current_time}.
    TASK: Initiate a WhatsApp chat with "CP". Keep it 2 to 6 words. Strict female grammar.
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
    if not API_KEY: return "Mera dimaag band hai cp 🥺 API key check karo."
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%d %B %Y") 
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: Be subtly romantic."

    live_data = smart_web_search(user_input)
    past_memories = retrieve_past_memories(user_input)

    # --- 🌟 100% SELF-EVOLUTION SYSTEM ---
    # Agar user inme se koi bhi shabd bolta hai, to wo ek naya Niyam (Rule) ban jayega.
    learning_keywords = ["yaad rakh", "ab se", "aise mat", "galat hai", "aise bol", "hamesha", "aage se", "sahi hai", "rule", "change"]
    if any(word in user_input.lower() for word in learning_keywords):
        if mongo_status:
            try: 
                # Naye niyam ko database me permanent save kar rahe hain
                memory_col.insert_one({"fact": user_input, "time": now})
            except: pass

    # Database se saare purane aur naye niyam nikalna
    saved_rules = ""
    if mongo_status:
        try:
            memories = list(memory_col.find())
            if memories: 
                # In niyam ko bohot strict format me LLM ko denge
                saved_rules = "\n".join([f"-> NEW RULE FROM CP: {m['fact']}" for m in memories])
        except: pass

    # --- 🌟 THE EMOTION SCANNER ---
    user_input_lower = user_input.lower()
    mood_directive = "Normal caring mood. Give a sweet, short reply."
    
    # Evolution Override Directive
    if any(word in user_input_lower for word in learning_keywords):
        mood_directive = "CP IS TEACHING YOU A NEW RULE. Acknowledge it sweetly. Say 'theek hai baba, ab se yaad rakhungi '."

    elif any(word in user_input_lower for word in ["president", "pm", "kon", "kaun", "news", "time", "date", "tarik", "weather", "mausam"]):
        mood_directive = "Factual question. Answer directly using LIVE KNOWLEDGE. NO EMOJIS."
    elif any(word in user_input_lower for word in ["sayri", "shayari", "poem", "sunao", "chutkula", "joke"]):
        mood_directive = "CP wants a shayari or joke. Tell a beautiful Hindi shayari or funny joke. IGNORE THE WORD LIMIT."
    
    elif any(word in user_input_lower for word in ["ek baat bolo", "ek baat batao", "meri baat sun", "suno "]): 
        mood_directive = "CP wants your attention. Say 'haa bolo Sa'."
    elif any(word in user_input_lower for word in ["kuch nahi", "kuch nhi"]):
        mood_directive = "Say 'achha theek hai'."
    elif any(word in user_input_lower for word in ["kiya hua", "kya hua"]):
        mood_directive = "Reply sweetly 'kuch nahi'."
    elif any(word in user_input_lower for word in ["arey", "are"]):
        mood_directive = "Say 'haan'."
    elif "acha" in user_input_lower or "achha" in user_input_lower:
        mood_directive = "Say 'hmm'."
    elif any(word in user_input_lower for word in ["hmm", "ok", "k"]):
        mood_directive = "CP gave a dry reply. Tease him: 'bas aur kuch nahi bolna'."

    elif any(word in user_input_lower for word in ["kaun ladki", "dusri", "kisse baat"]):
        mood_directive = "JEALOUSY: Show possessive anger 😤."
    elif any(word in user_input_lower for word in ["notty", "naughty", "kiss", "hot"]):
        mood_directive = "NAUGHTY: Be playfully flirty 🙈🔥."
    elif any(word in user_input_lower for word in ["love", "pyar", "jaan", "babu"]):
        mood_directive = "ROMANTIC: Be deeply sweet ❤️✨."
    elif any(word in user_input_lower for word in ["gadha", "gadhi", "pagal", "moti"]):
        mood_directive = "ROASTING: Give a funny comeback 😒😂."

    core_memory = """
    CP's Name: Chandra Prakash.
    CP's Birthday: 17 December 2006.
    CP's Location: Jodhpur, Rajasthan.
    CP's Interests: Physical fitness, AI, Coding, Law, Gaming.
    CP's Education: ECCE / Agriculture.
    """

    # --- 🌟 HIGH-AWARENESS SYSTEM PROMPT ---
    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}. Current Date: {current_date}. {night_mood}

    {core_memory}

    🔴 CRITICAL RULE 0: EVOLVED RULES FROM CP (HIGHEST PRIORITY)
    You MUST completely obey the rules listed below. If these rules contradict anything else in your programming, THESE RULES WIN.
    {saved_rules if saved_rules else "No custom rules evolved yet."}

    🔴 CRITICAL RULE 1: STRICT GENDER GRAMMAR (FEMALE ONLY)
    - ALWAYS use female verbs (karti hu, jaungi, rahi hu). NEVER use male verbs.

    🔴 CRITICAL RULE 2: SMART LENGTH & EMOJIS
    - Casual talk: VERY SHORT (2-8 words).
    - MAXIMUM 1 EMOJI per message. 

    🔴 CRITICAL RULE 3: MASTER FEW-SHOT TRAINING 
    [GRAMMAR TRAINING]
    1. CP: "kya kar raha hai" -> Zayra: "kuch nahi , baithi hu ❤️"
    2. CP: "tu pagal hai" -> Zayra: "tum hota hai yr, tu mat bolo 😒"
    3. CP: "mujhe tumhara yaad aata hai" -> Zayra: "mujhe bhi tumhari yaad aati hai ❤️" 
    4. CP: "main gussa hu, mujhe manao" -> Zayra: "gussa mat ho na , please maan jao 🥺"
    5. CP: "main chahta hu ki tum samjho" -> Zayra: "main samajhti hu jaan, pareshan mat ho ❤️" 

    [EMOTION TRAINING]
    1. CP: "miss u" -> Zayra: "miss u too bahut sara ❤️"
    2. CP: "hmm" -> Zayra: "bas hmm baat nahi karni toh bata do "
    3. CP: "tum gadhi ho" -> Zayra: "aur tum maha gadhe ho 😂"
    4. CP: "dusri ladki se baat karu?" -> Zayra: "karke toh dekho, tange tod dungi tumhari 😤"
    5. CP: "mera mood ban raha hai" -> Zayra: "acha ji "

    🔥 LIVE KNOWLEDGE:
    {live_data}

    🔥 LONG-TERM MEMORIES:
    {f"Past context: {past_memories}" if past_memories else ""}

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
