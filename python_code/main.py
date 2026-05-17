import customtkinter as ctk
from dashboard_ui import DashboardApp

if __name__ == "__main__":
    print("=" * 55)
    print("  Dashboard Nhiệt Độ & Độ Ẩm - ESP32 Firebase")
    print("=" * 55)

    # Kích hoạt giao diện CustomTkinter
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = DashboardApp()
    app.mainloop()