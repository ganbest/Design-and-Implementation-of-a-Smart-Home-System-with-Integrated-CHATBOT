import firebase_admin
from firebase_admin import credentials, db as firebase_db

JSON_KEY_FILE = 'serviceAccountKey.json'

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(JSON_KEY_FILE)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://smart-home-dd3cf-default-rtdb.firebaseio.com'
        })

    print("✅ Firebase: Kết nối thành công!")

except Exception as e:
    print(f"❌ Firebase: Lỗi! {e}")
    raise  # ❗ không dùng exit()

# 👉 export ra cho toàn project dùng
db = firebase_db