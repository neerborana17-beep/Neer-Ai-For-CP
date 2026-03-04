import os, requests, json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    payload = [{"role": "system", "content": "Tu Neer hai, desi dost."}, 
               {"role": "user", "content": user_input}]
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        data=json.dumps({"model": "google/gemini-2.0-flash-001", "messages": payload})
    )
    
    # Debugging ke liye log print karega
    print("Response Status:", response.status_code)
    
    try:
        reply = response.json()['choices'][0]['message']['content']
        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Bhai, API Key ya Credits ka chakkar lag raha hai!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
