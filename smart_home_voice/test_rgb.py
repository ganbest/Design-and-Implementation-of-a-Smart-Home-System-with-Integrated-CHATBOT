import time
from adafruit_servokit import ServoKit

# Khởi tạo PCA9685
try:
    kit = ServoKit(channels=16)
    print("--- Đã kết nối PCA9685 thành công ---")
except Exception as e:
    print(f"Lỗi kết nối PCA9685: {e}")
    exit()

def test_all_ports():
    # Danh sách các cổng muốn test
    ports = [0, 1, 2, 3]
    
    print("Bắt đầu quy trình kiểm tra 4 cổng...")
    print("Lưu ý: Quan sát xem Servo nào nhúc nhích.")

    for port in ports:
        try:
            print(f"\n[Đang test CỔNG {port}]")
            
            # Quay đến 90 độ
            kit.servo[port].angle = 90
            print(f"Cổng {port}: Đang MỞ (90 độ)")
            time.sleep(1.5)
            
            # Quay về 0 độ
            kit.servo[port].angle = 0
            print(f"Cổng {port}: Đang ĐÓNG (0 độ)")
            time.sleep(1)
            
        except Exception as e:
            print(f"Cổng {port} gặp lỗi: {e}")

    print("\n--- Kiểm tra kết thúc! ---")
    print("Ông xác nhận lại: Cổng nào KHÔNG quay?")

if __name__ == "__main__":
    test_all_ports()