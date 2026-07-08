class IntentClassifier:
    def __init__(self):
        pass

    def get_intent(self, text):
        text = text.lower()
        
        # --- LOGIC CŨ CỦA BẠN (GIỮ NGUYÊN) ---
        if "đi ngủ" in text: return "SLEEP"
        if "đi làm" in text or "rời nhà" in text: return "AWAY"
        if "xem phim" in text: return "MOVIE"
        if "mở tiệc" in text or "party" in text: return "PARTY"
        
        # --- BỔ SUNG THÊM ĐỂ KHỚP VỚI MAIN.PY ---
        
        # Nhận diện lệnh hỏi giờ
        if "mấy giờ" in text or "thời gian" in text: 
            return "TIME"
            
        # Nhận diện lệnh khẩn cấp/nguy hiểm
        if "nguy hiểm" in text or "mở hết cửa" in text or "cứu hộ" in text: 
            return "EMERGENCY"

        return "NORMAL"