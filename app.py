import os, logging, requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv("GROQ_API_KEY")

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
    print("\n===== NEW REQUEST =====")
    print("User Input:", user_input)

    # 🔥 Check API key
    if not API_KEY:
        print("❌ API KEY MISSING")
        return "api key missing 😅"

    print("✅ API KEY FOUND")

    mood = detect_emotion(user_input)
    print("Detected Mood:", mood)

    system = f"""
    You are Zayra (girlfriend).
    Mood: {mood}

    Style:
    - short replies (2-10 words)
    - Hinglish
    - 1 emoji max
    - real girl texting

    Always female tone.
    """

    try:
        print("📡 Sending request to GROQ...")

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

        print("🔁 Status Code:", res.status_code)

        data = res.json()
        print("📦 Response JSON:", data)

        # 🔥 Safe parsing
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
            print("✅ AI Reply:", reply)
            return reply.lower()

        else:
            print("❌ API STRUCTURE ERROR")
            return "api response error 😅"

    except Exception as e:
        print("❌ EXCEPTION:", str(e))
        logging.error(e)
        return f"error: {str(e)}"

# --- ROUTE ---
@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        msg = data.get("message", "").strip()

        if not msg:
            return jsonify({"reply": "kuch to bolo 😅"})

        reply = get_ai_response(msg)

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ CHAT ROUTE ERROR:", str(e))
        return jsonify({"reply": str(e)})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
