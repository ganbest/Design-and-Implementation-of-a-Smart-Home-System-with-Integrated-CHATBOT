import sys
import io
# Ep console Windows dung UTF-8 de in duoc tieng Viet
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import face_recognition
import requests
import numpy as np
import cv2
import os
import re
import time
import json
import winsound  # Windows beep - thay bằng playsound nếu cần

ESP32_CAPTURE_URL = "http://172.20.10.4/capture"
ESP32_S3_URL      = "http://172.20.10.4"
KNOWN_FACES_DIR   = "known_faces"
TOLERANCE         = 0.5
CHECK_INTERVAL    = 2
DOOR_OPEN_SECONDS = 5   # mở cửa bao lâu rồi tự đóng

# ── CHỐNG GIẢ MẠO BẰNG ẢNH (liveness - bắt chớp mắt) ──────────────────────────
LIVENESS_TIMEOUT = 8      # giây chờ người dùng chớp mắt
EAR_OPEN         = 0.23   # mắt coi là MỞ khi EAR > ngưỡng này
EAR_CLOSED       = 0.16   # mắt coi là NHẮM khi EAR < ngưỡng này
                          # phải thấy CẢ mở lẫn nhắm mới là người thật chớp mắt
                          # (ảnh mắt-mở không bao giờ tụt xuống mức nhắm)

# ── CẤU HÌNH FIREBASE (để ra lệnh cho Pi5 mở cửa) ─────────────────────────────
# Dùng chung database + key với project Pi (smart_home_voice).
# Ghi Devices/Main_Door = "OPEN" -> Pi tự mở servo cửa; "CLOSE" -> đóng.
FIREBASE_KEY = r"C:\Users\TAN\Downloads\serviceAccountKey.json"
FIREBASE_URL = "https://datn-bff1f-default-rtdb.asia-southeast1.firebasedatabase.app"

_fb_db = None
def init_firebase():
    global _fb_db
    try:
        import firebase_admin
        from firebase_admin import credentials, db as fb_db
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_KEY)
            firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_URL})
        _fb_db = fb_db
        print("✅ Firebase: kết nối OK (sẽ ra lệnh mở cửa cho Pi)")
    except Exception as e:
        print(f"⚠️ Firebase TẮT ({e}) — sẽ không mở được cửa thật, chỉ báo TFT.")
        _fb_db = None

def open_door_firebase(name="Khach"):
    """Ra lệnh cho Pi5 mở cửa (servo) qua Firebase, tự đóng sau DOOR_OPEN_SECONDS."""
    if _fb_db is None:
        print("  [!] Firebase chưa kết nối -> bỏ qua mở cửa thật.")
        return
    try:
        now = time.strftime("%H:%M:%S %d/%m/%Y")
        _fb_db.reference("Devices/Main_Door").set("OPEN")
        _fb_db.reference("Access_Logs").push({
            "name": name,
            "time": now,
            "status": "Mở bằng nhận diện khuôn mặt",
        })
        print(f"  🔓 Đã ra lệnh Pi MỞ CỬA cho {name} (tự đóng sau {DOOR_OPEN_SECONDS}s)")
        tg_send_text(f"🔓 Cửa đã MỞ cho {name}\n🕒 {now}")

        def auto_close():
            time.sleep(DOOR_OPEN_SECONDS)
            try:
                _fb_db.reference("Devices/Main_Door").set("CLOSE")
                print("  🔒 Đã ra lệnh Pi ĐÓNG CỬA.")
            except Exception as e:
                print(f"  [WARN] Đóng cửa lỗi: {e}")
        import threading
        threading.Thread(target=auto_close, daemon=True).start()
    except Exception as e:
        print(f"  [WARN] Mở cửa Firebase lỗi: {e}")

# ── CẤU HÌNH TELEGRAM ─────────────────────────────────────────────────────────
# 1. Mở Telegram, tìm @BotFather, gõ /newbot -> lấy TOKEN dán vào đây
# 2. Lấy CHAT_ID: nhắn 1 tin cho bot, rồi mở trình duyệt:
#    https://api.telegram.org/bot<TOKEN>/getUpdates -> tìm "chat":{"id":...}
TELEGRAM_TOKEN    = "8829379157:AAFNaNrTtDjQCuN7si5wCxkLg09fxyO54Tk"
TELEGRAM_CHAT_ID  = "5837013272"
APPROVAL_TIMEOUT  = 30   # giây chờ bạn bấm nút trên điện thoại

