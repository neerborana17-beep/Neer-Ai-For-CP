import os, logging, requests, asyncio, hashlib, random
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import edge_tts

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

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

# --- AI RESPONSE ---
def get_ai_response(user_input):
    mood = detect_emotion(user_input)

    system = f"""
    You are Zayra, a cute 19 year old girlfriend.
    Mood: {mood}

    Personality:
    - emotional, caring, slightly possessive
    - short replies (2–10 words)
    - Hinglish
    - real girl texting
    - max 1 emoji

    Always respond like a real girlfriend.
    """

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
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7
            },
            timeout=15
        )

        data = res.json()

        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]

            if chat_col is not None:
                chat_col.insert_one({"user": user_input, "ai": reply})

            return reply

        return "hmm samajh nahi aaya 😅"

    except Exception as e:
        logging.error(e)
        return "network thoda slow h 😅"

# --- ULTRA HUMAN VOICE ---
VOICE = "en-US-AriaNeural"

async def generate_voice(text, path):
    clean = text.strip().replace("\n", " ")

    # 🔥 breathing simulation
    breaths = ["hmm...", "uh...", "", "hmm.."]
    clean = random.choice(breaths) + " " + clean

    # 🔥 pauses
    clean = clean.replace(".", "... ")
    clean = clean.replace("?", "... ")
    clean = clean.replace(",", ", ")

    # 🔥 emotion tuning
    if "love" in clean or "miss" in clean:
        rate = "0.85"
        pitch = "+5%"
    elif "sad" in clean:
        rate = "0.78"
        pitch = "-2%"
    elif "angry" in clean:
        rate = "1.0"
        pitch = "+2%"
    elif "haha" in clean:
        rate = "0.95"
        pitch = "+4%"
    else:
        rate = "0.90"
        pitch = "+3%"

    ssml = f"""
    <speak>
        <voice name="{VOICE}">
            <prosody rate="{rate}" pitch="{pitch}">
                {clean}
                <break time="400ms"/>
            </prosody>
        </voice>
    </speak>
    """

    tts = edge_tts.Communicate(ssml, voice=VOICE)
    await tts.save(path)

# --- SPEAK ---
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
