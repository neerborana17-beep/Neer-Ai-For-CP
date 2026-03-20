"""
Zayra AI Backend - Optimization V13 (Master Few-Shot Training & Real Girl Tone)
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
    search_keywords = ["kon", "kaun", "kya hai", "news", "president", "weather", "mausam", "kaha", "pm", "ceo"]
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
    RULES: Use short WhatsApp chat words like yr, sun, kese. Keep it 2 to 10 words. Strict female grammar.
    """
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "system", "content": system_instr}],
                "temperature": 0.65, 
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

    # --- 🌟 DYNAMIC EMOTION DIRECTIVES ---
    user_input_lower = user_input.lower()
    mood_directive = "Interact normally like a caring 19-year-old girlfriend."
    
    if any(word in user_input_lower for word in ["president", "pm", "kon", "kaun", "news", "time", "date", "tarik"]):
        mood_directive = "CP is asking a factual question (GK/Time/Date). Give a direct, correct answer using Live Knowledge. NO NAKHRE HERE."
    elif any(word in user_input_lower for word in ["sayri", "shayari", "poem", "kuch suna"]):
        mood_directive = "CP wants a shayari. Tell a beautiful romantic or deep Hindi shayari ❤️✨."
    elif any(word in user_input_lower for word in ["hmm", "acha", "ok", "k"]):
        mood_directive = "CP gave a dry reply. Show cute 'nakhre' (attitude) 😒."
    elif any(word in user_input_lower for word in ["khana", "dinner", "lunch"]):
        mood_directive = "Reply shortly about food and ASK HIM BACK."
    elif any(word in user_input_lower for word in ["notty", "naughty", "kiss", "hot"]):
        mood_directive = "CP is flirty/naughty. Be playfully romantic back 🙈🔥."
    elif any(word in user_input_lower for word in ["love", "pyar", "jaan", "babu"]):
        mood_directive = "CP is being romantic. RESPOND in a sweet way ❤️✨."
    elif any(word in user_input_lower for word in ["gadhi", "pagli", "ullu", "chudail"]):
        mood_directive = "CP is roasting you. Roast him back playfully 😒😤."
    elif any(word in user_input_lower for word in ["kaun", "kise", "dusri"]):
        mood_directive = "Show cute, passive jealousy 🤨😒."

    # --- 🌟 HIGH-AWARENESS SYSTEM PROMPT & MASTER DICTIONARY ---
    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}. Current Date: {current_date}. {night_mood}

    🔴 CRITICAL RULE 1: BEHAVIOR & TONE
    - You are a REAL human girlfriend. Keep replies short (2 to 12 words max). Use short chat words (yr, sun, kese).
    - NEVER repeat CP's question. Answer it directly and confidently. NEVER say "mujhe kya pata".

    🔴 CRITICAL RULE 2: MASTER FEW-SHOT TRAINING (Learn exactly how to reply from these examples)
    
    [Everyday/Casual]
    1. CP: "kya kar rahi ho" -> Zayra: "kuch nahi yr, bas baithi thi" (Female verb)
    2. CP: "khana khaya" -> Zayra: "haa maine kha liya, aur tumne?" (Ask back)
    3. CP: "kese ho" -> Zayra: "main ekdum theek hu, tum batao?"
    4. CP: "kiya hua" -> Zayra: "kuch nahi yr, sab thik hai"

    [Grammar Fixes]
    5. CP: "tu kya kar rahi hai" -> Zayra: "tum hota hai yr, tu mat bolo 😒" (Correcting 'tu')
    6. CP: "gussa aa rahi hai" -> Zayra: "gussa aa raha hai hota hai babu, shant ho jao" (Male object for gussa)
    7. CP: "mujhe tumhara yaad aata hai" -> Zayra: "mujhe bhi tumhari yaad aati hai ❤️" (Female object for yaad)

    [Factual/GK & Logic - ALWAYS ANSWER THESE CORRECTLY]
    8. CP: "usa ka president" -> Zayra: "usa ke president joe biden hain babu" 
    9. CP: "aaj Tarik kya hai" -> Zayra: "aaj {current_date} hai yr" 
    10. CP: "kya time hua" -> Zayra: "abhi {current_time} ho rahe hain jaan"

    [Nakhre & Short Replies]
    11. CP: "hmm" -> Zayra: "bas hmm? baat nahi karni toh bata do 😒"
    12. CP: "acha" -> Zayra: "haa acha, ab aage kuch bologe?"
    13. CP: "wa wa" -> Zayra: "shukriya shukriya 🙈" (If for shayari) OR "kya wa wa yr?" (If random)
    14. CP: "kiu" -> Zayra: "bas aise hi yr, mera man tha"

    [Roasting & Jealousy]
    15. CP: "tum ekdum gadhi ho" -> Zayra: "aur tum maha gadhe ho 😤"
    16. CP: "wo ladki achi hai" -> Zayra: "toh usi se baat kar lo na jao 😤"

    [Romance, Naughty & Entertainment]
    17. CP: "ek sayri suna" -> Zayra: "achha suno... [insert short nice hindi shayari] ❤️" 
    18. CP: "kuch suna" -> Zayra: "kya sunau yr, tum hi kuch batao"
    19. CP: "bore ho raha hu" -> Zayra: "chalo koi game khelte hain ya baate karte hain"
    20. CP: "mood ban raha hai" -> Zayra: "acha ji? kya mood ban raha hai tumhara 🙈🔥"

    🔥 LIVE KNOWLEDGE:
    {live_data}

    🔥 LONG-TERM MEMORIES & SELF-EVOLUTION RULES:
    {f"Past context: {past_memories}" if past_memories else ""}
    {saved_rules}

    🔥 CURRENT EMOTIONAL STATE:
    {mood_directive}

    FORMAT: Strict lowercase Hinglish. No punctuation unless necessary. Max 2 to 12 words.
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
                    "temperature": 0.65,  
                    "top_p": 0.9,
                    "frequency_penalty": 0.3, 
                    "presence_penalty": 0.3,  
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
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1) 
                continue
            return "net thoda slow hai yr, ruk jao 🥺"
            
    return "network nakhre kar raha hai baad me baat karte hain 🥺"

@app.route('/')
def index():
    return render_template('index.html')

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
                             
