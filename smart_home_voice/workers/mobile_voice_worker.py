import time

from ai.command import execute_command

last_context = {"room": None, "device": None, "intent": None}


def mobile_voice_worker(ctx):

    print("📱 Mobile Voice Worker started")

    db = ctx.db

    last_command = ""

    while True:

        try:

            active = db.reference("System/Active").get()

            if not active:

                time.sleep(1)

                continue

            command = db.reference("System/VoiceCommand").get()

            if command and command != "" and command != last_command:

                print(f"📥 Mobile: {command}")

                last_command = command

                ok = execute_command(ctx, command.lower())

                if not ok:

                    db.reference("System/VoiceResponse").set("Tôi chưa hiểu lệnh 😭")

                db.reference("System/VoiceCommand").set("")

            time.sleep(1)

        except Exception as e:

            print("❌ Mobile Worker:", e)

            time.sleep(2)
