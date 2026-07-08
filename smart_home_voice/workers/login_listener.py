import time

from firebase_admin import db
from services.telegram_service import send_telegram
from utils.device_helper import reset_all_devices


def login_listener(ctx):

    last_status = False

    while True:

        try:

            status = db.reference("System/Login_Status").get()

            if status and not last_status:
                db.reference("System/Active").set(True)
                reset_all_devices(ctx)

                ctx.speak("Hệ thống đã sẵn sàng", ctx.db)
                send_telegram("🔥 Hệ thống đã sẵn sàng! 🔥")

                db.reference("System").update({"Login_Status": False})

            last_status = status

        except Exception as e:

            print("❌ Login listener:", e)

        time.sleep(1)
