# KyBot v9.0 - AI Chatbot

KyBot v9.0 adalah chatbot berbasis AI yang menggunakan model **llama-3.3-70b-versatile** dari **Groq API**. Chatbot ini mendukung riwayat percakapan, fitur DeepSearch untuk pencarian web, dan antarmuka pengguna yang modern serta responsif.

DEMO: **https://kybot.up.railway.app/**

## 🚀 Fitur

- **Chatbot interaktif dengan AI** (Model: llama-3.3-70b-versatile)
- **Riwayat percakapan tersimpan** untuk setiap sesi pengguna (disimpan di database SQLite)
- **DeepSearch Mode** untuk mencari informasi di web menggunakan SerpAPI
- **Tombol "New Chat"** untuk menghapus riwayat dan memulai obrolan baru
- **Tombol "Export Chat"** untuk mengunduh riwayat percakapan
- **Mode Gelap & Terang** otomatis/dapat diubah manual
- **Logging terperinci** untuk debugging dan pemantauan
- **Pembersihan otomatis riwayat** (pesan lebih dari 30 hari akan dihapus)
- **Mudah di-deploy dan dijalankan secara lokal atau di cloud**

## 📂 Struktur Folder

```
KyBot/
│── templates/
│   ├── index.html
│── logs/
│   ├── kybot.log
│── .env (Tambahkan API Key di sini)
│── app.py
│── requirements.txt
│── chat_history.db (Akan dibuat otomatis)
│── README.md
```

## 🛠️ Instalasi dan Menjalankan KyBot v9.0

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

Buat file `.env` dan tambahkan **GROQ_API_KEY** dan **SERPAPI_KEY** (jika menggunakan DeepSearch):

```
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here # opsional, tapi diperlukan untuk DeepSearch
SECRET_KEY=your_secret_key
```


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
   PORT=5000
   GROQ_API_KEY=your_groq_api_key_here
   SERPAPI_KEY=your_serpapi_key_here
   SECRET_KEY=your_secret_key
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
2. Salin URL (contoh: `https://kybot-production.up.railway.app/`)
3. Buka di browser, dan KyBot siap digunakan!

## 💡 Catatan Tambahan

- **Logging**: Log disimpan di folder `logs/kybot.log` dengan rotasi file (maksimum 1MB, 3 backup).
- **Database**: Riwayat chat disimpan di `chat_history.db` menggunakan SQLite.
- **Keamanan**: Input pengguna dibersihkan menggunakan `bleach` untuk mencegah serangan XSS.
- **DeepSearch**: Menggunakan SerpAPI untuk pencarian web. Pastikan `SERPAPI_KEY` sudah diatur di `.env` untuk mengaktifkan fitur ini.

## 📜 Lisensi

Proyek ini dibuat hanya untuk pembelajaran dan hiburan. Tidak disarankan untuk penggunaan komersial tanpa izin.
Dibuat oleh **Kypau** dan tersedia di [GitHub](https://github.com/Skyw4lkeR77).

# Cuma proyek iseng-iseng :v
