# workers/ai_worker.py
import time
from datetime import datetime


demo_scripts = [

    {
        "text":
        "Nhiệt độ hiện tại khá cao, "
        "bạn có muốn tôi bật quạt mức 3 không?",

        "action": "fan_hot"
    },

    {
        "text":
        "Đã 22 giờ 30 rồi, "
        "bạn đi ngủ chưa? "
        "Tôi bật chế độ đi ngủ cho bạn nha.",

        "action": "sleep_mode"
    },

    {
        "text":
        "Bạn ơi dậy thôi, "
        "đã sáng rồi.",

        "action": "morning_mode"
    },

    {
        "text":
        "Đã 8 giờ rồi, "
        "bạn đi làm chưa? "
        "Tôi bật chế độ an ninh cho bạn nha.",

        "action": "security_mode"
    },

    {
        "text":
        "Đã 17 giờ rồi, "
        "bạn đang về nha. "
        "Tôi mở quạt cho mát nhà nha.",

        "action": "welcome_home"
    }

]


def ai_control_worker(ctx):

    print("🧠 AI Worker started")

    db = ctx.db
    speak = ctx.speak

    while True:
        active = ctx.db.reference("System/Active").get()

        if not active:

            time.sleep(1)

            continue

        try:

            # ==========================================
            # UPDATE AI MEMORY
            # ==========================================

            db.reference("AI/Stats").update(
                {
                    "light_khach_memory": len(ctx.brain_light_khach.X_train),
                    "fan_khach_memory": len(ctx.brain_fan_khach.X_train),
                    "light_ngu_memory": len(ctx.brain_light_ngu.X_train),
                    "fan_ngu_memory": len(ctx.brain_fan_ngu.X_train),
                }
            )

            # ==========================================
            # AI MODE
            # ==========================================

            ai_mode = db.reference("System/AI_Mode").get()

            if ai_mode not in [1, True]:

                time.sleep(5)
                continue

            # ==========================================
            # TIME
            # ==========================================

            hour = datetime.now().hour
            night_mode = hour >= 23 or hour <= 6
            # ==========================================
            # SENSOR
            # ==========================================

            temp_khach = db.reference("Sensors/Khach/Temp").get() or 30

            humi_khach = db.reference("Sensors/Khach/Humi").get() or 70

            temp_ngu = db.reference("Sensors/Ngu/Temp").get() or 28

            humi_ngu = db.reference("Sensors/Ngu/Humi").get() or 75

            # ==========================================
            # LIGHT KHACH
            # ==========================================

            light_khach = ctx.brain_light_khach.predict(hour, temp_khach, humi_khach)
            if night_mode:

                light_khach = 0

            prob_light_khach = ctx.brain_light_khach.get_probability(
                hour, temp_khach, humi_khach
            )


            if prob_light_khach >= 10:

                override_time = ctx.state.manual_override.get("Light/Khach")

                if override_time and (time.time() - override_time < 300):

                    print("⛔ Manual override Light/Khach")

                else:

                    current_light = db.reference("Light/Khach").get() or 0

                    if light_khach != current_light:

                        if light_khach > current_light:

                            speak(
                                f"Ui hơi tối á 😅 "
                                f"Tui tăng đèn phòng khách "
                                f"lên mức {light_khach} nha.",
                                db,
                            )

                        elif light_khach < current_light:

                            speak(
                                f"Tui giảm đèn phòng khách "
                                f"xuống mức {light_khach} nha 😄",
                                db,
                            )

                        db.reference("Light/Khach").set(light_khach)

                   

            # ==========================================
            # FAN KHACH
            # ==========================================

            fan_khach = ctx.brain_fan_khach.predict(hour, temp_khach, humi_khach)
            if night_mode and fan_khach > 1:

                fan_khach = 1
            prob_fan_khach = ctx.brain_fan_khach.get_probability(
                hour, temp_khach, humi_khach
            )

            

            if prob_fan_khach >= 95:

                override_time = ctx.state.manual_override.get("Devices/Fan_Khach")

                if override_time and (time.time() - override_time < 300):

                    print("⛔ Manual override Fan_Khach")

                else:

                    current_fan = db.reference("Devices/Fan_Khach").get() or 0

                    if fan_khach != current_fan:

                        if fan_khach > current_fan:

                            speak(
                                f"Ui hơi oi á � "
                                f"Tui tăng quạt phòng khách "
                                f"lên mức {fan_khach} nha.",
                                db,
                            )

                        elif fan_khach < current_fan:

                            speak(
                                f"Phòng mát hơn rồi 😄 "
                                f"Tui giảm quạt phòng khách "
                                f"xuống mức {fan_khach} nha.",
                                db,
                            )

                        db.reference("Devices/Fan_Khach").set(fan_khach)


            # ==========================================
            # LIGHT NGU
            # ==========================================

            light_ngu = ctx.brain_light_ngu.predict(hour, temp_ngu, humi_ngu)

            prob_light_ngu = ctx.brain_light_ngu.get_probability(
                hour, temp_ngu, humi_ngu
            )

            
            if prob_light_ngu >= 95:

                override_time = ctx.state.manual_override.get("Light/Ngu")

                if override_time and (time.time() - override_time < 300):

                    print("⛔ Manual override Light/Ngu")

                else:

                    current_light = db.reference("Light/Ngu").get() or 0

                    if light_ngu != current_light:

                        if light_ngu > current_light:

                            speak(
                                f"Ui hơi tối á 😅 "
                                f"Tui tăng đèn phòng ngủ "
                                f"lên mức {light_ngu} nha.",
                                db,
                            )

                        elif light_ngu < current_light:

                            speak(
                                f"Tui giảm đèn phòng ngủ "
                                f"xuống mức {light_ngu} nha 😄",
                                db,
                            )

                        db.reference("Light/Ngu").set(light_ngu)

                   

            # ==========================================
            # FAN NGU
            # ==========================================

            fan_ngu = ctx.brain_fan_ngu.predict(hour, temp_ngu, humi_ngu)

            prob_fan_ngu = ctx.brain_fan_ngu.get_probability(hour, temp_ngu, humi_ngu)

            

            if prob_fan_ngu >= 95:

                override_time = ctx.state.manual_override.get("Devices/Fan_Ngu")

                if override_time and (time.time() - override_time < 300):

                    print("⛔ Manual override Fan_Ngu")

                else:

                    current_fan = db.reference("Devices/Fan_Ngu").get() or 0

                    if fan_ngu != current_fan:

                        if fan_ngu > current_fan:

                            speak(
                                f"Ui hơi oi á � "
                                f"Tui tăng quạt phòng ngủ "
                                f"lên mức {fan_ngu} nha.",
                                db,
                            )

                        elif fan_ngu < current_fan:

                            speak(
                                f"Phòng mát hơn rồi 😄 "
                                f"Tui giảm quạt phòng ngủ "
                                f"xuống mức {fan_ngu} nha.",
                                db,
                            )

                        db.reference("Devices/Fan_Ngu").set(fan_ngu)

                

        except Exception as e:
            print("❌ AI Worker lỗi:", e)
            time.sleep(10)
        time.sleep(5)



