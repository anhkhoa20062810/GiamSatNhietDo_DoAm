import threading
import time
from datetime import datetime
import customtkinter as ctk
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import numpy as np

from config import (BG_COLOR, CARD_COLOR, TEXT_DIM, TEMP_COLOR, HUMID_COLOR,
                    HEAT_COLOR, FETCH_INTERVAL, apply_matplotlib_style)
from data_manager import SensorDataManager
from gauge_widget import GaugeCanvas


class DashboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("  ESP32 Advanced IoT Analytics Dashboard")
        self.geometry("1250x750")  # Mở rộng kích thước cửa sổ để đồ thị hiển thị đẹp nhất
        self.minsize(1100, 680)
        self.configure(fg_color=BG_COLOR)

        apply_matplotlib_style()
        self.data_mgr = SensorDataManager()

        self._build_ui()
        self._start_data_thread()
        self._schedule_ui_update()

    def _build_ui(self):
        # ---- Header ----
        hdr = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=0, height=54)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="    IoT Data Analytics & Big Data System",
                     font=ctk.CTkFont("Helvetica", 18, "bold"), text_color="#E8F4FF").pack(side="left", padx=16,
                                                                                           pady=10)

        self.status_lbl = ctk.CTkLabel(hdr, text="● Đang kết nối...", font=ctk.CTkFont("Helvetica", 11),
                                       text_color="#FFE66D")
        self.status_lbl.pack(side="right", padx=16)

        self.time_lbl = ctk.CTkLabel(hdr, text="", font=ctk.CTkFont("Helvetica", 11), text_color=TEXT_DIM)
        self.time_lbl.pack(side="right", padx=4)

        # ---- Nội dung chính ----
        container = ctk.CTkFrame(self, fg_color=BG_COLOR)
        container.pack(fill="both", expand=True, padx=10, pady=6)
        container.columnconfigure(0, weight=3)  # Vùng đồ thị thời gian thực (Bên trái)
        container.columnconfigure(1, weight=2)  # Vùng Đồ thị thống kê Analytics (Bên phải)
        container.rowconfigure(0, weight=1)

        # ============================================================
        # ---- VÙNG BÊN TRÁI (GAUGES & LINE CHARTS) ----
        # ============================================================
        left_panel = ctk.CTkFrame(container, fg_color=BG_COLOR)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_panel.columnconfigure(0, weight=1)
        left_panel.columnconfigure(1, weight=1)
        left_panel.rowconfigure(1, weight=1)

        # Hàng gauge
        gauge_row = ctk.CTkFrame(left_panel, fg_color=BG_COLOR)
        gauge_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        gauge_row.columnconfigure((0, 1, 2), weight=1)

        self.temp_card = self._make_gauge_card(gauge_row, 0, "Nhiệt Độ", min_v=0, max_v=50, unit="°C", color=TEMP_COLOR)
        self.humid_card = self._make_gauge_card(gauge_row, 1, "Độ Ẩm", min_v=0, max_v=100, unit="%", color=HUMID_COLOR)
        self.heat_card = self._make_gauge_card(gauge_row, 2, "Chỉ Số Nhiệt", min_v=0, max_v=55, unit="°C",
                                               color=HEAT_COLOR)

        # Hệ thống 2 đồ thị đường (Line charts)
        self.fig_temp, self.ax_temp = self._make_chart_frame(left_panel, row=1, col=0,
                                                             title="Biến động Nhiệt độ chuỗi thời gian", y_label="°C",
                                                             color=TEMP_COLOR)
        self.fig_humid, self.ax_humid = self._make_chart_frame(left_panel, row=1, col=1,
                                                               title="Biến động Độ ẩm chuỗi thời gian", y_label="%",
                                                               color=HUMID_COLOR)

        # ============================================================
        # ---- VÙNG BÊN PHẢI (BIG DATA ANALYTICS GRAPH PANEL) ----
        # ============================================================
        right_panel = ctk.CTkFrame(container, fg_color=CARD_COLOR, corner_radius=12)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=4)

        ctk.CTkLabel(right_panel, text="📊 DATA ANALYTICS GRAPH",
                     font=ctk.CTkFont("Helvetica", 14, "bold"), text_color="#E8F4FF").pack(pady=(15, 5))

        # Đồ thị cột thống kê nâng cấp chuyên sâu
        self.fig_stat = Figure(figsize=(4.0, 5.0), dpi=96)
        self.ax_stat = self.fig_stat.add_subplot(111)
        self.fig_stat.tight_layout(pad=1.8)

        self.canvas_stat = FigureCanvasTkAgg(self.fig_stat, master=right_panel)
        self.canvas_stat.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=10)

        # Nút bấm xuất báo cáo chuyên sâu sang tập tin Excel
        export_btn = ctk.CTkButton(right_panel, text="💾 Xuất báo cáo Excel (.xlsx)",
                                   font=ctk.CTkFont("Helvetica", 12, "bold"),
                                   fg_color="#228B22", hover_color="#006400", height=42,
                                   command=self._trigger_export)
        export_btn.pack(fill="x", padx=15, pady=(5, 15))

    def _make_gauge_card(self, parent, col, title, min_v, max_v, unit, color):
        card = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=12)
        card.grid(row=0, column=col, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Helvetica", 11, "bold"), text_color=TEXT_DIM).pack(pady=(8, 0))
        gauge = GaugeCanvas(card, size=135, min_val=min_v, max_val=max_v, unit=unit, color=color)
        gauge.pack(pady=2)
        val_lbl = ctk.CTkLabel(card, text="-- " + unit, font=ctk.CTkFont("Helvetica", 12), text_color=color)
        val_lbl.pack(pady=(0, 8))
        return {"gauge": gauge, "label": val_lbl, "unit": unit}

    def _make_chart_frame(self, parent, row, col, title, y_label, color):
        frame = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=12)
        frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont("Helvetica", 11, "bold"), text_color=TEXT_DIM).pack(
            pady=(8, 0))

        fig = Figure(figsize=(4.0, 2.6), dpi=96)
        ax = fig.add_subplot(111)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=(2, 8))
        fig._canvas_widget = canvas
        return fig, ax

    def _trigger_export(self):
        filename = f"sensor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        success = self.data_mgr.export_to_excel(filename)
        if success:
            messagebox.showinfo("Thành Công",
                                f"Đã ứng dụng thuật toán Pandas trích xuất\ndữ liệu lớn ra file báo cáo:\n{filename}")
        else:
            messagebox.showwarning("Thất bại", "Chưa thu thập đủ dữ liệu chuỗi thời gian để phân tích!")

    def _start_data_thread(self):
        def loop():
            while True:
                try:
                    self.data_mgr.fetch()
                except Exception as e:
                    print(f"[Thread] Lỗi: {e}")
                time.sleep(FETCH_INTERVAL)

        threading.Thread(target=loop, daemon=True).start()

    def _schedule_ui_update(self):
        self._update_ui()
        self.after(1500, self._schedule_ui_update)

    def _update_ui(self):
        latest, temps, humids, heats, times = self.data_mgr.snapshot()

        # 1. Cập nhật hiển thị vòng tròn kim đo (Gauges)
        self.temp_card["gauge"].set_value(latest["temperature"])
        self.temp_card["label"].configure(text=f"{latest['temperature']:.1f} {self.temp_card['unit']}")
        self.humid_card["gauge"].set_value(latest["humidity"])
        self.humid_card["label"].configure(text=f"{latest['humidity']:.1f} {self.humid_card['unit']}")
        self.heat_card["gauge"].set_value(latest["heat_index"])
        self.heat_card["label"].configure(text=f"{latest['heat_index']:.1f} {self.heat_card['unit']}")

        # 2. Cập nhật thanh trạng thái hệ thống đám mây
        st = latest.get("status", "connecting")
        if st == "live":
            self.status_lbl.configure(text="● Cloud Live - Big Data Connected", text_color="#4ECDC4")
        elif st == "simulated":
            self.status_lbl.configure(text="● Hệ thống đang mô phỏng", text_color=HEAT_COLOR)

        self.time_lbl.configure(text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

        # 3. Cập nhật 2 Đồ thị đường chạy thời gian thực ở bên trái
        if len(times) >= 2:
            self._update_chart(self.fig_temp, self.ax_temp, times, temps, TEMP_COLOR, "°C")
            self._update_chart(self.fig_humid, self.ax_humid, times, humids, HUMID_COLOR, "%")

        # 4. CẬP NHẬT ĐỒ THỊ THỐNG KÊ BIỂU ĐỒ CỘT (BAR CHART CHUYÊN SÂU BÊN PHẢI)
        analysis_results = self.data_mgr.analyze_data()
        if analysis_results:
            stats, _ = analysis_results

            # Xóa sạch đồ thị cũ để chuẩn bị render khung hình mới
            self.ax_stat.clear()
            self.ax_stat.grid(True, linestyle="--", alpha=0.3, axis="y", zorder=1)

            # Nhãn danh mục tính toán của Pandas
            categories = ['Thấp nhất (Min)', 'Trung vị (Avg)', 'Cao nhất (Max)']
            temp_metrics = [stats['temp_min'], stats['temp_avg'], stats['temp_max']]
            humid_metrics = [stats['humid_min'], stats['humid_avg'], stats['humid_max']]

            # Tính toán vị trí tọa độ các cột kép san sát nhau
            x = np.arange(len(categories))
            width = 0.35

            # Vẽ 2 nhóm cột tương tác
            rects1 = self.ax_stat.bar(x - width / 2, temp_metrics, width, label='Nhiệt Độ (°C)', color=TEMP_COLOR,
                                      alpha=0.9, zorder=3)
            rects2 = self.ax_stat.bar(x + width / 2, humid_metrics, width, label='Độ Ẩm (%)', color=HUMID_COLOR,
                                      alpha=0.9, zorder=3)

            # Định dạng giao diện trục của đồ thị thống kê
            self.ax_stat.set_ylabel('Giá trị đo đạc thống kê', fontsize=9, color=TEXT_DIM)
            self.ax_stat.set_title(f'Thống kê từ tập dữ liệu gồm {stats["total_records"]} mẫu mẫu lưu', fontsize=9,
                                   color=TEXT_DIM, pad=10)
            self.ax_stat.set_xticks(x)
            self.ax_stat.set_xticklabels(categories, fontsize=9)
            self.ax_stat.legend(loc='upper left', fontsize=8, framealpha=0.6)

            # Hàm bổ trợ vẽ số liệu chi tiết lên đỉnh đầu mỗi cột
            def autolabel(rects):
                for rect in rects:
                    height = rect.get_height()
                    if not np.isnan(height):
                        self.ax_stat.annotate(f'{height:.1f}',
                                              xy=(rect.get_x() + rect.get_width() / 2, height),
                                              xytext=(0, 3),
                                              textcoords="offset points",
                                              ha='center', va='bottom', fontsize=8, color="#C8D8E8")

            autolabel(rects1)
            autolabel(rects2)

            # Điều chỉnh linh hoạt độ cao trục Y để tránh chữ bị tràn viền đồ thị
            max_val = max(stats['temp_max'], stats['humid_max'])
            if not np.isnan(max_val):
                self.ax_stat.set_ylim(0, max_val * 1.25)

            self.fig_stat.tight_layout(pad=1.8)
            self.canvas_stat.draw_idle()

    def _update_chart(self, fig, ax, times, values, color, ylabel):
        ax.clear()
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.tick_params(axis="x", labelsize=7, rotation=20)
        ax.tick_params(axis="y", labelsize=8)

        if len(values) > 1:
            ax.plot(times, values, color=color, linewidth=1.6, alpha=0.9, zorder=3)
            ax.fill_between(times, values, alpha=0.18, color=color, zorder=2)
            ax.scatter([times[-1]], [values[-1]], color=color, s=28, zorder=4)
            ax.annotate(f"{values[-1]:.1f}", xy=(times[-1], values[-1]), xytext=(6, 4), textcoords="offset points",
                        fontsize=8, color=color)

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        fig.tight_layout(pad=1.0)
        fig._canvas_widget.draw_idle()