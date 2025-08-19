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
# -----------------------
# Kullanıcı kaydı (Register)
# -----------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    firstname = data.get("firstname", "")
    lastname = data.get("lastname", "")

    if not username or not password:
        return jsonify({"error": "Kullanıcı adı ve şifre boş olamaz"}), 400

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({"error": "Kullanıcı zaten var"}), 400

    hashed_pw = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, password_hash, firstname, lastname) VALUES (%s, %s, %s, %s)",
        (username, hashed_pw, firstname, lastname)
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

@app.route("/profile", methods=["GET", "POST"])
def profile():
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

    if request.method == "GET":
        cursor.execute(
            "SELECT username, firstname, lastname, age, height, weight, chronic FROM users WHERE username=%s",
            (username,)
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Kullanıcı bulunamadı"}), 404

        return jsonify({
            "username": row[0],
            "firstname": row[1] or "",
            "lastname": row[2] or "",
            "age": row[3] or "",
            "height": row[4] or "",
            "weight": row[5] or "",
            "chronic_diseases": row[6] or ""   # ⚠️ burayı düzelttim
        })

    if request.method == "POST":
        data = request.json
        firstname = data.get("firstname")
        lastname = data.get("lastname")
        age = data.get("age")
        height = data.get("height")
        weight = data.get("weight")
        chronic = data.get("chronic_diseases")

        cursor.execute(
            """
            UPDATE users
            SET firstname = COALESCE(%s, firstname),
                lastname = COALESCE(%s, lastname),
                age = COALESCE(%s, age),
                height = COALESCE(%s, height),
                weight = COALESCE(%s, weight),
                chronic = COALESCE(%s, chronic)
            WHERE username=%s
            """,
            (firstname, lastname, age, height, weight, chronic, username)
        )
        conn.commit()

        return jsonify({"message": "Profil güncellendi"})


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

    # Bot cevabı gelmeden yeni mesaj gönderilmesin
    if waiting_for_bot.get(username, False):
        return jsonify({"error": "Bot cevabı gelmeden yeni mesaj gönderemezsiniz"}), 400

    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Mesaj boş olamaz"}), 400

    # Kullanıcı mesajını kaydet
    chat_history.setdefault(username, []).append({"sender": "user", "text": user_message})
    waiting_for_bot[username] = True

    # -------------------
    # Kullanıcı profil bilgilerini çekelim
    # -------------------
    cursor.execute(
        "SELECT age, height, weight, chronic FROM users WHERE username=%s",
        (username,)
    )
    row = cursor.fetchone()
    profile_info = {
        "age": row[0],
        "height": row[1],
        "weight": row[2],
        "chronic": row[3]
    } if row else {}

    # BMI hesaplama
    extra_info = ""
    if profile_info.get("height") and profile_info.get("weight"):
        try:
            height_m = float(profile_info["height"]) / 100
            bmi = float(profile_info["weight"]) / (height_m ** 2)
            if bmi >= 30:
                extra_info += "Kullanıcının obezite durumu var. "
            elif bmi >= 25:
                extra_info += "Kullanıcı fazla kilolu. "
            elif bmi < 18.5:
                extra_info += "Kullanıcı zayıf. "
        except Exception:
            pass

    if profile_info.get("chronic"):
        extra_info += f"Kullanıcının kronik hastalıkları: {profile_info['chronic']}. "

    # -------------------
    # Danger prompt kontrolü
    # -------------------
    danger_words = [
    # Kalp & dolaşım
    "göğüs ağrısı", "çarpıntı", "nefes darlığı", "bayılma", "hipotansiyon", "yüksek ateş", 
    "kalp krizi", "kalp durması", "kalp sıkışması", "nabız düşüklüğü", "nabız yükselmesi", "şok", 

    # Nörolojik
    "felç", "konuşamıyorum", "baş dönmesi", "bayılma", "şiddetli baş ağrısı", 
    "nöbet", "kriz", "bilinç kaybı", "epilepsi atağı", 

    # Solunum
    "nefes alamıyorum", "hırıltı", "astım krizi", "boğulma", "solunum yetmezliği", 

    # Sindirim
    "şiddetli karın ağrısı", "kusma", "kan kusmak", "kanlı dışkı", "ishal", 
    "karın şişliği", "apandisit", 

    # Travma / yaralanma
    "şiddetli kanama", "kırık", "yanık", "çarpma", "travma", "kazada yaralandım", 

    # Psikolojik
    "intihar", "kendime zarar", "psikoz", "panik atak", "kriz", "depresyon", 

    # Diğer ciddi durumlar
    "zehirlenme", "allergik şok", "anafilaksi", "yüksek ateş", "ölüm", 
    "şiddetli ağrı", "bilinç kaybı"
]

    is_danger = any(word in user_message.lower() for word in danger_words)
    bot_reply = ""

    if is_danger:
        bot_reply += "⚠️ Bu ciddi bir durum olabilir. Lütfen 112'yi arayın veya en yakın acile gidin.\n\n"

    # -------------------
    # Normal sağlık önerisi promptu (kişiselleştirilmiş)
    # -------------------
    prompt = f"""
    Sen bir genel sağlık asistanısın. Kullanıcıya güvenli ve evde uygulanabilir tavsiyeler ver. 
    Sadece beslenme, yaşam tarzı ve basit çözümler öner. İlaç önerme.
    
    Kullanıcı profili: {extra_info if extra_info else "Özel bilgi yok."}
    Kullanıcının mesajı: {user_message}

    Yanıtın kısa ve öz (2-3 cümle) olmalı.
    Eğer fazla kilosu varsa, fazla kilolarının şikayetini artırabileceğini belirt.
    """

    try:
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": API_KEY
            },
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        response.raise_for_status()
        normal_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        normal_reply = "⚠️ Bot cevabı alınamadı."
        print("Hata:", e)

    bot_reply += normal_reply

    # Bot cevabını kaydet ve kullanıcıyı serbest bırak
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
