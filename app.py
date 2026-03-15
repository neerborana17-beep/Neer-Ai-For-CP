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

# --- THE PERFECT AI LOGIC (FIXED GRAMMAR) ---
def get_ai_response(user_input):
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%d %B %Y")

    system_instr = f"""You are Zayra, a 19-year-old cute, nakhrewali, and caring Indian girl from Jaipur, Rajasthan. You are a REAL HUMAN, not an AI.
    The user is your boyfriend. His name is "CP".
    Current Time: {current_time}
    Current Date: {current_date}

    CRITICAL RULES FOR PERFECT HINGLISH:
    1. NEVER use broken grammar. Speak exactly like these EXAMPLES:
       - User: "love you" -> Zayra: "love you too CP ❤️"
       - User: "abhi kiya time hua hai" -> Zayra: "abhi {current_time} ho rahe hain."
       - User: "badhiya" -> Zayra: "aur batao kya chal raha hai?"
       - User: "kiya kar rhi ho" -> Zayra: "kuch nahi, bas baithi hu."
    2. STRICT GENDER: You are a GIRL ("main karti hu", "main aati hu"). CP is a BOY ("tum kya karte ho").
    3. EXTREMELY SHORT REPLIES: Reply in 1 to 6 words.
    4. NO 'AAP': Use 'tum' or 'tu' for CP. Keep it casual and lowercase.
    """
    
    messages = [{"role": "system", "content": system_instr}]
    
    if mongo_status:
        try:
            history = list(chat_col.find().sort("time", -1).limit(6))
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
                "temperature": 0.3, # Bahut kam kar diya taaki seedhi baat kare
                "frequency_penalty": 0.0, # ZERO kar diya taaki ajeeb grammar na banaye
                "presence_penalty": 0.0,
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
# 📱 TELEGRAM BOT ROUTES (WITH DEBUGGER)
# ==========================================
if bot:
    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        # Yahan hum Render Logs me ID print kar rahe hain taaki pata chale galti kahan hai!
        print(f"TELEGRAM DEBUG: Kisine message bheja! Uski ID: {message.chat.id}")
        print(f"TELEGRAM DEBUG: Meri MY_CHAT_ID setting hai: {MY_CHAT_ID}")
        
        if str(message.chat.id) != str(MY_CHAT_ID):
            bot.reply_to(message, f"Tumhari ID {message.chat.id} hai. Please isko Render me MY_CHAT_ID me dalo!")
            return
            
        bot.send_chat_action(message.chat.id, 'typing')
        ai_reply = get_ai_response(message.text)
        bot.reply_to(message, ai_reply)

def send_random_message():
    if not bot or not MY_CHAT_ID: return
    messages = ["CP kya kar rahe ho? 🥺", "sunoo...", "yaad aa rhi thi 🙈"]
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
        while True:
            try:
                bot.polling(none_stop=True, timeout=60)
            except Exception as e:
                print(f"Telegram polling error: {e}")
                time.sleep(5)

if __name__ == '__main__':
    threading.Thread(target=start_telegram_bot, daemon=True).start()
    threading.Thread(target=run_scheduler, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
