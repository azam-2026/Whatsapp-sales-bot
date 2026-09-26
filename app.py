import os
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Render Environment Variables se keys read karega
GREEN_API_ID_INSTANCE = os.environ.get("GREEN_API_ID_INSTANCE", "710722747289")
GREEN_API_TOKEN_INSTANCE = os.environ.get("GREEN_API_TOKEN_INSTANCE", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Sales Bot is Running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "No payload"}), 400

    type_webhook = data.get("typeWebhook")

    # Jab koi WhatsApp par message bhejta hai
    if type_webhook == "incomingMessageReceived":
        sender_data = data.get("senderData", {})
        chat_id = sender_data.get("chatId")
        message_data = data.get("messageData", {})

        # Text Message extract kar rahe hain
        text_message = ""
        if message_data.get("typeMessage") == "textMessage":
            text_message = message_data.get("textMessageData", {}).get("textMessage", "")
        elif message_data.get("typeMessage") == "extendedTextMessage":
            text_message = message_data.get("extendedTextMessageData", {}).get("text", "")

        if text_message and chat_id and client:
            try:
                # Groq AI se reply generate kar rahe hain
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "Aap ek helpful aur polite AI Sales Assistant ho. Customer ke sawalon ka chhota, clear aur friendly Hinglish me reply do."
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
                ai_reply = "Aapka message mil gaya hai. Hum jald hi aap se sampark karenge!"

            # Green-API ke through WhatsApp reply send kar rahe hain
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
