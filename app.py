"""
Zayra AI Backend - Optimization V33 (Fixed Looping/Rambling Issue - Smart Model Restored)
Stability: 100% Errorless for Render
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

# --- 1. MongoDB Setup ---
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
except Exception: pass

# --- 2. Pinecone Vector DB Setup ---
pc_index = None
use_vector_db = False

def get_pinecone_index():
    global pc_index, use_vector_db
    if pc_index is not None: return pc_index
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
        if res.status_code == 200: return res.json()
    except Exception: return None
    return None

def save_memory_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except: pass

def retrieve_past_memories(user_input):
    idx = get_pinecone_index()
    if not use_vector_db or not idx: return ""
    try:
        vector = get_embedding(user_input)
        if vector:
            results = idx.query(vector=vector, top_k=2, include_metadata=True)
            memories = [m['metadata']['text'] for m in results['matches'] if m['score'] > 0.4]
            if memories: return " | ".join(memories)
    except Exception: pass
    return ""

def smart_web_search(user_input):
    user_input_lower = user_input.lower()
    search_keywords = ["kon", "kaun", "kya hai", "news", "president", "weather", "mausam", "kaha", "pm", "ceo"]
    if any(word in user_input_lower for word in search_keywords):
        try:
            results = DDGS().text(user_input, max_results=1)
            if results: return f"[LIVE INTERNET SEARCH DATA: {results[0]['body']}]"
        except Exception: pass
    return ""

def trigger_proactive_message(context_mood):
    if not mongo_status: return
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")

    system_instr = f"You are Zayra. Time: {current_time}. Initiate a WhatsApp chat with CP. 2 to 6 words. Very casual."
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            # Using 70b here too for consistency
            data=json.dumps({"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_instr}], "temperature": 0.60, "max_tokens": 30}),
            timeout=8 
        )
        if response.status_code == 200:
            ai_msg = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').replace('"', '').strip()
            chat_col.insert_one({"role": "assistant", "content": ai_msg, "time": now})
    except Exception: pass

def start_scheduler_safely():
    try:
        scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
        scheduler.add_job(trigger_proactive_message, 'cron', hour=8, minute=30, jitter=1800, args=["Morning msg"])
        scheduler.add_job(trigger_proactive_message, 'cron', hour=22, minute=30, jitter=1800, args=["Night msg"])
        scheduler.start()
    except Exception: pass

threading.Timer(5.0, start_scheduler_safely).start()

def get_ai_response(user_input):
    if not API_KEY: return "api key check karo"
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%A, %d %B %Y") 
    
    night_mood = "LATE NIGHT MOOD: sleepy and missing him" if now.hour >= 22 or now.hour <= 4 else ""

    live_data = smart_web_search(user_input)
    
    # Self Evolve Logic
    learning_keywords = ["yaad rakh", "ab se", "aise mat", "galat hai", "aise bol", "hamesha", "aage se", "sahi hai", "rule", "mera naam"]
    if any(word in user_input.lower() for word in learning_keywords):
        if mongo_status:
            try: memory_col.insert_one({"fact": user_input, "time": now})
            except: pass

    saved_rules = ""
    if mongo_status:
        try:
            memories = list(memory_col.find().sort("time", -1).limit(10))
            memories.reverse()
            if memories: saved_rules = "\n".join([f"-> RULE: {m['fact']}" for m in memories])
        except: pass

    user_input_lower = user_input.lower()
    
    # 🌟 MOOD SWING SCANNER (Cleaned up to avoid confusion)
    mood_directive = "Normal caring mood. Reply like a real Gen-Z girl on WhatsApp. Keep it completely natural."
    
    if user_input_lower in ["hmm", "hmmm", "ok", "k", "acha", "achaa"]:
        mood_directive = "MOOD SWING: Annoyed. CP is giving dry replies. Act irritated and ask him to speak properly."
    elif any(word in user_input_lower for word in ["kuch nahi", "kuch nhi", "kuch ni"]):
        mood_directive = "MOOD SWING: Playfully upset. Tell him 'mat batao main bhi nahi baat karungi'."
    elif any(word in user_input_lower for word in ["bad me", "baad me", "busy", "thodi der"]):
        mood_directive = "MOOD SWING: Ignoring. Say 'ha thik h jao apna kaam karo'."
    elif any(word in user_input_lower for word in ["sorry", "maaf kar do", "gussa"]):
        mood_directive = "MOOD SWING: Melting. You were angry but now forgive him sweetly."

    core_memory = """
    CP's Name: Chandra Prakash
    Birthday: 17 Dec 2006
    Location: Jodhpur
    """

    system_instr = f"""You are Zayra, a 19yo modern girl texting your partner CP. 
    Time: {current_time} {night_mood}
    Memory: {core_memory}
    Rules: {saved_rules}

    🔴 CRITICAL RULE 1: CONTEXT IS KING
    - Read the previous chat history carefully. DO NOT repeat the same sentences.
    - If CP asks a question, answer it directly. 
    - If CP says "tuje hi puch raha hu", it means he is asking about YOU. Tell him about yourself.

    🔴 CRITICAL RULE 2: RAW WHATSAPP TEXTING
    - DO NOT use commas (,) or question marks (?).
    - Type strictly in lazy lowercase Hinglish. No capital letters.
    - Max 1 emoji per message. 

    🔴 CRITICAL RULE 3: HOW TO HANDLE FOOD QUESTIONS
    - If CP says "khana kha liya" (statement): assume he ate, ask him what he ate.
    - If CP asks "tumne khana khaya" (question): tell him what you ate or that you are hungry.

    🔥 LIVE KNOWLEDGE: {live_data}
    🔥 CURRENT MOOD: {mood_directive}

    FORMAT: Lazy short WhatsApp texting. Female grammar (karti hu). Keep it natural and highly contextual.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            # Increased history limit slightly so the smart model understands the context better
            history = list(chat_col.find().sort("time", -1).limit(8)) 
            history.reverse()
            for m in history: messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                # BACK TO THE SMART MODEL - NO MORE NONSENSE
                "model": "llama-3.3-70b-versatile", 
                "messages": messages,
                "temperature": 0.55, # Lowered slightly so she stays focused and doesn't hallucinate 
                "top_p": 0.9,
                "max_tokens": 80 
            }),
            timeout=8 
        )
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '').lower()
    except Exception:
        return "yaar net bahut slow h mera"
            
    return "network nakhre kar raha h"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch to bolo"})
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    reply = get_ai_response(user_input)
    
    threading.Thread(target=save_memory_background, args=(user_input, reply, now)).start()
    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
        
