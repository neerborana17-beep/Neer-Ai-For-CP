import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB with super fast timeout
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
    db = client['neer_db']
    chat_col = db['history']
    mongo_status = True
except:
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bol! 😂"})

    # Personality Context
    system_instr = (
        "Tera naam Neer hai. Tu CP ka pakka desi yaar hai. "
        "Short, fast aur natural Hinglish mein reply kar. "
        "Pichhli baaton ka dhayan rakh par bhashan mat de."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # Fast History (Only last 5 for speed)
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(5))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Switching to Flash-Lite for 2x Speed
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", # Fastest Model
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150 # Limit tokens for faster response
            }),
            timeout=8 # Timeout tight rakha hai speed ke liye
        )
        
        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Save to DB in background style
        if mongo_status:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, net slow hai ya mera dimaag, fir se bol! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
