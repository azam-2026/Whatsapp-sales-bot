import os
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

GREEN_API_ID_INSTANCE = os.environ.get("GREEN_API_ID_INSTANCE", "710722747289")
GREEN_API_TOKEN_INSTANCE = os.environ.get("GREEN_API_TOKEN_INSTANCE", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Kill Switch: Bot Active/Inactive control
BOT_ACTIVE = os.environ.get("BOT_ACTIVE", "true").lower() == "true"

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Keywords jinse Bot activate hoga
TRIGGER_KEYWORDS = ["demo", "property", "flat", "plot", "real estate", "2bhk", "3bhk", "buy", "rent", "#bot"]

@app.route("/", methods=["GET"])
def home():
    status = "Active" if BOT_ACTIVE else "Suspended"
    return f"WhatsApp AI Bot status: {status}"

@app.route("/webhook", methods=["POST"])
def webhook():
    # Agar admin ne Bot OFF kar diya ho
    if not BOT_ACTIVE:
        return jsonify({"status": "bot_disabled"}), 200

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No payload"}), 400

    type_webhook = data.get("typeWebhook")

    if type_webhook == "incomingMessageReceived":
        sender_data = data.get("senderData", {})
        chat_id = sender_data.get("chatId")
        message_data = data.get("messageData", {})

        text_message = ""
        if message_data.get("typeMessage") == "textMessage":
            text_message = message_data.get("textMessageData", {}).get("textMessage", "")
        elif message_data.get("typeMessage") == "extendedTextMessage":
            text_message = message_data.get("extendedTextMessageData", {}).get("text", "")

        msg_lower = text_message.lower().strip()
        is_triggered = any(keyword in msg_lower for keyword in TRIGGER_KEYWORDS)

        if is_triggered and chat_id and client:
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "Aap ek professional Real Estate AI Sales Assistant ho. Customer se unka Budget, Preferred Location, 2BHK ya 3BHK requirement, aur Site Visit ka time puchho. Short, polite aur helpful Hinglish me reply do."
                        },
                        {
                            "role": "user",
                            "content": text_message
                        }
                    ]
                )
                ai_reply = response.choices[0].message.content
            except Exception as e:
                print(f"Groq API Error: {e}")
                ai_reply = "Aapka message mil gaya hai! Humare Real Estate Agent jald hi aap se contact karenge."

            send_url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/sendMessage/{GREEN_API_TOKEN_INSTANCE}"
            payload = {
                "chatId": chat_id,
                "message": ai_reply
            }
            try:
                requests.post(send_url, json=payload, timeout=10)
            except Exception as e:
                print(f"Green-API Send Error: {e}")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
