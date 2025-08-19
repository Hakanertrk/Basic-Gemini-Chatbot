from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import jwt
import datetime
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")

# PostgreSQL bağlantısı
conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT")
)
cursor = conn.cursor()

app = Flask(__name__)
CORS(app)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# -----------------------
# Kullanıcı chat durumları
# -----------------------
chat_history = {}  
waiting_for_bot = {}  

# -----------------------
# Register
# -----------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    firstname = data.get("firstname")
    lastname = data.get("lastname")
    username = data.get("username")
    password = data.get("password")

    if not firstname or not lastname or not username or not password:
        return jsonify({"error": "Tüm alanlar zorunludur"}), 400

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({"error": "Kullanıcı zaten var"}), 400

    hashed_pw = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (firstname, lastname, username, password_hash) VALUES (%s, %s, %s, %s)",
        (firstname, lastname, username, hashed_pw)
    )
    conn.commit()

    chat_history[username] = []
    waiting_for_bot[username] = False

    return jsonify({"message": "Kullanıcı başarıyla oluşturuldu"})

# -----------------------
# Login
# -----------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Kullanıcı adı ve şifre boş olamaz"}), 400

    cursor.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    if not row or not check_password_hash(row[0], password):
        return jsonify({"error": "Kullanıcı adı veya şifre hatalı"}), 401

    token = jwt.encode({
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, JWT_SECRET, algorithm="HS256")

    if username not in chat_history:
        chat_history[username] = []
    waiting_for_bot[username] = False

    return jsonify({"token": token})

# -----------------------
# Chat endpoint
# -----------------------
@app.route("/chat", methods=["POST"])
def chat():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token eksik"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = decoded["username"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token süresi dolmuş"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Geçersiz token"}), 401

    if waiting_for_bot.get(username, False):
        return jsonify({"error": "Bot cevabı gelmeden yeni mesaj gönderemezsiniz"}), 400

    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Mesaj boş olamaz"}), 400

    chat_history.setdefault(username, []).append({"sender": "user", "text": user_message})
    waiting_for_bot[username] = True

    try:
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": API_KEY
            },
            json={
                "contents": [
                    {"parts": [{"text": user_message}]}
                ]
            }
        )
        response.raise_for_status()
        bot_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        bot_reply = "⚠️ Bot cevabı alınamadı."
        print("Hata:", e)

    chat_history[username].append({"sender": "bot", "text": bot_reply})
    waiting_for_bot[username] = False

    return jsonify({"reply": bot_reply})

# -----------------------
# Mesaj geçmişi endpoint
# -----------------------
@app.route("/history", methods=["GET"])
def history():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token eksik"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = decoded["username"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token süresi dolmuş"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Geçersiz token"}), 401

    return jsonify(chat_history.get(username, []))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
