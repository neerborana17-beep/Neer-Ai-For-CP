# app.py

import os, json, logging
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import requests

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)

# --- ENV ---
API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- DB ---
chat_col = None
mood_col = None

if MONGO_URI:
    client = MongoClient(MONGO_URI)
    db = client["zayra_db"]
    chat_col = db["chat"]
    mood_col = db["moods"]

# --- EMOTION DETECTION ---
def detect_emotion(text):
    t = text.lower()

    if any(w in t for w in ["miss", "love", "jaan", "baby", "pyar"]):
        return "romantic"
    if any(w in t for w in ["sad", "alone", "cry", "hurt", "dukhi"]):
        return "sad"
    if any(w in t for w in ["angry", "gussa", "irritate"]):
        return "angry"
    if any(w in t for w in ["haha", "lol", "funny", "mazak"]):
        return "playful"

    return "neutral"

# --- SAVE MOOD ---
def save_mood(mood):
    if mood_col:
        mood_col.insert_one({"mood": mood, "time": datetime.now()})

# --- MOOD TREND ---
def get_mood_trend():
    if not mood_col:
        return "neutral"

    moods = list(mood_col.find().sort("time", -1).limit(5))
    arr = [m["mood"] for m in moods]

    if arr.count("sad") >= 3:
        return "sad"
    if arr.count("romantic") >= 3:
        return "romantic"
    if arr.count("angry") >= 2:
        return "angry"
    if arr.count("playful") >= 3:
        return "playful"

    return "neutral"

# --- MEMORY ---
def get_memory():
    if not chat_col:
        return ""

    msgs = list(chat_col.find().sort("time", -1).limit(6))
    msgs.reverse()

    memory = ""
    for m in msgs:
        memory += f"{m['role']}: {m['text']}\n"

    return memory

# --- SAVE CHAT ---
def save_chat(user, ai):
    if chat_col:
        chat_col.insert_many([
            {"role": "user", "text": user, "time": datetime.now()},
            {"role": "assistant", "text": ai, "time": datetime.now()}
        ])

# --- MOOD STYLE ---
def mood_instruction(mood, trend):
    return f"""
    Current mood: {mood}
    Mood trend: {trend}

    Rules:
    - romantic → flirty, possessive
    - sad → caring, soft
    - angry → calm but slightly dominant
    - playful → teasing, funny

    Always act like a real girlfriend texting.
    """

# --- AI RESPONSE ---
def get_ai_response(user_input):
    if not API_KEY:
        return "api key missing"

    mood = detect_emotion(user_input)
    save_mood(mood)
    trend = get_mood_trend()
    memory = get_memory()

    system = f"""
    You are Zayra (19 year old girl, girlfriend).

    Personality:
    - Cute, emotional, slightly possessive
    - Talks in Hinglish
    - Short replies (2–10 words)
    - Max 1 emoji
    - Real human texting style (no robotic lines)

    {mood_instruction(mood, trend)}

    Memory:
    {memory}

    IMPORTANT:
    - Always use female tone
    - Keep it short and natural
    - No long sentences
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
            timeout=8
        )

        reply = res.json()["choices"][0]["message"]["content"].lower()

        save_chat(user_input, reply)

        return reply

    except Exception as e:
        logging.error(e)
        return "thoda network issue h 😅"

# --- ROUTES ---
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message", "")

        if not msg:
            return jsonify({"reply": "kuch to bolo 😅"})

        reply = get_ai_response(msg)

        return jsonify({"reply": reply})

    except Exception as e:
        logging.error(e)
        return jsonify({"reply": "server busy 😅"})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