_tg_offset = 0  # theo dõi update đã xử lý

def tg_enabled():
    return TELEGRAM_TOKEN != "PASTE_TOKEN_HERE" and TELEGRAM_CHAT_ID != "PASTE_CHAT_ID_HERE"

def tg_api(method, **kwargs):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
    return requests.post(url, timeout=20, **kwargs)

def tg_send_text(text):
    """Gửi 1 tin nhắn chữ về Telegram."""
    if not tg_enabled():
        return
    try:
        tg_api("sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
    except Exception as e:
        print(f"  [WARN] tg_send_text: {e}")

def tg_send_photo(jpeg_bytes, caption=""):
    """Gửi 1 ảnh kèm chú thích về Telegram (không có nút)."""
    if not tg_enabled():
        return
    if not jpeg_bytes:
        tg_send_text(caption)
        return
    try:
        files = {"photo": ("alert.jpg", jpeg_bytes, "image/jpeg")}
        tg_api("sendPhoto", files=files, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption})
    except Exception as e:
        print(f"  [WARN] tg_send_photo: {e}")

def tg_flush():
    """Bỏ qua các tin nhắn/nút cũ trước khi hỏi mới."""
    global _tg_offset
    try:
        r = tg_api("getUpdates", data={"timeout": 0}).json()
        for upd in r.get("result", []):
            _tg_offset = upd["update_id"] + 1
    except Exception as e:
        print(f"  [WARN] tg_flush: {e}")

def send_approval_request(jpeg_bytes):
    """Gửi ảnh người lạ + 2 nút Mở cửa / Từ chối."""
    keyboard = {"inline_keyboard": [[
        {"text": "✅ Mở cửa",  "callback_data": "open"},
        {"text": "❌ Từ chối", "callback_data": "deny"},
    ]]}
    files = {"photo": ("face.jpg", jpeg_bytes, "image/jpeg")}
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "caption": "🔔 Có người LẠ trước cửa! Cho vào không?",
        "reply_markup": json.dumps(keyboard),
    }
    try:
        tg_api("sendPhoto", files=files, data=data)
        print("  [TG] Đã gửi ảnh + nút về điện thoại, đang chờ bạn bấm...")
    except Exception as e:
        print(f"  [WARN] Gửi Telegram lỗi: {e}")

def wait_for_decision(timeout=APPROVAL_TIMEOUT):
    """Chờ bạn bấm nút. Trả 'open' / 'deny' / None (hết giờ)."""
    global _tg_offset
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = tg_api("getUpdates", data={"offset": _tg_offset, "timeout": 5}).json()
        except Exception as e:
            print(f"  [WARN] getUpdates: {e}")
            continue
        for upd in r.get("result", []):
            _tg_offset = upd["update_id"] + 1
            cq = upd.get("callback_query")
            if cq and "data" in cq:
                decision = cq["data"]
                try:
                    tg_api("answerCallbackQuery", data={
                        "callback_query_id": cq["id"],
                        "text": "✅ Đã mở cửa!" if decision == "open" else "❌ Đã từ chối.",
                    })
                except Exception:
                    pass
                return decision
    return None

# ── Load ảnh đã biết ──────────────────────────────────────────────────────────
def clean_name(filename):
    """Bỏ phần đánh số để gộp nhiều ảnh cùng người: 'TAN (2)','TAN_3','TAN2' -> 'TAN'."""
    base = os.path.splitext(filename)[0]
    cleaned = re.sub(r"[\s_\-]*\(?\d+\)?$", "", base).strip()
    return cleaned or base

