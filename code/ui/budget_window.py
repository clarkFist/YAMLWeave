import tkinter as tk
from tkinter import ttk

class BudgetWindow(tk.Toplevel):
    """月度预算管理窗口"""

    def __init__(self, master, total=0.0, used=0.0):
        super().__init__(master)
        self.title("月度预算")
        self.total_var = tk.DoubleVar(value=total)
        self.used_var = tk.DoubleVar(value=used)

        self.style = ttk.Style(self)
        self.style.configure("Card.TFrame", background="#1F1F1F")
        self.style.configure("CardTitle.TLabel", font=("Segoe UI", 12, "bold"), foreground="#FFFFFF", background="#1F1F1F")
        self.style.configure("CardSubtitle.TLabel", font=("Segoe UI", 10), foreground="#ffffff60", background="#1F1F1F")
        self.style.configure(
            "Card.Horizontal.TProgressbar",
            troughcolor="#FFFFFF20",
            background="#FFFFFF",
            thickness=4,
        )
        self.style.configure("Card.TButton", font=("Segoe UI", 10), foreground="#ffffff", background="#1F1F1F", borderwidth=1)

        frame = ttk.Frame(self, style="Card.TFrame", padding=(12, 8))
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="本月预算", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.total_entry = ttk.Entry(frame, textvariable=self.total_var, width=10)
        self.total_entry.grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(frame, text="已使用", style="CardSubtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 2))
        self.used_entry = ttk.Entry(frame, textvariable=self.used_var, width=10)
        self.used_entry.grid(row=1, column=1, padx=5, sticky="w")

        self.pb = ttk.Progressbar(frame, style="Card.Horizontal.TProgressbar", mode="determinate", length=200)
        self.pb.grid(row=2, column=0, columnspan=2, pady=8, sticky="we")

        self.update_progress()

        ttk.Button(frame, text="更新", command=self.update_progress, style="Card.TButton").grid(row=3, column=0, columnspan=2, pady=4)

    def update_progress(self):
        total = self.total_var.get() or 0.0
        used = self.used_var.get() or 0.0
        pct = 0 if total == 0 else min(max(used / total * 100, 0), 100)
        self.pb["value"] = pct
        self.pb.update_idletasks()
