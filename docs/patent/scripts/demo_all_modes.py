#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMLWeave 测试模式演示脚本

展示GUI和CLI模式的所有功能特性
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🚀 YAMLWeave 二级功能测试 - 完整功能演示")
    print("=" * 60)
    print()

def check_dependencies():
    """检查依赖"""
    print("📋 检查依赖环境...")

    try:
        import matplotlib.pyplot as plt
        import numpy as np
        print("✅ GUI依赖已安装 (matplotlib, numpy)")
        return True
    except ImportError:
        print("❌ GUI依赖缺失")
        print("   运行: python run_gui_test.py --install")
        return False

def demo_gui_features():
    """演示GUI功能"""
    print("\n🎨 GUI模式功能特性:")
    print("   • 实时进度显示和状态更新")
    print("   • 可视化测试配置界面")
    print("   • 多标签页结果报告")
    print("   • 图表可视化 (饼图、柱状图)")
    print("   • 系统通知集成")
    print("   • 非阻塞多线程设计")

    gui_has_deps = check_dependencies()

    if gui_has_deps:
        print("\n🎯 启动GUI模式演示...")
        print("   提示: GUI窗口将打开，您可以:")
        print("   1. 点击'配置'调整测试参数")
        print("   2. 点击'开始测试'运行测试")
        print("   3. 查看实时进度和结果")

        response = input("\n是否启动GUI模式? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            try:
                # 启��GUI模式
                subprocess.run([sys.executable, "run_gui_test.py"],
                             cwd=os.path.dirname(__file__))
            except KeyboardInterrupt:
                print("\n用户中断了GUI模式")
            except Exception as e:
                print(f"\nGUI启动失败: {e}")
    else:
        print("\n⚠️  GUI依赖未安装，跳过GUI演示")

def demo_cli_features():
    """演示CLI功能"""
    print("\n💻 CLI模式功能特性:")
    print("   • 命令行参数配置")
    print("   • 彩色进度显示")
    print("   • 详细日志输出")
    print("   • 间隔时间控制")
    print("   • 倒计时显示")

    print("\n🎯 启动CLI模式演示...")
    print("   提示: 将运行快速测试版本")

    response = input("\n是否运行CLI模式? (y/n): ").lower().strip()
    if response in ['y', 'yes', '是']:
        try:
            # 启动CLI模式（使用快速参数）
            subprocess.run([
                sys.executable, "run_gui_test.py", "--cli",
                "--gap-section", "2",
                "--gap-sub", "1",
                "--no-countdown"
            ], cwd=os.path.dirname(__file__))
        except KeyboardInterrupt:
            print("\n用户中断了CLI模式")
        except Exception as e:
            print(f"\nCLI启动失败: {e}")

def show_usage_examples():
    """显示使用示例"""
    print("\n📖 使用示例:")
    print()
    print("1. 启动GUI模式:")
    print("   python run_gui_test.py")
    print()
    print("2. 启动CLI模式:")
    print("   python run_gui_test.py --cli")
    print()
    print("3. CLI模式参数:")
    print("   python run_gui_test.py --cli --gap-section 5 --no-countdown")
    print()
    print("4. 安装GUI依赖:")
    print("   python run_gui_test.py --install")
    print()
    print("5. 直接运行原版测试:")
    print("   python test_secondary_features.py")
    print()
    print("6. GUI版测试脚本:")
    print("   python test_secondary_features_gui.py")

def show_file_structure():
    """显示文件结构"""
    print("\n📁 相关文件:")
    script_dir = Path(__file__).parent

    files = [
        ("run_gui_test.py", "GUI启动器 - 推荐使用"),
        ("test_secondary_features_gui.py", "GUI增强版测试脚本"),
        ("test_secondary_features.py", "原版命令行测试脚本"),
        ("system_notifier.py", "系统通知模块"),
        ("requirements_gui.txt", "GUI依赖列表"),
        ("README_GUI.md", "详细使用说明"),
    ]

    for filename, description in files:
        filepath = script_dir / filename
        status = "✅" if filepath.exists() else "❌"
        print(f"   {status} {filename:<35} - {description}")

def show_test_coverage():
    """显示测试覆盖范围"""
    print("\n🧪 测试覆盖范围:")

    modules = [
        ("扫描并插入", [
            "文件扫描与备份输出",
            "锚点解析与YAML容错",
            "安全插入与统计反馈",
            "无锚点文件统计"
        ]),
        ("清除日志", [
            "重置日志通道",
            "着色分级保留",
            "一键清空界面日志"
        ]),
        ("导出日志", [
            "执行日志归档与检索",
            "统一目录结构",
            "导出当前UI日志"
        ]),
        ("反向生成YAML", [
            "提取插桩片段",
            "规范聚合与保留格式",
            "后台导出与状态反馈"
        ])
    ]

    for module_name, features in modules:
        print(f"\n   📦 {module_name}:")
        for feature in features:
            print(f"      • {feature}")

def main():
    """主函数"""
    print_banner()

    # 显示文件结构
    show_file_structure()

    # 显示测试覆盖范围
    show_test_coverage()

    # 显示使用示例
    show_usage_examples()

    # 询问用户想要演示哪种模式
    print("\n" + "=" * 60)
    print("🎭 演示模式选择:")
    print("1. GUI模式演示")
    print("2. CLI模式演示")
    print("3. 全部演示")
    print("4. 仅查看信息")
    print("=" * 60)

    choice = input("\n请选择 (1-4): ").strip()

    if choice == "1":
        demo_gui_features()
    elif choice == "2":
        demo_cli_features()
    elif choice == "3":
        demo_gui_features()
        demo_cli_features()
    elif choice == "4":
        print("\n✅ 演示完成！")
    else:
        print("\n⚠️  无效选择，演示结束")

    print("\n🎉 感谢使用YAMLWeave测试工具！")
    print("📖 更多信息请查看: README_GUI.md")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")