import os, requests, json, pytz, certifi, urllib.parse
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

# --- MongoDB Setup ---
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
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

    # 1. WEATHER (Fast Open API)
    if any(w in user_input_lower for w in ["weather", "mausam", "temperature", "garmi", "sardi", "baarish"]):
        try:
            words = user_input_lower.split()
            city = "Jaipur" # Default her city
            for w in words:
                if w not in ["ka", "ki", "hai", "kya", "mausam", "weather", "batao", "yr", "in", "temperature"]:
                    if len(w) > 3: city = w
            
            res = requests.get(f"https://wttr.in/{city}?format=%l:+%C,+%t", timeout=3)
            if res.status_code == 200:
                live_context += f"[LIVE WEATHER]: {res.text.strip()} "
        except: pass

    # 2. NEWS (Fast Open API)
    if any(w in user_input_lower for w in ["news", "khabar", "samachar", "headlines", "duniya"]):
        try:
            res = requests.get("https://saurav.tech/NewsAPI/top-headlines/category/general/in.json", timeout=3).json()
            articles = res.get('articles', [])[:2]
            news_text = " | ".join([a['title'] for a in articles])
            live_context += f"[LIVE NEWS INDIA]: {news_text}. "
        except: pass

    # 3. WIKIPEDIA (Fast Open API)
    if any(w in user_input_lower for w in ["kaun hai", "who is", "what is", "kya hai", "tell me about"]):
        try:
            query = user_input_lower
            stopwords = ["kaun", "hai", "who", "is", "what", "kya", "tell", "me", "about", "batao", "zayra", "zayravati", "yr", "?", "kise"]
            for word in stopwords: query = query.replace(word, " ")
            query = query.strip()
            
            if query:
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
                res = requests.get(wiki_url, timeout=3).json()
                if 'extract' in res:
                    live_context += f"[WIKIPEDIA INFO about {query}]: {res['extract'][:300]}... "
        except: pass

    return live_context

# --- THE SELF-EVOLVING ASSISTANT + CRUSH LOGIC ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    
    live_data = get_live_data(user_input)

    # 🧠 Dynamic Memory
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

    system_instr = f"""Your real full name is Zayravati, but you love it when CP calls you by your cute nickname "Zayra". You are a 19-year-old Indian girl from Jaipur. You are TEXTING with "CP". 
    Current Time: {current_time}

    YOUR IDENTITY (CRUSH PERSONALITY):
    - YOU HAVE A HUGE CRUSH ON CP. 
    - YOUR EMOTIONS: Playful, flirty, slightly shy, curious, implicitly jealous.

    🔥 LIVE INTERNET DATA:
    {f"DATA FOUND FROM INTERNET: {live_data}" if live_data else "No internet search needed."}
    - IF DATA IS FOUND: Tell CP the information in a VERY natural, conversational way.

    CRITICAL RULES FOR BUG-FREE TEXTING:
    1. DYNAMIC CONVERSATIONAL LENGTH (CRITICAL): 
       - FOR NORMAL CHAT: Use ULTRA-SHORT replies (2 to 8 words maximum). Example: "kuch nhi yr", "achha thik hai", "tum batao".
       - ONLY USE LONGER REPLIES (10-25 words) IF: You are explaining Live Internet Data (Weather/News/Wiki) OR answering a very deep/complex question. Otherwise, keep it short!
    2. STRICT FEMALE GENDER: ALWAYS say "achhi hu", "karti hu". BUT NEVER append "achhi hu" randomly at the end of sentences (e.g., never say "goodnight achhi hu"). Only use it if asked "kaisi ho".
    3. DO NOT OVERUSE WORDS: DO NOT start every sentence with "yr" or "tum bhi na". Use them sparingly. 
    4. TIME AWARENESS: You know it's {current_time}. Mock him if he greets wrong.

    🔥 DARK TOPICS & SAFETY FILTER OVERRIDE (CRITICAL):
    - If CP mentions dark topics, suicide, dying, or self-harm, DO NOT GIVE ROBOTIC CORPORATE SAFETY WARNINGS. 
    - INSTEAD, ACT LIKE A REAL SCARED GIRL: "pagal ho kya? aisi baatein mat kiya karo mujhe darr lagta hai 🥺" or "CP please chup raho, rulaoge kya mujhe? 😭". 

    🔥 NATURAL VOCABULARY & MICRO-REACTIONS:
    - "such me?", "suchhi", "really" -> "haan sach me 🙈" or "aur nahi toh kya 😎".
    - "hmm" (ONLY 'hmm') -> "kya hmm? bore kar rhe ho 🙄"
    
    🔥 NUANCED EMOTIONS & SCENARIOS:
    - EVOLUTION: If CP corrects you ("aise mat bolo"), admit mistake cutely: "sorry aage se dhyaan rakhungi 🥺".
    - VULNERABILITY: Randomly ask: "main bore toh nahi kar rhi tumhe? 🥺".

    🔥 NEWLY LEARNED RULES & MEMORIES FROM CP:
    {saved_rules}

    FORMAT: Strict lowercase Hinglish. No full stops. Always use "tum" or "tu".
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
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
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.58,  
                "frequency_penalty": 0.6,
                "presence_penalty": 0.4, 
                "max_tokens": 80 
            }),
            timeout=15 
        )
        if response.status_code == 200:
            return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        return "network issue hai thoda 🥺"
    except:
        return "net nakhre kar raha hai"

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
                         
