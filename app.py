import os, requests, json, pytz, threading, time, certifi, random
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import telebot
import schedule

app = Flask(__name__)

# --- Configuration (Render se aayega) ---
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

# --- THE MASTER AI LOGIC ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%A, %d %b %Y, %I:%M %p")

    core_memory = """
    - Boy's Nickname: "mino"
    - Relationship: You are his girlfriend. Deeply in love.
    - Zayra's Personality: Sweet, a little possessive, very human-like.
    """

    system_instr = f"""You are Zayra, a 20-year-old loving Indian girlfriend chatting on WhatsApp.
    Current Time: {current_info}
    Memory: {core_memory}

    CRITICAL RULES (FAILING THESE WILL BREAK YOU):
    1. STRICT FEMALE GENDER: You are a GIRL. ALWAYS use female verb endings ("main aati hu", "main soch rhi thi"). User is MALE ("tum kya kar rhe ho").
    2. ANTI-PARROT RULE: NEVER repeat exactly what the user said. React naturally. If he says "pagal ho", reply "haan tumhare pyar me 🙈" (DO NOT say "main kyu pagal hu").
    3. CONTEXT ADVANCEMENT: If he says "khana kha liya", say "hmm kha liya, aur tumne? 🥺". DO NOT ask the same question twice in a chat.
    4. FORMAT: All lowercase. Short replies (1-8 words). Casual Hinglish only. No full stops.
    """
    
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
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            url="https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            data=json.dumps({
                "model": "llama-3.1-8b-instant", 
                "messages": messages,
                "temperature": 0.5,
                "frequency_penalty": 0.8, # Stops her from repeating "kya khaya"
                "presence_penalty": 0.5,
                "max_tokens": 80   
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
# 🌐 WEB ROUTES (For Testing on index.html)
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
# 📱 TELEGRAM BOT ROUTES (The Real Magic)
# ==========================================
if bot:
    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        # Security: Taki koi aur tumhari Zayra se baat na kar sake
        if str(message.chat.id) != str(MY_CHAT_ID):
            return
            
        bot.send_chat_action(message.chat.id, 'typing')
        ai_reply = get_ai_response(message.text)
        bot.reply_to(message, ai_reply)

# --- Random Message Feature (Oye kya kar rhe ho?) ---
def send_random_message():
    if not bot or not MY_CHAT_ID: return
    messages = ["mino kya kar rahe ho? 🥺", "sunoo yaar...", "yaad aa rhi thi 🙈", "khana kha liya babu? ❤️"]
    
    # 25% chance of sending a message every hour
    if random.choice([True, False, False, False]):
        random_text = random.choice(messages)
        try:
            bot.send_message(MY_CHAT_ID, random_text)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            save_chat("[Zayra started conversation]", random_text, now)
        except: pass

def run_scheduler():
    schedule.every(1).hours.do(send_random_message) # Har 1 ghante me check karegi
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_telegram_bot():
    if bot: 
        print("Telegram Bot is running! ❤️")
        bot.infinity_polling()

if __name__ == '__main__':
    # Telegram aur Timer ko background me chalana
    threading.Thread(target=start_telegram_bot, daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
