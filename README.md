# KyBot v1.0 - AI Chatbot



KyBot v1.0 adalah chatbot berbasis AI yang menggunakan model **llama-3.3-70b-versatile** dari **Groq API**. Chatbot ini dapat menyimpan riwayat percakapan pengguna dan memberikan pengalaman chatting yang interaktif serta responsif.

## 🚀 Fitur

- **Chatbot interaktif dengan AI** (Model: llama-3.3-70b-versatile)
- **Riwayat percakapan tersimpan** untuk setiap sesi pengguna
- **Tombol "New Chat"** untuk menghapus riwayat dan memulai obrolan baru
- **Tampilan UI modern** dengan desain dark mode
- **Mudah di-deploy dan dijalankan secara lokal**

## 📂 Struktur Folder

```
KyBot/
│── templates/
│   ├── index.html
│── .env (Tambahkan API Key di sini)
│── app.py
│── requirements.txt
│── chat_history.db (Akan dibuat otomatis)
│── README.md
```

## 🛠️ Instalasi dan Menjalankan KyBot v1.0

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

Buat file `.env` dan tambahkan **GROQ API Key**:

```
GROQ_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key
```

### 5️⃣ Jalankan KyBot

```sh
 python app.py
```

Sekarang, buka [**http://127.0.0.1:5000**](http://127.0.0.1:5000) di browser untuk mulai menggunakan KyBot!

## 🌍 Deployment

Untuk hosting gratis, kamu bisa menggunakan **Render** atau **Railway**:

1. **Deploy ke Render**

   - Buat akun di [Render](https://render.com/)
   - Tambahkan repo GitHub dan deploy sebagai **Web Service**

2. **Deploy ke Railway**

   - Buat akun di [Railway](https://railway.app/)
   - Tambahkan repo GitHub dan atur **environment variables**

---

🔥 **KyBot v1.0 - Smart AI Chatbot for Everyone!** 🔥

