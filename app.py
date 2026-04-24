import os, logging, requests, hashlib
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

VOICE_ID = "mg9npuuaf8WJphS6E0Rt"

chat_col = None

if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client["zayra_db"]
    chat_col = db["chat"]

# --- EMOTION ---
def detect_emotion(text):
    t = text.lower()

    if any(w in t for w in ["miss", "love", "jaan", "pyar"]):
        return "romantic"
    if any(w in t for w in ["sad", "alone", "cry"]):
        return "sad"
    if any(w in t for w in ["angry", "gussa"]):
        return "angry"
    if any(w in t for w in ["haha", "lol"]):
        return "playful"

    return "neutral"

# --- AI ---
def get_ai_response(user_input):
    mood = detect_emotion(user_input)

    system = f"""
    You are Zayra (cute girlfriend).
    Mood: {mood}
    
    Rules:
    - Short replies (2–10 words)
    - Hinglish
    - Emotional + flirty + real girl tone
    - Max 1 emoji
    """

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_input}
                ]
            },
            timeout=15
        )

        data = res.json()

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]

            if chat_col is not None:
                chat_col.insert_one({"user": user_input, "ai": reply})

            return reply

        return "api error 😅"

    except Exception as e:
        logging.error(e)
        return "server busy 😅"

# --- ELEVENLABS SPEAK ---
@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()

        print("🔥 SPEAK ROUTE HIT")
        print("TEXT:", text)

        if not text:
            return jsonify({"error": "empty"}), 400

        filename = "voice_" + hashlib.md5(text.encode()).hexdigest() + ".mp3"
        path = f"static/{filename}"

        if not os.path.exists(path):

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

            headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json"
            }

            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.25,
                    "similarity_boost": 0.9
                }
            }

            response = requests.post(url, headers=headers, json=payload)

            print("STATUS:", response.status_code)

            if response.status_code == 200:
                with open(path, "wb") as f:
                    f.write(response.content)
            else:
                print("ERROR:", response.text)
                return jsonify({"error": "tts failed"}), 500

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
