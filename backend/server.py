from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import datetime
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import fitz
import re

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")
ALLOWED_EXTENSIONS = {'pdf'}

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "PDF dosyası bulunamadı"}), 400

    pdf_file = request.files['pdf']
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")

    text = ""
    for page in doc:
        text += page.get_text()

    # --- 1. Genel özet ---
    
    genel_ozet = f"Genel değerlendirme yapılıyor..."

    # --- 2. Regex ile test sonuçlarını yakala ---
    pattern = r"([A-Za-zçğıöşüÇĞİÖŞÜ ]+):\s*([\d.,]+)\s*(\w+/?.*)\s*\(Ref[:\-]?\s*([<>]?\d+[\-–]?\d*)\)?"
    matches = re.findall(pattern, text)

    referans_disi = []
    for test, value, unit, ref in matches:
        try:
            value_num = float(value.replace(",", "."))
            if "-" in ref:
                low, high = ref.split("-")
                low, high = float(low), float(high)
                if value_num < low:
                    referans_disi.append(f"{test.strip()} düşük ({value_num} {unit}, ref: {ref})")
                elif value_num > high:
                    referans_disi.append(f"{test.strip()} yüksek ({value_num} {unit}, ref: {ref})")
            elif "<" in ref:
                limit = float(ref.replace("<", ""))
                if value_num >= limit:
                    referans_disi.append(f"{test.strip()} yüksek ({value_num} {unit}, ref: {ref})")
            elif ">" in ref:
                limit = float(ref.replace(">", ""))
                if value_num <= limit:
                    referans_disi.append(f"{test.strip()} düşük ({value_num} {unit}, ref: {ref})")
        except:
            continue

    # --- 3. AI ile analiz (Gemini) ---
    prompt = f"""
    Sen bir sağlık asistanısın. Kullanıcının tahlil raporunu inceledin.

    Görevlerin:
    1. Genel durumu 1-2 cümle ile özetle.
    2. Referans dışı değerleri listele (eğer varsa).
    3. Her referans dışı değer için kısa ve basit öneriler ver.
    4. Referans dışı değer yoksa böyle devam etmesi için önerilerde bulun.
    

    Rapor metni:
    {text[:3000]}
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
        ai_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        ai_reply = "⚠️ AI analizi yapılamadı."
        print("PDF analiz hatası:", e)

    # --- 4. Sonuç birleştirme ---
    bot_reply = genel_ozet
    if referans_disi:
        bot_reply += "\n\n⚠️ Referans dışı değerler bulundu:\n- " + "\n- ".join(referans_disi)
    else:
        bot_reply += "\n✅ Önemli değerler referans aralıklarında."

    bot_reply += f"\n\n AI Önerisi:\n{ai_reply}"

    return jsonify({"reply": bot_reply})

# -----------------------
# Register
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

# -----------------------
# Profile
# -----------------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token eksik"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = decoded["username"]
    except ExpiredSignatureError:
        return jsonify({"error": "Token süresi dolmuş"}), 401
    except InvalidTokenError:
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
            "chronic_diseases": row[6] or ""
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
    except ExpiredSignatureError:
        return jsonify({"error": "Token süresi dolmuş"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Geçersiz token"}), 401

    if waiting_for_bot.get(username, False):
        return jsonify({"error": "Bot cevabı gelmeden yeni mesaj gönderemezsiniz"}), 400

    data = request.json
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Mesaj boş olamaz"}), 400

    chat_history.setdefault(username, []).append({"sender": "user", "text": user_message})
    waiting_for_bot[username] = True

    # Profil bilgileri ve ekstra info
    cursor.execute("SELECT age, height, weight, chronic FROM users WHERE username=%s", (username,))
    row = cursor.fetchone()
    profile_info = {"age": row[0], "height": row[1], "weight": row[2], "chronic": row[3]} if row else {}
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
        except:
            pass
    if profile_info.get("chronic"):
        extra_info += f"Kullanıcının kronik hastalıkları: {profile_info['chronic']}. "

    # Danger kontrolü
    danger_words = [
        "göğüs ağrısı", "çarpıntı", "nefes darlığı", "bayılma", "hipotansiyon",
        "kalp krizi", "kalp durması", "nabız düşüklüğü", "nabız yükselmesi",
        "felç", "konuşamıyorum", "baş dönmesi", "nöbet", "astım krizi",
        "şiddetli karın ağrısı", "kusma", "kan kusmak", "şiddetli kanama",
        "intihar", "kendime zarar", "zehirlenme", "allergik şok", "anafilaksi"
    ]
    is_danger = any(word in user_message.lower() for word in danger_words)

    bot_reply = ""
    if is_danger:
        bot_reply += "⚠️ Bu ciddi bir durum olabilir. Lütfen 112'yi arayın veya en yakın acile gidin.\n\n"

    # -------------------
    # Normal sağlık önerisi promptu
    # -------------------
    history_text = ""
    for m in chat_history.get(username, [])[-10:]:
        history_text += f"{m['sender'].capitalize()}: {m['text']}\n"

    prompt = f"""
