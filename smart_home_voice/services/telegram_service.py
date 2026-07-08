
import requests

BOT_TOKEN = "8840809463:AAEotY5N2KZVKRnGrpElr0a69uAov-bIn7s"

CHAT_ID = "8977579179"


def send_telegram(message):

    try:

        url = (
            f"https://api.telegram.org/bot"
            f"{BOT_TOKEN}/sendMessage"
        )

        data = {

            "chat_id": CHAT_ID,

            "text": message

        }

        requests.post(
            url,
            data=data,
            timeout=10
        )

        print("✅ Telegram sent")

    except Exception as e:

        print(
            "❌ Telegram error:",
            e
        )

