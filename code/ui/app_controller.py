#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave Controller 模块 - 连接UI和核心处理逻辑
"""

import os
import sys
import threading
import logging
import traceback
import shutil
import datetime
from typing import Callable, Dict, List, Optional, Any, Tuple
from ..utils.logger import add_ui_handler

# 定义一个模拟的StubProcessor类，在无法导入真实类时使用
class MockStubProcessor:
    def __init__(self):
        self.logger = logging.getLogger('yamlweave')
        self.logger.error("使用了模拟的StubProcessor实现")
        self.yaml_file = None
    
    def set_yaml_file(self, yaml_file):
        self.yaml_file = yaml_file
        self.logger.warning(f"模拟StubProcessor: 设置YAML文件 {yaml_file}")
    
    def process_directory(self, root_dir):
        self.logger.warning(f"模拟StubProcessor: 无法处理目录 {root_dir}")
        return {
            "total_files": 0,
            "processed_files": 0,
            "successful_stubs": 0,
            "errors": [{
                "file": "N/A",
                "error": "StubProcessor未正确加载，无法执行处理"
            }]
        }

# 尝试各种导入方式
try:
    # 首先尝试从当前目录或项目根目录导入stub_processor.py
    import sys
    import os
    # 获取可能路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parent_dir = os.path.dirname(current_dir)
    
    # 调试信息
    logging.info(f"当前目录: {current_dir}")
    logging.info(f"父级目录: {parent_dir}")
    
    # 将当前目录和父级目录添加到sys.path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    try:
        # 优先使用相对导入
        from code.core.stub_processor import StubProcessor
        logging.info("成功从code.core包导入StubProcessor")
        found_real_processor = True
    except ImportError:
        try:
            # 尝试从code.core导入
            from code.core.stub_processor import StubProcessor
            logging.info("成功从code.core包导入StubProcessor")
            found_real_processor = True
        except ImportError:
            try:
                # 尝试从YAMLWeave包导入
                from YAMLWeave.core.stub_processor import StubProcessor
                logging.info("成功从YAMLWeave包导入StubProcessor")
                found_real_processor = True
            except ImportError:
                # 与程序一起打包时，此模块可能不存在，使用模拟类
                StubProcessor = MockStubProcessor
                found_real_processor = False
                logging.getLogger('yamlweave').warning("无法导入StubProcessor，将使用模拟实现")
except Exception as e:
    logging.error(f"导入StubProcessor时发生未预期的错误: {str(e)}")
    StubProcessor = MockStubProcessor
    found_real_processor = False

# 添加StubProcessor的兼容适配器类
class StubProcessorAdapter:
    """
    适配器类，为StubProcessor提供兼容接口，确保无论导入哪个版本的StubProcessor都能正常工作
    """
    
    def __init__(self, processor):
        """
        初始化适配器
        
        Args:
            processor: 原始StubProcessor实例
        """
        self.processor = processor
        self.logger = logging.getLogger('yamlweave')
        self.ui = None  # 添加UI属性
        
        # 检查处理器属性，打印详细诊断信息
        self.logger.info("创建StubProcessor适配器")
        self.logger.info(f"处理器类型: {type(processor).__name__}")
        
        # 检查关键方法是否存在
        if hasattr(processor, 'process_files'):
            self.logger.info("处理器具有process_files方法")
        elif hasattr(processor, 'process_directory'):
            self.logger.info("处理器具有process_directory方法")
        else:
            self.logger.warning("处理器既没有process_files也没有process_directory方法，可能需要修复")
        
    def set_yaml_file(self, yaml_file):
        """设置YAML配置文件"""
        try:
            if hasattr(self.processor, 'set_yaml_file'):
                self.processor.set_yaml_file(yaml_file)
                self.logger.info(f"通过set_yaml_file方法设置YAML文件: {yaml_file}")
            elif hasattr(self.processor, 'yaml_file'):
                self.processor.yaml_file = yaml_file
                self.logger.info(f"通过直接属性设置YAML文件: {yaml_file}")
            else:
                self.logger.warning(f"处理器不支持yaml_file设置，可能需要更新或添加此功能")
        except Exception as e:
            self.logger.error(f"设置YAML文件时出错: {str(e)}")
    
    def process_directory(self, root_dir):
        """
        处理目录 - 兼容接口
        
        如果原始处理器有process_directory方法，直接调用；
        如果没有，但有process_files方法，则进行适配调用。
        """
        try:
            # 详细日志
            self.logger.info(f"适配器处理目录: {root_dir}")
            
            # 创建必要的时间戳，用于备份和结果目录
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = f"{root_dir}_backup_{timestamp}"
            stubbed_dir = f"{root_dir}_stubbed_{timestamp}"
            
            if hasattr(self.processor, 'process_directory'):
                # 调用原生process_directory方法
                self.logger.info("使用原生process_directory方法")
                
                # 确保processor具有必要的目录属性
                self.processor.project_dir = root_dir
                
                # 尝试创建备份目录和结果目录
                try:
                    self.logger.info(f"开始备份整个项目目录: {root_dir} -> {backup_dir}")
                    shutil.copytree(root_dir, backup_dir)
                    self.logger.info(f"项目目录备份成功: {backup_dir}")
                    
                    self.logger.info(f"创建插桩结果目录: {stubbed_dir}")
                    shutil.copytree(root_dir, stubbed_dir)
                    
                    # 将备份和结果目录设置为处理器属性
                    self.processor.backup_dir = backup_dir
                    self.processor.stubbed_dir = stubbed_dir
                except Exception as backup_error:
                    self.logger.error(f"创建备份或结果目录失败: {str(backup_error)}")
                
                # 调用原始方法处理目录
                result = self.processor.process_directory(root_dir)
                
                # 处理完成后，将结果目录信息添加到返回结果中
                if not hasattr(result, "backup_dir"):
                    result["backup_dir"] = backup_dir
                if not hasattr(result, "stubbed_dir"):
                    result["stubbed_dir"] = stubbed_dir
                
                return result
            elif hasattr(self.processor, 'process_files'):
                # 通过process_files方法适配
                self.logger.info("通过process_files方法适配process_directory调用")
                
                # 确保正确设置project_dir
                self.processor.project_dir = root_dir
                
                # 调用process_files方法
                try:
                    success, message, stats = self.processor.process_files()
                    
                    # 构造与process_directory兼容的返回格式
                    result = {
                        "total_files": stats.get('scanned_files', 0),
                        "processed_files": stats.get('updated_files', 0),
                        "successful_stubs": stats.get('inserted_stubs', 0),
                        "errors": [{"file": "统计信息", "error": f"失败文件数: {stats.get('failed_files', 0)}"}] 
                        if stats.get('failed_files', 0) > 0 else [],
                        "backup_dir": getattr(self.processor, 'backup_dir', backup_dir),
                        "stubbed_dir": getattr(self.processor, 'stubbed_dir', stubbed_dir)
                    }
                    
                    return result
                except AttributeError as attr_err:
                    # 特殊处理process_files方法的属性错误
                    self.logger.error(f"调用process_files方法时出现属性错误: {str(attr_err)}")
                    
                    # 尝试添加process_files方法
                    if "'StubProcessor' object has no attribute 'process_files'" in str(attr_err):
                        self.logger.info("检测到StubProcessor缺少process_files方法，尝试动态添加")
                        
                        # 尝试导入core版本的process_files方法
                        try:
                            # 尝试从core目录导入StubProcessor
                            import sys
                            import os
                            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                            
                            # 先尝试直接导入
                            try:
                                from code.core.stub_processor import StubProcessor as CoreStubProcessor
                                self.logger.info("成功导入core版本的StubProcessor")
                                
                                # 将core版本的process_files方法复制到当前处理器
                                if hasattr(CoreStubProcessor, 'process_files'):
                                    import types
                                    self.processor.process_files = types.MethodType(
                                        CoreStubProcessor.process_files, self.processor)
                                    self.logger.info("成功添加process_files方法到处理器")
                                    
                                    # 使用新添加的方法
                                    success, message, stats = self.processor.process_files()
                                    
                                    # 构造与process_directory兼容的返回格式
                                    result = {
                                        "total_files": stats.get('scanned_files', 0),
                                        "processed_files": stats.get('updated_files', 0),
                                        "successful_stubs": stats.get('inserted_stubs', 0),
                                        "errors": [{"file": "统计信息", "error": f"失败文件数: {stats.get('failed_files', 0)}"}] 
                                        if stats.get('failed_files', 0) > 0 else [],
                                        "backup_dir": getattr(self.processor, 'backup_dir', backup_dir),
                                        "stubbed_dir": getattr(self.processor, 'stubbed_dir', stubbed_dir)
                                    }
                                    
                                    return result
                            except ImportError:
                                self.logger.warning("无法导入core版本的StubProcessor")
                            
                            # 失败处理：返回默认错误结果
                            return {
                                "total_files": 0,
                                "processed_files": 0,
                                "successful_stubs": 0,
                                "errors": [{"file": "适配错误", "error": f"处理器缺少process_files方法: {str(attr_err)}"}]
                            }
                        except Exception as import_err:
                            self.logger.error(f"尝试导入core版本StubProcessor时出错: {str(import_err)}")
                            return {
                                "total_files": 0,
                                "processed_files": 0,
                                "successful_stubs": 0,
                                "errors": [{"file": "导入错误", "error": str(import_err)}]
                            }
                    
                    # 其他属性错误
                    return {
                        "total_files": 0,
                        "processed_files": 0,
                        "successful_stubs": 0,
                        "errors": [{"file": "属性错误", "error": str(attr_err)}]
                    }
            else:
                # 两种方法都不可用，尝试创建新的处理器
                self.logger.error("StubProcessor既没有process_directory也没有process_files方法，尝试使用替代方法")
                
                # 创建备份和结果目录
                try:
                    self.logger.info(f"开始备份整个项目目录: {root_dir} -> {backup_dir}")
                    shutil.copytree(root_dir, backup_dir)
                    self.logger.info(f"项目目录备份成功: {backup_dir}")
                    
                    self.logger.info(f"创建插桩结果目录: {stubbed_dir}")
                    shutil.copytree(root_dir, stubbed_dir)
                except Exception as backup_error:
                    self.logger.error(f"创建备份或结果目录失败: {str(backup_error)}")
                
                # 尝试从core目录导入StubProcessor并创建新的实例
                try:
                    from code.core.stub_processor import StubProcessor as CoreStubProcessor
                    core_processor = CoreStubProcessor(root_dir)
                    core_processor.backup_dir = backup_dir
                    core_processor.stubbed_dir = stubbed_dir
                    result = core_processor.process_files()
                    
                    # 转换结果格式
                    if isinstance(result, tuple) and len(result) >= 3:
                        success, message, stats = result
                        return {
                            "total_files": stats.get('scanned_files', 0),
                            "processed_files": stats.get('updated_files', 0),
                            "successful_stubs": stats.get('inserted_stubs', 0),
                            "errors": [] if success else [{"file": "处理错误", "error": message}],
                            "backup_dir": backup_dir,
                            "stubbed_dir": stubbed_dir
                        }
                except Exception as core_err:
                    self.logger.error(f"尝试使用核心处理器时出错: {str(core_err)}")
                
                # 如果所有尝试都失败，返回错误结果
                return {
                    "total_files": 0,
                    "processed_files": 0,
                    "successful_stubs": 0,
                    "errors": [{"file": "N/A", "error": "StubProcessor没有可用的处理方法"}],
                    "backup_dir": backup_dir,
                    "stubbed_dir": stubbed_dir
                }
        except Exception as e:
            self.logger.error(f"处理目录时出错: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {
                "total_files": 0,
                "processed_files": 0,
                "successful_stubs": 0,
                "errors": [{"file": "异常", "error": str(e)}]
            }

class AppController:
    """
    应用控制器，连接UI和核心处理
    """
    
    def __init__(self, ui=None):
        # 实例变量初始化 - 首先设置UI属性
        self.ui = ui
        
        # 日志系统初始化
        self.setup_logging()
        
        # 记录处理器初始化
        try:
            # 创建StubProcessor实例并包装到适配器中
            raw_processor = StubProcessor(ui=self.ui)
            self.processor = StubProcessorAdapter(raw_processor)
            
            # 设置UI引用
            if self.ui and self.processor:
                self.processor.ui = self.ui
                # 设置内部处理器的UI引用
                if hasattr(self.processor, 'processor') and hasattr(self.processor.processor, 'ui'):
                    self.processor.processor.ui = self.ui
                    self.log_info("初始化时设置了处理器的UI引用")
            
            if not found_real_processor:
                self.log_warning("使用模拟的StubProcessor实现，功能将受限")
            else:
                self.log_info("成功初始化StubProcessor")
                
                # 检查处理方法
                if hasattr(raw_processor, 'process_directory'):
                    self.log_info("StubProcessor具有process_directory方法")
                elif hasattr(raw_processor, 'process_files'):
                    self.log_info("StubProcessor具有process_files方法")
                else:
                    self.log_warning("StubProcessor不具备处理方法，功能受限")
        except Exception as e:
            self.log_error(f"初始化处理器失败: {str(e)}")
            self.processor = None
        
        # UI回调设置
        if self.ui is not None:
            try:
                self.ui.set_process_callback(self.process_directory)
                self.ui.set_reverse_callback(self.export_yaml)
                self.log_info("成功设置处理回调")
            except Exception as e:
                self.log_error(f"设置UI回调失败: {str(e)}")
    
    def setup_logging(self):
        """设置日志系统"""
        self.logger = logging.getLogger('yamlweave')
        self.logger.setLevel(logging.INFO)
        # 不再单独添加文件handler，全部由全局setup_global_logger统一管理
        if self.ui:
            try:
                add_ui_handler(self.ui)
            except Exception as e:
                self.logger.error(f"添加UI日志处理器失败: {str(e)}")
    
    def log_info(self, message):
        """记录信息级别日志"""
        self.logger.info(message)
        if self.ui:
            self.ui.log(f"[信息] {message}")
    
    def log_warning(self, message):
        """记录警告级别日志"""
        self.logger.warning(message)
        if self.ui:
            self.ui.log(f"[警告] {message}")
    
    def log_error(self, message):
        """记录错误级别日志"""
        self.logger.error(message)
        if self.ui:
            self.ui.log(f"[错误] {message}")

    def log_missing(self, message):
        """记录缺失锚点信息"""
        self.logger.warning(message)
        if self.ui:
            self.ui.log(f"[缺失] {message}", tag="missing")
    
    def process_directory(self, root_dir, yaml_file=None):
        """处理目录"""
        if not root_dir or not os.path.isdir(root_dir):
            self.log_error(f"无效的目录路径: {root_dir}")
            return
        
        # 更新状态
        if self.ui:
            self.ui.update_status("正在处理...")
        
        # 创建并启动处理线程
        thread = threading.Thread(
            target=self._process_directory_thread,
            args=(root_dir, yaml_file)
        )
        thread.daemon = True
        thread.start()
    
    def _process_directory_thread(self, root_dir, yaml_file=None):
        """在独立线程中运行目录处理"""
        try:
            self.log_info(f"开始处理目录: {root_dir}")
            
            # 处理器检查
            if self.processor is None:
                self.log_error("处理器未初始化，无法执行操作")
                if self.ui:
                    self.ui.update_status("错误: 处理器未初始化")
                return
            
            # 设置YAML文件
            if yaml_file:
                self.log_info(f"使用YAML配置: {yaml_file}")
                self.processor.set_yaml_file(yaml_file)
                
                # 如果处理器有内部处理器（适配器情况），确保内部处理器也设置了yaml_file
                if hasattr(self.processor, 'processor') and hasattr(self.processor.processor, 'yaml_file'):
                    self.processor.processor.yaml_file = yaml_file
                    self.log_info("已设置内部处理器的yaml_file")
            
            # 确保UI引用正确传递给处理器
            if self.ui:
                self.log_info("设置UI引用给处理器")
                # 设置适配器的UI引用
                if hasattr(self.processor, 'ui'):
                    self.processor.ui = self.ui
                
                # 设置内部处理器的UI引用
                if hasattr(self.processor, 'processor') and hasattr(self.processor.processor, 'ui'):
                    self.processor.processor.ui = self.ui
                    self.log_info("已设置内部处理器的UI引用")
            
            # 处理目录
            try:
                result = self.processor.process_directory(root_dir)
                
                # 处理结果
                self.log_info(f"文件总数: {result.get('total_files', 0)}")
                self.log_info(f"处理成功文件: {result.get('processed_files', 0)}")
                self.log_info(f"成功插入桩点: {result.get('successful_stubs', 0)}")

                missing = result.get('missing_stubs', 0)
                if missing > 0:
                    self.log_warning(f"缺失桩代码锚点: {missing} 个")
                    details = result.get('missing_anchor_details', [])
                    if details:
                        self.log_warning("以下锚点在YAML中未找到:")
                        for entry in details:
                            msg = f"{entry.get('file')} 第 {entry.get('line')} 行: {entry.get('anchor')}"
                            self.log_missing(msg)
                
                # 显示备份和结果目录信息
                backup_dir = result.get('backup_dir', '')
                stubbed_dir = result.get('stubbed_dir', '')
                
                if backup_dir:
                    self.log_info(f"原始项目备份目录: {backup_dir}")
                    if self.ui:
                        self.ui.log(f"[信息] 原始项目备份在: {os.path.basename(backup_dir)}")
                
                if stubbed_dir:
                    self.log_info(f"处理结果目录: {stubbed_dir}")
                    if self.ui:
                        self.ui.log(f"[信息] 处理结果保存在: {os.path.basename(stubbed_dir)}")
                
                # 如果有错误
                errors = result.get('errors', [])
                if errors:
                    self.log_error(f"遇到 {len(errors)} 个错误")
                    for error in errors:
                        self.log_error(f"  - {error.get('file')}: {error.get('error')}")
                
                # 更新状态
                if self.ui:
                    self.ui.update_status(f"完成. 处理了 {result.get('processed_files', 0)} 个文件")
            except AttributeError as attr_err:
                # 特殊处理AttributeError，可能是'process_files'方法不存在
                error_msg = f"处理器方法调用失败: {str(attr_err)}"
                self.log_error(error_msg)
                self.log_error(traceback.format_exc())
                self.log_error("可能是处理器方法不匹配导致的问题 - 尝试兼容处理")
                
                # 尝试兼容处理 - 直接使用基础处理器
                if hasattr(self.processor, 'processor'):
                    try:
                        if hasattr(self.processor.processor, 'process_files'):
                            self.log_info("尝试直接调用内部处理器的process_files方法")
                            # 确保设置project_dir和yaml_file
                            self.processor.processor.project_dir = root_dir
                            if yaml_file:
                                self.processor.processor.yaml_file = yaml_file
                                
                            # 直接调用process_files方法
                            success, message, stats = self.processor.processor.process_files()
                            if success:
                                self.log_info(f"处理成功: {message}")
                                self.log_info(f"处理统计: 扫描 {stats.get('scanned_files', 0)}, 更新 {stats.get('updated_files', 0)}, 插入 {stats.get('inserted_stubs', 0)}")
                                
                                # 显示备份和结果目录信息
                                if hasattr(self.processor.processor, 'backup_dir'):
                                    backup_dir = self.processor.processor.backup_dir
                                    self.log_info(f"原始项目备份目录: {backup_dir}")
                                    if self.ui:
                                        self.ui.log(f"[信息] 原始项目备份在: {os.path.basename(backup_dir)}")
                                
                                if hasattr(self.processor.processor, 'stubbed_dir'):
                                    stubbed_dir = self.processor.processor.stubbed_dir
                                    self.log_info(f"处理结果目录: {stubbed_dir}")
                                    if self.ui:
                                        self.ui.log(f"[信息] 处理结果保存在: {os.path.basename(stubbed_dir)}")
                                
                                if self.ui:
                                    self.ui.update_status(f"完成. 处理了 {stats.get('updated_files', 0)} 个文件")
                            else:
                                self.log_error(f"处理失败: {message}")
                                if self.ui:
                                    self.ui.update_status("处理失败")
                        else:
                            self.log_error("内部处理器也没有可用的process_files方法")
                            if self.ui:
                                self.ui.update_status("错误: 处理器方法不可用")
                    except Exception as inner_err:
                        self.log_error(f"兼容处理尝试失败: {str(inner_err)}")
                        self.log_error(traceback.format_exc())
                        if self.ui:
                            self.ui.update_status("处理失败: 兼容尝试出错")
                else:
                    self.log_error("无法进行兼容处理: 处理器没有内部处理器")
                    if self.ui:
                        self.ui.update_status("错误: 无法兼容处理")
        except Exception as e:
            error_msg = f"处理目录时出错: {str(e)}"
            self.log_error(error_msg)
            self.log_error(traceback.format_exc())
            
            # 更新状态
            if self.ui:
                self.ui.update_status("处理时出错")

    def export_yaml(self, root_dir, output_file):
        """反向生成YAML配置文件"""
        if not root_dir or not os.path.isdir(root_dir):
            self.log_error(f"无效的目录路径: {root_dir}")
            return

        thread = threading.Thread(
            target=self._export_yaml_thread,
            args=(root_dir, output_file),
        )
        thread.daemon = True
        thread.start()

    def _export_yaml_thread(self, root_dir, output_file):
        try:
            self.log_info(f"开始导出YAML: {output_file}")
            if self.processor is None:
                self.log_error("处理器未初始化，无法导出")
                if self.ui:
                    self.ui.update_status("错误: 处理器未初始化")
                return

            success = self.processor.extract_to_yaml(root_dir, output_file)
            if success:
                if self.ui:
                    self.ui.log(f"[成功] YAML已导出到: {os.path.basename(output_file)}", tag="success")
                    self.ui.update_status("导出完成")
                self.log_info("YAML导出成功")
            else:
                self.log_error("YAML导出失败")
                if self.ui:
                    self.ui.update_status("导出失败")
        except Exception as e:
            self.log_error(f"导出YAML出错: {str(e)}")
            self.log_error(traceback.format_exc())
            if self.ui:
                self.ui.update_status("导出失败")


# def main():
#     """创建并启动应用"""
#     import tkinter as tk
#     from ..ui.app_ui import AutoStubUI  # 使用相对导入
    
#     root = tk.Tk()
#     app_ui = AutoStubUI(root)
#     controller = AppController(app_ui)
    
#     root.mainloop()


# if __name__ == "__main__":
#     main() 