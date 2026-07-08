import time
import threading
from voice.voice import is_bot_speaking
from services.telegram_service import send_telegram

def uart_worker(ctx):
    if ctx.ser is None:

        print("❌ UART unavailable")

        return
    ser = ctx.ser
    db = ctx.db
    kit = ctx.kit
    speak = ctx.speak
    print("🚀 [UART] Worker đang chạy, sẵn sàng nhận dữ liệu từ ESP32...")
    
    while True:
        active = ctx.db.reference(
            "System/Active"
            ).get()

        if not active:

            time.sleep(1)

            continue
        if ser.in_waiting > 0:
            try:
                line = (
                ser.readline()
                .decode(
                    'utf-8',
                    errors='ignore'
                )
                .strip()
)
                if not line or ":" not in line: 
                    continue


                parts = line.split(":")
                key = parts[0].replace("UPDATE_", "").strip()
                
                val_raw = parts[1].strip()

                try:

                    val = int(float(val_raw))

                except ValueError:

                    val = val_raw

                # SENSOR
                if "SENSOR_" in key:
                    s_info = key.split("_")
                    room = s_info[1]
                    stype = s_info[2]
                    db.reference(f'Sensors/{room}/{stype}').set(float(val))

                # LIGHT
                elif key in ["Khach", "Ngu"]:
                    db.reference(f'Light/{key}').set(val)
                elif key == "TOILET_L":
                    db.reference('Light/Toilet').set(val)

                # DEVICES
                elif key in ["Fan_Khach", "Fan_Ngu"]:
                    db.reference(f'Devices/{key}').set(val)
                elif key == "TOILET_F":
                    db.reference('Devices/Fan_Toilet').set(val)
                
                # DOOR/WINDOW
                elif "SET_DOOR" in key or "SET_WIN" in key:
                    name = key.replace("SET_", "")
                    db.reference(f'Devices/{name}').set("OPEN")

                # GAS
                elif key == "GAS":
                    db.reference('Security/Gas').set(val)
                    
                    if val == "DANGER":
                        print("🚨 CẢNH BÁO: Rò rỉ khí Gas!")
                        send_telegram("🚨 CẢNH BÁO: Rò rỉ khí Gas!")

                        if not is_bot_speaking():
                            threading.Thread(
                                target=speak,
                                args=("Cảnh báo rò rỉ khí ga. Đang mở toàn bộ cửa sổ.", db)
                            ).start()
                        
                        db.reference('Devices/Main_Door').set("OPEN")
                        db.reference('Devices/Window_Living').set("OPEN")
                        db.reference('Devices/Window_Bed').set("OPEN")
                        
                        if kit:
                            try:
                                kit.servo[0].angle = 90
                                kit.servo[3].angle = 0
                                kit.servo[1].angle = 0
                            except Exception as servo_err:
                                print(f"❌ Lỗi Servo: {servo_err}")

                    elif val == "SAFE":
                        print("✅ Gas đã an toàn.")
                        send_telegram("✅ Khí Gas đã an toàn.")

                # TROM
                elif key == "TROM":
                    db.reference('Security/Trom').set(val)
                    if val == 1:
                        print("🚨 CẢNH BÁO: Có trộm!")
                        send_telegram("🚨 CẢNH BÁO: Có trộm!")

            except Exception as e:
                print(f"❌ Lỗi xử lý dữ liệu UART: {e}")
        
        time.sleep(0.01)