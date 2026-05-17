import os
from config import FIREBASE_DB_URL, SERVICE_ACCOUNT

firebase_available = False
db = None

try:
    import firebase_admin
    from firebase_admin import credentials, db as firebase_db

    if os.path.exists(SERVICE_ACCOUNT):
        cred = credentials.Certificate(SERVICE_ACCOUNT)
        firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})
        db = firebase_db
        firebase_available = True
        print("[Firebase] Kết nối thành công!")
    else:
        print(f"[CẢNH BÁO] Không tìm thấy {SERVICE_ACCOUNT} - dùng dữ liệu mô phỏng")
except Exception as e:
    print(f"[CẢNH BÁO] Firebase lỗi: {e} - dùng dữ liệu mô phỏng")