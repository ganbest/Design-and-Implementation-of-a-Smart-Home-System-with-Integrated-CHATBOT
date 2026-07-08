import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import requests
import time
import os
import face_recognition
import numpy as np

# ── CẤU HÌNH (giống face_recognition_door.py) ─────────────────────────────────
ESP32_CAPTURE_URL = "http://172.20.10.4/capture"
KNOWN_FACES_DIR   = "known_faces"
NUM_PHOTOS        = 8      # số ảnh muốn chụp
DELAY             = 1.5    # giây giữa mỗi ảnh (để đổi góc mặt)

def main():
    if len(sys.argv) < 2:
        print("Cách dùng:  python enroll_face.py <tên>")
        print("Ví dụ:      python enroll_face.py TAN")
        return

    name = sys.argv[1]
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

    print(f"Sẽ chụp {NUM_PHOTOS} ảnh cho '{name}'.")
    print("Đứng trước camera, MỖI ẢNH đổi góc mặt một chút (thẳng, nghiêng trái/phải, ngẩng/cúi nhẹ).")
    print("Bắt đầu sau 3 giây...")
    time.sleep(3)

    saved = 0
    attempt = 0
    while saved < NUM_PHOTOS and attempt < NUM_PHOTOS * 3:
        attempt += 1
        try:
            raw = requests.get(ESP32_CAPTURE_URL, timeout=5).content
        except Exception as e:
            print(f"  [ERR] Lỗi lấy ảnh: {e}")
            time.sleep(1)
            continue

        # Kiểm tra có thấy mặt rõ không trước khi lưu
        arr = np.frombuffer(raw, dtype=np.uint8)
        import cv2
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        if not face_recognition.face_encodings(rgb):
            print(f"  [--] Ảnh {attempt}: không thấy mặt rõ, bỏ qua. Đưa mặt gần + đủ sáng.")
            time.sleep(DELAY)
            continue

        fname = os.path.join(KNOWN_FACES_DIR, f"{name}_{saved+1}.jpg")
        with open(fname, "wb") as f:
            f.write(raw)
        saved += 1
        print(f"  [OK] Đã lưu {fname}  ({saved}/{NUM_PHOTOS}) — đổi góc mặt!")
        time.sleep(DELAY)

    print(f"\nXong! Đã lưu {saved} ảnh cho '{name}' vào '{KNOWN_FACES_DIR}'.")
    print("Giờ chạy lại: python -u face_recognition_door.py")

if __name__ == "__main__":
    main()
