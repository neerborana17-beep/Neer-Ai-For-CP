import os, requests, asyncio, hashlib
from flask import Flask, request, jsonify, render_template
import edge_tts

app = Flask(__name__, static_folder="static", template_folder="templates")

API_KEY = os.getenv("GROQ_API_KEY")

# 🧠 MEMORY STORE (simple session)
conversation_memory = []

# --- AI ---
def get_ai_response(user_input):
    global conversation_memory

    try:
        conversation_memory.append({"role": "user", "content": user_input})

        # keep last 6 messages
        conversation_memory = conversation_memory[-6:]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Zayra, a real humanoid girl. "
                    "Soft emotional Hinglish. Natural, caring, slightly flirty. "
                    "Short replies. Feels real."
                )
            }
        ] + conversation_memory

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages
            },
            timeout=15
        )

        reply = res.json()["choices"][0]["message"]["content"]

        conversation_memory.append({"role": "assistant", "content": reply})
        conversation_memory = conversation_memory[-6:]

        return reply

    except Exception as e:
        print("AI Error:", e)
        return "hmm... phir se bolo na ❤️"

# --- TTS ---
async def generate_voice(text, path):
    ssml = f"""
    <speak>
        <voice name="en-US-AriaNeural">
            <prosody rate="0.92" pitch="+4%">
                {text}
            </prosody>
        </voice>
    </speak>
    """

    tts = edge_tts.Communicate(ssml, voice="en-US-AriaNeural")
    await tts.save(path)

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json()
    text = data.get("text", "")

    filename = "voice_" + hashlib.md5(text.encode()).hexdigest() + ".mp3"
    path = os.path.join("static", filename)

    if not os.path.exists(path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_voice(text, path))
        loop.close()

    return jsonify({"audio": "/" + path})

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "")
    reply = get_ai_response(msg)
    return jsonify({"reply": reply})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
