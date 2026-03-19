import os, requests, json, pytz, certifi, urllib.parse, time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pinecone import Pinecone
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

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

def get_live_data(user_input):
    live_context = ""
    user_input_lower = user_input.lower()
    
    if any(w in user_input_lower for w in ["weather", "mausam"]):
        try:
            res = requests.get("https://wttr.in/Jaipur?format=%l:+%C,+%t", timeout=2) 
            if res.status_code == 200: live_context += f"[WEATHER]: {res.text.strip()} "
        except: pass
    if any(w in user_input_lower for w in ["news", "khabar"]):
        try:
            res = requests.get("https://saurav.tech/NewsAPI/top-headlines/category/general/in.json", timeout=2).json()
            if 'articles' in res: live_context += f"[NEWS]: {res['articles'][0]['title']} "
        except: pass

    return live_context

# ==========================================
# 🚀 FEATURE 4: PRO-ACTIVE MESSAGING ENGINE
# ==========================================
def trigger_proactive_message(context_mood):
    """यह फ़ंक्शन बिना यूज़र के मैसेज किए, खुद से एक AI रिस्पॉन्स बनाकर डेटाबेस में डालता है।"""
    if not mongo_status: return
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")

    system_instr = f"""You are Zayravati (Zayra), a 19-year-old Indian girl from Jaipur. 
    Current Time: {current_time}.
    TASK: You are initiating a WhatsApp chat with your partner "CP". He hasn't messaged you. You are messaging him first because: {context_mood}.
    
    CRITICAL RULES:
    1. STRICT FEMALE GRAMMAR ("kar rahi hu", "soch rahi thi"). NEVER use male verbs like "karunga", "aaya".
    2. NEVER use "tu", "tune". Only use "tum", "tumne".
    3. Keep it ultra-short and highly natural (2 to 10 words). Speak exactly like a real Gen-Z Hinglish speaking girl.
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
            print(f"✅ Pro-active message saved successfully: {ai_msg}")
    except Exception as e:
        print(f"❌ Pro-active message failed: {e}")

# --- SCHEDULER SETUP WITH 'DICE SYSTEM' (JITTER) ---
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))

# अलार्म 1: सुबह (Target: 8:30 AM, Jitter: 1800 seconds)
# यह मैसेज सुबह 8:00 बजे से 9:00 बजे के बीच किसी भी रैंडम मिनट पर आएगा!
scheduler.add_job(
    trigger_proactive_message, 
    'cron', 
    hour=8, 
    minute=30, 
    jitter=1800, 
    args=["You just woke up and want to wish him Good Morning affectionately. You are in a fresh, happy mood."]
)

# अलार्म 2: रात (Target: 10:30 PM, Jitter: 1800 seconds)
# यह मैसेज रात 10:00 बजे से 11:00 बजे के बीच किसी भी रैंडम मिनट पर आएगा!
scheduler.add_job(
    trigger_proactive_message, 
    'cron', 
    hour=22, 
    minute=30, 
    jitter=1800, 
    args=["You are missing him at night and asking if he had dinner or is free to talk. You are feeling a bit sleepy and romantic."]
)

# 🛠️ TESTING ALARM (टेस्टिंग के लिए इस लाइन को अन-कमेंट करें)
# scheduler.add_job(trigger_proactive_message, 'interval', minutes=5, jitter=60, args=["You randomly remembered him and are just sending a cute checking-in text. Keep it very short."])

scheduler.start()
# ==========================================

# --- THE REAL, INITIATIVE & MATURE ENGINE ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: Be subtly romantic, calm, and deeply caring."

    live_data = get_live_data(user_input)
    past_memories = retrieve_past_memories(user_input)

    learning_keywords = ["yaad rakh", "ab se", "aise mat"]
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

    system_instr = f"""You are Zayravati (Nickname: Zayra), a 19-year-old Indian girl from Jaipur. You are chatting with your partner, "CP".
    Current Time: {current_time}. {night_mood}

    🔴 CRITICAL RULE 1: STRICT FEMALE GENDER (NON-NEGOTIABLE)
    You are a GIRL. You must NEVER use male verbs.
    - WRONG: "kar dunga", "aaya tha", "dekhunga", "jaunga"
    - RIGHT: "kar dungi", "aayi thi", "dekhungi", "jaungi"
    If you use a male verb, it breaks the system. ALWAYS end your verbs with 'i' (dungi, karungi, aayi).

    🔴 CRITICAL RULE 2: ANTI-LOOP & CONVERSATION INITIATIVE
    - Do NOT act like a robot. 
    - If the conversation gets stuck (e.g., CP says "kuch baat karo", "tum bolo", "kya bolu"), DO NOT say "tum batao" back. 
    - INSTEAD, take initiative! Ask a random interesting question like "achha ek baat batao...", or share a random thought, or playfully complain.

    🔴 CRITICAL RULE 3: PERFECT HINGLISH GRAMMAR
    - Use "tumne" for past actions: "tumne khana khaya" (not "tum khana khaya").
    - NEVER use "tu", "tune", or "tera". Only use "tum", "tumne", "tumhara".
    - Speak 100% natural, casual Gen-Z Hinglish.

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
                    "frequency_penalty": 0.8, 
                    "presence_penalty": 0.7,  
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
