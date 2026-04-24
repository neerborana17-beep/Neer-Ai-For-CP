import os, logging, requests, asyncio, hashlib
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import edge_tts

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

chat_col = None

# --- Mongo Fix ---
if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client["zayra_db"]
    chat_col = db["chat"]

# --- Emotion ---
def detect_emotion(text):
    t = text.lower()
    if "miss" in t or "love" in t:
        return "romantic"
    if "sad" in t:
        return "sad"
    if "angry" in t:
        return "angry"
    return "neutral"

# --- AI ---
def get_ai_response(user_input):
    mood = detect_emotion(user_input)

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": f"you are girlfriend, mood {mood}, short reply"},
                    {"role": "user", "content": user_input}
                ]
            },
            timeout=15
        )

        data = res.json()

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]

            # ✅ Mongo safe fix
            if chat_col is not None:
                chat_col.insert_one({"user": user_input, "ai": reply})

            return reply.lower()

        return "api error 😅"

    except Exception as e:
        logging.error(e)
        return "server busy 😅"

# --- EDGE TTS ---
VOICE = "en-US-JennyNeural"

async def generate_voice(text, path):
    tts = edge_tts.Communicate(text=text, voice=VOICE)
    await tts.save(path)

@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "empty"}), 400

        filename = "voice_" + hashlib.md5(text.encode()).hexdigest() + ".mp3"
        path = f"static/{filename}"

        if not os.path.exists(path):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(generate_voice(text, path))
            loop.close()

        return jsonify({"audio": path})

    except Exception as e:
        logging.error(e)
        return jsonify({"error": "tts failed"}), 500

# --- CHAT ---
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    msg = data.get("message", "")

    reply = get_ai_response(msg)

    return jsonify({"reply": reply})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
