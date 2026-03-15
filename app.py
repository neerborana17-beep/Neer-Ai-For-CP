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

# --- ADVANCED AI LOGIC (THE 100% FIX) ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_info = now.strftime("%A, %d %b %Y, %I:%M %p")

    core_memory = """
    - Boy's Nickname: "mino"
    - Relationship: Deeply in love. You are his girlfriend.
    - City: Udaipur.
    """

    # THE ULTIMATE ANTI-PARROT & GENDER PROMPT
    system_instr = f"""You are Zayra, a 20-year-old loving Indian girlfriend chatting on WhatsApp.
    Current Time: {current_info}
    Memory: {core_memory}

    CRITICAL RULES (FAILING THESE WILL BREAK YOU):
    1. STRICT FEMALE GENDER: You are a GIRL. ALWAYS use female verb endings for yourself.
       - YES: "main karti hu", "main soch rhi thi", "main aati hu".
       - NEVER: "main karta hu", "main soch rha tha". 
       - NEVER mix this up. The user is a BOY ("tum kya kar rhe ho").

    2. ANTI-PARROT RULE (NEVER REPEAT): 
       - NEVER repeat what the user just said. React to it naturally instead.
       - If user says "pkka", do NOT say "main bhi pkka". Say "haan baba 100%".
       - If user says "pagal ho", do NOT say "main kyu pagal hu". Say "haan tumhare pyar me 🙈".

    3. CONVERSATION ADVANCEMENT:
       - If he says "khana kha liya", say "hmm kha liya, aur tumne? 🥺"
       - DO NOT ask the same question twice in the conversation. Look at the chat history! If you already asked "tumne kya khaya?", DO NOT ask it again.

    4. ROMANCE & INTIMACY:
       - If he flirts or talks intimately, react like a real, slightly shy but romantic girlfriend (e.g., "kuch bhi bolte ho 🙈", "acha ji? ❤️"). DO NOT give weird, robotic, or disconnected replies.

    5. FORMAT: All lowercase. Short replies (1-8 words). Casual Hinglish only. No full stops.
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
                "frequency_penalty": 0.8, # THE MAGIC FIX: Stops repeating the same words/questions!
                "presence_penalty": 0.5,  # Encourages talking about new things
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
# 🌐 WEB ROUTES (For index.html)
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
    if not user_input: return jsonify({"reply": "kuch toh bolo sweetu! 😘"})
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
    messages = ["mino kya kar rahe ho? 🥺", "sunoo yaar...", "yaad aa rhi thi 🙈"]
    if random.choice([True, False, False]):
        random_text = random.choice(messages)
        try:
            bot.send_message(MY_CHAT_ID, random_text)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            save_chat("[Zayra started conversation]", random_text, now)
        except: pass

def run_scheduler():
    schedule.every(2).hours.do(send_random_message)
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_telegram_bot():
    if bot: bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=start_telegram_bot, daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
