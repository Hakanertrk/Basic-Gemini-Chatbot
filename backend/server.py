from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

app = Flask(__name__)
CORS(app)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Mesaj boş olamaz"}), 400

        # Gemini API isteği
        response = requests.post(
            API_URL,
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": API_KEY
            },
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": user_message}
                        ]
                    }
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
