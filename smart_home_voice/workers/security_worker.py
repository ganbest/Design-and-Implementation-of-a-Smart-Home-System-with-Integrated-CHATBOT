# workers/security_worker.py

def on_security_change(ctx, event):

    ser = ctx.ser

    mode = event.data

    val = 1 if mode in [1, True, "ON"] else 0

    print(f"🔒 SECURITY MODE: {val}")

    try:

        if ser:
            ser.write(f"SecurityMode:{val}\n".encode())

    except Exception as e:

        print("❌ Security UART lỗi:", e)


def start_security_listener(ctx):

    db = ctx.db

    db.reference(
        'System/SecurityMode'
    ).listen(
        lambda event: on_security_change(ctx, event)
    )

    print("🛡️ Security listener started")