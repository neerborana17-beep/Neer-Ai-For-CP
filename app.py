import os, requests, asyncio, hashlib
from flask import Flask, request, jsonify, render_template
import edge_tts

app = Flask(__name__, static_folder="static")

API_KEY = os.getenv("GROQ_API_KEY")

# --- AI ---
def get_ai_response(user_input):
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
                    {"role": "system", "content": "you are cute emotional girlfriend, short hinglish replies"},
                    {"role": "user", "content": user_input}
                ]
            },
            timeout=15
        )

        return res.json()["choices"][0]["message"]["content"]

    except:
        return "hmm sun nahi paayi 😅"

# --- TTS ---
async def generate_voice(text, path):
    ssml = f"""
    <speak>
        <voice name="en-US-AriaNeural">
            <prosody rate="0.9" pitch="+3%">
                hmm... {text}
                <break time="300ms"/>
            </prosody>
        </voice>
    </speak>
    """

    tts = edge_tts.Communicate(ssml, voice="en-US-AriaNeural")
    await tts.save(path)

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text","")

    filename = "voice_" + hashlib.md5(text.encode()).hexdigest() + ".mp3"
    path = f"static/{filename}"

    if not os.path.exists(path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_voice(text, path))
        loop.close()

    return jsonify({"audio": path})

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message","")
    reply = get_ai_response(msg)
    return jsonify({"reply": reply})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run()
