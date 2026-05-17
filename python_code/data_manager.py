import threading
import math
from datetime import datetime
from collections import deque
import pandas as pd
import firebase_mgr
from config import MAX_HISTORY, FETCH_INTERVAL


class SensorDataManager:
    def __init__(self):
        self.temp_history = deque(maxlen=MAX_HISTORY)
        self.humid_history = deque(maxlen=MAX_HISTORY)
        self.heat_history = deque(maxlen=MAX_HISTORY)
        self.time_history = deque(maxlen=MAX_HISTORY)
        self.latest = {"temperature": 0.0, "humidity": 0.0, "heat_index": 0.0,
                       "timestamp": "--", "status": "connecting"}
        self._lock = threading.Lock()
        self._sim_t = 0.0

    def fetch(self):
        if firebase_mgr.firebase_available and firebase_mgr.db:
            self._fetch_firebase()
        else:
            self._fetch_simulated()

    def _fetch_firebase(self):
        try:
            # 1. Lấy dữ liệu Realtime mới nhất
            ref_latest = firebase_mgr.db.reference("/sensor_data/latest")
            data = ref_latest.get()

            if data:
                now = datetime.now()
                temp = float(data.get("temperature", 0))
                humid = float(data.get("humidity", 0))
                heat = float(data.get("heat_index", 0))
                timestamp_str = data.get("timestamp", now.strftime("%Y-%m-%d %H:%M:%S"))

                with self._lock:
                    self.latest = {
                        "temperature": temp,
                        "humidity": humid,
                        "heat_index": heat,
                        "timestamp": timestamp_str,
                        "status": "live",
                    }
                    self.temp_history.append(temp)
                    self.humid_history.append(humid)
                    self.heat_history.append(heat)
                    self.time_history.append(now)

                # 2. TỰ ĐỘNG LƯU LỊCH SỬ (Giả lập ESP32 chưa kịp lưu chuỗi thời gian)
                # Trong thực tế, ESP32 sẽ trực tiếp đẩy vào nhánh history này.
                date_str = now.strftime("%Y-%m-%d")
                time_str = now.strftime("%H-%M-%S")
                ref_history = firebase_mgr.db.reference(f"/sensor_data/history/{date_str}/{time_str}")
                ref_history.set({
                    "temperature": temp,
                    "humidity": humid,
                    "heat_index": heat,
                    "timestamp": timestamp_str
                })

        except Exception as e:
            print(f"[Firebase] Lỗi dữ liệu lớn: {e}")

    def _fetch_simulated(self):
        self._sim_t += FETCH_INTERVAL
        t = self._sim_t
        temp = 28 + 5 * math.sin(t / 60) + 1.5 * math.sin(t / 15)
        humid = 65 + 15 * math.cos(t / 90) + 3 * math.cos(t / 20)
        temp = round(max(15, min(45, temp)), 1)
        humid = round(max(20, min(99, humid)), 1)
        heat = round(temp + (humid - 40) * 0.1, 1)

        with self._lock:
            self.latest = {
                "temperature": temp,
                "humidity": humid,
                "heat_index": heat,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "status": "simulated",
            }
            now = datetime.now()
            self.temp_history.append(temp)
            self.humid_history.append(humid)
            self.heat_history.append(heat)
            self.time_history.append(now)

    def snapshot(self):
        with self._lock:
            return (
                dict(self.latest),
                list(self.temp_history),
                list(self.humid_history),
                list(self.heat_history),
                list(self.time_history),
            )

    # ================= KHU VỰC PHÂN TÍCH DỮ LIỆU LỚN (PANDAS) =================
    def analyze_data(self):
        """Chuyển đổi dữ liệu lưu trữ từ deque sang Pandas DataFrame để phân tích thống kê"""
        with self._lock:
            if len(self.time_history) == 0:
                return None

            data_dict = {
                "Timestamp": list(self.time_history),
                "Temperature": list(self.temp_history),
                "Humidity": list(self.humid_history),
                "Heat_Index": list(self.heat_history)
            }

        df = pd.DataFrame(data_dict)

        # Tiến hành phân tích chuyên sâu các chỉ số
        summary = {
            "temp_max": df["Temperature"].max(),
            "temp_min": df["Temperature"].min(),
            "temp_avg": df["Temperature"].mean(),
            "temp_std": df["Temperature"].std(),  # Độ lệch chuẩn (độ biến động)

            "humid_max": df["Humidity"].max(),
            "humid_min": df["Humidity"].min(),
            "humid_avg": df["Humidity"].mean(),

            "total_records": len(df)
        }
        return summary, df

    def export_to_excel(self, file_path="python_code/sensor_report.xlsx"):
        """Xuất toàn bộ cấu trúc dữ liệu chuỗi thời gian hiện tại ra file Excel"""
        analysis = self.analyze_data()
        if analysis is None:
            return False

        _, df = analysis
        # Định dạng lại cột thời gian trước khi xuất
        df["Timestamp"] = df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df.to_excel(file_path, index=False, sheet_name="Sensor Data Logging")
        print(f"[Data Analytics] Đã xuất báo cáo thành công ra file: {file_path}")
        return True