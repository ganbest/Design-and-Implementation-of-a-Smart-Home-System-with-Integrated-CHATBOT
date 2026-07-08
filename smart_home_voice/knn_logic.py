import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import os

class SmartBrain:
    def __init__(self, file_path='habit_data.csv', default_level=0):
        self.file_path = file_path
        self.default_level = default_level # Thêm biến này để làm mồi chuẩn hơn cho từng thiết bị
        self.model = KNeighborsClassifier(n_neighbors=5) 
        self.X_train = []
        self.y_train = []
        self.load_data()
        self.file_path = file_path

    def load_data(self):
        """Tải dữ liệu thói quen từ file CSV hoặc dùng dữ liệu mồi"""
        if os.path.exists(self.file_path):
            try:
                df = pd.read_csv(self.file_path)
                # ĐÚNG VỚI FILE CSV CỦA ÔNG: Cột cuối cùng tên là 'level'
                self.X_train = df[['hour', 'temp', 'humi']].values.tolist()
                self.y_train = df['level'].values.tolist()
                print(f"🧠 AI: Đã tải {len(self.X_train)} mẫu dữ liệu từ file.")
            except Exception as e:
                print(f"❌ Lỗi đọc file CSV: {e}")
                self._load_default_data()
        else:
            self._load_default_data()
        
        self.update_model()

    def _load_default_data(self):
        """Dữ liệu mặc định ban đầu nếu chưa có file thói quen"""
        print("🧠 AI: Khởi tạo dữ liệu mặc định ban đầu.")
        self.X_train = [[22, 25, 60], [23, 24, 65], [0, 24, 70], [19, 28, 55], [12, 32, 40]]
        self.y_train = [1, 1, 0, 3, 0]

    def update_model(self):
        """Huấn luyện lại mô hình với dữ liệu mới nhất"""
        # Đảm bảo số lượng mẫu phải lớn hơn hoặc bằng n_neighbors (5)
        if len(self.X_train) >= 5: 
            try:
                self.model.fit(self.X_train, self.y_train)
            except Exception as e:
                print(f"❌ Lỗi khi train model: {e}")
        else:
            # Nếu chưa đủ 5 mẫu thì tạm thời dùng k bằng số mẫu hiện có để không bị lỗi crash
            try:
                self.model.n_neighbors = max(1, len(self.X_train))
                self.model.fit(self.X_train, self.y_train)
            except Exception as e:
                print(f"❌ Lỗi khi train model (fallback k): {e}")

    def learn(self, hour, temp, humi, level):
        """Lưu thói quen mới vào bộ nhớ và cập nhật file CSV"""
        self.X_train.append([hour, temp, humi])
        self.y_train.append(level)
        
        # Cập nhật model ngay lập tức
        self.update_model()

        # Lưu xuống file CSV để không bị mất khi tắt nguồn
        try:
            df = pd.DataFrame(self.X_train, columns=['hour', 'temp', 'humi'])
            df['level'] = self.y_train
            df.to_csv(self.file_path, index=False)
            print(f"🧠 AI: Đã học mẫu mới tại {hour}h - {temp} độ. Tổng: {len(self.X_train)}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu CSV: {e}")

    def predict(self, hour, temp, humi):
        """Dự đoán mức thiết bị (0, 1, 2, 3) dựa trên ngữ cảnh"""
        try:
            prediction = self.model.predict([[hour, temp, humi]])
            return int(prediction[0])
        except:
            return 0 # Mặc định tắt nếu có lỗi

    def get_probability(self, hour, temp, humi):
        """Tính xác suất (%) của hành động để hiển thị chuẩn xác lên Web"""
        try:
            # Lấy danh sách các nhãn mà mô hình đã học (Ví dụ: [0, 1, 3])
            classes = self.model.classes_
            
            # Tính xác suất của từng nhãn
            probs = self.model.predict_proba([[hour, temp, humi]])[0]
            
            # Tìm nhãn có xác suất cao nhất
            max_prob_index = np.argmax(probs)
            best_class = classes[max_prob_index]
            prob_percent = int(probs[max_prob_index] * 100)

            # --- LOGIC ĐỂ HIỂN THỊ LÊN WEB CHUẨN ---
            # Nếu AI dự đoán là Tắt (0) -> Lấy 100% trừ đi để ra số thấp (AI không muốn bật)
            if best_class == 0:
                return 100 - prob_percent
            
            # Nếu AI dự đoán là Bật (1, 2, 3) -> Trả về số % cao
            return prob_percent
        except:
            return 50 # Trả về 50% nếu có lỗi hoặc chưa đủ dữ liệu