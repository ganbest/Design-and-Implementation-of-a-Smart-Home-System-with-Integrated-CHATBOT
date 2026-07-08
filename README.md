## 🚀 Kiến Trúc Hệ Thống (System Architecture)

Hệ thống được thiết kế theo mô hình phân lớp xử lý song song nhằm tối ưu hóa băng thông và giảm thiểu độ trễ:

```mermaid
graph TD
    %% Định nghĩa các node chính
    OpenAI["OpenAI API (ChatGPT LLM)"]
    Pi5["Raspberry Pi 5<br>(Bộ xử lý trung tâm / Edge Core)"]
    App["Web / Android App<br>(Capacitor / Firebase RTDB)"]
    Cam["ESP32-CAM / Camera<br>(Trích xuất Face Embeddings)"]
    ESP32["ESP32 DevKitC<br>(Khối ngoại vi IoT Node)"]
    
    subgraph Sensors ["Khối Cảm Biến Đầu Vào"]
        DHT["DHT11 (Nhiệt độ/Độ ẩm)"]
        MQ2["MQ-2 (Khói/Khí Gas)"]
        PIR["HC-SR501 (Hồng ngoại)"]
        Rain["Cảm biến mưa"]
    end

    subgraph Actuators ["Khối Chấp Hành / Cảnh Báo"]
        Servo["Động cơ Servo (Cửa/Giàn phơi)"]
        Relay["Module Relay (Đèn chiếu sáng)"]
        Fan["Quạt DC (Transistor Đệm 2N2222)"]
        Buzzer["Buzzer / Đèn LED (Báo động)"]
    end

    %% Định nghĩa các kết nối và giao thức
    Pi5 <--> |"HTTPS API"| OpenAI
    App <--> |"WebSockets / Realtime DB"| Pi5
    Cam --> |"RTSP / CSI Stream"| Pi5
    Pi5 <--> |"UART Serial / MQTT"| ESP32
    
    ESP32 --- DHT
    ESP32 --- MQ2
    ESP32 --- PIR
    ESP32 --- Rain
    
    ESP32 --- Servo
    ESP32 --- Relay
    ESP32 --- Fan
    ESP32 --- Buzzer

    %% Định nghĩa style màu sắc cho trực quan
    style OpenAI fill:#10a37f,stroke:#fff,stroke-width:2px,color:#fff
    style Pi5 fill:#c51a4a,stroke:#fff,stroke-width:2px,color:#fff
    style App fill:#4285f4,stroke:#fff,stroke-width:2px,color:#fff
    style Cam fill:#e67e22,stroke:#fff,stroke-width:2px,color:#fff
    style ESP32 fill:#2ecc71,stroke:#fff,stroke-width:2px,color:#fff


---

## 🛠️ Phân Tích Chức Năng Kỹ Thuật Chi Tiết

### 1. Trợ Lý Giọng Nói AI & Xử Lý Ngôn Ngữ Tự Nhiên (NLP Chatbot)
* **Luồng xử lý (Pipeline):** `Audio Input` ➔ `Wake Word Detection ("NHÀ ƠI")` ➔ `Speech-to-Text (STT)` ➔ `Local Command Parsing` ➔ `OpenAI ChatGPT API` ➔ `Intent Extraction & Action Trigger` ➔ `Text-to-Speech (TTS)`.
* **Cơ chế hoạt động:** * Bộ xử lý trung tâm chạy một tiến trình lắng nghe cục bộ để nhận diện câu lệnh kích hoạt (Wake word).
  * Khi nhận được câu lệnh, dữ liệu âm thanh dạng sóng được số hóa và chuyển đổi thành văn bản. Nếu câu lệnh không khớp với danh sách cấu hình cứng cục bộ (ví dụ: *"Bật đèn"*), chuỗi văn bản sẽ được đóng gói dạng JSON kèm theo ngữ cảnh hệ thống (System Prompt) và gửi tới `OpenAI API`.
  * Phản hồi trả về từ GPT được bóc tách để lấy thực thể hành động (Action Entity) gửi xuống tầng phần cứng, đồng thời phần phản hồi bằng chữ được chuyển qua bộ Engine TTS để phát ra loa, tương tác thời gian thực với người dùng.

### 2. Tự Động Hóa Dựa Trên Học Máy (KNN Machine Learning)
* **Thuật toán áp dụng:** K-Nearest Neighbors (KNN) phân loại dữ liệu đa đặc trưng.
* **Tập dữ liệu đầu vào (Features):** `[Thời gian trong ngày, Nhiệt độ môi trường, Độ ẩm, Cường độ ánh sáng, Trạng thái thiết bị hiện tại]`.
* **Cơ chế học thói quen:**
  * Mỗi khi người dùng tương tác thay đổi trạng thái thiết bị hoặc theo chu kỳ thời gian nhất định, hệ thống tự động ghi nhật ký môi trường vào tệp cơ sở dữ liệu (`.xlsx` hoặc `CSV` cục bộ trên Edge).
  * Khi kích hoạt chế độ Auto-Learning, thuật toán KNN sẽ tính toán khoảng cách Euclidean giữa vector trạng thái môi trường hiện tại với các vector trong lịch sử quá khứ để tìm ra $K$ điểm lân cận gần nhất.
  * Hệ thống thực hiện bỏ phiếu (Majority Voting) để dự đoán xác suất hành vi của chủ nhà đối với từng thiết bị (Ví dụ: Dự đoán quạt nên bật ở mức 2 khi nhiệt độ phòng vượt quá 30°C vào lúc 21:00) và tự động thực thi lệnh không cần cấu hình bằng tay.

### 3. Kiểm Soát Ra Vào Bảo Mật Đa Lớp (Access Control & Smart Security)
* **Xác thực RFID:** Module `PN532` kết nối qua giao tiếp SPI/I2C với vi điều khiển. Đọc mã định danh UID của thẻ từ, đối sánh với mảng dữ liệu (White-list) được mã hóa trong EEPROM/Firebase để kích hoạt mở khóa bằng Servo.
* **Nhận diện khuôn mặt (FaceID) & Chống giả mạo (Anti-Spoofing):**
  * Luồng Stream từ `ESP32-CAM` / `Camera OV5640` được truyền về Pi 5. Hệ thống trích xuất đặc trưng khuôn mặt tạo thành các vector nhúng (Face Embeddings).
  * **Công nghệ chống giả mạo bằng ảnh in (Liveness Detection):** Thuật toán phân tích tần suất chớp mắt (Eye Blink Detection) dựa trên tỷ lệ khía cạnh mắt (Eye Aspect Ratio - EAR) thông qua các điểm mốc khuôn mặt (Facial Landmarks). Nếu tỷ lệ EAR giảm đột ngột dưới ngưỡng cấu hình trong một số khung hình liên tiếp, hệ thống xác nhận thực thể sống.
  * **Xử lý sự cố (Incident Management):** Khi phát hiện khuôn mặt lạ hoặc phát hiện hành vi gian lận bằng ảnh in, hệ thống lập tức khóa quyền truy cập, kích hoạt còi báo động `Buzzer`, đồng thời gửi tín nhắn cảnh báo kèm hình ảnh Snapshot của đối tượng qua `Telegram Bot API` dưới dạng một Inline Button tương tác (`[Cho phép mở cửa] / [Từ chối]`).

### 4. Giám Sát Môi Trường & Điều Khiển Ngoại Vi (IoT Nodes)
* **Tầng cảm biến:** `ESP32 DevKitC` thu thập dữ liệu liên tục từ các cảm biến: `DHT11` (Nhiệt độ/Độ ẩm), `MQ-2` (Nồng độ khí gas/Khói), `HC-SR501` (Chuyển động hồng ngoại), Cảm biến mưa.
* **Tầng chấp hành:** Điều khiển Động cơ Servo `SG90` (Điều khiển góc mở cửa/giàn phơi thông qua băm xung PWM), Hệ thống Relay kích hoạt đèn, Transistor đệm `2N2222` điều khiển tốc độ quạt DC bằng thay đổi chu kỳ xung.
* **Cơ chế an toàn phần cứng (Failsafe):** Tích hợp ngắt phần cứng (Hardware Interrupt) đối với cảm biến khí gas MQ-2. Khi nồng độ gas vượt ngưỡng nguy hiểm, ESP32 sẽ tự động hú còi báo động cục bộ và đóng van/mở cửa sổ mà không cần đợi lệnh từ Raspberry Pi 5 để đảm bảo an toàn tuyệt đối khi mất kết nối mạng.

### 5. Giao Diện Người Dùng & Đồng Bộ Thời Gian Thực (Data Synchronization)
* **Cơ sở dữ liệu:** Sử dụng `Firebase Realtime Database` (NoSQL) cấu trúc dạng cây JSON.
* **Cơ chế đồng bộ:** Áp dụng mô hình Publish/Subscribe thông qua kết nối WebSocket duy trì liên tục. Mọi thay đổi trạng thái cảm biến tại phần cứng được `PUSH` lên Firebase và ngay lập tức kích hoạt sự kiện `onValue` cập nhật giao diện người dùng trên Web/App Android (được đóng gói qua framework Capacitor) với độ trễ dưới < 200ms.

---

## 💾 Sơ Đồ Khối Luồng Dữ Liệu (Data Flow Diagram)

[Hardware Node: ESP32] ──(Dữ liệu cảm biến)──► [Firebase RTDB] ◄──(Đồng bộ)──► [Web/App Dashboard]
▲
│ (Lệnh điều khiển / PWM)
│
[Central Edge: Raspberry Pi 5] ◄──(Trigger)── [Telegram Bot API] ◄──(Cảnh báo / OTP)
▲
├─► [Local Machine Learning: KNN Algorithm] ➔ Tự động hóa thiết bị
└─► [AI Core: OpenAI API] ➔ Phân tích ngữ cảnh lệnh giọng nói tiếng Việt


---

## 🔧 Yêu Cầu Thành Phần Phần Cứng & Phần Mềm

### Phần cứng (Hardware)
* **Master Controller:** Raspberry Pi 5 (8GB RAM khuyên dùng)
* **Slave Controller:** ESP32 DevKitC V4, ESP32-CAM (hoặc ESP32-S3-WROOM)
* **Sensors:** DHT11, MQ-2, HC-SR501, Rain Sensor, PN532 RFID Reader.
* **Actuators:** Động cơ Servo SG90, Module Relay 4-Kênh, Còi Chíp 5V, Quạt DC 5V.
* **Power Supply:** Mạch hạ áp Buck DC-DC LM2596 (12V xuống 5V/3A & 3.3V).

### Phần mềm & Thư viện (Software Stack)
* **Firmware:** C++, Arduino IDE, FreeRTOS (Tối ưu hóa đa nhiệm trên ESP32).
* **Edge Core:** Python 3.10+, OpenCV, Dlib/Face_recognition, Sockets, Pandas, Scikit-learn (KNN model).
* **Cloud & Frontend:** Firebase SDK, HTML5/CSS3/JavaScript (ES6), Capacitor Core.
