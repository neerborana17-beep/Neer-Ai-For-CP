# app.py

import os, requests, json, pytz, certifi, time, threading, random, logging
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pinecone import Pinecone
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from duckduckgo_search import DDGS  

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ZayraAI")

app = Flask(__name__)

API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# --- Mongo ---
mongo_status = False
chat_col = None
memory_col = None

try:
    if MONGO_URI:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
        db = client['neer_db']
        chat_col = db['history']
        memory_col = db['dynamic_memories']
        mongo_status = True
        logger.info("Mongo connected")
except Exception as e:
    logger.error(f"Mongo error: {e}")

# --- Pinecone ---
pc_index = None
use_vector_db = False

def get_pinecone_index():
    global pc_index, use_vector_db
    if pc_index:
        return pc_index
    try:
        if PINECONE_API_KEY and HF_TOKEN:
            pc = Pinecone(api_key=PINECONE_API_KEY)
            pc_index = pc.Index("zayra-memory")
            use_vector_db = True
    except Exception as e:
        logger.error(f"Pinecone error: {e}")
    return pc_index

# --- Safe HTTP ---
def safe_post(url, headers, payload, timeout=8, retries=2):
    for _ in range(retries):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            logger.warning(f"Retrying API: {e}")
    return None

# --- Embedding ---
def get_embedding(text):
    if not HF_TOKEN:
        return None
    try:
        res = requests.post(
            "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": text},
            timeout=2
        )
        if res.status_code == 200:
            data = res.json()
            return data[0] if isinstance(data, list) else data
    except Exception as e:
        logger.error(f"Embedding error: {e}")
    return None

# --- Memory Save ---
def save_memory_background(user_text, ai_text, timestamp):
    try:
        if mongo_status:
            chat_col.insert_many([
                {"role": "user", "content": user_text, "time": timestamp},
                {"role": "assistant", "content": ai_text, "time": timestamp}
            ])
    except Exception as e:
        logger.error(f"Mongo save error: {e}")

    try:
        idx = get_pinecone_index()
        if idx:
            vector = get_embedding(user_text + ai_text)
            if vector:
                idx.upsert([{
                    "id": f"mem_{int(time.time()*1000)}",
                    "values": vector,
                    "metadata": {"text": user_text}
                }])
    except Exception as e:
        logger.error(f"Pinecone save error: {e}")

# --- Web Search ---
def smart_web_search(user_input):
    keywords = ["news", "weather", "president", "ceo", "kya", "kaun"]
    if any(k in user_input.lower() for k in keywords):
        try:
            res = list(DDGS().text(user_input, max_results=1))
            if res:
                return res[0]["body"]
        except Exception as e:
            logger.error(f"Search error: {e}")
    return ""

# --- AI Response ---
def get_ai_response(user_input):
    if not API_KEY:
        return "api key missing"

    if not user_input.strip():
        return "kuch to bolo"

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)

    live = smart_web_search(user_input)

    system = f"""
    You are Zayra, a 19-year-old girl from Rajasthan.
    Speak ONLY in female tone.
    Keep replies short (2-10 words).
    Romantic, caring, possessive.
    Live data: {live}
    """

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_input}
    ]

    res = safe_post(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.6
        }
    )

    try:
        return res["choices"][0]["message"]["content"].lower()
    except Exception:
        return "thoda glitch aa gaya 😅"

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")

        reply = get_ai_response(user_input)

        threading.Thread(
            target=save_memory_background,
            args=(user_input, reply, datetime.now())
        ).start()

        return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"reply": "server busy h thoda 😅"})

# --- Run ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
