import time
import threading
from services.telegram_service import send_telegram


def rfid_worker(ctx, pn532):
    db = ctx.db
    ser = ctx.ser
    kit = ctx.kit
    speak = ctx.speak
    lock = ctx.pn532_lock

    print("🚀 Luồng RFID/Door đã kích hoạt...")

    last_uid = None
    last_scan_time = 0

    while True:
        active = ctx.db.reference("System/Active").get()

        if not active:

            time.sleep(0.2)

            continue
        if ctx.pn532 is None:

            time.sleep(1)

            continue

        pn532 = ctx.pn532

        try:
            door = db.reference("Devices/Main_Door").get()

            if door == "OPEN":

                time.sleep(1)

                continue
            with lock:

                uid = pn532.read_passive_target(timeout=0.5)

            if uid:
                uid_hex = "".join(["{:02X}".format(i) for i in uid])

                # 🔥 chống spam quét liên tục
                if uid_hex == last_uid and time.time() - last_scan_time < 5:
                    continue

                last_uid = uid_hex
                last_scan_time = time.time()

                print(f"💳 Quẹt thẻ: {uid_hex}")

                cards = db.reference("RFID_Cards").get()

                if cards and uid_hex in cards:
                    user_name = cards[uid_hex].get("name", "Chủ nhà")
                    time_now = time.strftime("%H:%M:%S %d/%m/%Y")

                    hello_text = f"Chào mừng {user_name} đã về nhà"
                    send_telegram(f"{user_name} đã về nhà lúc {time_now}")

                    # 🔊 chạy speak non-block
                    threading.Thread(target=speak, args=(hello_text, db)).start()

                    # log
                    db.reference("Access_Logs").push(
                        {"name": user_name, "time": time_now, "status": "Hợp lệ"}
                    )

                    # mở cửa
                    db.reference("Devices/Main_Door").set("OPEN")

                    if ser:
                        ser.write(b"SET_DOOR:OPEN\n")

                    if kit:
                        kit.servo[0].angle = 90

                    # ⏳ delay đóng cửa (non-block)
                    def auto_close():
                        time.sleep(4)
                        print("🔒 Tự động đóng cửa...")
                        db.reference("Devices/Main_Door").set("CLOSE")

                        if ser:
                            ser.write(b"SET_DOOR:CLOSE\n")

                        if kit:
                            kit.servo[0].angle = 0

                    threading.Thread(target=auto_close).start()

                else:
                    print(f"🚫 Thẻ lạ: {uid_hex}")
                    send_telegram(f"🚫 Thẻ lạ: {uid_hex}")

                    db.reference("System/Last_Unknown_Card").set(uid_hex)

                    threading.Thread(
                        target=speak,
                        args=("Phát hiện thẻ mới, vui lòng nhập tên để đăng ký", db),
                        daemon=True,
                    ).start()

        except Exception as e:

            print(f"⚠️ RFID Error: {e}")

            # =====================================
            # PN532 BUSY / DISCONNECTED
            # =====================================

            try:

                ctx.pn532 = None

                print("♻️ Đang reconnect PN532...")

                time.sleep(2)

                from services.pn532_service import init_pn532

                new_pn532 = init_pn532()

                if new_pn532:

                    pn532 = new_pn532

                    ctx.pn532 = new_pn532

                    print("✅ PN532 đã reconnect")

                else:

                    print("❌ Reconnect thất bại")

            except Exception as reconnect_error:

                print("❌ Lỗi reconnect:", reconnect_error)

            time.sleep(2)
            continue