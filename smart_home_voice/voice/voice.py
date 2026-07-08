import os
import threading
import time
import uuid

from firebase_admin import db
import pygame
from gtts import gTTS
import speech_recognition as sr

from ai.command import execute_command
from utils.constants import *

# =========================================================
# ===== STATE =====
# =========================================================

is_bot_speaking_flag = False
speak_lock = threading.Lock()
tts_cache = {}

# =========================================================
# ===== CHECK BOT SPEAKING =====
# =========================================================


def is_bot_speaking():

    with speak_lock:

        return is_bot_speaking_flag


# =========================================================
# ===== INIT AUDIO =====
# =========================================================


def init_audio():

    try:

        if not pygame.mixer.get_init():

            pygame.mixer.init()

        print("🔊 Audio: OK", flush=True)
        print("🔊 Mixer:", pygame.mixer.get_init(), flush=True)

    except Exception as e:

        print(f"❌ Audio lỗi: {e}", flush=True)

# =========================================================
# ===== SPEAK =====
# =========================================================


def speak(text, db):
    print(f"🔊 SPEAK CALLED: {text}", flush=True)
    global is_bot_speaking_flag

    with speak_lock:

        is_bot_speaking_flag = True

        filename = None

        try:

            print(f"Bot: {text}")

            db.reference("System/VoiceResponse").set(text)

            safe_text = text.strip().lower()

            if safe_text in tts_cache:

                filename = tts_cache[safe_text]

            else:

                filename = f"/tmp/voice_" f"{uuid.uuid4().hex}.mp3"

                tts = gTTS(text=text, lang="vi")

                tts.save(filename)

                tts_cache[safe_text] = filename
            time.sleep(0.3)
            print(f"🎵 Loading: {filename}", flush=True)
            pygame.mixer.music.load(filename)

            pygame.mixer.music.play()
            

            while pygame.mixer.music.get_busy():

                active = db.reference("System/Active").get()

                if not active:

                    pygame.mixer.music.stop()

                    break

                time.sleep(0.1)

            # =========================
            # CHỐNG ECHO
            # =========================

            time.sleep(0.7)

            db.reference("System/VoiceResponse").set("Đang chờ lệnh...")

        except Exception as e:

            print(f"❌ Lỗi âm thanh: {e}")

        finally:

            is_bot_speaking_flag = False


# =========================================================
# ===== VOICE MAIN =====
# =========================================================


def voice_main(ctx):

    r = sr.Recognizer()

    # =========================
    # TỐI ƯU MIC
    # =========================

    r.pause_threshold = 0.6

    r.non_speaking_duration = 0.4

    r.energy_threshold = 3000

    r.dynamic_energy_threshold = True
    r.operation_timeout = 3
    mic = sr.Microphone()

    # =========================
    # CALIBRATE MIC 1 LẦN
    # =========================

    with mic as source:

        print("🎤 Calibrating mic...")

        r.adjust_for_ambient_noise(source, duration=1)

    while True:

        try:

            # =========================
            # SYSTEM ACTIVE ?
            # =========================

            active = ctx.db.reference("System/Active").get()

            if not active:

                # print("😴 Voice sleeping...")

                time.sleep(1)

                continue

            # =========================
            # BOT ĐANG NÓI
            # =========================

            if is_bot_speaking():

                time.sleep(0.15)

                continue
            time.sleep(0.3)

            print("🎤 --- Đang đợi 'Alo' ---")

            # =========================
            # OPEN MIC
            # =========================

            with mic as source:

                audio = r.listen(source, timeout=None, phrase_time_limit=2)

            if is_bot_speaking():

                continue

            text = r.recognize_google(audio, language="vi-VN").lower()

            print(f"🗣️ Nghe: {text}")

            # =========================
            # WAKE WORD
            # =========================

            if VOICE_WAKE_WORD in text:

                speak("Tôi đây, bạn cần gì?", ctx.db)

                while is_bot_speaking():

                    time.sleep(0.1)
                last_active = time.time()
                # =========================
                # SESSION COMMAND
                # =========================

                while time.time() - last_active < 15:

                    try:

                        if is_bot_speaking():

                            time.sleep(0.5)

                            continue

                        remain = int(15 - (time.time() - last_active))

                        print(f"🎧 --- " f"Đang nghe lệnh " f"({remain}s) ---")

                        # =========================
                        # MIC MỚI
                        # =========================

                        with mic as source:

                            audio_cmd = r.listen(
                                source,
                                timeout=VOICE_TIMEOUT,
                                phrase_time_limit=VOICE_PHRASE_LIMIT,
                            )

                        if is_bot_speaking():

                            continue

                        cmd_text = r.recognize_google(
                            audio_cmd, language="vi-VN"
                        ).lower()

                        print(f"👉 Lệnh: " f"{cmd_text}")

                        # =========================
                        # CHỐNG LỆNH TRÙNG
                        # =========================

                        if (
                            hasattr(ctx.state, "last_cmd")
                            and ctx.state.last_cmd == cmd_text
                        ):

                            print("⚠️ Bỏ lệnh trùng")

                            continue

                        ctx.state.last_cmd = cmd_text

                        # =========================
                        # EXECUTE COMMAND
                        # =========================

                        if execute_command(ctx, cmd_text):

                            while is_bot_speaking():

                                time.sleep(0.1)

                            # =========================
                            # CHỜ MIC SẠCH
                            # =========================

                            time.sleep(0.8)

                            last_active = time.time()

                        else:

                            speak("Tôi chưa hiểu, bạn nói lại được không?", ctx.db)

                            while is_bot_speaking():

                                time.sleep(0.1)

                            time.sleep(2)

                    except sr.WaitTimeoutError:

                        continue

                    except Exception as e:

                        print("Voice cmd error:", e)

                        continue

                # =========================
                # GO SLEEP
                # =========================

                while is_bot_speaking():

                    time.sleep(0.1)

                speak("Tôi đi ngủ đây.", ctx.db)

        except sr.WaitTimeoutError:

            continue

        except Exception as e:

            print("Voice error:", e)

            continue
