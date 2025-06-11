#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave UI 模块 - 提供图形界面和日志显示功能
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import datetime
import re
from typing import Callable, Dict, List, Optional, Any, Tuple

class YAMLWeaveUI:
    """YAMLWeave工具的图形用户界面"""
    
    def __init__(self, root):
        """
        初始化UI界面
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title("YAMLWeave - C代码插桩工具")
        self.root.geometry("900x700")

        # 使用ttk主题并设置基础样式，使界面更专业
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass
        default_font = ("Segoe UI", 10)
        self.style.configure("TLabel", font=default_font)
        self.style.configure("TButton", font=default_font)
        self.style.configure("TEntry", font=default_font)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   "data", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"设置图标失败: {str(e)}")
        
        # 创建变量
        self.project_dir = tk.StringVar()
        self.yaml_file = tk.StringVar()
        self.status = tk.StringVar(value="就绪")
        self.progress = tk.IntVar(value=0)
        
        # 回调函数
        self.process_callback = None
        self.reverse_callback = None
        
        # 创建UI组件
        self._create_widgets()
        self._configure_tags()
        
        # 初始化已处理行数
        self.processed_lines = 0
        
        # 结束初始化日志
        self.log("[初始化] YAMLWeave界面初始化完成", tag="info")
        self.log("[提示] 请设置项目目录和YAML配置文件，然后点击\"扫描并插入\"", tag="info")
    
    def _create_widgets(self):
        """创建UI组件"""
        # 创建菜单栏
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="退出", command=self.root.quit)
        menu_bar.add_cascade(label="文件", menu=file_menu)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="关于", command=self._show_about)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        self.root.config(menu=menu_bar)

        # 创建主Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入Frame
        input_frame = ttk.LabelFrame(main_frame, text="配置", padding="5")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 项目目录选择
        ttk.Label(input_frame, text="项目目录:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.project_dir, width=50).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(input_frame, text="浏览...", command=self._browse_project_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # YAML文件选择
        ttk.Label(input_frame, text="YAML配置:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(input_frame, textvariable=self.yaml_file, width=50).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(input_frame, text="浏览...", command=self._browse_yaml_file).grid(row=1, column=2, padx=5, pady=5)
        
        # 操作按钮
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="扫描并插入", command=self._process).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除日志", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出日志", command=self._export_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="反向生成YAML", command=self._reverse_extract).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关于", command=self._show_about).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="执行日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 使用Text控件并设置滚动条
        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=20, font=("Consolas", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="状态:").pack(side=tk.LEFT, padx=5)
        ttk.Label(status_frame, textvariable=self.status).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        ttk.Label(status_frame, text="进度:").pack(side=tk.LEFT, padx=5)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress, length=300, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        # 设置列权重以允许自动调整大小
        input_frame.columnconfigure(1, weight=1)
    
    def _configure_tags(self):
        """配置文本标签样式"""
        # 基本标签
        self.log_text.tag_configure("info", foreground="black")
        self.log_text.tag_configure("warning", foreground="orange")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("missing", foreground="red")
        
        # 特殊标签 - 锚点和插桩信息 - 使用更醒目的样式
        self.log_text.tag_configure("header", foreground="blue", font=("Helvetica", 10, "bold"))
        self.log_text.tag_configure("find", foreground="purple", background="#F5F0FF", font=("Helvetica", 10, "bold"))
        self.log_text.tag_configure("insert", foreground="green", background="#F0FFF0", font=("Helvetica", 10, "bold"))
        self.log_text.tag_configure("file", foreground="blue")
        self.log_text.tag_configure("stats", foreground="teal")

        # 测试用例相关标签
        self.log_text.tag_configure("case", foreground="#990099", background="#FFF0FF",
                                   font=("Helvetica", 10, "bold"))
        
        # 新增加的增强标签
        # 锚点相关标签
        self.log_text.tag_configure("anchor_name", foreground="#FF00FF", background="#FFF0FF", 
                                   font=("Courier New", 10, "bold"))
        self.log_text.tag_configure("file_location", foreground="#0066CC", 
                                   font=("Helvetica", 9, "italic"))
        
        # 代码插入相关标签
        self.log_text.tag_configure("stub_name", foreground="#007700", background="#F0FFF0", 
                                   font=("Courier New", 10, "bold"))
        
        # 代码内容相关标签
        self.log_text.tag_configure("code_arrow", foreground="#666666", 
                                   font=("Helvetica", 9, "bold"))
        self.log_text.tag_configure("code_content", foreground="#000088", background="#F5F5FF", 
                                   font=("Courier New", 9))
        
        # 统计和分隔线
        self.log_text.tag_configure("separator", foreground="#999999")
    
    def _browse_project_dir(self):
        """浏览并选择项目目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.project_dir.set(directory)
            self.log(f"[信息] 已设置项目目录: {directory}", tag="info")
    
    def _browse_yaml_file(self):
        """浏览并选择YAML配置文件"""
        file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")])
        if file_path:
            self.yaml_file.set(file_path)
            self.log(f"[信息] 已设置YAML配置: {file_path}", tag="info")
    
    def _process(self):
        """处理目录并插入桩代码"""
        # 检查输入
        project_dir = self.project_dir.get()
        yaml_file = self.yaml_file.get()
        
        if not project_dir:
            messagebox.showwarning("输入错误", "请选择项目目录")
            return
        
        if not os.path.isdir(project_dir):
            messagebox.showwarning("输入错误", "选择的项目目录不存在")
            return
        
        if yaml_file and not os.path.isfile(yaml_file):
            messagebox.showwarning("输入错误", "选择的YAML配置文件不存在")
            return
        
        # 更新状态
        self.update_status("开始处理...")
        self.progress.set(0)
        
        # 清除日志
        self._clear_log()
        self.log("[信息] 开始处理目录: " + project_dir, tag="info")
        if yaml_file:
            self.log("[信息] 使用YAML配置: " + yaml_file, tag="info")
        
        # 如果有回调函数，调用回调函数
        if self.process_callback:
            try:
                self.process_callback(project_dir, yaml_file)
            except Exception as e:
                self.log(f"[错误] 调用处理回调出错: {str(e)}", tag="error")
                import traceback
                self.log(traceback.format_exc(), tag="error")
                self.update_status("处理失败")
        else:
            self.log("[错误] 未设置处理回调函数", tag="error")
            self.update_status("处理失败")
    
    def _clear_log(self):
        """清除日志文本"""
        self.log_text.delete(1.0, tk.END)
        self.processed_lines = 0
        self.log("[信息] 日志已清除", tag="info")
    
    def _export_log(self):
        """导出日志到文件"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"yamlweave_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log(f"[信息] 日志已导出到: {file_path}", tag="success")
            except Exception as e:
                messagebox.showerror("导出错误", f"导出日志时出错: {str(e)}")

    def _reverse_extract(self):
        """反向提取YAML配置"""
        project_dir = self.project_dir.get()
        if not project_dir or not os.path.isdir(project_dir):
            messagebox.showwarning("输入错误", "请选择有效项目目录")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
            initialfile="reversed.yaml",
        )
        if not output_path:
            return

        self.update_status("开始导出YAML...")
        self.log(f"[信息] 反向提取YAML到: {output_path}", tag="info")

        if self.reverse_callback:
            try:
                self.reverse_callback(project_dir, output_path)
            except Exception as e:
                self.log(f"[错误] 导出YAML失败: {str(e)}", tag="error")
                self.update_status("导出失败")
        else:
            self.log("[错误] 未设置导出回调函数", tag="error")
            self.update_status("导出失败")
    
    def _show_about(self):
        """显示关于对话框"""
        messagebox.showinfo(
            "关于 YAMLWeave",
            "YAMLWeave - C代码插桩工具\n\n"
            "版本: 1.0.0\n\n"
            "功能:\n"
            "- 支持基于注释的传统插桩\n"
            "- 支持基于YAML配置的锚点插桩\n"
            "- 自动备份原始文件\n"
            "- 详细的执行日志\n\n"
            "© 2025 YAMLWeave"
        )
    
    def set_process_callback(self, callback):
        """设置处理回调函数"""
        self.process_callback = callback

    def set_reverse_callback(self, callback):
        """设置反向导出回调函数"""
        self.reverse_callback = callback
    
    def update_status(self, status_text):
        """更新状态栏文本"""
        self.status.set(status_text)
        self.root.update_idletasks()
    
    def update_progress(self, value, status_text=None, current=None, total=None):
        """更新进度条和状态栏"""
        self.progress.set(value)
        
        if status_text:
            self.update_status(status_text)
        
        if current is not None and total is not None:
            percentage = f"{value}%" if value <= 100 else "100%"
            progress_text = f"{current}/{total} ({percentage})"
            self.update_status(progress_text)
        
        self.root.update_idletasks()
    
    def log(self, message, tag="info"):
        """添加日志消息到日志区域
        
        Args:
            message: 日志消息
            tag: 用于设置文本样式的标签
        """
        # 直接打印日志信息，便于调试
        print(f"UI日志输出: [{tag}] {message}")
        
        # 获取当前时间
        timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
        
        # 特殊处理锚点消息
        if "[锚点]" in message:
            print(f"锚点信息: {message}")
            # 强制使用特定格式高亮显示
            self.log_text.insert(tk.END, timestamp, "info")
            self.log_text.insert(tk.END, message + "\n", "find")
            self.log_text.see(tk.END)
            self.log_text.update_idletasks()
            self.processed_lines += 1
            return

        # 根据消息内容自动选择标签
        if tag == "info":
            if "测试用例" in message or "用例" in message:
                tag = "case"
            elif "插桩" in message and "[插桩]" in message:
                tag = "insert"
            elif "[文件]" in message:
                tag = "file"
            elif "[统计]" in message:
                tag = "stats"
        
        # 常规日志条目
        self.log_text.insert(tk.END, timestamp + message + "\n", tag)
        
        # 自动滚动到最新消息
        self.log_text.see(tk.END)
        
        # 强制更新UI
        self.root.update_idletasks()
        
        # 增加处理行数计数
        self.processed_lines += 1
    
    def get_log_content(self):
        """获取日志内容"""
        return self.log_text.get(1.0, tk.END)

def main():
    """创建并启动独立UI测试"""
    print("启动YAMLWeave UI测试...")
    print("如果界面没有弹出，请检查是否有其他窗口被遮挡")
    
    root = tk.Tk()
    root.title("YAMLWeave UI测试")
    root.deiconify()  # 确保窗口显示在前台
    root.lift()       # 尝试将窗口提升到顶层
    root.attributes('-topmost', True)  # 设置为最顶层窗口
    root.update()
    root.attributes('-topmost', False)  # 取消最顶层设置，以便用户可以使用其他窗口
    
    app = YAMLWeaveUI(root)
    
    print("UI创建完成，开始测试日志输出...")
    
    # 测试日志输出
    app.log("[信息] 这是一条普通信息", tag="info")
    app.log("[警告] 这是一条警告信息", tag="warning")
    app.log("[错误] 这是一条错误信息", tag="error")
    app.log("[成功] 这是一条成功信息", tag="success")
    
    # 测试锚点信息显示
    app.log("[锚点] 在文件 test.c 的第 42 行找到锚点: TC001 STEP1 segment1", tag="find")
    app.log("[代码] void process_data(int data) {  // TC001 STEP1 segment1", tag="info")
    
    # 测试插桩信息显示
    app.log("[插桩] 在文件 test.c 第 42 行插入 TC001 STEP1 segment1 桩代码 (3行)", tag="insert")
    app.log("[代码]     if (data < 0 || data > 100) {", tag="info")
    app.log("[代码]         log_error(\"无效数据: %d\", data);", tag="info")
    app.log("[代码]         return;", tag="info")
    
    # 测试多个锚点显示
    app.log("[锚点] 在文件 other.c 的第 78 行找到锚点: TC002 STEP3 init", tag="find")
    app.log("[代码] int initialize_module() {  // TC002 STEP3 init", tag="info")
    app.log("[插桩] 在文件 other.c 第 78 行插入 TC002 STEP3 init 桩代码 (2行)", tag="insert")
    
    # 测试统计信息显示
    app.log("[统计] 总文件数: 10, 已处理: 5, 插入桩点: 15", tag="stats")
    
    # 测试处理完成信息
    app.log("[信息] ===== 处理完成 =====", tag="header")
    app.log("[信息] 所有文件处理完毕", tag="info")
    app.log("[成功] 插桩操作已成功完成", tag="success")
    
    print("测试日志输出完成，进入主事件循环...")
    
    root.mainloop()
    
    print("UI测试结束")

if __name__ == "__main__":
    main() 