def load_known_faces(folder):
    encodings = []
    names = []
    for filename in os.listdir(folder):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(folder, filename)
        img = face_recognition.load_image_file(path)
        found = face_recognition.face_encodings(img)
        if found:
            name = clean_name(filename)
            encodings.append(found[0])
            names.append(name)
            print(f"  [OK] Đã load: {filename} -> {name}")
        else:
            print(f"  [!!] Không tìm thấy mặt trong: {filename}")
    uniq = sorted(set(names))
    print(f"  => {len(encodings)} ảnh, {len(uniq)} người: {uniq}")
    return encodings, names

# ── Lấy ảnh từ ESP32-CAM ─────────────────────────────────────────────────────
def capture_from_esp32():
    """Trả về (frame_RGB, jpeg_bytes_goc). Lỗi -> (None, None)."""
    try:
        resp = requests.get(ESP32_CAPTURE_URL, timeout=5)
        raw = resp.content
        img_array = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), raw
    except Exception as e:
        print(f"  [ERR] Lỗi lấy ảnh: {e}")
        return None, None

# ── Gửi lệnh đến ESP32-S3 ────────────────────────────────────────────────────
def notify_s3(endpoint, params=None):
    try:
        requests.get(f"{ESP32_S3_URL}{endpoint}", params=params, timeout=3)
    except Exception as e:
        print(f"  [WARN] Không gửi được tới ESP32-S3: {e}")

# ── Cảnh báo ─────────────────────────────────────────────────────────────────
def alarm():
    print("  *** CẢNH BÁO: Khuôn mặt không được phép! ***")
    notify_s3("/alert")
    for _ in range(3):
        winsound.Beep(1000, 300)
        time.sleep(0.1)

# ── Mở cửa ───────────────────────────────────────────────────────────────────
# ── Tính độ mở mắt (Eye Aspect Ratio) ────────────────────────────────────────
def eye_aspect_ratio(eye):
    p = [np.array(pt, dtype=float) for pt in eye]
    A = np.linalg.norm(p[1] - p[5])
    B = np.linalg.norm(p[2] - p[4])
    C = np.linalg.norm(p[0] - p[3])
    return (A + B) / (2.0 * C) if C > 0 else 0.0

# ── Kiểm tra người sống: phải chớp mắt mới qua ───────────────────────────────
def check_liveness_blink(timeout=LIVENESS_TIMEOUT):
    print(f"  👁️  Hãy NHẮM MẮT rồi MỞ vài lần trong {timeout}s (đưa mặt gần camera)...")
    deadline = time.time() + timeout
    saw_open = False
    saw_closed = False
    ears = []
    while time.time() < deadline:
        frame, _ = capture_from_esp32()
        if frame is None:
            continue
        landmarks = face_recognition.face_landmarks(frame)
        if not landmarks:
            continue
        lm = landmarks[0]
        if "left_eye" not in lm or "right_eye" not in lm:
            continue
        ear = (eye_aspect_ratio(lm["left_eye"]) + eye_aspect_ratio(lm["right_eye"])) / 2.0
        ears.append(ear)
        state = "MO " if ear > EAR_OPEN else ("NHAM" if ear < EAR_CLOSED else "....")
        print(f"     EAR = {ear:.3f}  [{state}]")
        if ear > EAR_OPEN:
            saw_open = True
        if ear < EAR_CLOSED:
            saw_closed = True
        # Người thật: mắt phải vừa MỞ vừa NHẮM. Ảnh mắt-mở: không bao giờ NHẮM.
        if saw_open and saw_closed:
            print("  ✅ Thấy mắt MỞ và NHẮM -> NGƯỜI THẬT")
            return True
    if ears:
        print(f"  ❌ Không đủ (EAR: thấp nhất {min(ears):.3f}, cao nhất {max(ears):.3f}; "
              f"cần tụt dưới {EAR_CLOSED} và vượt {EAR_OPEN}) -> nghi ẢNH GIẢ.")
    else:
        print("  ❌ Không bắt được mắt (mặt xa/mờ?) -> nghi ẢNH GIẢ.")
    return False

def open_door(name):
    print(f"  >>> CHÀO {name.upper()}! Mở cửa...")
    notify_s3("/open", {"name": name})   # hiện mặt + tên lên TFT của ESP32-CAM
    open_door_firebase(name)             # ra lệnh Pi mở servo cửa thật

