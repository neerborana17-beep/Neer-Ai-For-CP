from flask import Flask, render_template, request, jsonify
import requests, json, os, re
from datetime import datetime

app = Flask(__name__)

API_KEY = "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"
MEMORY_FILE = "neer_chat.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f: return json.load(f)
    return [{"role": "system", "content": "Tera naam Neer hai. Tu 2026 mein reh raha ek desi dost hai. Hinglish bol."}]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    chat_history = load_memory()
    
    now = datetime.now()
    system_instruction = {"role": "system", "content": f"Date: {now.strftime('%d %b %Y')}. Year: 2026. Be a natural friend."}
    
    payload = [system_instruction] + chat_history + [{"role": "user", "content": user_input}]
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data=json.dumps({"model": "google/gemini-2.0-flash-001", "messages": payload})
    )
    
    reply = response.json()['choices'][0]['message']['content']
    reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

    chat_history.append({"role": "user", "content": user_input})
    chat_history.append({"role": "assistant", "content": reply})
    
    with open(MEMORY_FILE, "w") as f: json.dump(chat_history[-15:], f)
    
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
