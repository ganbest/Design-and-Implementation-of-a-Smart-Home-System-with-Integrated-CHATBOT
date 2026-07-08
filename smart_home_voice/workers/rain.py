# workers/rain.py

import time
from services.telegram_service import send_telegram
from voice.voice import is_bot_speaking

# ==========================================
# RAIN WORKER
# ==========================================


def rain_sensor_worker(ctx):

    db = ctx.db

    kit = ctx.kit

    speak_fn = ctx.speak

    rain_sensor = ctx.rain_sensor

    print("☔ Hệ thống cảm biến mưa đang chạy...")

    # ==========================================
    # NO SENSOR
    # ==========================================

    if rain_sensor is None:

        print("⚠️ Không có cảm biến mưa")

        return

    last_rain_state = None

    # ==========================================
    # LOOP
    # ==========================================

    while True:

        active = db.reference("System/Active").get()

        if not active:

            time.sleep(1)

            continue

        try:

            # ==========================================
            # FIX LOGIC MƯA
            # ==========================================

            current_rain_state = rain_sensor.is_pressed


            # ==========================================
            # STATE CHANGED
            # ==========================================

            if current_rain_state != last_rain_state:

                # ==========================================
                # RAINING
                # ==========================================

                if current_rain_state:

                    print("🌧️ PHÁT HIỆN MƯA!")

                    send_telegram("🌧️ Phát hiện mưa!")

                    # ======================================
                    # SPEAK FIRST
                    # ======================================

                    if not is_bot_speaking():

                        speak_fn("Phát hiện có mưa, tôi đang thu giàn phơi.", db)

                    # ======================================
                    # CLOSE LAUNDRY
                    # ======================================

                    db.reference("Devices/Laundry").set("CLOSE")

                    if kit is not None:

                        try:

                            kit.servo[2].angle = 0

                        except Exception as e:

                            print(f"❌ Servo lỗi: {e}")

                # ==========================================
                # NO RAIN
                # ==========================================

                else:

                    print("☀️ Đã hết mưa.")

                    send_telegram("☀️ Trời đã hết mưa!")

                    # ======================================
                    # SPEAK FIRST
                    # ======================================

                    if not is_bot_speaking():

                        speak_fn("Trời đã hết mưa.", db)

                    # ======================================
                    # OPEN LAUNDRY
                    # ======================================

                    db.reference("Devices/Laundry").set("OPEN")

                    if kit is not None:

                        try:

                            kit.servo[2].angle = 90

                        except Exception as e:

                            print(f"❌ Servo lỗi: {e}")

                last_rain_state = current_rain_state

        except Exception as e:

            print(f"❌ Lỗi luồng mưa: {e}")

        time.sleep(3)
