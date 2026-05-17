import math
import matplotlib.pyplot as plt

# ---- CẤU HÌNH FIREBASE ----
FIREBASE_DB_URL = "https://monitoremp-f1080-default-rtdb.asia-southeast1.firebasedatabase.app"
SERVICE_ACCOUNT = "serviceAccountKey2.json"
FETCH_INTERVAL = 3
MAX_HISTORY = 100  # Tăng lên để hiển thị nhiều điểm hơn trên đồ thị

# ---- THEME & STYLE ----
TEMP_COLOR = "#FF6B6B"
HUMID_COLOR = "#4ECDC4"
HEAT_COLOR = "#FFE66D"
BG_COLOR = "#0F1923"
CARD_COLOR = "#1A2535"
TEXT_DIM = "#7A8A9A"

def apply_matplotlib_style():
    plt.rcParams.update({
        "figure.facecolor": BG_COLOR,
        "axes.facecolor": CARD_COLOR,
        "axes.edgecolor": "#2A3A4A",
        "axes.labelcolor": TEXT_DIM,
        "text.color": "#C8D8E8",
        "xtick.color": TEXT_DIM,
        "ytick.color": TEXT_DIM,
        "grid.color": "#1E2D3D",
        "grid.alpha": 0.6,
        "font.family": "DejaVu Sans",
        "font.size": 9,
    })