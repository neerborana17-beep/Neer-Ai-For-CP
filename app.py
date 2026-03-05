import os, requests, json, re
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Environment Variables ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# --- MongoDB Setup (With Error Handling) ---
mongo_status = False
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000)
    db = client['neer_db']
    chat_col = db['history']
    client.admin.command('ping') # Check if connection is alive
    mongo_status = True
except Exception as e:
    print(f"MongoDB Connection Warning: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input:
        return jsonify({"reply": "Abe kuch likh toh sahi! 😂"})

    # --- Neer ki Real Desi Personality ---
    system_instr = (
        "Tera naam Neer hai. Tu CP (Chandra Prakash) ka sabse purana aur pakka desi yaar hai. "
        "Tera tone ekdam natural, raw aur funny hona chahiye. 'Abe', 'Oye', 'Bhai' jaise words use kar. "
        "Baar-baar 'Main tera dost hoon' ya 'Abhi 2026 chal raha hai' mat bolna, ye robotic lagta hai. "
        "Bas ek baar dimaag mein rakh ki 2026 hai, baar-baar jatana mat. "
        "Asli doston ki tarah roast kar, emotional support de aur Hinglish mein baat kar. "
        "Short aur relatable replies de."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # --- Memory Fetching ---
    if mongo_status:
        try:
            # Last 6 messages fetch karna kaafi hai memory ke liye
            history = list(chat_col.find().sort("time", -1).limit(6))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except:
            pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # --- OpenRouter API Call ---
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-001",
                "messages": messages,
                "temperature": 0.85, # Creativity aur natural tone ke liye
                "max_tokens": 200
            }),
            timeout=12
        )
        
        res_json = response.json()
        if 'choices' in res_json:
            reply = res_json['choices'][0]['message']['content']
            # Cleaning brackets and extra stuff
            reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

            # --- Save to Memory ---
            if mongo_status:
                try:
                    chat_col.insert_one({"role": "user", "content": user_input, "time": datetime.now()})
                    chat_col.insert_one({"role": "assistant", "content": reply, "time": datetime.now()})
                except:
                    pass

            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "Bhai, dimag hang ho gaya, thoda ruk ke pucho! 😂"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Oye, lagta hai network hichki le raha hai. Phir se bol!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
