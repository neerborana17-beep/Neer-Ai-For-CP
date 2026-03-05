import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- Optimized MongoDB Connection ---
try:
    # Timeout kam rakha hai taaki speed bani rahe
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
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
    if not user_input: return jsonify({"reply": "Kuch toh bol bhai! 😂"})

    now = datetime.now()
    current_time = now.strftime("%I:%M %p")

    # 1. Neer ka Asli Dimaag (Instruction upgrade)
    system_instr = (
        "Tera naam Neer hai. Tu CP ka pakka yaar hai. "
        "Tujhe hamesha pichhli chat yaad rakhni hai. Agar user 'Wo kaise?' ya 'Kyun?' puche, "
        "toh tu pichhle message ka reference lekar jawab dega. "
        "Boring bhashan mat de, short aur natural Hinglish mein baat kar. "
        "Baar-baar 2026 ya dost hone ka dhindora mat peet."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # 2. Perfect Memory Logic (Pichhle 10 messages ka flow)
    if mongo_status:
        try:
            # Time ke hisaab se last 10 messages uthao
            history = list(chat_col.find().sort("time", -1).limit(10))
            history.reverse() # Inhe sahi order (purane se naye) mein lagao
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "temperature": 0.7, # Accuracy ke liye temperature thoda kam kiya
                "max_tokens": 250
            }),
            timeout=15
        )
        
        res_data = response.json()
        reply = res_data['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # 3. Save to Database (With Timestamp)
        if mongo_status:
            try:
                # User ka message aur AI ka reply save karo
                chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
            except: pass

        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, dimag hang ho gaya, fir se pucho! 😂"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
