import os
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)


api_key = os.environ.get("GROQ_API_KEY")
if api_key is None:
    raise ValueError("GROQ_API_KEY tidak ditemukan. Pastikan sudah ditambahkan ke file .env.")

client = Groq(api_key=api_key)

def query_groq_api(message):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": message}],
            model="llama-3.3-70b-versatile", 
            stream=False,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.form['message']
    ai_response = query_groq_api(user_message)
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    app.run(debug=True)
