#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave UI模块 (优化版)
提供用户界面操作YAML配置和锚点插桩功能

本模块实现了note.md中描述的"锚点与桩代码分离"的用户界面操作流程:
1. 选择项目目录(包含源代码文件的目录)
2. 选择YAML配置文件(包含桩代码的配置文件)
3. 点击"扫描并插入"按钮，执行自动插桩操作
4. 在日志区域显示处理结果

支持两种模式：
1. 传统模式 - 基于注释的代码插入:
```c
// TC001 STEP1: 测试描述
// code: printf("执行测试\n");
```

2. 分离模式 - 基于锚点与YAML配置:
```c
// TC001 STEP1 segment1
```
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import logging
import threading
import datetime

class YAMLWeaveUI:
    """
    自动插桩工具用户界面
    
    实现了note.md中描述的UI操作流程，支持两种工作模式:
    1. 传统模式：基于注释的code字段提取代码
    2. 分离模式：基于锚点与YAML配置文件加载桩代码
    
    UI操作流程:
    1. 选择项目目录 - 包含源代码的目录
    2. 选择YAML配置文件(可选) - 包含桩代码的配置文件
    3. 执行扫描与插入 - 点击"扫描并插入"按钮
    4. 显示执行日志 - 记录处理过程和结果
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("YAMLWeave 插桩工具")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        self.project_dir = tk.StringVar()
        self.yaml_file = tk.StringVar()
        self.status_message = tk.StringVar()
        self.status_message.set("就绪")
        
        # 回调函数
        self.on_process_callback = None
        
        # 添加日志缓冲区
        self.log_buffer = []
        self.log_timer = None
        
        self._create_ui()
        
    def _create_ui(self):
        """创建用户界面组件"""
        # 创建主框架
        main_frame = self._create_main_frame()
        
        # 创建目录选择区域
        self._create_directory_selection(main_frame)
        
        # 创建操作按钮区域
        self._create_action_buttons(main_frame)
        
        # 添加进度条区域
        self._create_progress_area(main_frame)
        
        # 创建日志显示区域
        self._create_log_area(main_frame)
        
        # 创建状态栏
        self._create_status_bar()
        
    def _create_main_frame(self):
        """创建主框架"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        return main_frame
    
    def _create_directory_selection(self, main_frame):
        """
        创建目录和YAML配置文件选择区域
        
        用户可以浏览并选择:
        1. 包含源代码的项目目录
        2. 包含桩代码的YAML配置文件(可选)
        """
        # 项目目录选择
        dir_frame = ttk.LabelFrame(main_frame, text="项目目录", padding="5")
        dir_frame.pack(fill=tk.X, pady=5)
        
        dir_entry = ttk.Entry(dir_frame, textvariable=self.project_dir)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_dir_btn = ttk.Button(dir_frame, text="浏览...", command=self._browse_directory)
        browse_dir_btn.pack(side=tk.RIGHT, padx=5)
        
        # YAML配置文件选择
        yaml_frame = ttk.LabelFrame(main_frame, text="YAML配置文件 (可选)", padding="5")
        yaml_frame.pack(fill=tk.X, pady=5)
        
        yaml_entry = ttk.Entry(yaml_frame, textvariable=self.yaml_file)
        yaml_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_yaml_btn = ttk.Button(yaml_frame, text="浏览...", command=self._browse_yaml_file)
        browse_yaml_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_action_buttons(self, main_frame):
        """
        创建操作按钮区域
        
        提供一个"扫描并插入"按钮，支持两种工作模式:
        1. 不选择YAML文件: 使用传统模式，从注释中提取code字段
        2. 选择YAML文件: 使用分离模式，从YAML配置中加载桩代码
        """
        action_frame = ttk.Frame(main_frame, padding="5")
        action_frame.pack(fill=tk.X, pady=5)
        
        process_btn = ttk.Button(
            action_frame, 
            text="扫描并插入", 
            command=self._on_process_click,
            style="Action.TButton"
        )
        process_btn.pack(fill=tk.X, ipady=5)
    
    def _create_progress_area(self, main_frame):
        """
        创建进度显示区域
        
        用于在处理大型项目时提供实时进度反馈，包含:
        - 进度条：显示整体处理完成比例
        - 进度标签：显示当前处理状态的文字描述
        """
        progress_frame = ttk.Frame(main_frame, padding="5")
        progress_frame.pack(fill=tk.X, pady=5)
        
        # 进度标签 - 显示当前正在处理的文件
        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.pack(fill=tk.X, pady=(0, 5), anchor=tk.W)
        
        # 进度条 - 使用ttk主题风格
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)
        
        # 进度详情 - 显示"已处理X/总共Y个文件"
        self.progress_detail = ttk.Label(progress_frame, text="")
        self.progress_detail.pack(fill=tk.X, pady=(5, 0), anchor=tk.E)
    
    def _create_log_area(self, main_frame):
        """
        创建日志显示区域
        
        用于显示处理过程中的信息，包括:
        - 扫描到的注释信息
        - 解析到的桩点数量
        - 代码插入结果
        - 错误和警告信息
        """
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 定义不同类型日志的颜色标签
        self.log_text.tag_config('info', foreground='black')
        self.log_text.tag_config('warning', foreground='orange')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('header', foreground='blue', font=('Helvetica', 10, 'bold'))
        
        # 优化特殊标签的视觉效果
        self.log_text.tag_config('find', foreground='purple', font=('Helvetica', 9, 'bold'))
        self.log_text.tag_config('config', foreground='blue', font=('Helvetica', 9, 'bold'))
        self.log_text.tag_config('insert', foreground='green', font=('Helvetica', 9, 'bold'))
        self.log_text.tag_config('skip', foreground='gray')
        self.log_text.tag_config('file', foreground='blue')
        
        # 添加更新和统计标签样式
        self.log_text.tag_config('update', foreground='#0066CC', font=('Helvetica', 9, 'bold'))
        self.log_text.tag_config('stats', foreground='#663399', font=('Helvetica', 9, 'bold'))
        
        # 分隔线标签样式
        self.log_text.tag_config('separator', foreground='#CCCCCC')
    
    def _create_status_bar(self):
        """创建状态栏"""
        status_bar = ttk.Label(self.root, textvariable=self.status_message, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建按钮样式
        style = ttk.Style()
        style.configure("Action.TButton", font=("Helvetica", 10, "bold"))
    
    def _browse_directory(self):
        """
        打开目录选择对话框
        
        允许用户浏览文件系统并选择包含源代码的项目目录
        """
        directory = filedialog.askdirectory(title="选择项目目录")
        if directory:
            self.project_dir.set(directory)
            self.status_message.set(f"已选择目录: {directory}")
    
    def _browse_yaml_file(self):
        """
        打开YAML文件选择对话框
        
        允许用户浏览文件系统并选择包含桩代码的YAML配置文件
        """
        yaml_file = filedialog.askopenfilename(
            title="选择YAML配置文件",
            filetypes=[("YAML文件", "*.yaml *.yml"), ("所有文件", "*.*")]
        )
        if yaml_file:
            self.yaml_file.set(yaml_file)
            self.status_message.set(f"已选择YAML配置文件: {yaml_file}")
    
    def _on_process_click(self):
        """
        处理按钮点击事件
        当用户点击"扫描并插入"按钮时，启动桩处理流程:
        1. 检查是否已选择有效目录
        2. 如果选择了YAML文件，则使用分离模式
        3. 否则使用传统模式
        """
        if not self.project_dir.get().strip():
            messagebox.showwarning("提示", "请先选择项目目录")
            return
        # 检查YAML文件是否存在
        yaml_file = self.yaml_file.get().strip()
        if yaml_file and not os.path.exists(yaml_file):
            messagebox.showwarning("提示", f"YAML配置文件不存在: {yaml_file}")
            return
        if self.on_process_callback:
            self.clear_log()
            # 启动新线程执行耗时处理，避免阻塞UI
            threading.Thread(target=self._process_in_thread, args=(self.project_dir.get(), yaml_file), daemon=True).start()

    def _process_in_thread(self, project_dir, yaml_file):
        # 在后台线程中调用回调，并用after调度所有UI更新
        def safe_callback(*args, **kwargs):
            # 用于UI更新的回调，自动用after调度
            self.root.after(0, self.on_process_callback, *args, **kwargs)
        # 调用回调（如AppController/FallbackAppController的process_files等）
        # 假设回调本身已实现进度条的after安全更新
        safe_callback(project_dir, yaml_file)
    
    def set_process_callback(self, callback):
        """设置处理回调函数"""
        self.on_process_callback = callback
    
    def log(self, message):
        self.log_buffer.append(message)
        self.root.after(0, self._flush_log_buffer)

    def _flush_log_buffer(self):
        self.log_text.config(state=tk.NORMAL)
        while self.log_buffer:
            message = self.log_buffer.pop(0)
            # 这里可以加格式化和tag处理
            self.log_text.insert(tk.END, message + "\n", 'info')
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def process_log_content(self, log_content):
        """
        处理日志内容并显示到UI
        
        Args:
            log_content: 要显示的日志内容
        """
        try:
            def _process():
                self.clear_log()
                for line in log_content.splitlines():
                    if line.strip():  # 忽略空行
                        self.log(line)
            self.root.after(0, _process)
        except Exception as e:
            print(f"日志内容处理错误: {str(e)}")

    def clear_log(self):
        """清空日志区域"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """
        更新状态栏消息
        
        用于显示当前处理状态，如:
        - "正在扫描文件..."
        - "正在处理桩点..."
        - "处理完成，共插入 10 个桩点"
        """
        self.status_message.set(message)
        self.root.update_idletasks()

    def update_progress(self, percentage, current_file="", processed=0, total=0):
        """
        更新处理进度显示
        
        Args:
            percentage: 完成百分比(0-100)
            current_file: 当前处理的文件名(可选)
            processed: 已处理文件数(可选)
            total: 总文件数(可选)
        """
        print(f"[DEBUG][{datetime.datetime.now()}] update_progress called: percentage={percentage}, current_file={current_file}, processed={processed}, total={total}")
        if percentage > 100:
            percentage = 100
        elif percentage < 0:
            percentage = 0
        
        # 更新进度条值
        self.progress_bar['value'] = percentage
        
        # 更新进度标签
        if current_file:
            self.progress_label.config(text=f"正在处理: {current_file}")
        
        # 更新进度详情
        if total > 0:
            self.progress_detail.config(text=f"进度: {processed}/{total} 文件 ({percentage:.1f}%)")
        
        # 强制更新UI
        self.root.update_idletasks()
        print(f"[DEBUG][{datetime.datetime.now()}] update_progress finished: percentage={percentage}")

    def reset_progress(self):
        """重置进度显示为初始状态"""
        self.progress_bar['value'] = 0
        self.progress_label.config(text="就绪")
        self.progress_detail.config(text="")
        self.root.update_idletasks()

def main():
    """UI主入口函数"""
    root = tk.Tk()
    app = YAMLWeaveUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 