import customtkinter as ctk
import tkinter as tk
from pathlib import Path

# 系统默认主题和外观
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("现代化 iOS 风格组件")
root.geometry("760x520")
root.resizable(False, False)

# 全局字体设置
ctk_font = ("SF Pro", 16)
ctk_label_font = ("SF Pro Display", 32, "bold")

# 头部区域
header = ctk.CTkFrame(root, fg_color="transparent")
header.pack(pady=20)

icon_path = Path("app_icon.png")
if icon_path.exists():
    img = ctk.CTkImage(light_image=icon_path, size=(48, 48))
    icon_label = ctk.CTkLabel(header, image=img, text="")
else:
    icon_label = ctk.CTkLabel(header, text="🅰️", font=("SF Pro", 40))
icon_label.pack(side="left", padx=(0, 8))

ctk.CTkLabel(header, text="iOS 风格组件展示", font=ctk_label_font).pack(side="left")

# 按钮区域
btn_frame = ctk.CTkFrame(root, fg_color="transparent")
btn_frame.pack(pady=(10, 25))

btn_kwargs = dict(width=140, height=46, corner_radius=12, font=("SF Pro", 18, "bold"))

primary_btn = ctk.CTkButton(btn_frame, text="主操作", fg_color="#007AFF", **btn_kwargs)
success_btn = ctk.CTkButton(btn_frame, text="✓ 成功", fg_color="#28CD41", hover_color="#1DA836", **btn_kwargs)
warning_btn = ctk.CTkButton(btn_frame, text="警告", fg_color="#FFCC00", text_color="#000", hover_color="#E5B700", **btn_kwargs)
danger_btn = ctk.CTkButton(btn_frame, text="危险", fg_color="#FF3B30", hover_color="#E2332A", **btn_kwargs)

for w in (primary_btn, success_btn, warning_btn, danger_btn):
    w.pack(side="left", padx=10)

# 表单区域
form_frame = ctk.CTkFrame(root, fg_color="transparent")
form_frame.pack(fill="x", padx=180)

username = ctk.CTkEntry(form_frame, placeholder_text="请输入用户名", height=46, corner_radius=12, font=ctk_font)
email = ctk.CTkEntry(form_frame, placeholder_text="请输入邮箱地址", height=46, corner_radius=12, font=ctk_font)
username.pack(fill="x", pady=6)
email.pack(fill="x", pady=6)

options = ["选项 A", "选项 B", "选项 C"]
combo = ctk.CTkOptionMenu(form_frame, values=options, corner_radius=12, height=46, font=ctk_font)
combo.set("请选择选项")
combo.pack(fill="x", pady=6)

textbox = ctk.CTkTextbox(form_frame, height=160, corner_radius=12, font=ctk_font, wrap="word")
placeholder = (
    "这是一个 iOS 风格的圆角文本框\n"
    "支持多行文本输入\n"
    "具有焦点状态下的蓝色边框效果"
)
textbox.insert("1.0", placeholder)
textbox.configure(state="disabled")

def on_focus_in(_):
    textbox.configure(state="normal")
    if textbox.get("1.0", "end-1c") == placeholder:
        textbox.delete("1.0", "end")


def on_focus_out(_):
    if not textbox.get("1.0", "end-1c").strip():
        textbox.insert("1.0", placeholder)
        textbox.configure(state="disabled")

textbox.bind("<FocusIn>", on_focus_in)
textbox.bind("<FocusOut>", on_focus_out)
textbox.pack(fill="x", pady=12)

root.mainloop()
