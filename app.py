import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Config
API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message")
        if not user_input: return jsonify({"reply": "Bol na bhai!"})

        # Real-time data for Neer
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        curr_dt = ist_now.strftime("%d %b %Y, %I:%M %p")

        # Clean & Fast System Prompt (No Galiyan, Only Friendship)
        system_instr = (
            f"Tera naam Neer hai. Tu CP ka sabse accha dost hai. "
            f"Tu Hinglish mein baat karta hai. Tera nature cool aur helpful hai. "
            f"Replies hamesha short aur to-the-point rakh. "
            f"Aaj ki date aur time {curr_dt} hai."
        )

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": [
                    {"role": "system", "content": system_instr},
                    {"role": "user", "content": user_input}
                ],
                "max_tokens": 150
            }),
            timeout=10
        )
        
        reply = response.json()['choices'][0]['message']['content'].strip()
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply)

        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": "Bhai, server thoda busy hai. Ek baar refresh kar le!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
