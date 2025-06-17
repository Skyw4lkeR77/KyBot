# KyBot v10.0 - AI Chatbot

KyBot v10.0 adalah chatbot berbasis AI yang memanfaatkan model llama-3.3-70b-versatile dari Groq API dan Gemini API untuk pembuatan dan pengeditan gambar. Chatbot ini menawarkan percakapan interaktif, penyimpanan riwayat obrolan, kemampuan bermain peran, serta fitur pembuatan gambar. Dirancang untuk responsif, ramah pengguna, dan sangat dapat disesuaikan.

DEMO: **https://kybot.up.railway.app/**

## 🚀 Fitur

- **Chatbot interaktif dengan AI** (Model: llama-3.3-70b-versatile)
- **Riwayat percakapan tersimpan** untuk setiap sesi pengguna (disimpan di database SQLite)
- **DeepSearch Mode** untuk pencarian lebih dalam
- **Image generation** berbasis teks prompt
- **Tombol "New Chat"** untuk menghapus riwayat dan memulai obrolan baru
- **Tombol "Export Chat"** untuk mengunduh riwayat percakapan
- **Mode Gelap & Terang** otomatis/dapat diubah manual
- **Voice input** via rekam langsung atau unggah audio
- **Logging terperinci** untuk debugging dan pemantauan
- **Pembersihan otomatis riwayat** (pesan lebih dari 30 hari akan dihapus)
- **Mudah di-deploy dan dijalankan secara lokal atau di cloud**

## 📂 Struktur Folder

```
KyBot/
│── templates/
│   ├── index.html
├── static/ (opsional)
│ ├── fonts/
│ │ └── Zyana.ttf (custom font)
│ └── img/
│ └── logo.png (custom logo)
│── logs/
│   ├── kybot.log
│── generated/
│   ├── (gambar yang dihasilkan)
│── uploads/
│   ├── (file audio sementara)
│── .env
│── app.py
│── requirements.txt
│── chat_history.db (dibuat otomatis)
│── README.md
```

## 🛠️ Instalasi dan Menjalankan KyBot v10.0

Ikuti langkah-langkah berikut untuk menginstal dan menjalankan chatbot ini di sistemmu.

### 1️⃣ Clone Repository

```sh
git clone https://github.com/Skyw4lkeR77/KyBot.git
cd KyBot
```

### 2️⃣ Buat Virtual Environment (Opsional tetapi Direkomendasikan)

```sh
python -m venv venv
source venv/bin/activate   # Untuk Linux/macOS
venv\Scripts\activate      # Untuk Windows
```

### 3️⃣ Instal Dependensi

```sh
pip install -r requirements.txt
```

### 4️⃣ Tambahkan API Key ke `.env`

Buat file `.env` di direktori utama dan tambahkan konfigurasi berikut:

```
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
SERPAPI_KEY=your_serpapi_key
SECRET_KEY=your_secret_key
PORT=5000
```
- GROQ_API_KEY: Dapatkan dari Groq (diperlukan untuk fungsi chatbot).
- GEMINI_API_KEY: Dapatkan dari Google untuk pembuatan/pengeditan gambar.
- SERPAPI_KEY: Dapatkan dari SerpAPI untuk integrasi pencarian web.
- SECRET_KEY: Kunci aman untuk manajemen sesi Flask.

### 5️⃣ Jalankan KyBot

```sh
python app.py
```

Sekarang, buka [**http://127.0.0.1:5000**](http://127.0.0.1:5000) di browser untuk mulai menggunakan KyBot!

## 🌍 Cara Deploy KyBot ke Railway

### 1️⃣ Buat Akun di Railway

1. Buka [Railway.app](https://railway.app/)
2. Login dengan GitHub

### 2️⃣ Hubungkan Repo GitHub ke Railway

1. Klik `New Project` → `Deploy from GitHub Repo`
2. Pilih repo `KyBot` → Klik **Deploy**

### 3️⃣ Tambahkan Environment Variables

1. Buka `Settings` → `Environment Variables`
2. Tambahkan variabel berikut:
   ```
   GROQ_API_KEY=your_groq_api_key
   GEMINI_API_KEY=your_gemini_api_key
   SERPAPI_KEY=your_serpapi_key
   SECRET_KEY=your_secret_key
   PORT=5000
   ```
3. Simpan & Redeploy

### 4️⃣ Gunakan Gunicorn untuk Stabilitas

- Edit `Start Command` di Railway (`Settings` → `Deployments`):
  ```sh
  gunicorn -w 4 -b 0.0.0.0:$PORT app:app
  ```
- Redeploy untuk menerapkan perubahan

### 5️⃣ Akses KyBot di Railway

1. Buka Railway → Tab `Settings` → `Domains`
2. Salin URL (contoh: `https://kybot-example.up.railway.app/`)
3. Buka di browser, dan KyBot siap digunakan!

## 💡 Catatan

- Logging: Log disimpan di logs/kybot.log dengan rotasi (maksimum 1MB, 3 cadangan) atau ditampilkan di konsol jika LOG_TO_CONSOLE=True.
- Database: Riwayat obrolan disimpan di chat_history.db menggunakan SQLite, dengan penghapusan otomatis untuk data yang lebih tua dari 30 hari.
- Penyimpanan Gambar: Gambar yang dihasilkan disimpan di folder generated/ dan dihapus saat memulai sesi obrolan baru.
- Unggahan Audio: File audio sementara untuk transkripsi disimpan di folder uploads/ dan dihapus setelah diproses.
- Keamanan: Input pengguna disanitasi menggunakan bleach untuk mencegah serangan XSS.

## 📜 Lisensi

Proyek ini dibuat hanya untuk pembelajaran dan hiburan. Tidak disarankan untuk penggunaan komersial tanpa izin.
Dibuat oleh **Kypau** dan tersedia di [GitHub](https://github.com/Skyw4lkeR77).

# Cuma proyek iseng-iseng :v
