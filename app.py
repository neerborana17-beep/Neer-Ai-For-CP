import os, json, requests, asyncio, hashlib
from flask import Flask, request, jsonify, render_template
import edge_tts

app = Flask(__name__, static_folder="static", template_folder="templates")

API_KEY = os.getenv("GROQ_API_KEY")
MEMORY_FILE = "memory.json"

# safe load memory
try:
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
except:
    memory = []

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory[-20:], f)

def get_ai_response(user_input):
    global memory

    memory.append({"role": "user", "content": user_input})

    messages = [
        {
            "role": "system",
            "content": "You are Zayra, a real humanoid girl. Soft emotional Hinglish, natural, short replies."
        }
    ] + memory[-10:]

    try:
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

        memory.append({"role": "assistant", "content": reply})
        save_memory()

        return reply

    except Exception as e:
        print(e)
        return "hmm... phir se bolo na ❤️"

async def generate_voice(text, path):
    tts = edge_tts.Communicate(text, voice="en-US-AriaNeural")
    await tts.save(path)

@app.route("/speak", methods=["POST"])
def speak():
    text = request.json.get("text", "")

    filename = "voice_" + hashlib.md5(text.encode()).hexdigest() + ".mp3"
    path = os.path.join("static", filename)

    if not os.path.exists(path):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_voice(text, path))
        loop.close()

    return jsonify({"audio": path})  # FIXED

@app.route("/chat", methods=["POST"])
def chat():
    msg = request.json.get("message", "")
    return jsonify({"reply": get_ai_response(msg)})

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
