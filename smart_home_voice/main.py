# main.py

# =========================================================
# ===== SYSTEM =====
# =========================================================
import time
import threading
import os
os.environ["ALSA_LOGLEVEL"] = "0"
import sys
sys.stdout.reconfigure(line_buffering=True)
from gpiozero import Button

# =========================================================
# ===== CORE =====
# =========================================================

from core.context import AppContext
from core.state import SystemState

# =========================================================
# ===== SERVICES =====
# =========================================================

from services.firebase import db
from services.uart import init_uart
from services.servo import init_servo
from services.pn532_service import init_pn532

# =========================================================
# ===== AI =====
# =========================================================

from ai.brain import SmartBrain
from ai.nlu import init_nlu
from workers.ai_worker import ai_control_worker
from ai.ngucanh import IntentClassifier

# =========================================================
# ===== VOICE =====
# =========================================================

from voice.voice import speak, init_audio, voice_main, is_bot_speaking

# =========================================================
# ===== WORKERS =====
# =========================================================

from workers.uart_worker import uart_worker
from workers.rfid_worker import rfid_worker
from workers.rain import rain_sensor_worker
from workers.firebase_listener import firebase_listener
from workers.security_worker import start_security_listener
from workers.login_listener import login_listener
from workers.mobile_voice_worker import mobile_voice_worker

# =========================================================
# ===== CONSTANTS =====
# =========================================================

from utils.constants import *

# =========================================================
# ===== INIT =====
# =========================================================

print("🚀 SYSTEM STARTING...")

db.reference("System/Active").set(False)


# ===== UART =====
ser = init_uart()

# ===== AUDIO =====
init_audio()

# ===== AI =====

brain_light_khach = SmartBrain("light_khach.csv")

brain_fan_khach = SmartBrain("fan_khach.csv")

brain_light_ngu = SmartBrain("light_ngu.csv")

brain_fan_ngu = SmartBrain("fan_ngu.csv")

nlu = init_nlu()

# ===== SERVO =====
kit = init_servo()

# ===== PN532 =====
pn532 = init_pn532()
pn532_lock = threading.Lock()
# ===== RAIN SENSOR =====
try:

    rain_sensor = Button(RAIN_PIN, pull_up=True)

    print("🌧️ Rain sensor OK")

except Exception as e:

    rain_sensor = None

    print("❌ Rain sensor lỗi:", e)


# =========================================================
# ===== STATE =====
# =========================================================

state = SystemState()


# =========================================================
# ===== CREATE CONTEXT =====
# =========================================================

ctx = AppContext(
    db=db,
    ser=ser,
    kit=kit,
    speak=speak,
    nlu=nlu,
    pn532=pn532,
    pn532_lock=pn532_lock,
    rain_sensor=rain_sensor,
    is_bot_speaking=is_bot_speaking,
    state=state,
    brain_light_khach=brain_light_khach,
    brain_fan_khach=brain_fan_khach,
    brain_light_ngu=brain_light_ngu,
    brain_fan_ngu=brain_fan_ngu,
    
)

ctx.nlu_context = IntentClassifier()
# =========================================================
# ===== START WORKERS =====
# =========================================================

threading.Thread(target=uart_worker, args=(ctx,), daemon=True).start()

print("✅ UART worker started", flush=True)


# ===== RFID =====
if pn532 is not None:

    threading.Thread(target=rfid_worker, args=(ctx, pn532), daemon=True).start()

    print("✅ RFID worker started", flush=True)

else:

    print("⚠️ RFID skipped", flush=True)


# ===== RAIN =====
threading.Thread(target=rain_sensor_worker, args=(ctx,), daemon=True).start()

print("✅ Rain worker started", flush=True)


# ===== FIREBASE =====
threading.Thread(target=firebase_listener, args=(ctx,), daemon=True).start()

print("✅ Firebase listener started", flush=True)


# ===== SECURITY =====
threading.Thread(target=start_security_listener, args=(ctx,), daemon=True).start()

print("✅ Security worker started", flush=True)


# ===== VOICE =====
threading.Thread(target=voice_main, args=(ctx,), daemon=True).start()

print("✅ Voice worker started", flush=True)

# ===== AI WORKER =====

threading.Thread(target=ai_control_worker, args=(ctx,), daemon=True).start()

print("✅ AI worker started", flush=True)

threading.Thread(target=mobile_voice_worker, args=(ctx,), daemon=True).start()

print("✅ Mobile worker started", flush=True)

# ===== LOGIN LISTENER =====

threading.Thread(target=login_listener, args=(ctx,), daemon=True).start()

print("✅ Login listener started", flush=True)

# =========================================================
# ===== SYSTEM READY =====
# =========================================================

state.system_ready = True

print("🔥 SYSTEM READY 🔥", flush=True)


# =========================================================
# ===== KEEP ALIVE =====
# =========================================================

while True:
    time.sleep(1)