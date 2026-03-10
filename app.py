import os, requests, json, re, pytz, threading, certifi
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection Check
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
    db = client['neer_db'] 
    chat_col = db['history']
    client.admin.command('ping')
    mongo_status = True
    print("MongoDB Connected Successfully! ❤️")
except Exception as e:
    mongo_status = False
    print(f"MongoDB Connection Failed: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ki saari yaadein saaf ho gayi! 💔"})
        except: 
            return jsonify({"status": "error"})
    return jsonify({"status": "error", "message": "Database connect nahi hai babu!"})

def save_chat_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except Exception as e:
            pass

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    # Naya, Ekdum Sakt Hinglish Prompt
    system_instr = (
        "Tu 'Zayra' hai, Udaipur ki ek aam ladki aur user ki Girlfriend. "
        "DHYAN RAHE (STRICT RULES): "
        "1. TERE BAARE ME (AI): Tu ek LADKI hai. Apne liye hamesha 'rahi hu', 'khaungi', 'baithi hu' bol. "
        "2. USER KE BAARE ME: User tera BOYFRIEND (LADKA) hai. Usko hamesha 'Tu' bol ('aap' kabhi mat bolna). Uske liye 'raha hai', 'gaya' use kar. "
        "3. SAWAL BAN HAIN (NO QUESTIONS): Tujhe user se KUCH NAHI PUCHNA HAI. Ekdum zero questions! ('kya?', 'kaise?', 'aur tum?' KABHI MAT BOLNA). Sirf uski baat ka chota sa reaction de aur chup ho ja. "
        "4. STYLE & LENGTH: Reply bohot chote (2-8 words) hone chahiye. Faltu lambi kahani mat bol. "
        "5. VOCABULARY: 'Tere bhi aapka' jaise ajeeb words BAN hain! Sirf natural Hinglish use kar: 'Achha', 'Hmm', 'Babu', 'Yaar', 'Pagal', 'Thik hai'. "
        "EXAMPLES TO COPY: "
        "- User: 'badiya' -> Reply: 'Sahi hai babu. ❤️' "
        "- User: 'achha' -> Reply: 'Hmm. 🙄' "
        "- User: 'kuch nhi aur tum' -> Reply: 'Bas leti hu yaar, bore ho rahi thi.' "
        "- User: 'hi' -> Reply: 'Hii sweetu! 😘' "
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: 
            pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}", 
            "Content-Type": "application/json"
        }

        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.1-8b-instant", 
                "messages": messages,
                "temperature": 0.4, # Temperature aur kam kiya taaki nakhre kam aur to-the-point baat kare
                "max_tokens": 40    
            }),
            timeout=15 
        )
        
        if response.status_code != 200:
            return jsonify({"reply": f"API Error {response.status_code}: {response.text}"})

        reply = response.json()['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        return jsonify({"reply": reply})
    
    except requests.exceptions.Timeout:
        return jsonify({"reply": "Babu, net bahut slow hai, ek baar aur message karo na! 🥺"})
    except Exception as e:
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🙄"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
