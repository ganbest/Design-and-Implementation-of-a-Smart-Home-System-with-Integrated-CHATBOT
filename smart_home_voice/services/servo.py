# services/servo.py

from adafruit_servokit import ServoKit


def init_servo():

    try:
        kit = ServoKit(channels=16)

        print("✅ Servo PCA9685 OK")

        return kit

    except Exception as e:

        print("❌ Servo init lỗi:", e)

        return None


def update_window_physical(ctx, key, value):

    kit = ctx.kit

    try:

        val = str(value).upper()
        is_open = val in ["1", "OPEN"]
        channel = -1

        if "Main_Door" in key:
            channel = 0
            angle = 90 if is_open else 0  # Giữ nguyên: Mở = 90, Đóng = 0
        elif "Window_Living" in key:
            channel = 3
            angle = 0 if is_open else 90
        elif "Window_Bed" in key:
            channel = 1
            angle = 0 if is_open else 90

        elif "Laundry" in key:
            channel = 2
            angle = 90 if is_open else 0

        if channel != -1 and kit:

            kit.servo[channel].angle = angle

            print(f"🔄 Servo {channel} -> {angle}")

    except Exception as e:

        print("❌ Servo error:", e)