import os
import sqlite3
import uuid
import logging
from logging.handlers import RotatingFileHandler
import bleach
import requests
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Setup logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'kybot.log')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

if os.environ.get("LOG_TO_CONSOLE", "False").lower() == "true":
    handler = logging.StreamHandler()
else:
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3)
handler.setFormatter(formatter)
logger.addHandler(handler)

ascii_art = """
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒███▓▒ ░▒█▓█▓▒     
░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓███████▓▒░ ░▒▓██████▓▒░  ░▒▓█▓▒░     

==================================================================
=                  Creator: Mr. kypau                            =
=                  versi  : 9.0                                  =
=                  GitHub : github.com/Skyw4lkeR77               =
==================================================================
"""
print(ascii_art)
logger.info("KyBot v9.0 started")

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

DB_FILE = "chat_history.db"
def inisialisasi_database():
    """Membuat tabel database dengan timestamp."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_message TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.debug("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
inisialisasi_database()

def hapus_riwayat_lama():
    """Menghapus riwayat chat yang lebih tua dari 30 hari."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("DELETE FROM chat WHERE timestamp < ?", (thirty_days_ago,))
            jumlah_dihapus = cursor.rowcount
            conn.commit()
        if jumlah_dihapus > 0:
            logger.debug(f"{jumlah_dihapus} old chat records deleted")
    except Exception as e:
        logger.error(f"Error deleting old chat records: {str(e)}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
if GROQ_API_KEY is None:
    logger.error("GROQ_API_KEY not found")
    raise ValueError("GROQ_API_KEY tidak ditemukan.")

client = Groq(api_key=GROQ_API_KEY)

def dapatkan_session_id():
    """Mengembalikan session ID pengguna."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
        logger.debug(f"New session ID created: {session['session_id']}")
    return session["session_id"]

def hapus_riwayat_chat(session_id):
    """Menghapus riwayat chat berdasarkan session ID."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM chat WHERE session_id = ?", (session_id,))
            jumlah_dihapus = cursor.rowcount
            conn.commit()
        logger.debug(f"{jumlah_dihapus} chat history deleted for session {session_id}")
    except Exception as e:
        logger.error(f"Error deleting chat history: {str(e)}")

def reset_chat():
    """Menghapus riwayat chat dan membuat session baru."""
    session_id = dapatkan_session_id()
    hapus_riwayat_chat(session_id)
    session["session_id"] = str(uuid.uuid4())
    logger.debug(f"New session ID created: {session['session_id']}")

def cari_web(query):
    """Mencari informasi di web menggunakan SerpAPI."""
    try:
        url = "https://serpapi.com/search"
        params = {"q": query, "api_key": SERPAPI_KEY}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        results = data.get("organic_results", [])
        if results:
            return "\n".join([f"{result.get('title', '')}: {result.get('snippet', '')}" for result in results[:3]])
        return "Tidak ada hasil pencarian ditemukan."
    except Exception as e:
        logger.error(f"SerpAPI error: {str(e)}")
        return f"Error saat mencari: {str(e)}"

def kirim_ke_ai(pesan, session_id, deep_search=False, browser_history=None):
    """Mengirim pesan ke AI dengan riwayat dan DeepSearch."""
    # Dapatkan waktu saat ini dalam WIB (UTC+7)
    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    hari = now.strftime("%A")  # Nama hari dalam bahasa Inggris
    hari_indo = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", 
                 "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", 
                 "Sunday": "Minggu"}.get(hari, hari)
    waktu = now.strftime("%d %B %Y, pukul %H:%M WIB")

    messages = [
        {"role": "system", "content": f"Kamu adalah KyBot v9.0, AI yang dibuat oleh Mr. Kypau. Jawab dengan relevan dan profesional dalam bahasa Indonesia menggunakan format Markdown. Hari ini adalah {hari_indo}, {waktu}."}
    ]
    
    if browser_history:
        for item in browser_history[-5:]:
            if item["role"] == "user":
                messages.append({"role": "user", "content": item["content"]})
            elif item["role"] == "bot":
                messages.append({"role": "assistant", "content": item["content"]})
    else:
        history = ambil_riwayat_chat(session_id)
        for user_msg, bot_msg in history[-5:]:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})
    
    if deep_search:
        search_results = cari_web(pesan)
        pesan = f"Pertanyaan: {pesan}\nHasil pencarian: {search_results}"
    
    messages.append({"role": "user", "content": pesan})
    
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        response = chat_completion.choices[0].message.content.strip()
        logger.debug(f"AI response generated for message: {pesan[:50]}...")
        return response
    except Exception as e:
        logger.error(f"Groq API error: {str(e)}")
        return f"Terjadi kesalahan: {str(e)}"

def simpan_chat(session_id, pesan_pengguna, respon_ai):
    """Menyimpan percakapan ke database."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chat (session_id, user_message, bot_response, timestamp) VALUES (?, ?, ?, ?)", 
                          (session_id, pesan_pengguna, respon_ai, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
        logger.debug(f"Chat saved for session {session_id}")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")

def ambil_riwayat_chat(session_id):
    """Mengambil riwayat chat berdasarkan session ID."""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_message, bot_response FROM chat WHERE session_id = ? ORDER BY id ASC", (session_id,))
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return []

@app.route('/')
def home():
    """Menampilkan halaman utama."""
    try:
        hapus_riwayat_lama()
        session_id = dapatkan_session_id()
        history = ambil_riwayat_chat(session_id)
        logger.debug(f"Home page accessed for session {session_id}")
        return render_template('index.html', ai_name="KyBot v9.0", creator="Mr. Kypau", chat_history=history)
    except Exception as e:
        logger.error(f"Home endpoint error: {str(e)}")
        return "Error loading page", 500

@app.route('/chat', methods=['POST'])
def chat():
    """Menerima pesan pengguna dan mengembalikan respon AI."""
    try:
        session_id = dapatkan_session_id()
        data = request.get_json()
        pesan_pengguna = bleach.clean(data.get("message", "").strip())
        deep_search = data.get("deep_search", False)
        
        if not pesan_pengguna:
            logger.warning("Empty message received")
            return jsonify({'response': "Pesan tidak boleh kosong."}), 400
        
        history = data.get("history", None)
        respon_ai = kirim_ke_ai(pesan_pengguna, session_id, deep_search, history)
        simpan_chat(session_id, pesan_pengguna, respon_ai)
        
        return jsonify({'response': respon_ai})
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    """Menghapus chat lama dan memulai sesi baru."""
    try:
        reset_chat()
        logger.debug("New chat started")
        return jsonify({'message': 'New chat started!'})
    except Exception as e:
        logger.error(f"New chat endpoint error: {str(e)}")
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/hybridaction/zybTrackerStatisticsAction', methods=['GET'])
def ignore_tracker():
    """Mengabaikan permintaan tracker."""
    logger.debug("Ignoring zybTrackerStatisticsAction request")
    return jsonify({}), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
