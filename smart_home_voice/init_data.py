import pandas as pd
import random

def generate_base_habits(n=500):
    data = []
    for _ in range(n):
        hour = random.randint(0, 23)
        # Giả lập nhiệt độ theo giờ (trưa nóng, đêm lạnh)
        if 11 <= hour <= 15:
            temp = random.uniform(31, 36)
        else:
            temp = random.uniform(24, 29)
        
        humi = random.uniform(60, 90)

        # LOGIC GỐC:
        # Nếu trưa nóng (>32 độ) -> 95% là Bật Quạt (1)
        if temp > 32:
            fan_status = 1 if random.random() < 0.95 else 0
        # Nếu đêm khuya (0h-5h) -> 80% là Tắt Đèn (0)
        elif 0 <= hour <= 5:
            light_status = 0 if random.random() < 0.8 else 1
            fan_status = 1 if temp > 27 else 0
        else:
            fan_status = random.randint(0, 1)
            light_status = random.randint(0, 1)

        data.append([hour, round(temp, 1), round(humi, 1), fan_status])

    df = pd.DataFrame(data, columns=['hour', 'temp', 'humi', 'level'])
    df.to_csv('habit_data.csv', index=False)
    print("✅ Đã khởi tạo bản năng gốc cho AI với 500 mẫu!")

generate_base_habits()