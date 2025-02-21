import os
import sqlite3
import uuid
from flask import Flask, render_template, request, jsonify, session
from groq import Groq
from dotenv import load_dotenv

ascii_art = """
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░     
░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓███████▓▒░ ░▒▓██████▓▒░  ░▒▓█▓▒░     


==================================================================
=                  Creator: Mr. kypau                            =
=                  versi  : 1.0                                  =
=                  Github : github.com/Skyw4lkeR77               =
==================================================================
"""
print(ascii_art)

# Memuat API Key dari file .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # Untuk sesi pengguna

# Setup Database SQLite
DB_FILE = "chat_history.db"
def inisialisasi_database():
    """Membuat tabel database jika belum ada."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL
            )
        ''')
        conn.commit()
inisialisasi_database()

# API Key untuk Groq
api_key = os.environ.get("GROQ_API_KEY")
if api_key is None:
    raise ValueError("GROQ_API_KEY tidak ditemukan. Pastikan sudah ditambahkan ke file .env.")

client = Groq(api_key=api_key)

# Mendapatkan atau membuat ID sesi unik untuk pengguna
def dapatkan_session_id():
    """Mengembalikan session ID pengguna, atau membuat yang baru jika belum ada."""
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    return session["session_id"]

# Menghapus semua chat pengguna berdasarkan session ID
def hapus_riwayat_chat(session_id):
    """Menghapus semua riwayat chat pengguna berdasarkan session ID."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")  # Pastikan foreign keys diaktifkan
        cursor.execute("DELETE FROM chat WHERE session_id = ?", (session_id,))
        jumlah_dihapus = cursor.rowcount  # Cek jumlah baris yang dihapus
        conn.commit()
        print(f"DEBUG: {jumlah_dihapus} chat history deleted for session {session_id}.")

# Reset chat: menghapus riwayat chat dan membuat sesi baru
def reset_chat():
    """Menghapus riwayat chat saat ini dan membuat session baru."""
    session_id = dapatkan_session_id()
    hapus_riwayat_chat(session_id)
    session["session_id"] = str(uuid.uuid4())
    print(f"DEBUG: New session ID created -> {session['session_id']}")

# Mengirim permintaan ke AI
def kirim_ke_ai(pesan):
    """Mengirim pesan pengguna ke AI dan mendapatkan respon."""
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Kamu adalah KyBot v1.0, AI yang dibuat oleh Mr. Kypau. Jawab dengan relevan dan profesional."},
                {"role": "user", "content": pesan}
            ],
            model="llama-3.3-70b-versatile",
            stream=False,
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"Terjadi kesalahan saat memproses permintaan: {str(e)}"

# Menyimpan chat ke database
def simpan_chat(session_id, pesan_pengguna, respon_ai):
    """Menyimpan percakapan pengguna dan respon AI ke database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat (session_id, user_message, bot_response) VALUES (?, ?, ?)", (session_id, pesan_pengguna, respon_ai))
        conn.commit()

# Mengambil riwayat chat dari database
def ambil_riwayat_chat(session_id):
    """Mengambil riwayat chat berdasarkan session ID pengguna."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_message, bot_response FROM chat WHERE session_id = ? ORDER BY id ASC", (session_id,))
        return cursor.fetchall()

@app.route('/')
def home():
    """Menampilkan halaman utama dengan riwayat chat pengguna."""
    session_id = dapatkan_session_id()
    history = ambil_riwayat_chat(session_id)
    return render_template('index.html', ai_name="KyBot v1.0", creator="Mr. kypau", chat_history=history)

@app.route('/chat', methods=['POST'])
def chat():
    """Menerima pesan pengguna dan mengembalikan respon AI."""
    try:
        session_id = dapatkan_session_id()
        data = request.get_json()
        pesan_pengguna = data.get("message", "").strip()
        if not pesan_pengguna:
            return jsonify({'response': "Pesan tidak boleh kosong."}), 400
        
        respon_ai = kirim_ke_ai(pesan_pengguna)
        simpan_chat(session_id, pesan_pengguna, respon_ai)
        
        return jsonify({'response': respon_ai})
    except Exception as e:
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    """Menghapus chat lama dan memulai sesi baru."""
    reset_chat()
    return jsonify({'message': 'New chat started!'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

