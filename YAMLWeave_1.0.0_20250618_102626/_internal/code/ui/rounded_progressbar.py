import tkinter as tk

class RoundedProgressBar(tk.Canvas):
    """自定义圆角进度条控件"""

    def __init__(self, master, width=300, height=10, bg_color="#DDDDDD", fg_color="#444444", radius=5, *args, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=bg_color, *args, **kwargs)
        self._width = width
        self._height = height
        self._radius = radius
        self._bg_color = bg_color
        self._fg_color = fg_color
        self._progress = 0
        self._create_items()

    def _rounded_points(self, x1, y1, x2, y2, r):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
        return points

    def _create_items(self):
        self.trough = self.create_polygon(
            self._rounded_points(0, 0, self._width, self._height, self._radius),
            fill=self._bg_color,
            outline="",
            smooth=True,
        )
        self.bar = self.create_polygon(
            self._rounded_points(0, 0, 0, self._height, self._radius),
            fill=self._fg_color,
            outline="",
            smooth=True,
        )

    def set(self, value: float):
        """设置进度值，取值范围0-100"""
        value = max(0.0, min(100.0, float(value)))
        self._progress = value
        bar_width = self._width * (self._progress / 100.0)
        points = self._rounded_points(0, 0, bar_width, self._height, self._radius)
        self.coords(self.bar, *points)

    def get(self) -> float:
        return self._progress

