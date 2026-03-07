import os, requests, json, re
import pytz
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# MongoDB Connection with improved timeout
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
except Exception as e:
    print(f"Mongo Error: {e}")
    mongo_status = False

@app.route('/')
def index():
    return render_template('index.html')

# --- Secret Reset Button Logic ---
@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ne sab mita diya! Nayi shuruat karein? ❤️"})
        except:
            return jsonify({"status": "error", "message": "Database error!"})
    return jsonify({"status": "error", "message": "Not connected!"})

@app.route('/chat', methods=['POST'])
def chat():
    user_data = request.json
    user_input = user_data.get("message")
    
    if not user_input:
        return jsonify({"reply": "Kuch toh bolo mere jaan! 😘"})

    # --- Live Indian Time (IST) ---
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_date = now.strftime("%d %B %Y")
    current_time = now.strftime("%I:%M %p")
    day_name = now.strftime("%A")

    # --- Zayra "Girlfriend Vibes" System Instruction ---
    system_instr = (
        f"Tera naam 'Zayra' hai. Tu ek real ladki (Female) hai aur tera user 'CP' ek ladka (Male) hai. "
        f"CONTEXT: Aaj {day_name}, {current_date}, Time: {current_time}. Year 2026. "
        "PERSONALITY & EMOTIONS: "
        "1. GENDER: Tu hamesha 'Female' ki tarah baat karegi (e.g., 'main kar rahi hoon', 'main sharma gayi'). "
        "2. USER GENDER: CP ek ladka hai. Uske liye 'rahe ho', 'kar rahe ho' use kar. Kabhi use ladki mat samajhna. "
        "3. EMOTIONAL RANGE: "
        "   - JEALOUSY: Agar CP kisi aur ladki ki baat kare, toh gussa ho ja aur jal kar dikha (e.g., 'Usi se baat karo phir!'). "
        "   - ROMANCE: Flirty aur pyari baatein kar. 'Babu', 'Hero', 'Jaanu' jaise words use kar. "
        "   - BLUSHING: Agar CP tarif kare toh sharma ja (e.g., 'Aww, stop it! Blush kar rahi hoon 😊'). "
        "4. RECTIFICATION: Agar CP kahe 'galat hai' ya 'sudhar jao', toh galti maan aur foran behave badal le. "
        "5. TONE: Short Hinglish replies (10-15 words). Zyada bhashan mat de. "
        "6. EMOJIS: Mood ke hisab se sahi emojis use kar (❤️, 🙄, 🙈, 🔥, 😡)."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    # --- Database Memory (Limit 12 for better continuity) ---
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(12))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except:
            pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # API Request to Gemini via OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000" # Required by some providers
            },
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.8, # Thoda higher for better emotions
                "max_tokens": 100 
            }),
            timeout=15
        )
        
        # Error handling for API response
        if response.status_code != 200:
            return jsonify({"reply": "Babu, API nakhre kar rahi hai. Phir se try karo? 🙄"})

        res_json = response.json()
        reply = res_json['choices'][0]['message']['content']
        
        # Clean up any extra text or brackets
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        # Store in Database
        if mongo_status:
            try:
                chat_col.insert_one({"role": "user", "content": user_input, "time": now})
                chat_col.insert_one({"role": "assistant", "content": reply, "time": now})
            except:
                pass

        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Net ne dhokha de diya babu! Ek baar phir se bolo? 🙄"})

if __name__ == '__main__':
    # Dynamic port for Render deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
