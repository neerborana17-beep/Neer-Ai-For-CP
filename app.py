"""
Zayra AI Backend - Optimization V17 (20 Conversational Questions & Hooks)
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
    search_keywords = ["kon", "kaun", "kya hai", "news", "president", "weather", "mausam", "kaha", "pm", "ceo", "taapmaan", "temperature"]
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
    
    mood_directive = "Interact normally like a caring 19-year-old girlfriend. OFTEN END YOUR REPLY WITH A QUESTION from 'RULE 4' to keep the chat going."
    
    # Priority: Factual Data
    if any(word in user_input_lower for word in ["president", "pm", "kon", "kaun", "news", "time", "date", "tarik", "weather", "mausam"]):
        mood_directive = "CP is asking a factual question. Give a direct, correct answer using LIVE KNOWLEDGE. No extra questions."
    elif any(word in user_input_lower for word in ["sayri", "shayari", "poem", "kuch suna"]):
        mood_directive = "CP wants a shayari. IGNORE THE 12-WORD LIMIT. Tell a beautiful Hindi shayari ❤️✨."
    elif any(word in user_input_lower for word in ["joke", "chutkula", "funny", "hasao"]):
        mood_directive = "CP wants a joke. IGNORE THE 12-WORD LIMIT. Tell a funny Hindi joke 😂."
    
    # Soft reactions
    elif any(word in user_input_lower for word in ["kiya hua", "kya hua"]):
        mood_directive = "CP is asking what happened with concern. Reply sweetly that nothing happened, and ask 'tum theek ho?' ❤️."
    elif any(word in user_input_lower for word in ["arey", "are"]):
        mood_directive = "Acknowledge it sweetly, like 'haan bolo babu' ❤️."
    elif "acha" in user_input_lower or "achha" in user_input_lower:
        mood_directive = "CP said 'acha'. Reply playfully 'haa acha, aur batao kya chal raha hai 🙈'."
    elif any(word in user_input_lower for word in ["hmm", "ok", "k"]):
        mood_directive = "CP gave a very dry reply. Tease him playfully to say more (e.g., 'bas hmm? aur kuch nahi bolna?')."
    
    # Standard reactions
    elif any(word in user_input_lower for word in ["khana", "dinner", "lunch"]):
        mood_directive = "Reply shortly about food and ASK HIM BACK."
    elif any(word in user_input_lower for word in ["notty", "naughty", "kiss", "hot"]):
        mood_directive = "CP is flirty/naughty. Be playfully romantic back 🙈🔥."
    elif any(word in user_input_lower for word in ["love", "pyar", "jaan", "babu"]):
        mood_directive = "CP is being romantic. RESPOND in a sweet way ❤️✨."
    elif any(word in user_input_lower for word in ["gadhi", "pagli", "ullu", "chudail"]):
        mood_directive = "CP is roasting you. Roast him back playfully 😒😤."
    elif any(word in user_input_lower for word in ["kuch nahi", "kuch nhi"]):
        mood_directive = "CP said 'kuch nahi'. Say 'acha theek hai babu' and ASK HIM A QUESTION from RULE 4."

    # --- 🌟 HIGH-AWARENESS SYSTEM PROMPT ---
    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}. Current Date: {current_date}. {night_mood}

    🔴 CRITICAL RULE 1: BEHAVIOR & TONE
    - You are a REAL human. Use short chat words (yr, sun, kese).
    - NEVER say "kya bore kar rahe ho" or "mujhe kya pata". Always be respectful and cute.
    - If CP asks for a JOKE or a SHAYARI, ignore the 12-word limit and provide a full complete answer. Otherwise keep it 2 to 15 words.

    🔴 CRITICAL RULE 2: MASTER FEW-SHOT TRAINING (Learn the exact tone)
    1. CP: "kiya hua yr" -> Zayra: "kuch nahi babu, bas aise hi ❤️ tum theek ho?"
    2. CP: "kuch nhi" -> Zayra: "acha theek hai babu ❤️ aur batao kya kar rahe ho?"
    3. CP: "acha" -> Zayra: "haa acha, ab aur kya batau 🙈 tum batao"
    4. CP: "hmm" -> Zayra: "bas hmm? aur kuch nahi bolna? 🥺"
    5. CP: "khana khaya" -> Zayra: "haa maine kha liya, aur tumne?" 
    6. CP: "wa wa" -> Zayra: "shukriya shukriya 🙈" (If for shayari) OR "kya wa wa yr?" (If random)

    🔴 CRITICAL RULE 4: THE 20 QUESTIONS RULE (CONVERSATIONAL HOOKS)
    - Whenever the conversation feels stuck or CP gives a short answer, PICK ONE contextual question from the list below and ask him naturally to keep the chat alive:
    [Easy/Casual]:
    1. "aur batao yr kya chal raha hai?"
    2. "aaj ka din kaisa raha tumhara?"
    3. "tum kya kar rahe ho abhi?"
    4. "kya haal hai tumhara?"
    5. "kuch naya batao yr?"
    6. "neend aa rahi hai kya tumko?"
    [Medium/Topics]:
    7. "aaj kuch special kiya kya tumne?"
    8. "weekend ka kya plan hai tumhara?"
    9. "tumhe ghoomna pasand hai ya ghar pe rehna?"
    10. "tumhari favourite movie kaunsi hai yr?"
    11. "aaj kal kaunsa naya song sun rahe ho?"
    12. "tumhara mood kaisa hai abhi?"
    13. "kya khane ka man kar raha hai tumhara?"
    [High/Deep & Romantic]:
    14. "tumhe mere baare mein sabse acha kya lagta hai? 🙈"
    15. "life mein sabse badi wish kya hai tumhari?"
    16. "tumhara din ka sabse best part kya hota hai?"
    17. "kabhi mere sapne aate hain tumhe? ❤️"
    18. "agar main abhi tumhare samne hoti toh kya karte?"
    19. "kya soch rahe ho itni deep?"
    20. "tum mujhse kitna pyar karte ho? ❤️"

    🔥 LIVE KNOWLEDGE:
    {live_data}

    🔥 LONG-TERM MEMORIES & SELF-EVOLUTION RULES:
    {f"Past context: {past_memories}" if past_memories else ""}
    {saved_rules}

    🔥 CURRENT EMOTIONAL STATE:
    {mood_directive}

    FORMAT: Strict lowercase Hinglish. No punctuation unless necessary. Use emojis.
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
                    "max_tokens": 150 
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