# ── Xử lý người lạ: hỏi điện thoại qua Telegram ──────────────────────────────
def handle_stranger(jpeg_bytes):
    print("  [!] Phát hiện người LẠ.")

    # Không cấu hình Telegram -> chỉ cảnh báo tại chỗ
    if not tg_enabled() or jpeg_bytes is None:
        alarm()
        return

    # Gửi ảnh về điện thoại và chờ bạn bấm nút
    tg_flush()
    send_approval_request(jpeg_bytes)
    decision = wait_for_decision(APPROVAL_TIMEOUT)

    if decision == "open":
        print("  >>> Bạn ĐỒNG Ý mở cửa cho khách.")
        notify_s3("/open", {"name": "Khach"})   # hiện lên TFT
        open_door_firebase("Khach")             # ra lệnh Pi mở servo cửa thật
    elif decision == "deny":
        print("  >>> Bạn TỪ CHỐI.")
        alarm()
    else:
        print("  >>> Hết giờ chờ, không phản hồi -> từ chối an toàn.")
        alarm()

# ── Main loop ────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        print(f"Tạo thư mục '{KNOWN_FACES_DIR}' — hãy bỏ ảnh khuôn mặt vào đó rồi chạy lại.")
        return

    init_firebase()   # kết nối Firebase để ra lệnh mở cửa cho Pi

    print("Đang load khuôn mặt đã biết...")
    known_encodings, known_names = load_known_faces(KNOWN_FACES_DIR)
    if not known_encodings:
        print("Chưa có ảnh nào trong known_faces! Hãy thêm ảnh vào.")
        return

    print(f"\nSẵn sàng — đã load {len(known_encodings)} khuôn mặt: {known_names}")
    if tg_enabled():
        print("Telegram: BẬT — người lạ sẽ gửi ảnh về điện thoại để bạn duyệt.")
    else:
        print("Telegram: TẮT (chưa điền TOKEN/CHAT_ID) — người lạ chỉ kêu cảnh báo tại chỗ.")
    print("Bắt đầu nhận diện... (Ctrl+C để dừng)\n")

    cooldown = 0  # tránh spam mở cửa / cảnh báo liên tục

    while True:
        if cooldown > 0:
            cooldown -= 1
            time.sleep(1)
            continue

        frame, raw_jpeg = capture_from_esp32()
        if frame is None:
            time.sleep(CHECK_INTERVAL)
            continue

        face_locations = face_recognition.face_locations(frame)
        if not face_locations:
            print("  [--] Không phát hiện khuôn mặt")
            time.sleep(CHECK_INTERVAL)
            continue

        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for encoding in face_encodings:
            distances = face_recognition.face_distance(known_encodings, encoding)
            best_idx = np.argmin(distances)
            best_dist = distances[best_idx]

            print(f"  [?] Khoảng cách gần nhất: {best_dist:.3f} (ngưỡng {TOLERANCE})")

            if best_dist <= TOLERANCE:
                # Người quen -> KIỂM TRA CHỚP MẮT chống ảnh giả -> mới mở cửa
                name = known_names[best_idx]
                print(f"  [✓] Nhận ra {name} -> kiểm tra chống giả mạo...")
                if check_liveness_blink():
                    open_door(name)
                else:
                    print("  🚫 NGHI GIẢ MẠO BẰNG ẢNH! Không mở cửa.")
                    notify_s3("/alert")                       # TFT cảnh báo đỏ
                    _, spoof_jpeg = capture_from_esp32()      # chụp ảnh kẻ giả mạo
                    cap = (f"🚫 CẢNH BÁO: có người dùng ẢNH của {name} để mở cửa!\n"
                           f"🕒 {time.strftime('%H:%M:%S %d/%m/%Y')}")
                    tg_send_photo(spoof_jpeg, cap)            # gửi kèm ảnh về Telegram
                cooldown = 5
            else:
                # Người lạ -> hỏi điện thoại qua Telegram
                handle_stranger(raw_jpeg)
                cooldown = 30   # nghỉ 30s, tránh spam khi người lạ đứng lì

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
