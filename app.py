import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Environment Variables (Security) ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI") 

# MongoDB Setup
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)

db = client['neer_database']
chat_col = db['history']
knowledge_col = db['permanent_memory']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    # 1. MongoDB se purani chat uthao
    history = list(chat_col.find().sort("_id", -1).limit(10))
    history.reverse()
    formatted_history = [{"role": m['role'], "content": m['content']} for m in history]
    
    # 2. Permanent Knowledge uthao
    p_mem = list(knowledge_col.find())
    knowledge_str = str([m['info'] for m in p_mem])

    now = datetime.now()
    system_instr = {
        "role": "system", 
        "content": f"Tu Neer hai, desi dost. Year 2026. Memory: {knowledge_str}. Use Hinglish."
    }
    
    payload = [system_instr] + formatted_history + [{"role": "user", "content": user_input}]
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data=json.dumps({"model": "google/gemini-2.0-flash-001", "messages": payload})
    )
    
    reply = response.json()['choices'][0]['message']['content']
    reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

    # 3. MongoDB mein Save karo (Memory Evolve)
    chat_col.insert_one({"role": "user", "content": user_input, "time": now})
    chat_col.insert_one({"role": "assistant", "content": reply, "time": now})
    
    # Auto-learning logic
    if "yaad rakh" in user_input.lower():
        knowledge_col.insert_one({"info": user_input, "date": now})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
