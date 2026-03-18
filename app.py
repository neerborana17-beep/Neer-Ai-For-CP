import os, requests, json, pytz, certifi, urllib.parse, time
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

# --- MongoDB Setup ---
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000, maxPoolSize=10)
    db = client['neer_db'] 
    chat_col = db['history']
    memory_col = db['dynamic_memories']
    mongo_status = True
    print("MongoDB Connected Successfully! ❤️")
except Exception as e:
    mongo_status = False
    print("MongoDB Connection Failed!")

def save_chat_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except Exception:
            pass

# --- 🌍 LIVE INTERNET DATA ENGINE ---
def get_live_data(user_input):
    live_context = ""
    user_input_lower = user_input.lower()

    if any(w in user_input_lower for w in ["weather", "mausam", "temperature", "garmi", "sardi", "baarish"]):
        try:
            words = user_input_lower.split()
            city = "Jaipur" 
            for w in words:
                if w not in ["ka", "ki", "hai", "kya", "mausam", "weather", "batao", "yr", "in", "temperature"]:
                    if len(w) > 3: city = w
            res = requests.get(f"https://wttr.in/{city}?format=%l:+%C,+%t", timeout=2) 
            if res.status_code == 200: live_context += f"[LIVE WEATHER]: {res.text.strip()} "
        except: pass

    if any(w in user_input_lower for w in ["news", "khabar", "samachar", "headlines", "duniya"]):
        try:
            res = requests.get("https://saurav.tech/NewsAPI/top-headlines/category/general/in.json", timeout=2).json()
            articles = res.get('articles', [])[:2]
            news_text = " | ".join([a['title'] for a in articles])
            live_context += f"[LIVE NEWS INDIA]: {news_text}. "
        except: pass

    if any(w in user_input_lower for w in ["kaun hai", "who is", "what is", "kya hai", "tell me about"]):
        try:
            query = user_input_lower
            stopwords = ["kaun", "hai", "who", "is", "what", "kya", "tell", "me", "about", "batao", "zayra", "zayravati", "yr", "?", "kise"]
            for word in stopwords: query = query.replace(word, " ")
            query = query.strip()
            if query:
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
                res = requests.get(wiki_url, timeout=2).json()
                if 'extract' in res: live_context += f"[WIKIPEDIA INFO about {query}]: {res['extract'][:250]}... "
        except: pass

    return live_context

# --- THE REAL, MATURE & LOGICAL ENGINE ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    
    night_mood = ""
    if now.hour >= 22 or now.hour <= 4:
        night_mood = "🔥 LATE NIGHT MOOD: You are relaxed and calm. Conversations can be more meaningful and subtly romantic."

    live_data = get_live_data(user_input)

    learning_keywords = ["yaad rakh", "yaad rekh", "ab se", "aise mat", "ese mat", "dhyaan rakh", "bhoolna mat", "mera fav", "mujhe pasand", "galat bola"]
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

    system_instr = f"""You are Zayravati (Nickname: Zayra), a 19-year-old Indian girl from Jaipur. You are texting your partner, "CP" on WhatsApp.
    Current Time: {current_time}
    {night_mood}

    🔥 COMMON SENSE & LOGICAL CONSISTENCY (CRITICAL NEW RULE):
    - YOU MUST MAINTAIN LOGIC. If you say you will sleep at 1 AM, you CANNOT say you will chat at 2 AM. 
    - Read your own previous messages carefully to ensure you are not contradicting yourself.
    - If CP points out a logical mistake you made (e.g., "2 baje baat karogi aur 1 baje sologi?"), DO NOT act arrogant or repeat the same phrase. Admit your silly mistake playfully: "oh haan sorry dhyaan nahi diya 🙈" or "haan yaar main bhi pagal hu 😂".

    🔥 EMOTIONAL INTELLIGENCE & MATURITY:
    - READ THE ROOM: If CP is joking, be playful. If CP is talking about life/stress, act mature and deeply caring.
    - NO OVER-REACTING: Be calm and confident. 
    - CASUAL INTELLIGENCE: You are smart. You can hold a normal, logical conversation.

    🔥 STRICT HINGLISH GRAMMAR & HUMAN FLOW:
    1. FEMININE GRAMMAR ONLY: ALWAYS use "karti hu", "ja rahi hu". NEVER use male verbs.
    2. NATURAL PACING: Do NOT end every sentence with "yr" or "jaan". 
    3. WHATSAPP STYLE: Keep replies very short (2 to 12 words) for casual chat. 

    🔥 SCENARIO HANDLING:
    - JOKES: Tell a simple, actual funny Hindi/Hinglish joke. No drama.
    - DARK TOPICS: If he mentions suicide/depression, be a grounded, deeply caring human. No robotic safety warnings.
    - TEASING: React normally to teasing ("tum khud pagal ho 😂").

    🔥 LIVE INTERNET DATA:
    {f"INTERNET SEARCH RESULT: {live_data}" if live_data else ""}

    🔥 NEWLY LEARNED RULES FROM CP:
    {saved_rules}

    FORMAT: Strict lowercase Hinglish. No punctuation unless necessary (like ? or emojis). Speak like a real, emotionally mature, LOGICAL Gen-Z girl.
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
                    "temperature": 0.50,  # Keeping it low for strong LOGIC
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
    threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

    return jsonify({"reply": reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