Sen bir genel sağlık asistanısın. Kullanıcıya güvenli ve evde uygulanabilir tavsiyeler ver.
Sadece beslenme, yaşam tarzı ve basit çözümler öner. İlaç önerme.

Konuşma geçmişi:
{history_text if history_text else 'Yok.'}

Kullanıcı profili: {extra_info if extra_info else "Özel bilgi yok."}
Kullanıcının mesajı: {user_message}
Yanıtın kısa ve öz (2-3 cümle) olmalı.
"""

    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json", "X-goog-api-key": API_KEY},
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        response.raise_for_status()
        normal_reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        normal_reply = "⚠️ Bot cevabı alınamadı."
        print("API Hatası:", e)

    bot_reply += normal_reply
    chat_history.setdefault(username, []).append({"sender": "bot", "text": bot_reply})
    waiting_for_bot[username] = False

    return jsonify({"reply": bot_reply})

# -----------------------
# Appointments
# -----------------------


# -------------------
# GET ve POST: Randevu listeleme ve ekleme
# -------------------
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token eksik"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = decoded["username"]
    except:
        return jsonify({"error": "Geçersiz token"}), 401

    # GET: Kullanıcının randevularını listele
    if request.method == "GET":
        cursor.execute(
            "SELECT id, title, datetime FROM appointments WHERE username=%s ORDER BY datetime",
            (username,)
        )
        rows = cursor.fetchall()
        appointments_list = [
            {"id": r[0], "title": r[1], "datetime": r[2].isoformat()} for r in rows
        ]
        return jsonify(appointments_list)  # Direkt array döndürüyoruz

    # POST: Yeni randevu ekle
    if request.method == "POST":
        data = request.json
        title = data.get("title", "").strip()
        dt_str = data.get("datetime", "").strip()

        if not title or not dt_str:
            return jsonify({"error": "Başlık ve tarih gereklidir"}), 400

        try:
            dt = datetime.datetime.fromisoformat(dt_str)
        except ValueError:
            return jsonify({"error": "Geçersiz tarih formatı"}), 400

        cursor.execute(
            "INSERT INTO appointments (username, title, datetime) VALUES (%s, %s, %s) RETURNING id",
            (username, title, dt)
        )
        appointment_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            "id": appointment_id,
            "title": title,
            "datetime": dt.isoformat(),
            "message": "Randevu eklendi"
        }) 

# -------------------
# DELETE: Randevu silme
# -------------------
@app.route("/appointments/<int:appt_id>", methods=["DELETE"])
def delete_appointment(appt_id):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token eksik"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = decoded["username"]
    except:
        return jsonify({"error": "Geçersiz token"}), 401

    # Randevuyu kontrol et ve sil
    cursor.execute(
        "DELETE FROM appointments WHERE id=%s AND username=%s RETURNING id",
        (appt_id, username)
    )
    deleted = cursor.fetchone()
    conn.commit()

    if deleted:
        return jsonify({"message": "Randevu silindi"})
    else:
        return jsonify({"error": "Randevu bulunamadı"}), 404





# -----------------------
# History
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
    except ExpiredSignatureError:
        return jsonify({"error": "Token süresi dolmuş"}), 401
    except InvalidTokenError:
        return jsonify({"error": "Geçersiz token"}), 401

    return jsonify(chat_history.get(username, []))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
