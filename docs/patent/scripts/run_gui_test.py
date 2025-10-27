#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMLWeave GUI测试启动器

使用方法:
    python run_gui_test.py              # 启动GUI模式
    python run_gui_test.py --cli        # 启动命令行模式
    python run_gui_test.py --install    # 安装GUI依赖
"""

import sys
import os
import subprocess

def install_dependencies():
    """安装GUI依赖"""
    print("正在安装GUI依赖库...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "matplotlib>=3.5.0",
            "numpy>=1.21.0"
        ])
        print("✅ GUI依赖安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ GUI依赖安装失败: {e}")
        print("请手动运行: pip install matplotlib numpy")
        return False

def check_dependencies():
    """检查依赖是否已安装"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        return True
    except ImportError:
        return False

def main():
    """主函数"""
    # 解析命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--install":
            install_dependencies()
            return
        elif arg == "--cli":
            print("启动命令行模式...")
            cli_script = os.path.join(os.path.dirname(__file__), "test_secondary_features.py")
            if os.path.exists(cli_script):
                subprocess.run([sys.executable, cli_script] + sys.argv[2:])
            else:
                print(f"错误: 找不到CLI脚本 {cli_script}")
            return
        elif arg in ["--help", "-h"]:
            print(__doc__)
            return

    # 检查依赖
    if not check_dependencies():
        print("❌ 缺少GUI依赖库")
        print("正在尝试自动安装...")
        if not install_dependencies():
            print("回退到命令行模式...")
            subprocess.run([sys.executable,
                           os.path.join(os.path.dirname(__file__), "test_secondary_features.py")])
            return

    # 启动GUI模式
    print("启动GUI模式...")
    try:
        from test_secondary_features_gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ 导入GUI模块失败: {e}")
        print("回退到命令行模式...")
        subprocess.run([sys.executable,
                       os.path.join(os.path.dirname(__file__), "test_secondary_features.py")])

if __name__ == "__main__":
    main()