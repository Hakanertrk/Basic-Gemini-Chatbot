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
# Kullanıcı kaydı
# -----------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({"error": "Kullanıcı zaten var"}), 400

    hashed_pw = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, hashed_pw)
    )
    conn.commit()
    return jsonify({"message": "Kullanıcı başarıyla oluşturuldu"})

# -----------------------
# Login
# -----------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    if not row or not check_password_hash(row[0], password):
        return jsonify({"error": "Kullanıcı adı veya şifre hatalı"}), 401

    token = jwt.encode({
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({"token": token})

# -----------------------
# Chat endpoint (JWT doğrulamalı)
# -----------------------
@app.route("/chat", methods=["POST"])
def chat():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token eksik"}), 401

    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token süresi dolmuş"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Geçersiz token"}), 401

    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Mesaj boş olamaz"}), 400

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
        return jsonify({"reply": bot_reply})
    except Exception as e:
        print("Hata:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
