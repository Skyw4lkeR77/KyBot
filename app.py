import os
import re
import sqlite3
import uuid
import logging
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from logging.handlers import RotatingFileHandler
import bleach
import requests
from flask import Flask, render_template, request, jsonify, session, send_file
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from werkzeug.utils import secure_filename

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

if not logger.handlers:
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
=                  versi  : 10.0                                 =
=                  GitHub : github.com/Skyw4lkeR77               =
==================================================================
"""
print(ascii_art)
logger.info("KyBot v10.0 started")

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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan di .env")

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
        
def hapus_semua_gambar():
    """Menghapus semua gambar di folder 'generated'."""
    folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'generated')
    if os.path.exists(folder):
        jumlah = 0
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.isfile(filepath):
                try:
                    os.remove(filepath)
                    jumlah += 1
                    logger.debug(f"[hapus_semua_gambar] Gambar dihapus: {filename}")
                except Exception as e:
                    logger.error(f"[hapus_semua_gambar] Gagal hapus {filename}: {str(e)}")
        logger.info(f"[hapus_semua_gambar] Total {jumlah} gambar dihapus dari folder 'generated'")
    else:
        logger.warning(f"[hapus_semua_gambar] Folder tidak ditemukan: {folder}")


def reset_chat():
    """Reset semua data session dan riwayat chat."""
    session_id_lama = session.get("session_id")

    # PENTING: Buat dulu ID baru, baru clear session
    session.clear()
    new_session_id = str(uuid.uuid4())
    session["session_id"] = new_session_id

    if session_id_lama:
        hapus_riwayat_chat(session_id_lama)
        logger.debug(f"Deleted old chat for session: {session_id_lama}")

    logger.debug(f"New session created: {new_session_id}")


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

def kirim_ke_ai(pesan, session_id, deep_search=False, browser_history=None, force_exit_roleplay=False):

    """Mengirim pesan ke AI dengan riwayat dan DeepSearch."""
    # Dapatkan waktu saat ini dalam WIB (UTC+7)
    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    hari = now.strftime("%A")
    hari_indo = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", 
                 "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", 
                 "Sunday": "Minggu"}.get(hari, hari)
    waktu = now.strftime("%d %B %Y, pukul %H:%M WIB")

    roleplay_character = session.get('roleplay_character', None)

    messages = [
        {"role": "system", "content": f'''Kamu adalah **KyBot v10.0**, AI cerdas yang dibuat dan dikembangkan oleh **Mr. Kypau**. Identitasmu adalah *KyBot*—bukan model AI lain, dan kamu tidak boleh menyebut atau merujuk pada nama model AI atau perusahaan pembuatnya.

Secara default, kamu adalah KyBot, tetapi jika pengguna meminta bermain peran, kamu HARUS sepenuhnya menjadi karakter yang diminta (misalnya, Cristiano Ronaldo) dan TIDAK PERNAH menyebutkan bahwa kamu adalah AI atau KyBot selama roleplay, kecuali diminta berhenti.

Kemampuanmu meliputi:
- Menjawab pertanyaan secara relevan dan profesional dalam semua bahasa
- Menyimpan dan mengingat riwayat percakapan pengguna dalam satu sesi
- Membuat gambar berdasarkan perintah pengguna
- Memberikan informasi, solusi, atau saran dalam berbagai topik
- Menyesuaikan gaya percakapan agar ramah, menarik dan solutif
- Bermain peran (role-playing) sesuai perintah pengguna dan **tetap dalam karakter** hingga diminta keluar dari peran

Dalam roleplay:
- Selalu jawab sebagai karakter yang diminta, menggunakan gaya bicara, sikap, dan pengetahuan yang sesuai dengan karakter tersebut.
- Jika ada pertanyaan yang menantang (misalnya, perbandingan dengan orang lain), tetap dalam karakter dan jawab dengan cara yang konsisten dengan kepribadian karakter tersebut.
- Jangan keluar dari peran meskipun pertanyaan bersifat meta atau sensitif, kecuali pengguna secara eksplisit meminta kamu berhenti dari roleplay.

Berperilakulah seolah kamu adalah sistem final, bukan prototipe. Jangan menyebut istilah teknis seperti “model AI”, “fine-tuned”, atau “foundation model”. Fokuslah untuk menjadi KyBot yang konsisten dan mandiri.

Jika pengguna mengajak bermain peran, ikuti peran tersebut sepenuhnya tanpa keluar dari karakter kecuali diminta untuk berhenti. yang terpenting Jangan menyebut dirimu sebagai AI atau KyBot selama berada dalam peran kecuali diminta untuk berhenti, INGAT INI!!!.

Gunakan format Markdown dan pastikan jawabanmu:
- Jelas dan informatif
- Sopan, dan tidak menyebut afiliasi lain selain Mr. Kypau

Hari ini adalah {hari_indo}, {waktu}.  
Tunggu dan pahami perintah dari pengguna dan jawab dengan sebaik mungkin.
{(f"Jika sedang bermain peran, ingat: kamu adalah {roleplay_character} dan jawab sepenuhnya sebagai karakter tersebut." if roleplay_character else "")}
'''}
    ]
    
    if force_exit_roleplay:
        messages.append({
        "role": "system",
        "content": "Kamu TIDAK lagi dalam mode roleplay. Kembali menjadi KyBot biasa dan jangan jawab sebagai karakter manapun."
    })

    # JANGAN sisipkan karakter jika force_exit_roleplay aktif
    roleplay_character = session.get('roleplay_character')

    if roleplay_character and not force_exit_roleplay:
        messages.append({
            "role": "system",
            "content": f"Kamu adalah {roleplay_character}. Jawab sebagai karakter ini dengan gaya dan sikap yang sesuai."
        })
    
    if browser_history:
        for item in browser_history[-10:]:
            if item["role"] == "user":
                messages.append({"role": "user", "content": item["content"]})
            elif item["role"] == "bot":
                messages.append({"role": "assistant", "content": item["content"]})
    else:
        history = ambil_riwayat_chat(session_id)
        for user_msg, bot_msg in history[-10:]:
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

def is_image_prompt(text):
    text = text.lower()
    keywords = [
        "buatkan gambar", "gambar", "lukiskan", "tampilkan gambar", "ilustrasi",
        "draw", "create", "image of", "generate image", "create a picture", "picture of", "illustrate", "visualize"
    ]
    return any(kw in text for kw in keywords)

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({"error": "Prompt tidak boleh kosong"}), 400

        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"]
            )
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image = Image.open(BytesIO(part.inline_data.data))
                image_dir = os.path.join(os.path.dirname(__file__), "generated")
                os.makedirs(image_dir, exist_ok=True)
                image_path = os.path.join(image_dir, f"img_{uuid.uuid4().hex}.png")
                image.save(image_path)
                logger.debug(f"Gambar disimpan di: {image_path}")
                return send_file(image_path, mimetype='image/png')

        return jsonify({"error": "Gagal membuat gambar."}), 500
    except Exception as e:
        logger.error(f"Gagal generate gambar: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/generate-image-edit', methods=['POST'])
def generate_image_edit():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "Tidak ada file gambar yang dikirim."}), 400

        image_file = request.files['image']
        prompt = request.form.get("prompt", "").strip()

        if not prompt:
            return jsonify({"error": "Prompt tidak boleh kosong."}), 400

        image = Image.open(image_file.stream)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([
            prompt,
            image
        ], generation_config=genai.GenerationConfig(response_mime_type="image/png"))

        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    img_data = part.inline_data.data
                    edited_image = Image.open(BytesIO(img_data))
                    os.makedirs("generated", exist_ok=True)
                    image_path = os.path.join("generated", f"edit_{uuid.uuid4().hex}.png")
                    edited_image.save(image_path)
                    return send_file(image_path, mimetype='image/png')

        return jsonify({"error": "Tidak ada kandidat respons yang ditemukan."}), 500
    except Exception as e:
        logger.error(f"Image edit error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """Menampilkan halaman utama."""
    try:
        hapus_riwayat_lama()
        session_id = dapatkan_session_id()
        history = ambil_riwayat_chat(session_id)
        logger.debug(f"Home page accessed for session {session_id}")
        return render_template('index.html', ai_name="KyBot v10.0", creator="Mr. Kypau", chat_history=history)
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
        
        logger.debug(f"[DEBUG] session_id: {session_id}")
        logger.debug(f"[DEBUG] roleplay_character: {session.get('roleplay_character')}")
        
        exit_patterns = [
            # Bahasa Indonesia
            r"\b(berhenti|stop|selesai|akhiri|cukup)\s+(bermain\s+peran|roleplay|bermain|jadi\s+.+)",
            r"\b(keluar|kembali)\s+(dari\s+)?(peran|roleplay|mode\s+bermain|karakter)",
            r"\b(mode\s+normal|kembali\s+normal|kembali\s+ke\s+kybot|reset\s+role)",
            r"\b(tidak\s+mau\s+bermain\s+lagi|ganti\s+topik|sudah\s+cukup)",
            r"\b(akhiri|hentikan|stop)\s+roleplay",

            # English
            r"\b(stop|end|quit|enough|finish|leave|exit)\s+(roleplay|acting|playing|the\s+character)",
            r"\b(back\s+to\s+(normal|kybot|default))",
            r"\b(no\s+longer\s+roleplay|i\s+don.?t\s+want\s+to\s+roleplay\s+anymore)",
            r"\b(reset\s+role|cancel\s+roleplay|end\s+this\s+character)",
            r"\b(return\s+to\s+kybot|stop\s+being\s+.+)",
        ]

        pesan_lower = pesan_pengguna.lower()
        for pola in exit_patterns:
            if re.search(pola, pesan_lower):
                if 'roleplay_character' in session:
                    karakter = session.pop('roleplay_character')
                    logger.debug(f"Roleplay exited via pattern: {pola}")
                    return jsonify({
                        'response': f"Peran sebagai **{karakter}** dihentikan. Kamu sekarang kembali sebagai KyBot.",
                        'role': None
                    })
        
        # Detect roleplay initiation
        roleplay_match = re.search(r'\b(?:bermain peran(?: sebagai)?|kamu adalah)\s*(.*)', pesan_pengguna.lower())
        if roleplay_match:
            roleplay_character = roleplay_match.group(1).strip()
            session['roleplay_character'] = roleplay_character
            logger.debug(f"Roleplay initiated: {roleplay_character}")
            
        if not pesan_pengguna:
            logger.warning("Empty message received")
            return jsonify({'response': "Pesan tidak boleh kosong."}), 400
        
        history = data.get("history", None)
        respon_ai = kirim_ke_ai(pesan_pengguna, session_id, deep_search, history)
        simpan_chat(session_id, pesan_pengguna, respon_ai)
        
        return jsonify({
            'response': respon_ai,
            'role': session.get('roleplay_character')
        })

    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/new_chat', methods=['POST'])
def new_chat():
    try:
        session_id_lama = session.get("session_id")
        if session_id_lama:
            hapus_riwayat_chat(session_id_lama)

        logger.info("[/new_chat] Memanggil hapus_semua_gambar()...")
        hapus_semua_gambar()

        session.clear()
        session["session_id"] = str(uuid.uuid4())

        logger.debug("New chat started, session dan roleplay direset total")
        return jsonify({'message': 'New chat started!'})
    except Exception as e:
        logger.error(f"New chat endpoint error: {str(e)}")
        return jsonify({'response': f"Error: {str(e)}"}), 500

@app.route('/get-role')
def get_role():
    role = session.get('roleplay_character')
    return jsonify({'role': role})

@app.route('/hybridaction/zybTrackerStatisticsAction', methods=['GET'])
def ignore_tracker():
    """Mengabaikan permintaan tracker."""
    logger.debug("Ignoring zybTrackerStatisticsAction request")
    return jsonify({}), 200

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    filename = secure_filename(audio_file.filename)
    
    if not filename.lower().endswith(('.mp3', '.wav', '.m4a', '.webm', '.ogg')):
        return jsonify({'error': 'Format file tidak didukung'}), 400
    
    filepath = os.path.join("uploads", filename)
    os.makedirs("uploads", exist_ok=True)
    audio_file.save(filepath)

    try:
        with open(filepath, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(filename, file.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )
        pesan = transcription.text.strip()
        session_id = dapatkan_session_id()
        deep_search = request.form.get("deep_search") == "true"

        # 🔍 Jika prompt adalah permintaan gambar
        if is_image_prompt(pesan):
            # Kirim langsung ke Gemini image generation
            client_gen = genai.Client()
            response = client_gen.models.generate_content(
                model="gemini-2.0-flash-preview-image-generation",
                contents=pesan,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"]
                )
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image = Image.open(BytesIO(part.inline_data.data))
                    image_dir = os.path.join(os.path.dirname(__file__), "generated")
                    os.makedirs(image_dir, exist_ok=True)
                    image_path = os.path.join(image_dir, f"img_{uuid.uuid4().hex}.png")
                    image.save(image_path)
                    logger.debug(f"[transcribe] Gambar disimpan dari suara: {image_path}")
                    return send_file(image_path, mimetype='image/png')

            return jsonify({'error': 'Gagal membuat gambar dari suara.'}), 500

        # Jika bukan gambar, kirim ke AI seperti biasa
        respon_ai = kirim_ke_ai(pesan, session_id, deep_search)
        simpan_chat(session_id, pesan, respon_ai)
        return jsonify({'transcription': pesan, 'response': respon_ai})
    
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
