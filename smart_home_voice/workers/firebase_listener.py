# workers/firebase_listener.py

from services.servo import update_window_physical


def firebase_listener(ctx):

    db = ctx.db
    ser = ctx.ser

    def listener(event):

        if event.data is None or event.path == "/":
            return

        key = event.path.replace("/", "")

        # ===== SERVO DEVICES =====
        if any(
            x in key
            for x in [
                "Main_Door",
                "Window_Bed",
                "Window_Living",
                "Laundry"
            ]
        ):

            update_window_physical(ctx, key, event.data)

        # ===== UART DEVICES =====
        else:

            try:
                msg = f"{key}:{event.data}\n"

                if ser:
                    ser.write(msg.encode())

            except Exception as e:
                print("❌ Firebase UART lỗi:", e)

    # ===== LISTEN =====
    db.reference('Light').listen(listener)

    db.reference('Devices').listen(listener)