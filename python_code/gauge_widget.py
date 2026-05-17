import math
import customtkinter as ctk
from config import CARD_COLOR, TEXT_DIM

class GaugeCanvas(ctk.CTkCanvas):
    def __init__(self, parent, size=160, min_val=0, max_val=100, unit="", color="#4ECDC4", **kw):
        super().__init__(parent, width=size, height=size, bg=CARD_COLOR, highlightthickness=0, **kw)
        self.size = size
        self.min_val = min_val
        self.max_val = max_val
        self.unit = unit
        self.color = color
        self._value = min_val
        self._draw(min_val)

    def set_value(self, val):
        if abs(val - self._value) > 0.05:
            self._value = val
            self._draw(val)

    def _draw(self, val):
        self.delete("all")
        s = self.size
        p = 14
        cx, cy = s // 2, s // 2 + 8

        # Track nền
        self.create_arc(p, p + 10, s - p, s - p + 10, start=220, extent=-260, style="arc", outline="#2A3A4A", width=10)

        # Arc giá trị
        pct = max(0, min(1, (val - self.min_val) / (self.max_val - self.min_val)))
        extent = -260 * pct
        if abs(extent) > 0.5:
            self.create_arc(p, p + 10, s - p, s - p + 10, start=220, extent=extent, style="arc", outline=self.color, width=10)

        # Điểm mút
        if pct > 0.01:
            angle_rad = math.radians(220 + extent)
            rx = (s - 2 * p) / 2
            ry = (s - 2 * p) / 2
            dot_x = cx + rx * math.cos(angle_rad)
            dot_y = cy - ry * math.sin(angle_rad) + 10
            self.create_oval(dot_x - 5, dot_y - 5, dot_x + 5, dot_y + 5, fill=self.color, outline="")

        # Chữ hiển thị số
        self.create_text(cx, cy - 2, text=f"{val:.1f}", font=("Helvetica", 22, "bold"), fill="#E8F4FF")
        self.create_text(cx, cy + 22, text=self.unit, font=("Helvetica", 10), fill=TEXT_DIM)

        # Nhãn Min / Max
        self.create_text(p + 2, s - p + 4, text=str(self.min_val), font=("Helvetica", 8), fill=TEXT_DIM, anchor="w")
        self.create_text(s - p - 2, s - p + 4, text=str(self.max_val), font=("Helvetica", 8), fill=TEXT_DIM, anchor="e")