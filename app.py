import os
import requests
from flask import Flask, request, jsonify
from groq import Groq

app = Flask(__name__)

# Environment Variables with strip() to remove spaces
GREEN_API_ID_INSTANCE = os.environ.get("GREEN_API_ID_INSTANCE", "710722747289").strip()
GREEN_API_TOKEN_INSTANCE = os.environ.get("GREEN_API_TOKEN_INSTANCE", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Real Estate AI Bot Active!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        print("--> No json data received", flush=True)
        return jsonify({"status": "no_data"}), 200

    type_webhook = data.get("typeWebhook")
    print(f"--> Webhook Received Type: {type_webhook}", flush=True)

    if type_webhook == "incomingMessageReceived":
        sender_data = data.get("senderData", {})
        chat_id = sender_data.get("chatId")
        message_data = data.get("messageData", {})

        text_message = ""
        type_msg = message_data.get("typeMessage")
        if type_msg == "textMessage":
            text_message = message_data.get("textMessageData", {}).get("textMessage", "")
        elif type_msg == "extendedTextMessage":
            text_message = message_data.get("extendedTextMessageData", {}).get("text", "")

        print(f"--> Message Content from {chat_id}: '{text_message}'", flush=True)

        if text_message and chat_id:
            ai_reply = "Namaste! Main aapka Real Estate AI Assistant hoon. Aapko kis location me property ya flat chahiye?"
            
            if client:
                try:
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "Aap ek Real Estate Sales Assistant hain. Short, helpful aur polite Hinglish me reply karein."},
                            {"role": "user", "content": text_message}
                        ],
                        max_tokens=300
                    )
                    ai_reply = res.choices[0].message.content
                except Exception as e:
                    print(f"--> Groq Error: {e}", flush=True)

            # Send Message back to WhatsApp
            send_url = f"https://api.green-api.com/waInstance{GREEN_API_ID_INSTANCE}/sendMessage/{GREEN_API_TOKEN_INSTANCE}"
            payload = {
                "chatId": chat_id,
                "message": ai_reply
            }
            
            try:
                response = requests.post(send_url, json=payload, timeout=10)
                print(f"--> Green-API Send Status: {response.status_code}, Response: {response.text}", flush=True)
            except Exception as e:
                print(f"--> Send Request Failed: {e}", flush=True)

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
