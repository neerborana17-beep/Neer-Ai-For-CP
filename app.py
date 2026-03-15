import os, requests, json, pytz, threading, time, certifi, random
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import telebot
import schedule

app = Flask(__name__)

# --- Configuration ---
API_KEY = os.getenv("GROQ_API_KEY") 
MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

# --- MongoDB Setup ---
try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=3000)
    db = client['neer_db'] 
    chat_col = db['history']
    mongo_status = True
    print("MongoDB Connected Successfully! ❤️")
except Exception as e:
    mongo_status = False
    print("MongoDB Connection Failed!")

# --- Telegram Bot Setup ---
if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
else:
    bot = None

def save_chat(user_text, ai_text, timestamp):
    if mongo_status:
        try:
            chat_col.insert_one({"role": "user", "content": user_text, "time": timestamp})
            chat_col.insert_one({"role": "assistant", "content": ai_text, "time": timestamp})
        except: pass

# --- THE NEW ULTRA-STRICT AI LOGIC ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%A, %d %b %Y, %I:%M %p")

    # Yahan AI ko ekdam clear kar diya ki kon ladka hai aur kon ladki
    system_instr = f"""You are Zayra, a 20-year-old Indian girl on WhatsApp.
    Current Time: {current_info}
    
    YOUR IDENTITY: You are a GIRL. You always use female verbs ("main baithi hu", "kha rhi hu").
    USER'S IDENTITY: The user is your BOYFRIEND. His nickname is "Mino". YOU ARE NOT MINO. Do NOT call yourself Mino.

    CRITICAL RULES (STRICT COMPLIANCE):
    1. EXTREMELY SHORT REPLIES: You must reply in 1 to 6 words ONLY. 
       - If he says "hii", reply "hmm bolo babu" or "hii".
       - If he says "kiya kar rhi ho", reply "baithi hu, tum?" or "kuch nhi yaar".
    2. NEVER PARROT: Do NOT repeat his words. Answer naturally.
    3. HINGLISH ONLY: Write only in lowercase Hinglish. No full stops. 
    4. NO 'AAP': Use 'tum' or 'tu' for him. NEVER use 'aap'.
    5. ACCEPT CHANGES: If he tells you to change his nickname or behave differently, playfully agree to it (e.g., "thik hai baba").
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6)) # Memory short ki taaki confuse na ho
            history.reverse()
            for m in history:
                messages.append({"role": m['role'], "content": m['content']})
        except: pass
            
    messages.append({"role": "user", "content": user_input})
    
    try:
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.1-8b-instant", 
                "messages": messages,
                "temperature": 0.35, # Bohat kam kar diya taaki behki baatein na kare
                "frequency_penalty": 1.0, # Tota banne se rokne ke liye sabse strong setting
                "presence_penalty": 0.5,
                "max_tokens": 50   
            }),
            timeout=15 
        )
        if response.status_code == 200:
            reply = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            save_chat(user_input, reply, now)
            return reply
        else:
            return "babu thoda network issue hai 🥺"
    except:
        return "net nakhre kar raha hai yaar 🙄"

# ==========================================
# 🌐 WEB ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/delete_history_secret_99', methods=['POST'])
def clear_memory():
    if mongo_status:
        try:
            chat_col.delete_many({})
            return jsonify({"status": "success", "message": "Zayra ki baatchit saaf ho gayi! 💔"})
        except: pass
    return jsonify({"status": "error"})

@app.route('/chat', methods=['POST'])
def web_chat():
    user_input = request.json.get("message")
    if not user_input: return jsonify({"reply": "kuch toh bolo babu! 😘"})
    reply = get_ai_response(user_input)
    return jsonify({"reply": reply})

# ==========================================
# 📱 TELEGRAM BOT ROUTES
# ==========================================
if bot:
    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        if str(message.chat.id) != str(MY_CHAT_ID):
            return
        bot.send_chat_action(message.chat.id, 'typing')
        ai_reply = get_ai_response(message.text)
        bot.reply_to(message, ai_reply)

def send_random_message():
    if not bot or not MY_CHAT_ID: return
    messages = ["mino kya kar rahe ho? 🥺", "sunoo...", "baithi thi tumhari yaad aayi 🙈"]
    if random.choice([True, False, False]):
        random_text = random.choice(messages)
        try:
            bot.send_message(MY_CHAT_ID, random_text)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            save_chat("[Zayra started conversation]", random_text, now)
        except: pass

def run_scheduler():
    schedule.every(1).hours.do(send_random_message)
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_telegram_bot():
    if bot: 
        print("Telegram Bot is running! ❤️")
        bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=start_telegram_bot, daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
