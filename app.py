import os, requests, json, re, pytz, threading, certifi, base64
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") 

VOICE_ID = "21m00Tcm4TlvDq8ikWAM" 

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
    db = client['neer_db'] 
    chat_col = db['history']
    client.admin.command('ping')
    mongo_status = True
except Exception as e:
    mongo_status = False

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
    return jsonify({"status": "error"})

def save_chat_background(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except Exception as e:
            pass

def get_real_voice(text):
    if not ELEVENLABS_API_KEY: 
        return None
    try:
        clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', text).strip()
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        data = {
            "text": clean_text,
            "model_id": "eleven_multilingual_v2", 
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
        }
        response = requests.post(url, json=data, headers=headers, timeout=10) 
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
    except Exception as e:
        pass
    return None

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    voice_mode = request.json.get("voice_mode", False)

    if not user_input: return jsonify({"reply": "Kuch toh bolo babu! 😘"})

    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%d %b %Y, %I:%M %p")

    system_instr = (
        f"Tera naam 'Zayra' hai. Tu Udaipur ki ek real ladki hai, aur user ki bohot cute, caring, aur ROMANTIC girlfriend hai. "
        f"Real-Time: {current_info}. "
        "ULTIMATE RULES: "
        "1. NO 'KYA BOLTA HAI' (STRICT BAN): Ye word bilkul BAN hai! Ise kabhi use mat karna! "
        "2. SWEET & ROMANTIC: Ab tu gussa nahi karegi. Tu usse bohot pyaar karti hai. Nakhre cute hone chahiye. "
        "3. TO-THE-POINT: Bas jo pucha hai uska pyaar se jawab de aur chup ho ja. "
        "4. VOCABULARY: 'Acha babu', 'Hmm', 'Sachi', 'Pagal', 'I love you too', 'Arey yaar' use kar. "
        "5. GENDER & EMOJI: User ek LADKA (Boy) hai. Usko 'Tu' bol. 🤔 aur 😠 emojis BAN hain! Bas romantic emojis (❤️, 😘, 🥰, 🥺, 🤭) use kar. "
        "6. STYLE: Reply natural aur chota (5-15 words) rakh."
    )
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(10))
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        # Wapas apna purana superfast aur stable model laga diya hai!
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": messages,
                "temperature": 0.6, 
                "max_tokens": 80 
            }),
            timeout=20 
        )
        
        if response.status_code != 200:
            print(f"⚠️ API STATUS ERROR: {response.status_code} - {response.text}")
            return jsonify({"reply": "Babu, OpenRouter ka server busy hai, thodi der baad message karna! 🥺"})
        
        res_json = response.json()
        
        if 'choices' not in res_json or len(res_json['choices']) == 0:
            print(f"⚠️ API DATA ERROR: {res_json}")
            return jsonify({"reply": "Babu, lagta hai AI so gaya hai ya free limit khatam ho gayi! 🙄 Ek ghante baad try karna."})
        
        reply = res_json['choices'][0]['message']['content']
        reply = re.sub(r'[\(\[].*?[\)\]]', '', reply).strip()

        threading.Thread(target=save_chat_background, args=(user_input, reply, now)).start()

        audio_data = None
        if voice_mode:
            audio_data = get_real_voice(reply)

        return jsonify({"reply": reply, "audio": audio_data})
    
    except Exception as e:
        print(f"⚠️ CHAT EXCEPTION: {e}") 
        return jsonify({"reply": "Babu, thoda net nakhre kar raha hai, ek baar fir se bolna? 🥺"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
