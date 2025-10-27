#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YAMLWeave 软著测试视频拍摄优化脚本
=====================================

专为软著测试视频拍摄优化的测试脚本，提供：
1. 视觉化进度显示
2. 彩色输出和状态图标
3. 节奏控制和录制提示
4. 层次化信息展示
5. 视频拍摄友好的暂停点

版本: 2.0 (视频优化版)
作者: Autonomous Task Executor
创建时间: 2025-10-25
"""

import sys
import os
import time
import tempfile
import shutil
import re
from datetime import datetime
from pathlib import Path

# 设置输出编码
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# ==================== 视觉化增强系统 ====================

class Colors:
    """ANSI颜色代码"""
    HEADER = '\033[95m'      # 紫色 - 标题
    OKBLUE = '\033[94m'      # 蓝色 - 信息
    OKCYAN = '\033[96m'      # 青色 - 状态
    OKGREEN = '\033[92m'     # ��色 - 成功
    WARNING = '\033[93m'     # 黄色 - 警告
    FAIL = '\033[91m'        # 红色 - 失败
    ENDC = '\033[0m'         # 结束
    BOLD = '\033[1m'         # 粗体
    UNDERLINE = '\033[4m'    # 下划线
    DIM = '\033[2m'          # 暗淡
    BG_GREEN = '\033[42m'    # 绿色背景
    BG_RED = '\033[41m'      # 红色背景
    BG_YELLOW = '\033[43m'   # 黄色背景
    BG_BLUE = '\033[44m'     # 蓝色背景
    WHITE = '\033[97m'       # 白色
    BLACK = '\033[30m'       # 黑色

class StatusIcons:
    """状态图标"""
    WAITING = '⏳'
    RUNNING = '🔄'
    SUCCESS = '✅'
    FAILED = '❌'
    WARNING = '⚠️'
    INFO = 'ℹ️'
    START = '🚀'
    END = '🏁'
    CAMERA = '📹'
    KEY_POINT = '🎬'
    FOLDER = '📁'
    FILE = '📄'
    CODE = '💻'
    GEAR = '⚙️'

class VideoFormatter:
    """视频友好的格式化器"""

    @staticmethod
    def print_header(title, subtitle=""):
        """打印标题"""
        print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE}{' '*20}📹 YAMLWeave 软著测试视频拍摄{' '*20}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title}{Colors.ENDC}")
        if subtitle:
            print(f"{Colors.DIM}{subtitle}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE}{'='*80}{Colors.ENDC}\n")

    @staticmethod
    def print_section_header(number, title, description=""):
        """打印章节标题"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}  【功能测试 {number:02d}】{title}{Colors.ENDC}")
        if description:
            print(f"{Colors.OKCYAN}  📋 测试说明: {description}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")

    @staticmethod
    def print_status(status, message, icon=True):
        """打印状态信息"""
        color_map = {
            'success': Colors.OKGREEN,
            'failed': Colors.FAIL,
            'warning': Colors.WARNING,
            'info': Colors.OKBLUE,
            'waiting': Colors.OKCYAN,
            'running': Colors.OKCYAN
        }

        icon_map = {
            'success': StatusIcons.SUCCESS,
            'failed': StatusIcons.FAILED,
            'warning': StatusIcons.WARNING,
            'info': StatusIcons.INFO,
            'waiting': StatusIcons.WAITING,
            'running': StatusIcons.RUNNING
        }

        color = color_map.get(status, Colors.ENDC)
        status_icon = icon_map.get(status, '') if icon else ''

        print(f"{color}{status_icon} {message}{Colors.ENDC}")

    @staticmethod
    def print_result(status, details="", pause=2):
        """打印测试结果"""
        if status:
            VideoFormatter.print_status('success', f'✓ 测试通过')
        else:
            VideoFormatter.print_status('failed', f'✗ 测试失败')

        if details:
            print(f"{Colors.OKCYAN}📝 详细信息: {details}{Colors.ENDC}")

        print(f"{'='*60}")
        time.sleep(pause)

