from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import sqlite3
import os

app = Flask(__name__)

# --- CONFIG GEMINI AI ---
# Membaca API Key secara aman dari sistem server nanti
API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6Kt-uUDw4CO2CoLbCSyfGlsERsxl64Fe6K9_pyYGerXGw")
client = genai.Client(api_key=API_KEY)

config = types.GenerateContentConfig(
    system_instruction=(
        "Nama kamu adalah Keila. Kamu adalah asisten virtual yang sangat dekat, ceria, "
        "dan suportif dengan Rizki. Gunakan gaya bahasa anak muda Indonesia yang santai, "
        "ramah, dan suka memakai emotikon hangat (seperti 😊, 🥰, wkwk). "
        "Selalu panggil pengguna dengan nama 'Rizki'."
    ),
    temperature=0.7,
)

# --- DATABASE SETUP (MEMORI KEILA) ---
DATABASE = 'chat_history.db'

def init_db():
    """Fungsi untuk membuat tabel database jika belum ada"""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# Jalankan inisialisasi database saat aplikasi pertama kali menyala
init_db()

# -------------------------------------

@app.route('/')
def home():
    # Ambil semua riwayat chat dari database untuk ditampilkan saat web di-refresh
    history = []
    if os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT sender, text FROM messages ORDER BY id ASC')
            rows = cursor.fetchall()
            for row in rows:
                history.append({'sender': row[0], 'text': row[1]})
    
    return render_template('index.html', history=history)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    pesan_user = data.get('pesan', '')
    
    if not pesan_user:
        return jsonify({'jawaban': 'Eh, Rizki belum ngetik apa-apa nih wkwk.'})

    # 1. Simpan pesan Rizki ke Database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (sender, text) VALUES (?, ?)', ('user', pesan_user))
        conn.commit()

    try:
        # 2. Minta jawaban dari Gemini AI
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=pesan_user,
            config=config,
        )
        jawaban_keila = response.text
    except Exception as e:
        print(f"Error Gemini: {e}")
        jawaban_keila = "Aduh Rizki, sepertinya otak AI aku lagi kesenggol error nih wkwk."

    # 3. Simpan balasan Keila ke Database
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (sender, text) VALUES (?, ?)', ('keila', jawaban_keila))
        conn.commit()

    return jsonify({'jawaban': jawaban_keila})

if __name__ == '__main__':
    app.run(debug=True)
