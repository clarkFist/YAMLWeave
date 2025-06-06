#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
备用StubProcessor模块
在导入原始模块失败时使用
"""
import os
import logging
import yaml
import re
import datetime
import shutil
import traceback
from typing import Tuple

logger = logging.getLogger(__name__)

class StubProcessor:
    """简化版的桩处理器类"""
    
    def __init__(self, project_dir=None, yaml_file=None, ui=None):
        self.project_dir = project_dir
        self.yaml_file = yaml_file
        self.yaml_config = {}
        self.stats = {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0, "failed_files": 0}
        self.ui = ui
        
        # 输出UI对象信息
        print(f"\n=== StubProcessor初始化 ===")
        print(f"UI对象存在: {ui is not None}")
        if ui:
            print(f"UI对象类型: {type(ui).__name__}")
            print(f"UI对象ID: {id(ui)}")
            print(f"UI对象方法: {[m for m in dir(ui) if not m.startswith('_') and callable(getattr(ui, m))][:5]}")
        print(f"=== StubProcessor初始化结束 ===\n")
        
        # 加载YAML配置
        if yaml_file and os.path.exists(yaml_file):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    self.yaml_config = yaml.safe_load(f) or {}
                    if not self.yaml_config:
                        logger.warning(f"YAML配置文件为空或格式不正确: {yaml_file}")
                        if self.ui:
                            self.ui.log(f"[警告] YAML配置文件为空或格式不正确: {yaml_file}", tag="warning")
            except Exception as e:
                logger.error(f"加载YAML配置失败: {str(e)}")
                if self.ui:
                    self.ui.log(f"[错误] 加载YAML配置失败: {str(e)}", tag="error")
    
    def process_files(self, callback=None):
        """
        处理文件并插入桩代码
        
        此方法与core/stub_processor.py中的process_files方法接口保持一致，
        确保在不同环境下能够正常调用。
        
        Args:
            callback: 可选的进度回调函数
            
        Returns:
            Tuple[bool, str, Dict]: (成功/失败, 消息, 统计信息)
        """
        # 调试信息 - 输出实例信息
        print("\n=== DEBUG STUB_PROCESSOR ===")
        print(f"StubProcessor.process_files 被调用: {self.__class__.__name__}")
        print(f"self.project_dir: {self.project_dir}")
        print(f"self.yaml_file: {self.yaml_file}")
        print(f"UI对象存在: {self.ui is not None}")
        if self.ui:
            print(f"UI对象ID: {id(self.ui)}")
        
        # 检查是否有钩子函数
        print(f"anchor_hook存在: {hasattr(self, 'anchor_hook')}")
        print(f"file_callback存在: {hasattr(self, 'file_callback')}")
        print("=== DEBUG STUB_PROCESSOR END ===\n")
        
        if not self.project_dir or not os.path.isdir(self.project_dir):
            error_msg = f"项目目录无效: {self.project_dir}"
            logger.error(error_msg)
            if self.ui:
                self.ui.log(f"[错误] {error_msg}")
            return False, error_msg, self.stats
        
        # 重置统计信息
        self.stats = {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0, "failed_files": 0}
        # 全局TC统计
        self.tc_stats = {}
        # 锚点详细信息存储
        self.anchor_details = {}
        
        # 调试UI对象
        if self.ui:
            print(f"\n=== DEBUG UI 对象信息 ===")
            print(f"UI对象类型: {type(self.ui).__name__}")
            print(f"UI对象ID: {id(self.ui)}")
            print(f"UI有log方法: {hasattr(self.ui, 'log')}")
            print(f"UI有root属性: {hasattr(self.ui, 'root')}")
            print(f"=== DEBUG UI 对象信息结束 ===\n")
            # 测试UI日志功能
            try:
                self.ui.log("[信息] StubProcessor: UI日志测试", tag="info")
                self.ui.log("[信息] 开始详细处理过程", tag="header")
                print("UI日志测试成功")
            except Exception as ui_error:
                print(f"UI日志测试失败: {str(ui_error)}")
                print(f"异常详情: {traceback.format_exc()}")
        
        # YAML配置健康检查
        if self.yaml_file:
            if not os.path.exists(self.yaml_file):
                logger.warning(f"YAML配置文件不存在: {self.yaml_file}")
                if self.ui:
                    self.ui.log(f"[警告] YAML配置文件不存在: {self.yaml_file}")
            elif not self.yaml_config:
                logger.warning(f"YAML配置内容为空: {self.yaml_file}")
                if self.ui:
                    self.ui.log(f"[警告] YAML配置内容为空: {self.yaml_file}")
            else:
                tc_count = len(self.yaml_config.keys())
                logger.info(f"YAML配置包含 {tc_count} 个测试用例")
                if self.ui:
                    self.ui.log(f"[配置] YAML包含 {tc_count} 个测试用例: {', '.join(self.yaml_config.keys())}")
        
        try:
            # 首先备份整个项目目录
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"{self.project_dir}_backup_{timestamp}"
            self.backup_dir = backup_dir  # 保存为实例属性
            
            try:
                logger.info(f"开始备份整个项目目录: {self.project_dir} -> {backup_dir}")
                if self.ui:
                    self.ui.log(f"[备份] 开始备份整个项目目录...")
                    self.ui.update_status("备份项目目录...")
                
                # 复制整个目录
                shutil.copytree(self.project_dir, backup_dir)
                
                logger.info(f"项目目录备份成功: {backup_dir}")
                if self.ui:
                    self.ui.log(f"[备份] 项目目录备份成功: {os.path.basename(backup_dir)}")
                    
                # 创建插桩结果目录
                stubbed_dir = f"{self.project_dir}_stubbed_{timestamp}"
                self.stubbed_dir = stubbed_dir  # 保存为实例属性
                logger.info(f"创建插桩结果目录: {stubbed_dir}")
                if self.ui:
                    self.ui.log(f"[信息] 创建插桩结果目录: {os.path.basename(stubbed_dir)}")
                
                # 复制项目目录作为插桩结果目录的基础
                shutil.copytree(self.project_dir, stubbed_dir)
                
            except Exception as backup_error:
                error_msg = f"项目目录备份失败: {str(backup_error)}"
                logger.error(error_msg)
                if self.ui:
                    self.ui.log(f"[错误] {error_msg}")
                    # 询问用户是否继续
                    import tkinter as tk
                    from tkinter import messagebox
                    result = messagebox.askquestion("备份失败", 
                        f"项目目录备份失败: {str(backup_error)}\n是否继续插桩操作？", 
                        icon='warning')
                    if result == 'no':
                        return False, "用户取消操作", self.stats
            
            # 扫描所有.c和.h文件（递归搜索子目录）
            logger.info(f"开始扫描目录: {self.project_dir}")
            if self.ui:
                self.ui.log(f"[信息] 扫描目录: {self.project_dir}")
            
            c_files = []
            for root, _, files in os.walk(self.project_dir):
                for file in files:
                    if file.endswith('.c') or file.endswith('.h'):
                        c_files.append(os.path.join(root, file))
            
            self.stats["scanned_files"] = len(c_files)
            total_files = len(c_files)
            
            if total_files == 0:
                warning_msg = f"目录中未找到C文件: {self.project_dir}"
                logger.warning(warning_msg)
                if self.ui:
                    self.ui.log(f"[警告] {warning_msg}")
                return True, warning_msg, self.stats
            
            logger.info(f"找到 {total_files} 个C/H文件")
            if self.ui:
                self.ui.log(f"[信息] 找到 {total_files} 个C/H文件待处理")
            
            # 处理每个文件
            for i, file_path in enumerate(c_files):
                try:
                    # 更新进度
                    percentage = int((i / total_files) * 100) if total_files > 0 else 0
                    current_file = os.path.basename(file_path)
                    if self.ui and hasattr(self.ui, "update_progress"):
                        self.ui.update_progress(percentage, f"处理: {current_file}", i, total_files)
                        # 确保UI更新
                        if hasattr(self.ui.root, "update_idletasks"):
                            self.ui.root.update_idletasks()
                    
                    logger.info(f"处理文件 ({i+1}/{total_files}): {file_path}")
                    
                    # 在开始处理每个文件前向UI输出明确的信息
                    if self.ui:
                        try:
                            self.ui.log(f"[文件] 开始处理: {os.path.basename(file_path)}", tag="file")
                        except Exception as log_error:
                            print(f"UI日志输出失败: {str(log_error)}")
                    
                    # 读取文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        try:
                            with open(file_path, 'r', encoding='gbk') as f:
                                content = f.read()
                            logger.info(f"使用GBK编码成功读取文件: {file_path}")
                        except Exception as enc_error:
                            error_msg = f"无法读取文件: {file_path}, 错误: {str(enc_error)}"
                            logger.error(error_msg)
                            if self.ui:
                                self.ui.log(f"[错误] {error_msg}")
                            self.stats["failed_files"] += 1
                            continue
                    except Exception as f_error:
                        error_msg = f"读取文件失败: {file_path}, 错误: {str(f_error)}"
                        logger.error(error_msg)
                        if self.ui:
                            self.ui.log(f"[错误] {error_msg}")
                        self.stats["failed_files"] += 1
                        continue
                    
                    # 寻找锚点和注释，处理文件内容
                    updated = False
                    try:
                        new_content = self.process_single_file(content, file_path, callback)
                        
                        if new_content != content:
                            updated = True
                            try:
                                # 计算插桩结果目录中对应的文件路径
                                rel_path = os.path.relpath(file_path, self.project_dir)
                                stub_file_path = os.path.join(stubbed_dir, rel_path)
                                
                                # 确保目标目录存在
                                stub_file_dir = os.path.dirname(stub_file_path)
                                os.makedirs(stub_file_dir, exist_ok=True)
                                
                                # 写入处理后的文件
                                with open(stub_file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                
                                self.stats["updated_files"] += 1
                                logger.info(f"成功更新文件: {stub_file_path}")
                                if self.ui:
                                    self.ui.log(f"[插桩] 已生成插桩文件: {rel_path}")
                            except Exception as w_error:
                                error_msg = f"写入文件失败: {stub_file_path}, 错误: {str(w_error)}"
                                logger.error(error_msg)
                                if self.ui:
                                    self.ui.log(f"[错误] {error_msg}")
                                self.stats["failed_files"] += 1
                    except Exception as p_error:
                        error_msg = f"处理文件内容失败: {file_path}, 错误: {str(p_error)}"
                        logger.error(error_msg)
                        if self.ui:
                            self.ui.log(f"[错误] {error_msg}")
                        self.stats["failed_files"] += 1
                        continue
                    
                    # 进度回调 - 使用注入的回调函数
                    if hasattr(self, 'file_callback'):
                        try:
                            self.file_callback(file_path, updated)
                        except Exception as e:
                            print(f"文件回调异常: {str(e)}")
                    elif callback:
                        callback(file_path, updated)
                except Exception as e:
                    error_msg = f"处理文件 {file_path} 时出错: {str(e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    if self.ui:
                        self.ui.log(f"[错误] {error_msg}")
                    self.stats["failed_files"] += 1
                    # 即使出错也更新进度
                    if self.ui and hasattr(self.ui, "update_progress"):
                        percentage = int(((i + 1) / total_files) * 100) if total_files > 0 else 0
                        self.ui.update_progress(percentage, "处理错误，继续执行", i + 1, total_files)
                        # 确保UI更新
                        if hasattr(self.ui.root, "update_idletasks"):
                            self.ui.root.update_idletasks()
            
            # 最终完成进度更新
            if self.ui and hasattr(self.ui, "update_progress"):
                self.ui.update_progress(100, "处理完成", total_files, total_files)
                # 确保UI更新
                if hasattr(self.ui.root, "update_idletasks"):
                    self.ui.root.update_idletasks()
            
            # 全局TC统计报告
            if hasattr(self, 'tc_stats') and self.tc_stats:
                logger.info("======= 全局测试用例统计 =======")
                if self.ui:
                    self.ui.log("[统计] ======= 测试用例汇总 =======")
                
                for tc_id, info in sorted(self.tc_stats.items()):
                    file_count = len(info.get("files", []))
                    anchor_count = info.get("anchors", 0)
                    insert_count = info.get("inserted", 0)
                    
                    tc_msg = f"测试用例 {tc_id}: 涉及文件 {file_count} 个, 锚点 {anchor_count} 个, 插入 {insert_count} 行代码"
                    logger.info(tc_msg)
                    if self.ui:
                        self.ui.log(f"[用例统计] {tc_msg}")
                    
                    # 输出步骤详细信息
                    if "steps" in info:
                        for step_id, step_info in sorted(info["steps"].items()):
                            step_msg = f"  └─ {step_id}: {len(step_info.get('segments', {}))} 个代码段"
                            logger.info(step_msg)
                            if self.ui:
                                self.ui.log(f"[步骤统计] {step_msg}")
                
                logger.info("===========================")
                if self.ui:
                    self.ui.log("[统计] ===========================")
            
            # 构建结果消息
            result_msg = f"处理完成: 扫描了 {self.stats['scanned_files']} 个文件，更新了 {self.stats['updated_files']} 个文件，插入了 {self.stats['inserted_stubs']} 个桩代码"
            if self.stats["failed_files"] > 0:
                result_msg += f"，失败 {self.stats['failed_files']} 个文件"
            
            # 添加目录信息
            result_msg += f"\n备份目录: {backup_dir}\n插桩结果目录: {stubbed_dir}"
            
            logger.info(result_msg)
            if self.ui:
                self.ui.log(f"[成功] {result_msg}")
                self.ui.log(f"[信息] 原始代码备份在: {os.path.basename(backup_dir)}")
                self.ui.log(f"[信息] 插桩结果保存在: {os.path.basename(stubbed_dir)}")
            
            # 保存详细的项目检查执行日志到固定目录
            try:
                # 尝试导入logger模块中的save_execution_log函数
                try:
                    from code.utils.logger import save_execution_log
                    logger.info("成功导入save_execution_log函数")
                except ImportError:
                    try:
                        # 尝试从相对路径导入
                        import sys
                        import os
                        module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils")
                        if module_path not in sys.path:
                            sys.path.append(module_path)
                        
                        from logger import save_execution_log
                        logger.info("通过相对路径导入save_execution_log函数")
                    except ImportError:
                        # 如果无法导入，定义简单的实现
                        def save_execution_log(stats, project_dir, backup_dir, stubbed_dir):
                            """简单的日志保存实现"""
                            try:
                                import json
                                import tempfile
                                import datetime
                                
                                # 获取时间戳
                                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                                
                                # 创建日志文件路径
                                log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "execution_logs")
                                os.makedirs(log_dir, exist_ok=True)
                                log_file = os.path.join(log_dir, f"execution_{timestamp}.log")
                                
                                # 创建执行信息
                                execution_info = {
                                    "timestamp": timestamp,
                                    "project_directory": project_dir,
                                    "stats": stats,
                                    "backup_directory": backup_dir,
                                    "stubbed_directory": stubbed_dir
                                }
                                
                                # 生成日志内容
                                content = f"===== 执行日志：{timestamp} =====\n"
                                content += f"项目目录: {project_dir}\n"
                                if backup_dir:
                                    content += f"备份目录: {backup_dir}\n"
                                if stubbed_dir:
                                    content += f"插桩结果目录: {stubbed_dir}\n"
                                
                                content += "\n----- 执行统计 -----\n"
                                content += f"总扫描文件数: {stats.get('scanned_files', 0)}\n"
                                content += f"更新的文件数: {stats.get('updated_files', 0)}\n"
                                content += f"插入的桩点数: {stats.get('inserted_stubs', 0)}\n"
                                failed = stats.get('failed_files', 0)
                                if failed > 0:
                                    content += f"处理失败文件: {failed}\n"
                                    
                                content += "=====================\n\n"
                                
                                # 添加JSON数据
                                content += "--- JSON数据 ---\n"
                                content += json.dumps(execution_info, ensure_ascii=False, indent=2)
                                
                                # 写入文件
                                with open(log_file, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                    
                                logger.info(f"执行日志已保存到: {log_file}")
                                return log_file
                            except Exception as e:
                                logger.error(f"保存执行日志失败: {str(e)}")
                                return None
                
                # 调用执行日志保存函数
                exec_log_path = save_execution_log(
                    stats=self.stats,
                    project_dir=self.project_dir,
                    backup_dir=backup_dir,
                    stubbed_dir=stubbed_dir
                )
                
                # 直接输出所有详细信息到UI，不依赖执行日志文件
                if self.ui:
                    self.ui.log("\n[信息] ===== 详细执行日志 =====", tag="header")
                    self.ui.log(f"[信息] 执行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    self.ui.log(f"[信息] 项目目录: {self.project_dir}")
                    self.ui.log(f"[信息] 备份目录: {backup_dir}")
                    self.ui.log(f"[信息] 插桩结果目录: {stubbed_dir}")
                    
                    # 配置文件信息
                    if hasattr(self, 'yaml_file') and self.yaml_file:
                        self.ui.log(f"[信息] 使用YAML配置: {self.yaml_file}", tag="file")
                        if hasattr(self, 'yaml_config') and self.yaml_config:
                            test_cases = len(self.yaml_config.keys())
                            self.ui.log(f"[信息] 配置中包含 {test_cases} 个测试用例", tag="stats")
                    
                    self.ui.log("\n[信息] ----- 执行统计 -----", tag="stats")
                    self.ui.log(f"[统计] 总扫描文件数: {self.stats.get('scanned_files', 0)}")
                    self.ui.log(f"[统计] 更新的文件数: {self.stats.get('updated_files', 0)}")
                    self.ui.log(f"[统计] 插入的桩点数: {self.stats.get('inserted_stubs', 0)}")
                    failed = self.stats.get('failed_files', 0)
                    if failed > 0:
                        self.ui.log(f"[统计] 处理失败文件: {failed}", tag="warning")
                    
                    # 处理测试用例统计数据
                    if hasattr(self, 'tc_stats') and self.tc_stats:
                        self.ui.log("\n[信息] ----- 测试用例详情 -----", tag="header")
                        for tc_id, info in sorted(self.tc_stats.items()):
                            file_count = len(info.get("files", []))
                            anchor_count = info.get("anchors", 0)
                            insert_count = info.get("inserted", 0)
                            
                            if insert_count > 0:
                                tag = "success"
                            elif anchor_count > 0:
                                tag = "info"
                            else:
                                tag = "skip"
                            
                            self.ui.log(f"[用例] {tc_id}: {file_count}个文件, {anchor_count}个锚点, {insert_count}行代码", tag=tag)
                            
                            # 步骤详情（最多显示5个步骤）
                            if "steps" in info:
                                step_items = sorted(list(info["steps"].items()))
                                display_steps = step_items[:5] if len(step_items) > 5 else step_items
                                for step_id, step_info in display_steps:
                                    seg_count = len(step_info.get('segments', {}))
                                    insert_count = step_info.get('inserted', 0)
                                    if insert_count > 0:
                                        self.ui.log(f"[步骤] └─ {step_id}: {seg_count}个代码段, 插入{insert_count}行代码", tag="success")
                                    else:
                                        self.ui.log(f"[步骤] └─ {step_id}: {seg_count}个代码段", tag="info")
                                if len(step_items) > 5:
                                    self.ui.log(f"[步骤] ...还有{len(step_items)-5}个步骤未显示...", tag="info")
                    
                    # 添加插桩详细信息
                    self.ui.log("\n[信息] ----- 锚点摘要 -----", tag="header")
                    if hasattr(self, 'anchor_details') and self.anchor_details:
                        for idx, (file_path, details) in enumerate(sorted(self.anchor_details.items())[:10]):  # 最多显示10个文件
                            file_name = os.path.basename(file_path)
                            self.ui.log(f"[文件] {file_name}: {len(details)}个锚点", tag="file")
                            for anchor_idx, anchor_info in enumerate(sorted(details[:3])):  # 每个文件最多显示3个锚点
                                tc_id = anchor_info.get('tc_id', '未知')
                                step_id = anchor_info.get('step_id', '未知')
                                segment_id = anchor_info.get('segment_id', '未知')
                                line_num = anchor_info.get('line', 0)
                                success = anchor_info.get('success', False)
                                if success:
                                    self.ui.log(f"[插桩] └─ 第{line_num}行: {tc_id} {step_id} {segment_id} 插桩成功", tag="success")
                                else:
                                    self.ui.log(f"[插桩] └─ 第{line_num}行: {tc_id} {step_id} {segment_id} 未找到桩代码", tag="warning")
                            if len(details) > 3:
                                self.ui.log(f"[文件] └─ ...还有{len(details)-3}个锚点未显示...", tag="info")
                        if len(self.anchor_details) > 10:
                            self.ui.log(f"[信息] ...还有{len(self.anchor_details)-10}个文件未显示...", tag="info")
                    else:
                        self.ui.log("[信息] 未找到有效锚点", tag="warning")
                    
                    self.ui.log("\n[信息] ===== 执行完成 =====", tag="header")
                    
                if exec_log_path:
                    logger.info(f"执行日志已保存: {exec_log_path}")
                    if self.ui:
                        try:
                            with open(exec_log_path, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                            # 使用新的日志处理方法
                            self.ui.process_log_content(log_content)
                        except Exception as e:
                            self.ui.log(f"[警告] 读取执行日志内容失败: {str(e)}", tag='warning')
                else:
                    logger.warning("执行日志保存失败")
                    if self.ui:
                        self.ui.log("[警告] 执行日志保存失败", tag='warning')
            except Exception as log_error:
                logger.error(f"保存执行日志时出错: {str(log_error)}")
                if self.ui:
                    self.ui.log(f"[警告] 保存执行日志失败: {str(log_error)}")
                    self.ui.log(f"[警告] 错误详情: {traceback.format_exc().splitlines()[-1]}")
            
            return True, result_msg, self.stats
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            if self.ui and hasattr(self.ui, "update_progress"):
                self.ui.update_progress(0, "错误", 0, 0)
            return False, error_msg, self.stats
    
    def process_single_file(self, content, file_path, callback=None):
        """处理单个文件，查找锚点并插入桩代码
        
        Args:
            content: 文件内容
            file_path: 文件路径
            callback: 可选回调函数，用于报告处理进度
        """
        # 调试信息 - 进入方法
        print(f"\n=== DEBUG PROCESS_SINGLE_FILE ===")
        print(f"处理文件: {file_path}")
        print(f"UI对象存在: {self.ui is not None}")
        if self.ui:
            print(f"UI对象ID: {id(self.ui)}")
        print(f"=== DEBUG PROCESS_SINGLE_FILE END ===\n")
        
        # 保存当前处理的文件路径，供拦截函数使用
        self.current_file = file_path
        
        lines = content.splitlines()
        new_lines = []
        i = 0
        file_anchors_count = 0
        file_stubs_inserted = 0
        # 文件级TC统计数据
        file_tc_stats = {}
        
        # 记录文件开始处理
        logger.info(f"处理文件内容: {file_path}")
        
        filename = os.path.basename(file_path)
        
        try:
            total_lines = len(lines)
            while i < total_lines:
                # 更新当前处理的行号，供拦截函数使用
                self.current_line = i + 1
                
                # 调用进度回调
                if callback:
                    progress = int((i / total_lines) * 100)
                    callback(progress, f"处理文件 {filename}: {i+1}/{total_lines} 行")
                
                line = lines[i]
                new_lines.append(line)
                
                # 查找锚点 (TC001 STEP1 segment1 格式)
                if '//' in line and 'TC' in line and 'STEP' in line:
                    # 直接输出到控制台
                    print(f"\n==== 可能的锚点 ====")
                    print(f"文件: {filename}")
                    print(f"行号: {i+1}")
                    print(f"内容: {line.strip()}")
                    print("==================\n")
                    
                    # 提取注释部分
                    comment_start = line.find('//')
                    comment_text = line[comment_start+2:].strip()
                    
                    # 分离锚点和注释
                    comment_parts = comment_text.split()
                    
                    # 检查是否有足够的部分形成锚点
                    if len(comment_parts) >= 3:
                        tc_id = comment_parts[0].upper()
                        step_id = comment_parts[1].upper()
                        segment_id = comment_parts[2].lower()
                        
                        # 记录找到锚点
                        file_anchors_count += 1
                        anchor_desc = f"{tc_id} {step_id} {segment_id}"
                        
                        # 直接输出到控制台
                        print(f"\n==== 确认锚点 ====")
                        print(f"文件: {filename}")
                        print(f"行号: {i+1}")
                        print(f"锚点: {tc_id} {step_id} {segment_id}")
                        print("=================\n")
                        
                        # 使用钩子函数输出锚点信息 - 如果存在
                        if hasattr(self, 'anchor_hook'):
                            try:
                                self.anchor_hook(os.path.basename(file_path), i+1, tc_id, step_id, segment_id)
                            except Exception as e:
                                print(f"使用钩子函数输出锚点信息失败: {str(e)}")
                                import traceback
                                print(traceback.format_exc())
                        
                        # 使用UI直接强制输出锚点信息
                        if self.ui:
                            try:
                                # 构造标准锚点信息消息
                                anchor_message = f"[锚点] 在文件 {filename} 的第 {i+1} 行找到锚点: {tc_id} {step_id} {segment_id}"
                                # 直接插入到Text控件
                                if hasattr(self.ui, 'log_text'):
                                    import tkinter as tk
                                    import datetime
                                    timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
                                    self.ui.log_text.insert(tk.END, timestamp + anchor_message + "\n", "find")
                                    self.ui.log_text.see(tk.END)
                                    self.ui.log_text.update_idletasks()
                                # 使用UI对象的log方法
                                self.ui.log(anchor_message, tag="find")
                                self.ui.log(f"[代码] {line.strip()}", tag="info")
                            except Exception as e:
                                print(f"向UI输出锚点信息失败: {str(e)}")
                                import traceback
                                print(traceback.format_exc())
                        
                        # 使用辅助方法直接输出锚点信息到UI
                        if hasattr(self, 'display_anchor'):
                            self.display_anchor(filename, i+1, tc_id, step_id, segment_id)
                        
                        # 统计到TC级别
                        if tc_id not in file_tc_stats:
                            file_tc_stats[tc_id] = {"anchors": 0, "steps": {}, "inserted": 0}
                        file_tc_stats[tc_id]["anchors"] += 1
                        
                        # 统计到STEP级别
                        if step_id not in file_tc_stats[tc_id]["steps"]:
                            file_tc_stats[tc_id]["steps"][step_id] = {"segments": {}, "inserted": 0}
                        
                        # 统计到segment级别
                        if segment_id not in file_tc_stats[tc_id]["steps"][step_id]["segments"]:
                            file_tc_stats[tc_id]["steps"][step_id]["segments"][segment_id] = 0
                        file_tc_stats[tc_id]["steps"][step_id]["segments"][segment_id] += 1
                        
                        # 收集锚点详情用于生成报告
                        if not hasattr(self, 'anchor_details'):
                            self.anchor_details = {}
                        if file_path not in self.anchor_details:
                            self.anchor_details[file_path] = []
                        
                        # 收集锚点信息
                        anchor_info = {
                            'tc_id': tc_id,
                            'step_id': step_id,
                            'segment_id': segment_id,
                            'line': i+1,
                            'success': False  # 默认为False，如果找到桩代码并插入则设为True
                        }
                        self.anchor_details[file_path].append(anchor_info)
                        
                        # 立即向UI输出锚点信息
                        if self.ui:
                            print(f"向UI发送锚点信息: {filename} 行 {i+1}: {tc_id} {step_id} {segment_id}")
                            try:
                                # 直接构造消息并同步输出到UI，不使用异步方式
                                anchor_message = f"[锚点] 在文件 {filename} 的第 {i+1} 行找到锚点: {tc_id} {step_id} {segment_id}"
                                print(f"发送消息: {anchor_message}")
                                
                                # 直接调用UI日志方法，不使用after或lambda
                                self.ui.log(anchor_message, tag="find")
                                
                                # 锚点代码内容显示
                                line_content = line.strip()
                                self.ui.log(f"[代码] {line_content}", tag="info")
                                
                                # 验证日志输出
                                print(f"UI日志调用成功，锚点信息和代码内容已显示")
                            except Exception as e:
                                print(f"UI日志调用异常: {str(e)}")
                                print(f"异常详情: {traceback.format_exc()}")
                                # 尝试确认UI对象和方法存在
                                print(f"UI存在: {self.ui is not None}")
                                if self.ui:
                                    print(f"UI类型: {type(self.ui).__name__}")
                                    print(f"UI log方法存在: {hasattr(self.ui, 'log')}")
                                    if hasattr(self.ui, 'log'):
                                        print(f"log方法类型: {type(self.ui.log).__name__}")
                        
                        # 查找传统模式的code注释
                        j = i + 1
                        traditional_code = None
                        if j < len(lines) and ('// code:' in lines[j].lower() or '//code:' in lines[j].lower()):
                            code_line = lines[j]
                            code_start = max(code_line.lower().find('// code:') + 8, code_line.lower().find('//code:') + 7)
                            traditional_code = code_line[code_start:].strip()
                            logger.info(f"找到传统模式code注释: {anchor_desc}")
                        
                        # 查找YAML配置中的桩代码
                        yaml_code = self.find_stub_code(tc_id, step_id, segment_id)
                        
                        # 优先使用YAML配置中的桩代码，如果没有再使用传统模式的code
                        code_to_insert = yaml_code or traditional_code
                        
                        if code_to_insert:
                            # 处理并添加代码
                            indent = len(line) - len(line.lstrip())
                            indent_str = ' ' * indent
                            stub_lines = code_to_insert.splitlines()
                            
                            # 记录桩代码插入详情
                            code_source = "YAML配置" if yaml_code else "传统注释"
                            logger.info(f"插入 {tc_id} {step_id} {segment_id} 桩代码 (来源: {code_source}, {len(stub_lines)}行)")
                            
                            # 向UI输出插桩详情
                            if self.ui:
                                self.ui.log(f"[插桩] 在文件 {filename} 第 {i+1} 行插入 {tc_id} {step_id} {segment_id} 桩代码 ({len(stub_lines)}行)", tag="insert")
                                # 最多显示3行代码预览
                                preview_lines = stub_lines[:3] if len(stub_lines) > 3 else stub_lines
                                for idx, preview in enumerate(preview_lines):
                                    self.ui.log(f"[代码] {' '*4}{preview}", tag="info")
                                if len(stub_lines) > 3:
                                    self.ui.log(f"[代码] {' '*4}...还有 {len(stub_lines)-3} 行未显示...", tag="info")
                            
                            # 添加桩代码行
                            for stub_line in stub_lines:
                                new_lines.append(f"{indent_str}{stub_line}  // 通过桩插入")
                                file_stubs_inserted += 1
                                self.stats["inserted_stubs"] += 1
                                
                                # 更新锚点详情，标记插入成功
                                for anchor in self.anchor_details.get(file_path, []):
                                    if (anchor['tc_id'] == tc_id and 
                                        anchor['step_id'] == step_id and 
                                        anchor['segment_id'] == segment_id and 
                                        anchor['line'] == i+1):
                                        anchor['success'] = True
                                        anchor['inserted_lines'] = len(stub_lines)
                                        break
                            
                            # 记录到TC统计
                            file_tc_stats[tc_id]["inserted"] += len(stub_lines)
                        else:
                            logger.warning(f"未找到 {tc_id} {step_id} {segment_id} 对应的桩代码")
                i += 1
            
            # 文件级别TC统计输出
            if file_tc_stats:
                logger.info(f"文件 {filename} 中的TC统计:")
                for tc_id, info in file_tc_stats.items():
                    tc_msg = f"  TC {tc_id}: 找到 {info['anchors']} 个锚点, 插入 {info['inserted']} 行代码"
                    logger.info(tc_msg)
                    if self.ui:
                        self.ui.log(f"[TC统计] {tc_msg}")
                    
                    # 输出步骤级别统计
                    for step_id, step_info in info["steps"].items():
                        segments_count = len(step_info["segments"])
                        segments_str = ", ".join(step_info["segments"].keys())
                        step_msg = f"    └─ {step_id}: {segments_count}个代码段 ({segments_str})"
                        logger.info(step_msg)
                        if self.ui:
                            self.ui.log(f"[步骤] {step_msg}")
                
                # 合并到全局TC统计
                for tc_id, info in file_tc_stats.items():
                    # 确保全局统计中存在此TC
                    if not hasattr(self, 'tc_stats'):
                        self.tc_stats = {}
                    
                    if tc_id not in self.tc_stats:
                        self.tc_stats[tc_id] = {"anchors": 0, "files": set(), "steps": {}, "inserted": 0}
                    
                    # 更新统计数据
                    self.tc_stats[tc_id]["anchors"] += info["anchors"]
                    self.tc_stats[tc_id]["files"].add(filename)
                    self.tc_stats[tc_id]["inserted"] += info["inserted"]
                    
                    # 合并步骤信息
                    for step_id, step_info in info["steps"].items():
                        if step_id not in self.tc_stats[tc_id]["steps"]:
                            self.tc_stats[tc_id]["steps"][step_id] = {"segments": {}}
                        
                        # 合并segment信息
                        for seg_id, seg_count in step_info["segments"].items():
                            if seg_id not in self.tc_stats[tc_id]["steps"][step_id]["segments"]:
                                self.tc_stats[tc_id]["steps"][step_id]["segments"][seg_id] = 0
                            self.tc_stats[tc_id]["steps"][step_id]["segments"][seg_id] += seg_count
        except Exception as file_err:
            # 处理整个文件失败的情况
            logger.error(f"处理文件 {filename} 异常: {str(file_err)}")
            logger.error(traceback.format_exc())
        
        return '\n'.join(new_lines)
    
    def find_stub_code(self, tc_id, step_id, segment_id):
        """从YAML配置中查找对应的桩代码"""
        try:
            # 检查YAML配置是否存在该桩点
            if not self.yaml_config:
                logger.warning(f"YAML配置为空，无法查找 {tc_id}.{step_id}.{segment_id}")
                return None
                
            if tc_id in self.yaml_config:
                if step_id in self.yaml_config[tc_id]:
                    if segment_id in self.yaml_config[tc_id][step_id]:
                        stub_code = self.yaml_config[tc_id][step_id][segment_id]
                        logger.info(f"找到桩代码 {tc_id}.{step_id}.{segment_id}: {len(stub_code.splitlines() if isinstance(stub_code, str) else '0')}行")
                        return stub_code
                    else:
                        logger.info(f"在 {tc_id}.{step_id} 中未找到segment {segment_id}")
                else:
                    logger.info(f"在 {tc_id} 中未找到步骤 {step_id}")
            else:
                logger.info(f"YAML配置中未找到测试用例 {tc_id}")
        except Exception as e:
            logger.error(f"查找桩代码 {tc_id}.{step_id}.{segment_id} 时出错: {str(e)}")
            logger.error(traceback.format_exc())
            
        return None

    def process_file(self, file_path: str, callback=None) -> Tuple[bool, str, int]:
        """
        处理单个文件，插入桩代码
        
        Args:
            file_path: 文件路径
            callback: 可选回调函数，用于报告处理进度
            
        Returns:
            Tuple[bool, str, int]: (成功/失败, 消息, 插入桩点数量)
        """
        logger.info(f"处理文件: {file_path}")
        
        if self.using_mocks:
            logger.warning(f"使用模拟处理: {file_path}")
            return True, "成功 (模拟)", 0
        
        # 实际处理文件
        try:
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}", 0
            
            # 处理文件并返回结果
            success, message, count = self.parser.process_file(file_path)
            
            if success:
                logger.info(f"文件处理成功: {file_path}, 插入了 {count} 个桩点")
            else:
                logger.warning(f"文件处理失败: {file_path}, {message}")
            
            return success, message, count
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0
