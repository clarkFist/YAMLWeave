#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统通知模块

支持跨平台的系统通知功能
"""

import os
import sys
import platform
from typing import Optional

class SystemNotifier:
    """系统通知类"""

    def __init__(self):
        self.system = platform.system()
        self.notifier = None
        self._setup_notifier()

    def _setup_notifier(self):
        """设置通知器"""
        try:
            if self.system == "Windows":
                # Windows使用toast通知
                try:
                    from win10toast import ToastNotifier
                    self.notifier = ToastNotifier()
                except ImportError:
                    print("警告: win10toast未安装，Windows通知功能不可用")

            elif self.system == "Darwin":  # macOS
                # macOS使用osascript
                self.notifier = "macos"

            elif self.system == "Linux":
                # Linux尝试使用notify2
                try:
                    import notify2
                    notify2.init("YAMLWeave")
                    self.notifier = notify2
                except ImportError:
                    print("警告: notify2未安装，Linux通知功能不可用")

        except Exception as e:
            print(f"通知系统初始化失败: {e}")

    def show_notification(self, title: str, message: str, duration: int = 5):
        """显示系统通知

        Args:
            title: 通知标题
            message: 通知内容
            duration: 显示时长（秒）
        """
        try:
            if self.system == "Windows" and self.notifier:
                self.notifier.show_toast(title, message, duration=duration)

            elif self.system == "Darwin":
                # macOS使用osascript
                script = f'''
                display notification "{message}" with title "{title}"
                '''
                os.system(f"osascript -e '{script}'")

            elif self.system == "Linux" and self.notifier:
                # Linux使用notify2
                notification = self.notifier.Notification(title, message)
                notification.show()

            else:
                # 回退到终端输出
                print(f"\n🔔 {title}")
                print(f"   {message}\n")

        except Exception as e:
            print(f"显示通知失败: {e}")

    def show_test_start(self, test_name: str):
        """显示测试开始通知"""
        self.show_notification(
            "YAMLWeave 测试",
            f"开始测试: {test_name}",
            duration=3
        )

    def show_test_complete(self, total: int, passed: int):
        """显示测试完成通知"""
        if passed == total:
            title = "YAMLWeave 测试完成 ✅"
            message = f"所有测试通过！({passed}/{total})"
        else:
            title = "YAMLWeave 测试完成 ⚠️"
            message = f"部分测试失败 ({passed}/{total})"

        self.show_notification(title, message, duration=10)

    def show_test_error(self, error_msg: str):
        """显示测试错误通知"""
        self.show_notification(
            "YAMLWeave 测试错误 ❌",
            f"测试过程中发生错误",
            duration=10
        )

class ProgressDialogManager:
    """进度对话框管理器"""

    def __init__(self):
        self.windows = []

    def create_progress_window(self, title: str = "测试进度"):
        """创建进度窗口"""
        import tkinter as tk
        from tkinter import ttk

        window = tk.Toplevel()
        window.title(title)
        window.geometry("400x150")
        window.resizable(False, False)

        # 居中显示
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

        # 内容
        main_frame = ttk.Frame(window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text=title, font=("Segoe UI", 12, "bold"))
        title_label.pack(pady=(0, 10))

        # 状态标签
        status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(main_frame, textvariable=status_var)
        status_label.pack(pady=(0, 10))

        # 进度条
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, length=300, variable=progress_var)
        progress_bar.pack(pady=(0, 5))

        # 百分比标签
        percent_var = tk.StringVar(value="0%")
        percent_label = ttk.Label(main_frame, textvariable=percent_var)
        percent_label.pack()

        self.windows.append({
            'window': window,
            'status_var': status_var,
            'progress_var': progress_var,
            'percent_var': percent_var
        })

        return len(self.windows) - 1  # 返回窗口索引

    def update_progress(self, window_id: int, status: str, progress: float):
        """更新进度"""
        if window_id < len(self.windows):
            window_data = self.windows[window_id]
            window_data['status_var'].set(status)
            window_data['progress_var'].set(progress)
            window_data['percent_var'].set(f"{progress:.0f}%")
            window_data['window'].update()

    def close_progress_window(self, window_id: int):
        """关闭进度窗口"""
        if window_id < len(self.windows):
            self.windows[window_id]['window'].destroy()
            del self.windows[window_id]

# 全局实例
system_notifier = SystemNotifier()
progress_manager = ProgressDialogManager()