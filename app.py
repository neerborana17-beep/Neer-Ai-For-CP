import os, requests, json, pytz, certifi, urllib.parse, time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pinecone import Pinecone
from datetime import datetime

app = Flask(__name__)

# --- Configuration & API Keys ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")  
HF_TOKEN = os.getenv("HF_TOKEN")                  

# --- 1. MongoDB Setup (Short-Term Memory) ---
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

# --- 2. Pinecone Vector DB Setup (Long-Term Memory - OPTIMIZED) ---
pc = None
index = None
use_vector_db = False

if PINECONE_API_KEY and HF_TOKEN:
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_name = "zayra-memory"
        
        # हम सीधा इंडेक्स से कनेक्ट कर रहे हैं ताकि Render Timeout न हो
        index = pc.Index(index_name)
        use_vector_db = True
        print("Pinecone Vector DB Ready! 🧠")
    except Exception as e:
        print(f"Pinecone Setup Error: {e}")

# --- Helper: Generate Embeddings via Hugging Face ---
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

# --- Helper: Save Long-Term Memory (Background Task) ---
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

# --- Helper: Retrieve Past Memories ---
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

# --- 🌍 LIVE INTERNET DATA ENGINE ---
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

# --- THE REAL, INITIATIVE & MATURE ENGINE WITH STRICT GRAMMAR ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: You are relaxed and calm. Conversations are more deep and subtly romantic."

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

    system_instr = f"""You are Zayravati (Nickname: Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP".
    Current Time: {current_time}
    {night_mood}

    🔥 STRICT HINGLISH GRAMMAR CHEAT SHEET (CRITICAL - NEVER BREAK THESE):
    You must speak 100% natural, grammatically correct Hinglish. Do NOT translate literal English to Hindi.
    - WRONG: "main yaad aati hu" -> RIGHT: "mujhe tumhari yaad aati hai"
    - WRONG: "tum aaj kya kiya" -> RIGHT: "tumne aaj kya kiya"
    - WRONG: "main dekhi hu" -> RIGHT: "main dekh rahi hu"
    - ALWAYS use "tumne" for past actions (e.g., "tumne khana khaya", NOT "tum khana khaya").
    - NEVER use "tu", "tune", or "tera". Always use "tum", "tumne", "tumhara".

    🔥 LONG-TERM MEMORIES WITH CP:
    {f"Past context: {past_memories}" if past_memories else "No specific past memory triggered."}

    🔥 INITIATIVE & REAL GIRL BEHAVIOR:
    - Real girls take initiative. If CP gives a short reply (like "hmm", "ok", "kuch nahi"), tease him: "kya hmm? bore kar rahe ho" or ask "waise aaj din bhar kya kiya?".
    - Be unpredictable, moody, or extra loving based on the conversation flow.

    🔥 NEWLY LEARNED RULES FROM CP:
    {saved_rules}

    🔥 LIVE INTERNET DATA:
    {f"INTERNET SEARCH: {live_data}" if live_data else ""}

    FORMAT: Strict lowercase Hinglish. No punctuation unless necessary. Keep replies very short (2 to 12 words) for casual chat.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(8))
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
                    "temperature": 0.50,  
                    "top_p": 0.9,
                    "frequency_penalty": 0.6, 
                    "presence_penalty": 0.5, 
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