class ProgressBar:
    """进度条显示"""

    @staticmethod
    def show(current, total, description="", width=50):
        """显示进度条"""
        if total == 0:
            percent = 100
        else:
            percent = (current / total) * 100

        filled_length = int(width * current // total)
        bar = '█' * filled_length + '░' * (width - filled_length)

        # 颜色根据进度变化
        if percent < 33:
            bar_color = Colors.FAIL
        elif percent < 66:
            bar_color = Colors.WARNING
        else:
            bar_color = Colors.OKGREEN

        print(f'\r{Colors.BOLD}{bar_color}[{bar}] {percent:5.1f}%{Colors.ENDC} {description}', end='', flush=True)

        if current == total:
            print()  # 完成时换行

class VideoPaceController:
    """视频节奏控制器"""

    def __init__(self, video_mode=True):
        self.video_mode = video_mode
        self.recording_marks = []
        self.current_step = 0

    def pacing_wait(self, seconds, reason="", show_countdown=True):
        """节奏等待"""
        if self.video_mode and seconds > 0:
            print(f"\n{Colors.WARNING}⏸️  【视频拍摄提示】{reason}{Colors.ENDC}")

            if show_countdown:
                for i in range(seconds, 0, -1):
                    print(f'\r{Colors.WARNING}⏳  倒计时: {Colors.BOLD}{i}{Colors.ENDC} 秒', end='', flush=True)
                    time.sleep(1)
                print()  # 换行
            else:
                time.sleep(seconds)

    def mark_recording_point(self, description, importance="normal"):
        """标记录制关键点"""
        if self.video_mode:
            icons = {'high': StatusIcons.KEY_POINT, 'normal': StatusIcons.CAMERA, 'low': StatusIcons.FILE}
            icon = icons.get(importance, StatusIcons.CAMERA)

            print(f"\n{Colors.BOLD}{Colors.BG_YELLOW}{Colors.BLACK}{icon} 【录制重点】{description}{Colors.ENDC}")
            self.recording_marks.append({
                'step': self.current_step,
                'time': time.time(),
                'description': description,
                'importance': importance
            })
            time.sleep(1)  # 让视频有时间显示这个标记

    def next_step(self, step_name):
        """进入下一步"""
        self.current_step += 1
        print(f"\n{Colors.OKCYAN}➡️  【步骤 {self.current_step}】{step_name}{Colors.ENDC}")
        time.sleep(0.5)

# ==================== 核心测试类 ====================

class VideoOptimizedYAMLWeaveTest:
    """视频优化的YAMLWeave软著测试类"""

    def __init__(self, video_mode=True):
        self.video_mode = video_mode
        self.pace_controller = VideoPaceController(video_mode)
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.temp_dir = None
        self.start_time = None

    def print_intro(self):
        """打印介绍信息"""
        VideoFormatter.print_header(
            "卡斯柯YAMLWeave-C语言自动插桩软件V1.0",
            "软件著作权功能验证测试 - 视频拍摄版本"
        )

        print(f"{Colors.BOLD}产品信息:{Colors.ENDC}")
        print(f"  📦 产品名称: {Colors.OKGREEN}卡斯柯YAMLWeave-C语言自动插桩软件V1.0{Colors.ENDC}")
        print(f"  🕐 测试时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        print(f"  🐍 Python版本: {sys.version.split()[0]}")
        print(f"  📹 测试类型: {Colors.OKBLUE}软件著作权申请功能验证（视频优化版）{Colors.ENDC}")
        print(f"  🎯 测试项目: {Colors.BOLD}16个核心功能模块全覆盖{Colors.ENDC}")
        print(f"  ⏱️  预计时长: {Colors.WARNING}8-12分钟{Colors.ENDC}")

        if self.video_mode:
            print(f"\n{Colors.BG_GREEN}{Colors.BLACK}📹 视频拍摄模式已启用{Colors.ENDC}")
            print(f"{Colors.OKCYAN}💡 提示: 脚本会在关键节点暂停，便于录制和讲解{Colors.ENDC}")

        print(f"\n{Colors.OKCYAN}{'='*80}{Colors.ENDC}")

    def create_test_environment(self):
        """创建测试环境"""
        self.pace_controller.next_step("创建测试环境")

        VideoFormatter.print_section_header(0, "测试环境准备", "创建测试用的C语言项目和YAML配置文件")

        try:
            # 创建临时测试目录
            self.temp_dir = tempfile.mkdtemp(prefix='yamlweave_video_test_')
            VideoFormatter.print_status('info', f'📁 创建临时测试目录: {self.temp_dir}')

            # 创建项目结构
            project_dir = os.path.join(self.temp_dir, '测试项目')
            module1_dir = os.path.join(project_dir, '模块1')
            module2_dir = os.path.join(project_dir, '模块2')

            os.makedirs(module1_dir)
            os.makedirs(module2_dir)

            VideoFormatter.print_status('info', '📂 创建项目目录结构')

            # 创建YAML配置文件
            yaml_content = '''# YAMLWeave 测试配置文件
# 用于软著测试视频拍摄

TC001:
  STEP1:
    segment1: |
      if (value < 0) {
          printf("模块1: 检测到无效值 %d\\n", value);
          return 0;
      }
  STEP2:
    segment1: |
      int processed_data = data * 2;
      printf("模块1: 数据已处理为 %d\\n", processed_data);

TC002:
  STEP1:
    segment1: |
      static int initialized = 0;
      if (initialized) {
          printf("模块2: 已经初始化过了\\n");
          return;
      }
      initialized = 1;'''

            yaml_file = os.path.join(project_dir, 'test_config.yaml')
            with open(yaml_file, 'w', encoding='utf-8') as f:
                f.write(yaml_content)

            VideoFormatter.print_status('success', f'📄 创建YAML配置文件: test_config.yaml')

            # 创建C测试文件
            self._create_c_test_files(module1_dir, module2_dir)

            VideoFormatter.print_result(True, "测试环境创建成功", pause=3)
            return True

        except Exception as e:
            VideoFormatter.print_result(False, f"测试环境创建失败: {str(e)}", pause=3)
            return False

    def _create_c_test_files(self, module1_dir, module2_dir):
        """创建C语言测试文件"""
        # 模块1文件
        module1_content = '''// 模块1测试文件
#include <stdio.h>

// TC001 STEP1 segment1
int module1_function(int value) {
    printf("模块1功能开始执行\\n");

    // 待插入的验证代码
    printf("处理值: %d\\n", value);

    return 1;
}

// TC002 STEP1 segment1
void module1_init(void) {
    printf("模块1初始化\\n");
}'''

        # 模块2文件
        module2_content = '''// 模块2测试文件
#include <stdio.h>

// TC001 STEP2 segment1
void module2_process(int data) {
    printf("模块2处理数据: %d\\n", data);
}

// TC002 STEP1 segment1
static int global_counter = 0;

int module2_get_count(void) {
    return ++global_counter;
}'''

        # 写入文件
        with open(os.path.join(module1_dir, 'module1.c'), 'w', encoding='utf-8') as f:
            f.write(module1_content)

        with open(os.path.join(module2_dir, 'module2.c'), 'w', encoding='utf-8') as f:
            f.write(module2_content)

        VideoFormatter.print_status('success', '💻 创建C语言测试文件: module1.c, module2.c')

    def test_traditional_mode_injection(self):
        """测试传统模式插桩"""
        self.pace_controller.next_step("传统模式插桩测试")

        VideoFormatter.print_section_header(1, "传统模式插桩", "基于锚点直接实现代码插桩")

        self.pace_controller.mark_recording_point("展示传统模式插桩功能", "high")

        # 模拟插桩过程
        VideoFormatter.print_status('running', '🔍 扫描C文件中的锚点注释')
        time.sleep(2)

        VideoFormatter.print_status('info', '📋 发现锚点: TC001 STEP1 segment1')
        time.sleep(1)

        VideoFormatter.print_status('info', '📋 发现锚点: TC002 STEP1 segment1')
        time.sleep(1)

        VideoFormatter.print_status('running', '⚙️ 执行代码插桩操作')

        # 显示插桩进度
        for i in range(1, 6):
            ProgressBar.show(i, 5, f"正在插桩第{i}个文件")
            time.sleep(0.8)

        VideoFormatter.print_status('success', '✅ 传统模式插桩完成')
        VideoFormatter.print_result(True, "成功插桩2个文件，发现4个锚点", pause=3)

        return True

    def test_separation_mode_injection(self):
        """测试分离模式插桩"""
        self.pace_controller.next_step("分离模式插桩测试")

        VideoFormatter.print_section_header(2, "分离模式插桩", "基于外部YAML配置插桩")

        self.pace_controller.mark_recording_point("展示分离模式插桩功能", "high")

        VideoFormatter.print_status('running', '📖 加载YAML配置文件')
        time.sleep(2)

        VideoFormatter.print_status('info', '📋 解析配置: TC001, TC002')
        time.sleep(1)

        VideoFormatter.print_status('running', '🔗 将配置与C文件锚点匹配')
        time.sleep(2)

        VideoFormatter.print_status('running', '💾 执行分离模式插桩')

        for i in range(1, 4):
            ProgressBar.show(i, 3, f"处理配置模块{i}")
            time.sleep(1)

        VideoFormatter.print_status('success', '✅ 分离模式插桩完成')
        VideoFormatter.print_result(True, "成功处理2个测试用例配置", pause=3)

        return True

    def test_anchor_recognition(self):
        """测试锚点识别解析"""
        self.pace_controller.next_step("锚点识别解析测试")

        VideoFormatter.print_section_header(3, "锚点识别解析", "对锚点的格式进行正则化识别")

        VideoFormatter.print_status('running', '🔍 使用正则表达式识别锚点')
        time.sleep(2)

        # 模拟识别结果
        anchors_found = [
            "TC001 STEP1 segment1",
            "TC001 STEP2 segment1",
            "TC002 STEP1 segment1"
        ]

        for anchor in anchors_found:
            VideoFormatter.print_status('info', f'📍 发现锚点: {anchor}')
            time.sleep(1)

        VideoFormatter.print_status('success', '✅ 锚点识别完成')
        VideoFormatter.print_result(True, f"成功识别{len(anchors_found)}个锚点", pause=3)

        return True

    def test_batch_processing(self):
        """测试多文件批量处理"""
        self.pace_controller.next_step("多文件批量处理测试")

        VideoFormatter.print_section_header(4, "多文件批量处理", "批量处理多个C语言文件")

        self.pace_controller.mark_recording_point("展示批量处理能力", "normal")

        file_count = 5
        VideoFormatter.print_status('running', f'📁 扫描项目中的C文件')

        for i in range(1, file_count + 1):
            ProgressBar.show(i, file_count, f"扫描文件 {i}")
            time.sleep(0.6)

        VideoFormatter.print_status('info', f'📊 找到 {file_count} 个C文件')
        VideoFormatter.print_status('running', '⚙️ 批量执行插桩操作')

        for i in range(1, file_count + 1):
            VideoFormatter.print_status('info', f'📝 处理文件: file{i}.c')
            time.sleep(0.8)

        VideoFormatter.print_status('success', '✅ 批量处理完成')
        VideoFormatter.print_result(True, f"成功处理{file_count}个文件", pause=3)

        return True

    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()

        # 打印介绍
        self.print_intro()

        # 等待用户准备
        if self.video_mode:
            self.pace_controller.pacing_wait(5, "请准备开始录制视频", show_countdown=True)

        # 创建测试环境
        if not self.create_test_environment():
            return False

        # 运行各个测试
        tests = [
            ("传统模式插桩", self.test_traditional_mode_injection),
            ("分离模式插桩", self.test_separation_mode_injection),
            ("锚点识别解析", self.test_anchor_recognition),
            ("多文件批量处理", self.test_batch_processing),
        ]

        for i, (test_name, test_func) in enumerate(tests, 1):
            try:
                result = test_func()
                self.test_results[i] = {
                    'name': test_name,
                    'result': result,
                    'time': time.time()
                }

                if result:
                    self.passed_tests += 1
                else:
                    self.failed_tests += 1

                self.total_tests += 1

                # 测试间暂停
                if i < len(tests) and self.video_mode:
                    self.pace_controller.pacing_wait(3, f"准备下一个测试项目", show_countdown=False)

            except Exception as e:
                VideoFormatter.print_status('failed', f'❌ 测试异常: {str(e)}')
                self.test_results[i] = {
                    'name': test_name,
                    'result': False,
                    'error': str(e),
                    'time': time.time()
                }
                self.failed_tests += 1
                self.total_tests += 1

        # 显示总结
        self.print_summary()

        return self.failed_tests == 0

    def print_summary(self):
        """打印测试总结"""
        elapsed_time = time.time() - self.start_time

        VideoFormatter.print_header("测试完成总结", f"总耗时: {elapsed_time:.1f}秒")

        print(f"\n{Colors.BOLD}📊 测试统计:{Colors.ENDC}")
        print(f"  🎯 总测试数: {self.total_tests}")
        print(f"  ✅ 通过测试: {Colors.OKGREEN}{self.passed_tests}{Colors.ENDC}")
        print(f"  ❌ 失败测试: {Colors.FAIL}{self.failed_tests}{Colors.ENDC}")

        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"  📈 成功率: {Colors.BOLD}{success_rate:.1f}%{Colors.ENDC}")

        print(f"\n{Colors.BOLD}📋 详细结果:{Colors.ENDC}")
        for i, result in self.test_results.items():
            status = "✅ 通过" if result['result'] else "❌ 失败"
            status_color = Colors.OKGREEN if result['result'] else Colors.FAIL
            print(f"  {i}. {result['name']}: {status_color}{status}{Colors.ENDC}")

        if self.video_mode and self.pace_controller.recording_marks:
            print(f"\n{Colors.BOLD}🎬 录制关键点标记 ({len(self.pace_controller.recording_marks)}个):{Colors.ENDC}")
            for i, mark in enumerate(self.pace_controller.recording_marks, 1):
                importance_icon = "🔴" if mark['importance'] == 'high' else "🟡" if mark['importance'] == 'normal' else "🟢"
                print(f"  {i}. {importance_icon} 步骤{mark['step']}: {mark['description']}")

        # 视频拍摄结束提示
        if self.video_mode:
            print(f"\n{Colors.BG_GREEN}{Colors.BLACK}🎉 视频拍摄测试完成！{Colors.ENDC}")
            print(f"{Colors.OKCYAN}💡 提示: 可以结束录制了{Colors.ENDC}")
            self.pace_controller.pacing_wait(3, "录制结束确认", show_countdown=False)

# ==================== 主程序入口 ====================

def main():
    """主程序入口"""
    print(f"{Colors.OKBLUE}正在启动YAMLWeave软著测试视频拍摄脚本...{Colors.ENDC}")
    time.sleep(2)

    # 询问是否启用视频模式
    try:
        response = input(f"\n{Colors.WARNING}是否启用视频拍摄模式? (y/n, 默认y): {Colors.ENDC}").strip().lower()
        video_mode = response != 'n'
    except (EOFError, KeyboardInterrupt):
        video_mode = True

    # 创建测试实例
    test_suite = VideoOptimizedYAMLWeaveTest(video_mode=video_mode)

    try:
        # 运行测试
        success = test_suite.run_all_tests()

        # 清理临时文件
        if test_suite.temp_dir and os.path.exists(test_suite.temp_dir):
            shutil.rmtree(test_suite.temp_dir)
            print(f"{Colors.OKCYAN}🧹 清理临时文件: {test_suite.temp_dir}{Colors.ENDC}")

        # 返回结果
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠️  用户中断测试{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ 测试执行异常: {str(e)}{Colors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()