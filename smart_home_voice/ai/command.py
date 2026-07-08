# ai/command.py

from datetime import datetime
from email.mime import text
import time
import threading
import subprocess


from utils.device_helper import reset_all_devices
from ai.openai_ai import ask_gpt


MUSIC_LIST = [
    "/home/quochieu/music/demo.mp3",
    "/home/quochieu/music/conmuangangqua.mp3",
    "/home/quochieu/music/qqqq.mp3"
]

current_music = 0


def execute_command(ctx, text):
    speak = ctx.speak
    db = ctx.db
    ser = ctx.ser
    kit = ctx.kit

    # ====================================
    # DEMO MODE START
    # ====================================

    if "demo" in text:

        ai_mode = db.reference("System/AI_Mode").get()

        if not ai_mode:

            speak("Bạn chưa bật chế độ AI tự động 😄", db)

            return True

        reset_all_devices(ctx)

        ctx.state.demo_mode = True
        ctx.state.demo_step = 0

        ctx.speak("Đã bật chế độ trình diễn AI.", ctx.db)

        from workers.ai_worker import demo_scripts

        demo = demo_scripts[0]

        ctx.state.waiting_demo_confirm = True

        ctx.speak(demo["text"], ctx.db)

        return True

    # ====================================
    # DEMO NEXT STEP
    # ====================================

    if ctx.state.demo_mode and "xong" in text:

        from workers.ai_worker import demo_scripts

        ctx.state.demo_step += 1

        if ctx.state.demo_step >= len(demo_scripts):

            ctx.state.demo_mode = False
            reset_all_devices(ctx)
            db.reference("System/SecurityMode").set(0)
            ctx.speak("Đã kết thúc chế độ trình diễn AI.", ctx.db)

            return True

        demo = demo_scripts[ctx.state.demo_step]

        ctx.state.waiting_demo_confirm = True

        ctx.speak(demo["text"], ctx.db)

        return True

    # ====================================
    # DEMO CONFIRM
    # ====================================

    if ctx.state.waiting_demo_confirm:
        if "xong" in text:

            ctx.state.waiting_demo_confirm = False

            return False

        from workers.ai_worker import demo_scripts

        demo = demo_scripts[ctx.state.demo_step]

        action = demo["action"]

        # =========================
        # YES
        # =========================

        if any(x in text for x in ["có", "ok", "oke", "ừ", "yes", "đồng ý"]):

            # =========================
            # FAN HOT
            # =========================

            if action == "fan_hot":

                db.reference("Devices/Fan_Khach").set(3)

                if ser and ser.is_open:

                    ser.write(b"Fan_Khach:3\n")

            # =========================
            # SLEEP MODE
            # =========================
            elif action == "sleep_mode":

                db.reference("Devices/Fan_Khach").set(0)
                db.reference("Light/Khach").set(0)

                db.reference("Light/Ngu").set(1)

                db.reference("Devices/Fan_Ngu").set(1)

                db.reference("Devices/Window_Bed").set("CLOSE")
                db.reference("System/SecurityMode").set(1)

            # =========================
            # MORNING MODE
            # =========================

            elif action == "morning_mode":
                db.reference("Devices/Fan_Ngu").set(0)

                db.reference("Devices/Window_Bed").set("OPEN")

                db.reference("Light/Ngu").set(0)
                db.reference("System/SecurityMode").set(0)

            # =========================
            # SECURITY MODE
            # =========================

            elif action == "security_mode":
                reset_all_devices(ctx)

                db.reference("System/SecurityMode").set(1)

            # =========================
            # WELCOME HOME
            # =========================

            elif action == "welcome_home":
                db.reference("System/SecurityMode").set(0)
                db.reference("Devices/Fan_Khach").set(2)

            speak("Đã thực hiện.", db)

            ctx.state.waiting_demo_confirm = False

        # =========================
        # NO
        # =========================

        elif any(x in text for x in ["không", "khỏi", "no", "không cần"]):

            speak("Được rồi 😄 " "tôi sẽ giữ nguyên trạng thái hiện tại.", db)
            ctx.state.waiting_demo_confirm = False
            return True

        else:

            speak("Bạn đồng ý hay không đồng ý nè 😄", db)

            return True

    # ====================================
    # WAITING LIGHT ROOM
    # ====================================

    if ctx.state.waiting_light_room:

        # =================================
        # MEMORY ROOM
        # =================================

        if "phòng" not in text and ctx.state.last_room:

            room = ctx.state.last_room

        else:

            room = None

        if "ngủ" in text:

            room = "ngu"

            ctx.state.last_room = "ngu"

        elif "khách" in text or "khach" in text:

            room = "khach"

            ctx.state.last_room = "khach"

        if room:

            ctx.state.waiting_light_room = False

            ctx.state.pending_action = None

            # ==========================
            # PHÒNG NGỦ
            # ==========================

            if room == "ngu":

                ctx.db.reference("Light/Ngu").set(3)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(b"Ngu:3\n")

                speak("Đã bật đèn phòng ngủ.", ctx.db)

            # ==========================
            # PHÒNG KHÁCH
            # ==========================

            else:

                ctx.db.reference("Light/Khach").set(3)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(b"Khach:3\n")

                speak("Đã bật đèn phòng khách.", ctx.db)

            return True

        else:

            speak("Bạn muốn bật đèn phòng khách hay phòng ngủ?", ctx.db)

            return True

    # ====================================
    # WAITING FAN ROOM
    # ====================================

    if ctx.state.waiting_fan_room:

        # =================================
        # MEMORY ROOM
        # =================================

        if "phòng" not in text and ctx.state.last_room:

            room = ctx.state.last_room

        else:

            room = None

        if "ngủ" in text:

            room = "ngu"

            ctx.state.last_room = "ngu"

        elif "khách" in text or "khach" in text:

            room = "khach"

            ctx.state.last_room = "khach"

        if room:

            ctx.state.waiting_fan_room = False

            ctx.state.pending_action = None

            # ==========================
            # PHÒNG NGỦ
            # ==========================

            if room == "ngu":

                ctx.db.reference("Devices/Fan_Ngu").set(3)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(b"Fan_Ngu:3\n")

                speak("Đã bật quạt phòng ngủ.", ctx.db)

            # ==========================
            # PHÒNG KHÁCH
            # ==========================

            else:

                ctx.db.reference("Devices/Fan_Khach").set(3)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(b"Fan_Khach:3\n")

                speak("Đã bật quạt phòng khách.", ctx.db)

            return True

        else:

            speak("Bạn muốn bật quạt phòng khách hay phòng ngủ?", ctx.db)

            return True

        # ====================================
    # WAITING REDUCE FAN ROOM
    # ====================================

    if ctx.state.waiting_reduce_fan_room:

        room = None

        # =================================
        # MEMORY ROOM
        # =================================

        if "phòng" not in text and ctx.state.last_room:

            room = ctx.state.last_room

        else:

            if "ngủ" in text:

                room = "ngu"

                ctx.state.last_room = "ngu"

            elif "khách" in text or "khach" in text:

                room = "khach"

                ctx.state.last_room = "khach"

        if room:

            ctx.state.waiting_reduce_fan_room = False

            ctx.state.pending_action = None
            # ==========================
            # PHÒNG NGỦ
            # ==========================

            if room == "ngu":

                current = ctx.db.reference("Devices/Fan_Ngu").get() or 1

                new_speed = max(1, current - 1)

                ctx.db.reference("Devices/Fan_Ngu").set(new_speed)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(f"Fan_Ngu:{new_speed}\n".encode())

                speak("Đã giảm quạt phòng ngủ.", ctx.db)

            # ==========================
            # PHÒNG KHÁCH
            # ==========================

            else:

                current = ctx.db.reference("Devices/Fan_Khach").get() or 1

                new_speed = max(1, current - 1)

                ctx.db.reference("Devices/Fan_Khach").set(new_speed)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(f"Fan_Khach:{new_speed}\n".encode())

                speak("Đã giảm quạt phòng khách.", ctx.db)

            return True
        else:

            speak("Bạn muốn giảm quạt phòng khách hay phòng ngủ?", ctx.db)

            return True

    # ====================================
    # WAITING REDUCE LIGHT ROOM
    # ====================================

    if ctx.state.waiting_reduce_light_room:

        room = None

        # =================================
        # MEMORY ROOM
        # =================================

        if "phòng" not in text and ctx.state.last_room:

            room = ctx.state.last_room

        else:

            if "ngủ" in text:

                room = "ngu"

                ctx.state.last_room = "ngu"

            elif "khách" in text or "khach" in text:

                room = "khach"

                ctx.state.last_room = "khach"

        if room:

            ctx.state.waiting_reduce_light_room = False

            ctx.state.pending_action = None
            # ==========================
            # PHÒNG NGỦ
            # ==========================

            if room == "ngu":

                current = ctx.db.reference("Light/Ngu").get() or 1

                new_level = max(1, current - 1)

                ctx.db.reference("Light/Ngu").set(new_level)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(f"Ngu:{new_level}\n".encode())

                speak("Đã giảm đèn phòng ngủ.", ctx.db)

            # ==========================
            # PHÒNG KHÁCH
            # ==========================

            else:

                current = ctx.db.reference("Light/Khach").get() or 1

                new_level = max(1, current - 1)

                ctx.db.reference("Light/Khach").set(new_level)

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(f"Khach:{new_level}\n".encode())

                speak("Đã giảm đèn phòng khách.", ctx.db)

            return True
        else:

            speak("Bạn muốn giảm đèn phòng khách hay phòng ngủ?", ctx.db)

            return True
    # ====================================
    # WAITING WINDOW ROOM
    # ====================================

    if ctx.state.waiting_window_room:
        if ("mở đi" in text or "ok" in text or "oke" in text) and ctx.state.last_room:

            room = "bed" if ctx.state.last_room == "ngu" else "living"
        # =================================
        # MEMORY ROOM
        # =================================

        if "phòng" not in text and ctx.state.last_room:

            room = "bed" if ctx.state.last_room == "ngu" else "living"

        if "ngủ" in text or "ngu" in text:

            room = "bed"

        elif "khách" in text or "khach" in text:

            room = "living"

        if room:

            ctx.state.waiting_window_room = False

            ctx.state.pending_action = None

            # ==========================
            # BEDROOM
            # ==========================

            if room == "bed":

                ctx.db.reference("Devices/Window_Bed").set("OPEN")

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(b"SET_WIN_BED:OPEN\n")

                speak("Đã mở cửa sổ phòng ngủ.", ctx.db)
                ctx.state.last_device = "window"
                ctx.state.last_room = "ngu"
                return True
            # ==========================
            # LIVING ROOM
            # ==========================

            else:

                ctx.db.reference("Devices/Window_Living").set("OPEN")

                if ctx.ser and ctx.ser.is_open:

                    ctx.ser.write(b"SET_WIN_LIVING:OPEN\n")

                speak("Đã mở cửa sổ phòng khách.", ctx.db)
                ctx.state.last_device = "window"
                ctx.state.last_room = "khach"
                return True

            return True

        else:

            speak("Bạn muốn mở cửa sổ phòng khách hay phòng ngủ?", ctx.db)

            return True

    # ====================================
    # CONFIRM AI ACTION
    # ====================================

    if ctx.state.pending_action:

        if any(
            x in text
            for x in [
                "ok",
                "oke",
                "đồng ý",
                "bật đi",
                "mở đi",
                "ừ",
                "yes",
                "giảm đi",
                "giảm nữa",
                "xuống đi",
            ]
        ):

            action = ctx.state.pending_action

            ctx.state.pending_action = None

            # ==========================
            # REDUCE FAN
            # ==========================

            if action == "reduce_fan":

                ctx.state.waiting_reduce_fan_room = True

                if ctx.state.last_room:

                    room_text = (
                        "phòng ngủ" if ctx.state.last_room == "ngu" else "phòng khách"
                    )

                    speak(f"Okii 😄 để tui giảm quạt {room_text} nha.", db)

                else:

                    speak("Bạn muốn giảm quạt phòng nào nè?", db)

                return True

            # ==========================
            # REDUCE LIGHT
            # ==========================

            elif action == "reduce_light":

                ctx.state.waiting_reduce_light_room = True

                if ctx.state.last_room:

                    room_text = (
                        "phòng ngủ" if ctx.state.last_room == "ngu" else "phòng khách"
                    )

                    speak(f"Okii 😄 để tui giảm đèn {room_text} nha.", db)

                else:

                    speak("Bạn muốn giảm đèn phòng nào nè?", db)

                return True

            # ==========================
            # WINDOW
            # ==========================

            if action == "window":

                ctx.state.waiting_window_room = True

                if ctx.state.last_room:

                    room_text = (
                        "phòng ngủ" if ctx.state.last_room == "ngu" else "phòng khách"
                    )

                    speak(f"Okii 😄 để tui mở cửa sổ {room_text} nha.", ctx.db)

                else:

                    speak("Bạn muốn mở cửa sổ phòng nào nè?", ctx.db)

                return True

            # ==========================
            # FAN
            # ==========================

            if action == "fan":
                ctx.state.waiting_fan_room = False

                db = ctx.db

                level = 3

                if "mức 1" in text:
                    level = 1

                elif "mức 2" in text:
                    level = 2

                elif "mức 3" in text:
                    level = 3

                room = ctx.state.last_room or "khach"

                # ==========================
                # PHÒNG NGỦ
                # ==========================

                if room == "ngu":

                    db.reference("Devices/Fan_Ngu").set(level)

                    if ctx.ser and ctx.ser.is_open:

                        ctx.ser.write(f"Fan_Ngu:{level}\n".encode())

                        speak(f"Đã bật quạt phòng ngủ mức {level}.", db)

                # ==========================
                # PHÒNG KHÁCH
                # ==========================

                else:

                    db.reference("Devices/Fan_Khach").set(level)

                    if ctx.ser and ctx.ser.is_open:

                        ctx.ser.write(f"Fan_Khach:{level}\n".encode())

                        speak(f"Đã bật quạt phòng khách mức {level}.", db)

                return True

            elif action == "light":
                ctx.state.waiting_light_room = False

                db = ctx.db

                level = 3

                if "mức 1" in text:
                    level = 1

                elif "mức 2" in text:
                    level = 2

                elif "mức 3" in text:
                    level = 3

                room = ctx.state.last_room or "khach"

                # ==========================
                # PHÒNG NGỦ
                # ==========================

                if room == "ngu":

                    db.reference("Light/Ngu").set(level)

                    if ctx.ser and ctx.ser.is_open:

                        ctx.ser.write(f"Ngu:{level}\n".encode())

                        speak(f"Đã bật đèn phòng ngủ mức {level}.", db)

                # ==========================
                # PHÒNG KHÁCH
                # ==========================

                else:

                    db.reference("Light/Khach").set(level)

                    if ctx.ser and ctx.ser.is_open:

                        ctx.ser.write(f"Khach:{level}\n".encode())

                        speak(f"Đã bật đèn phòng khách mức {level}.", db)

                return True

    print("NLU =", ctx.nlu)
    print(f"Xử lý lệnh: {text}")
    # ====================================
    # SHORT MEMORY
    # ====================================

    if "phòng khách" in text or "khách" in text:

        ctx.state.last_room = "khach"

    elif "phòng ngủ" in text or "ngủ" in text:

        ctx.state.last_room = "ngu"

    if "đèn" in text:

        ctx.state.last_device = "light"

    elif "quạt" in text:

        ctx.state.last_device = "fan"
    intent = ctx.nlu_context.get_intent(text)

    now = datetime.now()
    current_h = now.hour

    temp_val = db.reference("Sensors/Khach/Temp").get() or 30

    humi_val = db.reference("Sensors/Khach/Humi").get() or 70

    # ==================================================
    # AWAY MODE
    # ==================================================

    if intent == "AWAY":

        reset_all_devices(ctx)

        db.reference("System/SecurityMode").set(1)

        db.reference("Devices/Main_Door").set("CLOSE")

        db.reference("Devices/Window_Living").set("CLOSE")

        db.reference("Devices/Window_Bed").set("CLOSE")

        if ser and ser.is_open:
            ser.write(b"Main_Door:CLOSE\n")

        speak("Chế độ đi làm đã kích hoạt.", db)

        return True

    # ==================================================
    # SLEEP MODE
    # ==================================================

    if intent == "SLEEP":

        db.reference("Light/Khach").set(0)

        db.reference("Light/Ngu").set(1)

        db.reference("Devices/Fan_Ngu").set(2)

        db.reference("Devices/Fan_Khach").set(0)

        db.reference("Devices/Window_Living").set("CLOSE")

        db.reference("Devices/Window_Bed").set("CLOSE")

        if ser and ser.is_open:

            ser.write(b"Khach:0\n")
            ser.write(b"Ngu:1\n")
            ser.write(b"Fan_Ngu:2\n")

        db.reference("System/SecurityMode").set(1)

        speak("Chế độ đi ngủ kích hoạt.", db)

        return True

    # ==================================================
    # MOVIE MODE
    # ==================================================

    if intent == "MOVIE" or "xem phim" in text:

        db.reference("System/SecurityMode").set(0)

        db.reference("Light/Khach").set("MOVIE")

        db.reference("Devices/Fan_Khach").set(3)

        db.reference("Light/Ngu").set(0)

        db.reference("Devices/Fan_Ngu").set(0)

        db.reference("Devices/Window_Living").set("CLOSE")

        db.reference("Devices/Window_Bed").set("CLOSE")

        if ser and ser.is_open:
            ser.write(b"MOVIE:1\n")

        speak("Chế độ xem phim đã bật.", db)

        return True

    # ==================================================
    # PARTY MODE
    # ==================================================

    if intent == "PARTY" or "tiệc tùng" in text:

        db.reference("System/SecurityMode").set(0)

        db.reference("Light/Khach").set("PARTY")

        db.reference("Devices/Fan_Khach").set(3)

        db.reference("Light/Ngu").set(0)

        db.reference("Devices/Fan_Ngu").set(0)

        db.reference("Devices/Window_Living").set("OPEN")

        db.reference("Devices/Window_Bed").set("CLOSE")

        if ser and ser.is_open:
            ser.write(b"PARTY:1\n")

        speak("Chế độ tiệc tùng đã sẵn sàng.", db)

        return True

    # ==================================================
    # ĐÈN
    # ==================================================

    if "đèn" in text:

        # ==========================
        # BẬT
        # ==========================

        if "bật" in text or "mở" in text:

            level = 3

            if "mức 1" in text:
                level = 1

            elif "mức 2" in text:
                level = 2

            target = "Khach" if "khách" in text else "Ngu"

            db.reference(f"Light/{target}").set(level)
            ctx.state.last_device = "light"
            ctx.state.manual_override[f"Light/{target}"] = time.time()

            if ser and ser.is_open:

                ser.write(f"{target}:{level}\n".encode())

            # ==========================
            # AI LEARN
            # ==========================

            if target == "Khach":

                ctx.brain_light_khach.learn(current_h, temp_val, humi_val, level)

            else:

                ctx.brain_light_ngu.learn(current_h, temp_val, humi_val, level)

            threading.Thread(target=speak, args=("Đã bật đèn", db)).start()

            return True

        # ==========================
        # TẮT
        # ==========================

        elif "tắt" in text:

            target = "Khach" if "khách" in text else "Ngu"

            db.reference(f"Light/{target}").set(0)
            ctx.state.manual_override[f"Light/{target}"] = time.time()
            if ser and ser.is_open:

                ser.write(f"{target}:0\n".encode())

            # ==========================
            # AI LEARN
            # ==========================

            if target == "Khach":

                ctx.brain_light_khach.learn(current_h, temp_val, humi_val, 0)

            else:

                ctx.brain_light_ngu.learn(current_h, temp_val, humi_val, 0)

            speak("Đã tắt đèn", db)

            return True

    # ==================================================
    # QUẠT
    # ==================================================

    if "quạt" in text:

        # ==========================
        # BẬT
        # ==========================

        if "bật" in text or "mở" in text:

            speed = 3

            if "mức 1" in text:
                speed = 1

            elif "mức 2" in text:
                speed = 2

            target = "Fan_Khach" if "khách" in text else "Fan_Ngu"

            db.reference(f"Devices/{target}").set(speed)
            ctx.state.last_device = "fan"
            ctx.state.manual_override[f"Devices/{target}"] = time.time()
            if ser and ser.is_open:

                ser.write(f"{target}:{speed}\n".encode())

            # ==========================
            # AI LEARN
            # ==========================

            if target == "Fan_Khach":

                ctx.brain_fan_khach.learn(current_h, temp_val, humi_val, speed)

            else:

                ctx.brain_fan_ngu.learn(current_h, temp_val, humi_val, speed)

            if target == "Fan_Khach":

                ctx.state.last_room = "khach"

                speak("Đã bật quạt phòng khách.", db)

            else:

                ctx.state.last_room = "ngu"

                speak("Đã bật quạt phòng ngủ.", db)

            return True

        # ==========================
        # TẮT
        # ==========================

        elif "tắt" in text:

            target = "Fan_Khach" if "khách" in text else "Fan_Ngu"

            db.reference(f"Devices/{target}").set(0)
            ctx.state.manual_override[f"Devices/{target}"] = time.time()
            if ser and ser.is_open:

                ser.write(f"{target}:0\n".encode())

            # ==========================
            # AI LEARN
            # ==========================

            if target == "Fan_Khach":

                ctx.brain_fan_khach.learn(current_h, temp_val, humi_val, 0)

            else:

                ctx.brain_fan_ngu.learn(current_h, temp_val, humi_val, 0)

            speak("Đã tắt quạt", db)

            return True

    # ==================================================
    # CỬA SỔ
    # ==================================================

    if "cửa sổ" in text or "cua so" in text or "window" in text:
        # ==========================
        # MỞ
        # ==========================

        if "mở" in text or "open" in text:

            room = "bed" if ("ngủ" in text or "ngu" in text) else "living"

            # PHÒNG NGỦ

            if room == "bed":

                db.reference("Devices/Window_Bed").set("OPEN")
                if ser and ser.is_open:
                    ser.write(b"SET_WIN_BED:OPEN\n")
                speak("Đã mở cửa sổ phòng ngủ.", db)
                ctx.state.last_device = "window"
                ctx.state.last_room = "ngu"

            # PHÒNG KHÁCH

            else:

                db.reference("Devices/Window_Living").set("OPEN")

                if ser and ser.is_open:
                    ser.write(b"SET_WIN_LIVING:OPEN\n")
                speak("Đã mở cửa sổ phòng khách.", db)
                ctx.state.last_device = "window"
                ctx.state.last_room = "khach"
            return True

    # ==================================================
    # LẠNH
    # # ==================================================

    if "lạnh" in text:

        room = ctx.state.last_room or "khach"

        ctx.state.pending_action = "reduce_fan"

        room_text = "phòng ngủ" if room == "ngu" else "phòng khách"

        speak(f"Ui lạnh hả 😭 để tui giảm quạt {room_text} nha?", db)

        return True

    # ==================================================
    # ĐÓNG CỬA SỔ
    # ==================================================

    if "đóng cửa sổ" in text or ("đóng" in text and ctx.state.last_device == "window"):

        room = ctx.state.last_room or "khach"

        # ==========================
        # PHÒNG NGỦ
        # ==========================

        if room == "ngu":

            db.reference("Devices/Window_Bed").set("CLOSE")

            if ser and ser.is_open:

                ser.write(b"SET_WIN_BED:CLOSE\n")

            speak("Đã đóng cửa sổ phòng ngủ.", db)

        # ==========================
        # PHÒNG KHÁCH
        # ==========================

        else:

            db.reference("Devices/Window_Living").set("CLOSE")

            if ser and ser.is_open:

                ser.write(b"SET_WIN_LIVING:CLOSE\n")

            speak("Đã đóng cửa sổ phòng khách.", db)

        return True

    # ==================================================
    # SHORT MEMORY LEVEL
    # ==================================================

    if (
        "mức" in text
        or "giảm" in text
        or "tăng" in text
        or text.strip() in ["1", "2", "3", "1 đi", "2 đi", "3 đi"]
    ):

        room = ctx.state.last_room or "khach"

        device = ctx.state.last_device

        # ==========================
        # LEVEL
        # ==========================

        level = None

        if "1" in text:

            level = 1

        elif "2" in text:

            level = 2

        elif "3" in text:

            level = 3

        # ==========================
        # ĐÈN
        # ==========================

        if device == "light":

            target = "Khach" if room == "khach" else "Ngu"

            # GIẢM

            if "giảm" in text:

                current = db.reference(f"Light/{target}").get() or 1

                level = max(1, current - 1)

            # TĂNG

            elif "tăng" in text:

                current = db.reference(f"Light/{target}").get() or 1

                level = min(3, current + 1)

            if level:

                db.reference(f"Light/{target}").set(level)

                if ser and ser.is_open:

                    ser.write(f"{target}:{level}\n".encode())

                speak(f"Đã chỉnh đèn mức {level}.", db)

                return True

        # ==========================
        # QUẠT
        # ==========================

        elif device == "fan":

            target = "Fan_Khach" if room == "khach" else "Fan_Ngu"

            if "giảm" in text:

                current = db.reference(f"Devices/{target}").get() or 1

                level = max(1, current - 1)

            elif "tăng" in text:

                current = db.reference(f"Devices/{target}").get() or 1

                level = min(3, current + 1)

            if level:

                db.reference(f"Devices/{target}").set(level)

                if ser and ser.is_open:

                    ser.write(f"{target}:{level}\n".encode())

                speak(f"Đã chỉnh quạt mức {level}.", db)

                return True

    # ==================================================
    # SHORT MEMORY WINDOW CLOSE
    # ==================================================

    if ("đóng" in text or "close" in text) and ctx.state.last_device == "window":

        room = "bed" if ctx.state.last_room == "ngu" else "living"

        # ==========================
        # PHÒNG NGỦ
        # ==========================

        if room == "bed":

            db.reference("Devices/Window_Bed").set("CLOSE")

            if ser and ser.is_open:

                ser.write(b"SET_WIN_BED:CLOSE\n")

            speak("Đã đóng cửa sổ phòng ngủ.", db)

        # ==========================
        # PHÒNG KHÁCH
        # ==========================

        else:

            db.reference("Devices/Window_Living").set("CLOSE")

            if ser and ser.is_open:

                ser.write(b"SET_WIN_LIVING:CLOSE\n")

            speak("Đã đóng cửa sổ phòng khách.", db)

        return True

    # ==================================================
    # NHIỆT ĐỘ
    # ==================================================

    if "nhiệt độ" in text or "độ ẩm" in text or "thời tiết" in text:

        target = "Khach" if "khách" in text else "Ngu"

        room_name = "phòng khách" if target == "Khach" else "phòng ngủ"

        temp = db.reference(f"Sensors/{target}/Temp").get()

        humi = db.reference(f"Sensors/{target}/Humi").get()

        if temp is not None and humi is not None:

            speak(
                f"Tại {room_name}, "
                f"nhiệt độ là {temp} độ C "
                f"và độ ẩm là {humi} phần trăm.",
                db,
            )

        else:

            speak(f"Tôi chưa lấy được dữ liệu " f"cảm biến của {room_name}", db)

        return True

    # ==================================================
    # GIỜ
    # ==================================================

    if "mấy giờ" in text:

        t = datetime.now().strftime("%H:%M")

        speak(f"Bây giờ là {t}", db)

        return True

    global current_music
    # ====================================
    # PLAY MUSIC
    # ====================================

    if "lên nhạc" in text or "mở nhạc" in text:
        speak(
        "Oke 😄 để tui mở nhạc nha.",
        db
    )

        subprocess.run([
            "pkill",
            "-f",
            "mpg123"
        ])

        subprocess.Popen([
            "mpg123",
            MUSIC_LIST[current_music]
        ])

        return True

    # ====================================
    # STOP MUSIC
    # ====================================

    if "tắt nhạc" in text or "dừng nhạc" in text:

        subprocess.run([
            "pkill",
            "-f",
            "mpg123"
        ])

        speak(
            "Đã tắt nhạc.",
            db
        )

        return True
    
    if ("chuyển nhạc" in text or "bài tiếp theo" in text or "next" in text):
        current_music += 1

        if current_music >= len(MUSIC_LIST):
            current_music = 0

        subprocess.run([
            "pkill",
            "-f",
            "mpg123"
        ])

        subprocess.Popen([
            "mpg123",
            MUSIC_LIST[current_music]
        ])

        speak(
            "Đã chuyển bài.",
            db
        )

        return True

    # ==================================================
    # SMART HOME CONTEXT
    # ==================================================

    temp_khach = db.reference("Sensors/Khach/Temp").get() or 30

    humi_khach = db.reference("Sensors/Khach/Humi").get() or 70

    fan_khach = db.reference("Devices/Fan_Khach").get() or 0

    light_khach = db.reference("Light/Khach").get() or 0

    temp_ngu = db.reference("Sensors/Ngu/Temp").get() or 30

    humi_ngu = db.reference("Sensors/Ngu/Humi").get() or 70

    fan_ngu = db.reference("Devices/Fan_Ngu").get() or 0

    light_ngu = db.reference("Light/Ngu").get() or 0

    current_time = datetime.now().strftime("%H:%M")

    context = f"""

    Bây giờ là {current_time}

    ===== PHÒNG KHÁCH =====

    Nhiệt độ:
    {temp_khach} độ C

    Độ ẩm:
    {humi_khach} %

    Quạt:
    {'ĐANG BẬT' if fan_khach else 'ĐANG TẮT'}

    Đèn:
    {'ĐANG BẬT' if light_khach else 'ĐANG TẮT'}

    ===== PHÒNG NGỦ =====

    Nhiệt độ:
    {temp_ngu} độ C

    Độ ẩm:
    {humi_ngu} %

    Quạt:
    {'ĐANG BẬT' if fan_ngu else 'ĐANG TẮT'}

    Đèn:
    {'ĐANG BẬT' if light_ngu else 'ĐANG TẮT'}

    """

    # ==================================================
    # GPT
    # ==================================================
    ctx.state.chat_history.append({"role": "user", "content": text})

    reply = ask_gpt(text, context, ctx.state.chat_history[-4:])
    # =====================================
    # AI REDUCE FAN
    # =====================================

    if "giảm quạt" in reply.lower() or "quạt nhẹ hơn" in reply.lower():

        ctx.state.pending_action = "reduce_fan"

        ctx.state.waiting_reduce_fan_room = True

    # =====================================
    # AI REDUCE LIGHT
    # =====================================

    elif "giảm đèn" in reply.lower() or "giảm sáng" in reply.lower():

        ctx.state.pending_action = "reduce_light"

        ctx.state.waiting_reduce_light_room = True

    # =====================================
    # AI SUGGEST ACTION
    # =====================================

    reply_lower = reply.lower()

    # =========================
    # WINDOW
    # =========================

    if "mở cửa sổ" in reply_lower or "window" in reply_lower:

        ctx.state.pending_action = "window"
        ctx.state.waiting_window_room = True

    # =========================
    # LIGHT
    # =========================

    elif (
        (
            "bật đèn" in reply_lower
            or "mở đèn" in reply_lower
            or "turn on the light" in reply_lower
        )
        and "giảm" not in reply_lower
        and "tắt" not in reply_lower
    ):

        ctx.state.pending_action = "light"
        ctx.state.waiting_light_room = True

    # =========================
    # FAN
    # =========================

    elif (
        (
            "bật quạt" in reply_lower
            or "mở quạt" in reply_lower
            or "turn on the fan" in reply_lower
        )
        and "giảm" not in reply_lower
        and "tắt" not in reply_lower
    ):

        ctx.state.pending_action = "fan"
        ctx.state.waiting_fan_room = True

    # ==================================================
    # SPEAK
    # ==================================================

    speak(reply, db)

    ctx.state.chat_history.append({"role": "assistant", "content": reply})

    ctx.state.chat_history = ctx.state.chat_history[-10:]

    return True
    