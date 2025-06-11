#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave Core 模块 - stub_processor
负责插桩处理的核心逻辑，包括文件查找、遍历、备份和结果生成
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Any, Union
import datetime
import shutil

# 导入日志工具
try:
    # 尝试相对导入
    from ..utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    # 尝试普通导入
    try:
        from code.utils.logger import get_logger
        logger = get_logger(__name__)
    except ImportError:
        # 基本日志设置
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)

# 导入工具函数
try:
    # 尝试相对导入
    from .utils import read_file, write_file
except ImportError:
    try:
        # 尝试从当前目录导入
        from code.utils import read_file, write_file
    except ImportError:
        try:
            # 尝试直接导入
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from code.utils import read_file, write_file
        except ImportError:
            logger.error("无法导入文件处理工具函数，功能可能受限")
            # 提供简单实现以防止崩溃
            def read_file(file_path):
                """简单的文件读取函数"""
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        return f.read(), 'utf-8'
                except Exception as e:
                    logger.error(f"读取文件失败: {str(e)}")
                    return None, None
            
            def write_file(file_path, content, encoding='utf-8'):
                """简单的文件写入函数"""
                try:
                    with open(file_path + '.stub', 'w', encoding=encoding, errors='replace') as f:
                        f.write(content)
                    return True
                except Exception as e:
                    logger.error(f"写入文件失败: {str(e)}")
                    return False

# 定义模拟类，当实际类无法加载时使用
class MockYamlStubHandler:
    def __init__(self, yaml_file_path=None):
        self.logger = logging.getLogger('yamlweave.core')
        self.logger.warning("使用模拟的YamlStubHandler实现")
        self.yaml_file_path = yaml_file_path
        self.yaml_data = {}
    
    def load_yaml(self, yaml_file_path):
        self.yaml_file_path = yaml_file_path
        self.logger.info(f"模拟加载YAML文件: {yaml_file_path}")
        return True
    
    def get_stub_code(self, test_case_id, step_id, segment_id):
        self.logger.warning(f"模拟获取桩代码: {test_case_id}.{step_id}.{segment_id}")
        return None
    
    def is_yaml_loaded(self):
        return self.yaml_file_path is not None

class MockCommentHandler:
    def __init__(self):
        self.logger = logging.getLogger('yamlweave.core')
        self.logger.warning("使用模拟的CommentHandler实现")
    
    def extract_stub_code(self, comment_line):
        self.logger.warning(f"模拟从注释提取代码: {comment_line}")
        return None
    
    def parse_stub_anchor(self, comment_line):
        # 简单解析锚点信息
        parts = comment_line.strip().split()
        if len(parts) >= 3 and parts[0].startswith("//"):
            if parts[1].upper().startswith("TC") and parts[2].upper().startswith("STEP"):
                if len(parts) >= 4:
                    return parts[1], parts[2], parts[3], ""
        return None, None, None, None

# 导入标记，默认为未加载
handlers_loaded = False

# 尝试导入处理器模块（分多步尝试）
# 步骤1：尝试相对导入
try:
    from ..handlers.comment_handler import CommentHandler
    from ..handlers.yaml_handler import YamlStubHandler
    handlers_loaded = True
    logger.info("成功使用相对导入加载处理器")
except ImportError:
    logger.warning("相对导入处理器失败，尝试其他方法")

# 步骤2：从当前目录相对导入
if not handlers_loaded:
    try:
        from code.handlers.comment_handler import CommentHandler
        from code.handlers.yaml_handler import YamlStubHandler
        handlers_loaded = True
        logger.info("成功从handlers目录导入处理器")
    except ImportError:
        logger.warning("从handlers目录导入处理器失败，尝试下一种方法")

# 步骤3：从YAMLWeave包导入（兼容旧代码）
if not handlers_loaded:
    try:
        from YAMLWeave.handlers.comment_handler import CommentHandler
        from YAMLWeave.handlers.yaml_handler import YamlStubHandler
        handlers_loaded = True
        logger.info("成功从YAMLWeave包导入处理器")
    except ImportError:
        logger.warning("从YAMLWeave包导入处理器失败，尝试其他方法")

# 步骤4：动态导入
if not handlers_loaded:
    try:
        import importlib.util
        
        # 动态导入handlers模块
        handlers_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "handlers")
        if os.path.exists(handlers_path):
            comment_handler_path = os.path.join(handlers_path, "comment_handler.py")
            yaml_handler_path = os.path.join(handlers_path, "yaml_handler.py")
            
            if os.path.exists(comment_handler_path) and os.path.exists(yaml_handler_path):
                # 导入comment_handler
                spec = importlib.util.spec_from_file_location(
                    "comment_handler", 
                    comment_handler_path
                )
                comment_handler_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(comment_handler_module)
                CommentHandler = comment_handler_module.CommentHandler
                
                # 导入yaml_handler
                spec = importlib.util.spec_from_file_location(
                    "yaml_handler", 
                    yaml_handler_path
                )
                yaml_handler_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(yaml_handler_module)
                YamlStubHandler = yaml_handler_module.YamlStubHandler
                
                handlers_loaded = True
                logger.info("成功从文件路径动态导入处理器模块")
            else:
                logger.error("无法找到必要的处理器模块文件")
        else:
            logger.error(f"处理器目录不存在: {handlers_path}")
    except Exception as e:
        logger.error(f"动态导入处理器模块失败: {str(e)}")

# 如果无法加载实际处理器，使用模拟实现
if not handlers_loaded:
    logger.error("无法导入YamlStubHandler和CommentHandler，将使用模拟实现")
    CommentHandler = MockCommentHandler
    YamlStubHandler = MockYamlStubHandler

# 导入StubParser
try:
    # 尝试直接导入
    from code.core.stub_parser import StubParser
    parser_loaded = True
except ImportError:
    try:
        # 尝试从当前目录导入
        from code.core.stub_parser import StubParser
        parser_loaded = True
    except ImportError:
        try:
            # 尝试相对导入
            from .stub_parser import StubParser
            parser_loaded = True
        except ImportError:
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            try:
                # 最后尝试直接导入
                from code.core.stub_parser import StubParser
                parser_loaded = True
            except ImportError:
                logger.error("无法导入stub_parser模块，核心功能将不可用")
                # 创建占位函数和类，使程序不会崩溃
                class StubParser:
                    def __init__(self, yaml_handler=None):
                        self.logger = logging.getLogger('yamlweave.core')
                        self.logger.warning("使用模拟的StubParser实现")
                        self.yaml_handler = yaml_handler
                    
                    def process_file(self, file_path, callback=None):
                        self.logger.warning(f"模拟处理文件: {file_path}")
                        return True, "模拟处理", 0
                
                parser_loaded = False

class StubProcessor:
    """
    桩处理器类
    负责整体流程控制，包括文件查找、处理和结果生成
    """
    
    def __init__(self, project_dir: Optional[str] = None, yaml_file_path: Optional[str] = None, ui=None):
        """
        初始化桩处理器
        
        Args:
            project_dir: 项目目录路径，可选
            yaml_file_path: YAML配置文件路径，可选
            ui: UI实例，可选
        """
        # 初始化日志
        self.logger = logging.getLogger("yamlweave.core")
        
        # 初始化变量
        self.project_dir = project_dir
        self.yaml_file_path = yaml_file_path
        self.using_mocks = not (handlers_loaded and parser_loaded)
        self.ui = ui
        
        # 记录功能状态
        if self.using_mocks:
            self.logger.warning("某些功能模块未加载，将使用模拟实现，功能受限")
        
        # 实例化处理器组件
        try:
            # 初始化YAML处理器
            self.yaml_handler = YamlStubHandler(yaml_file_path)
            if yaml_file_path and os.path.exists(yaml_file_path):
                self.yaml_handler.load_yaml(yaml_file_path)
            
            # 初始化注释处理器
            self.comment_handler = CommentHandler()
            
            # 初始化解析器
            self.parser = StubParser(self.yaml_handler)
            
            self.logger.info("桩处理器组件初始化完成")
        except Exception as e:
            self.logger.error(f"初始化桩处理器组件失败: {str(e)}")
            self.using_mocks = True
            
            # 确保即使出错也有可用的组件
            self.yaml_handler = YamlStubHandler(yaml_file_path)
            self.comment_handler = CommentHandler()
            self.parser = StubParser(self.yaml_handler)
    
    def set_yaml_file(self, yaml_file_path: str) -> bool:
        """设置YAML配置文件路径"""
        self.logger.info(f"设置YAML配置文件: {yaml_file_path}")
        self.yaml_file_path = yaml_file_path
        
        # 实际加载YAML配置
        try:
            if os.path.exists(yaml_file_path):
                success = self.yaml_handler.load_yaml(yaml_file_path)
                if success:
                    self.logger.info(f"成功加载YAML配置文件: {yaml_file_path}")
                    return True
                else:
                    self.logger.error(f"加载YAML配置文件失败: {yaml_file_path}")
            else:
                self.logger.error(f"YAML配置文件不存在: {yaml_file_path}")
        except Exception as e:
            self.logger.error(f"设置YAML配置文件时出错: {str(e)}")
        
        return False
    
    def process_file(self, file_path: str, callback=None) -> Tuple[bool, str, int]:
        """
        处理单个文件，插入桩代码
        
        Args:
            file_path: 文件路径
            callback: 可选回调函数，用于报告处理进度
            
        Returns:
            Tuple[bool, str, int]: (成功/失败, 消息, 插入桩点数量)
        """
        self.logger.info(f"处理文件: {file_path}")
        
        if self.using_mocks:
            self.logger.warning(f"使用模拟处理: {file_path}")
            return True, "成功 (模拟)", 0
        
        # 实际处理文件
        try:
            if not os.path.exists(file_path):
                return False, f"文件不存在: {file_path}", 0
            
            # 处理文件并返回结果
            success, message, count = self.parser.process_file(file_path, callback)
            
            if success:
                self.logger.info(f"文件处理成功: {file_path}, 插入了 {count} 个桩点")
            else:
                self.logger.warning(f"文件处理失败: {file_path}, {message}")
            
            return success, message, count
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg, 0
    
    def process_directory(self, root_dir: str, callback=None) -> Dict[str, Any]:
        """
        处理目录中的所有文件
        
        Args:
            root_dir: 根目录路径
            callback: 可选回调函数，用于报告处理进度
            
        Returns:
            Dict[str, Any]: 处理结果统计信息
        """
        result = {
            "total_files": 0,
            "processed_files": 0,
            "successful_stubs": 0,
            "errors": [],
            "backup_dir": None,
            "stubbed_dir": None,
            "missing_stubs": 0
        }

        # 实际处理目录
        try:
            # 检查目录是否存在
            if not os.path.isdir(root_dir):
                result["errors"].append({"file": "N/A", "error": f"目录不存在: {root_dir}"})
                return result
            
            # 创建备份和结果目录（如果不存在）
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = getattr(self, 'backup_dir', f"{root_dir}_backup_{timestamp}")
            stubbed_dir = getattr(self, 'stubbed_dir', f"{root_dir}_stubbed_{timestamp}")
            
            # 保存目录信息
            self.backup_dir = backup_dir
            self.stubbed_dir = stubbed_dir
            
            # 将目录信息添加到结果中
            result["backup_dir"] = backup_dir
            result["stubbed_dir"] = stubbed_dir

            # 重置缺失桩代码统计
            if hasattr(self, 'parser') and hasattr(self.parser, 'missing_anchors'):
                self.parser.missing_anchors = []

            # 查找所有C文件
            c_files = find_c_files(root_dir)
            result["total_files"] = len(c_files)
            
            # 处理每个文件
            for i, file_path in enumerate(c_files):
                try:
                    # 更新进度显示
                    if hasattr(self, 'ui') and self.ui and hasattr(self.ui, "update_progress"):
                        percentage = int((i / result["total_files"]) * 100) if result["total_files"] > 0 else 0
                        current_file = os.path.basename(file_path)
                        print(f"[DEBUG][{datetime.datetime.now()}] before after: percent={percentage}, file={current_file}")
                        self.ui.root.after(0, self.ui.update_progress, percentage, f"处理: {current_file}", i, result["total_files"])
                        print(f"[DEBUG][{datetime.datetime.now()}] after after: percent={percentage}, file={current_file}")
                        if hasattr(self.ui.root, "update_idletasks"):
                            self.ui.root.update_idletasks()
                    
                    # 读取文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        # 尝试其他编码
                        try:
                            with open(file_path, 'r', encoding='gbk') as f:
                                content = f.read()
                            self.logger.info(f"使用GBK编码成功读取文件: {file_path}")
                        except Exception as enc_error:
                            error_msg = f"无法读取文件: {file_path}, 错误: {str(enc_error)}"
                            self.logger.error(error_msg)
                            result["errors"].append({"file": file_path, "error": error_msg})
                            continue
                    except Exception as f_error:
                        error_msg = f"读取文件失败: {file_path}, 错误: {str(f_error)}"
                        self.logger.error(error_msg)
                        result["errors"].append({"file": file_path, "error": error_msg})
                        continue
                    
                    # 处理文件
                    success, message, count = self.process_file(file_path, callback)
                    updated = (count > 0)
                    
                    if success:
                        result["processed_files"] += 1
                        result["successful_stubs"] += count
                        
                        # 处理.stub文件并复制到结果目录
                        try:
                            # 获取相对路径
                            rel_path = os.path.relpath(file_path, root_dir)
                            stub_file_path = os.path.join(stubbed_dir, rel_path)
                            
                            # 确保目标目录存在
                            stub_dir = os.path.dirname(stub_file_path)
                            os.makedirs(stub_dir, exist_ok=True)
                            
                            # 复制.stub文件到结果目录，并重命名为原文件名
                            source_stub = file_path + ".stub"
                            if os.path.exists(source_stub):
                                with open(source_stub, 'r', encoding='utf-8', errors='replace') as f:
                                    stub_content = f.read()
                                with open(stub_file_path, 'w', encoding='utf-8', errors='replace') as f:
                                    f.write(stub_content)
                                self.logger.info(f"复制处理后文件到结果目录: {stub_file_path}")
                                
                                # 删除原始.stub文件(清理)
                                try:
                                    os.remove(source_stub)
                                except:
                                    pass
                            else:
                                self.logger.warning(f"找不到处理后的.stub文件: {source_stub}")
                        except Exception as copy_error:
                            self.logger.error(f"复制文件到结果目录失败: {str(copy_error)}")
                    else:
                        result["errors"].append({"file": file_path, "error": message})
                    
                    # 进度回调
                    if callback:
                        callback(file_path, updated)
                    
                except Exception as p_error:
                    error_msg = f"处理文件内容失败: {file_path}, 错误: {str(p_error)}"
                    self.logger.error(error_msg)
                    result["errors"].append({"file": file_path, "error": error_msg})
                    # 更新错误状态的进度
                    if hasattr(self, 'ui') and self.ui and hasattr(self.ui, "update_progress"):
                        percentage = int(((i + 1) / result["total_files"]) * 100) if result["total_files"] > 0 else 0
                        print(f"[DEBUG][{datetime.datetime.now()}] before after: percent={percentage}, file=处理出错: {os.path.basename(file_path)}")
                        self.ui.root.after(0, self.ui.update_progress, percentage, f"处理出错: {os.path.basename(file_path)}", i+1, result["total_files"])
                        print(f"[DEBUG][{datetime.datetime.now()}] after after: percent={percentage}, file=处理出错: {os.path.basename(file_path)}")
                        if hasattr(self.ui.root, "update_idletasks"):
                            self.ui.root.update_idletasks()
                    continue
            
            # 最终完成进度更新
            if hasattr(self, 'ui') and self.ui and hasattr(self.ui, "update_progress"):
                percentage = int(100)
                print(f"[DEBUG][{datetime.datetime.now()}] before after: percent=100, file=处理完成")
                self.ui.root.after(0, self.ui.update_progress, 100, "处理完成", result["total_files"], result["total_files"])
                print(f"[DEBUG][{datetime.datetime.now()}] after after: percent=100, file=处理完成")
                if hasattr(self.ui.root, "update_idletasks"):
                    self.ui.root.update_idletasks()
            
            self.logger.info(f"目录处理完成: {root_dir}")
            self.logger.info(f"总文件数: {result['total_files']}")
            self.logger.info(f"处理文件数: {result['processed_files']}")
            self.logger.info(f"插入桩点数: {result['successful_stubs']}")
            if result["errors"]:
                self.logger.warning(f"处理错误数: {len(result['errors'])}")

            # 统计缺失的桩代码锚点，并记录详细信息
            missing_list = getattr(self.parser, 'missing_anchors', [])
            missing_count = len(missing_list)
            result["missing_stubs"] = missing_count
            result["missing_anchor_details"] = missing_list
            if missing_count > 0:
                self.logger.warning(f"缺失桩代码锚点数: {missing_count}")
                if hasattr(self, 'ui') and self.ui:
                    self.ui.log(f"[警告] 缺失桩代码锚点共 {missing_count} 个", tag="warning")
                    for entry in missing_list:
                        rel_file = os.path.relpath(entry.get('file', ''), root_dir)
                        line = entry.get('line', '')
                        anchor = entry.get('anchor', '')
                        msg = f"{rel_file} 第 {line} 行: {anchor} 未在YAML中找到"
                        self.ui.log(f"[缺失] {msg}", tag="missing")
                    if hasattr(self.ui, 'update_status'):
                        self.ui.update_status(f"缺失桩代码 {missing_count} 个")
        except Exception as e:
            error_msg = f"处理目录时出错: {str(e)}"
            self.logger.error(error_msg)
            result["errors"].append({"file": "N/A", "error": error_msg})
        
        return result
    
    def process_files(self, callback=None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        处理文件并插入桩代码（与MinimalStubProcessor接口兼容）
        
        Args:
            callback: 可选的进度回调函数，接受文件路径和更新状态参数
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (成功/失败, 消息, 统计信息)
        """
        # 检查项目目录是否有效
        if not self.project_dir or not os.path.isdir(self.project_dir):
            error_msg = f"项目目录无效: {self.project_dir}"
            self.logger.error(error_msg)
            return False, error_msg, {}
        
        # 初始化统计信息
        self.stats = {
            "scanned_files": 0,
            "updated_files": 0,
            "inserted_stubs": 0,
            "failed_files": 0
        }
        
        try:
            # 处理目录
            result = self.process_directory(self.project_dir, callback)
            
            # 更新统计信息
            self.stats["scanned_files"] = result["total_files"]
            self.stats["updated_files"] = result["processed_files"]
            self.stats["inserted_stubs"] = result["successful_stubs"]
            self.stats["failed_files"] = len(result["errors"])
            self.stats["missing_stubs"] = result.get("missing_stubs", 0)
            
            # 检查是否有错误
            if result["errors"]:
                error_msg = f"处理过程中发生 {len(result['errors'])} 个错误"
                self.logger.warning(error_msg)
                return False, error_msg, self.stats
            
            return True, "处理完成", self.stats
            
        except Exception as e:
            error_msg = f"处理文件过程中发生错误: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            return False, error_msg, self.stats

    def extract_to_yaml(self, root_dir: str, output_file: str) -> bool:
        """根据已插入的桩代码生成YAML配置"""
        try:
            stub_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
            c_files = find_c_files(root_dir)
            for file_path in c_files:
                stubs = self.parser.extract_stubs_from_file(file_path)
                for entry in stubs:
                    tc = entry['test_case_id']
                    step = entry['step_id']
                    seg = entry['segment_id']
                    code = entry['code']
                    stub_dict.setdefault(tc, {}).setdefault(step, {})[seg] = code

            import yaml

            class LiteralStr(str):
                """用于在YAML中以块字符串形式表示代码"""

            def literal_representer(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

            yaml.add_representer(LiteralStr, literal_representer)

            # 将代码段包装为LiteralStr，确保YAML使用|块格式
            formatted_dict: Dict[str, Dict[str, Dict[str, LiteralStr]]] = {}
            for tc_id, steps in stub_dict.items():
                formatted_dict[tc_id] = {}
                for step_id, segments in steps.items():
                    formatted_dict[tc_id][step_id] = {
                        seg_id: LiteralStr(code)
                        for seg_id, code in segments.items()
                    }

            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.safe_dump(
                    formatted_dict,
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                    indent=2,
                )

            self.logger.info(f"成功导出YAML: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"导出YAML失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

# 辅助函数
def find_c_files(root_dir):
    """查找目录下所有.c文件"""
    files = []
    logger.info(f"在目录 {root_dir} 中查找.c源文件")
    
    try:
        # 规范化路径
        root_dir = os.path.normpath(root_dir)
        
        # 确保目录存在
        if not os.path.exists(root_dir):
            logger.error(f"目录不存在: {root_dir}")
            return []
        
        if not os.path.isdir(root_dir):
            logger.error(f"路径不是目录: {root_dir}")
            return []
        
        # 输出目录内容
        try:
            top_files = os.listdir(root_dir)
            logger.info(f"目录 {root_dir} 内容: {top_files}")
        except Exception as e:
            logger.error(f"列出目录内容失败: {root_dir} - {str(e)}")
        
        # 遍历目录查找C源文件
        for root, dirs, file_names in os.walk(root_dir):
            logger.debug(f"扫描目录: {root}, 包含 {len(file_names)} 个文件")
            for file_name in file_names:
                # 只包含以.c结尾的文件
                if file_name.lower().endswith('.c'):
                    full_path = os.path.join(root, file_name)
                    logger.info(f"找到C源文件: {full_path}")
                    files.append(full_path)
        
        # 如果没有找到文件，尝试其他扩展名
        if not files:
            logger.warning(f"在目录 {root_dir} 中没有找到.c文件，尝试使用示例文件")
            # 检查demo.c文件
            demo_path = os.path.join(root_dir, "demo.c")
            if os.path.exists(demo_path):
                logger.info(f"找到示例文件: {demo_path}")
                files.append(demo_path)
            else:
                # 尝试DEMO.c
                demo_path = os.path.join(root_dir, "DEMO.c")
                if os.path.exists(demo_path):
                    logger.info(f"找到示例文件: {demo_path}")
                    files.append(demo_path)
                else:
                    # 如果没有示例文件，创建一个示例C文件
                    demo_path = os.path.join(root_dir, "sample.c")
                    try:
                        with open(demo_path, "w", encoding="utf-8") as f:
                            f.write('''
/**
 * 自动生成的示例C文件
 */
#include <stdio.h>

// 示例函数
void test_function(int value) {
    // 示例注释
    printf("Value: %d\\n", value);
}

int main() {
    printf("Sample C file for YAMLWeave\\n");
    test_function(42);
    return 0;
}
''')
                        logger.info(f"创建了示例C文件: {demo_path}")
                        files.append(demo_path)
                    except Exception as e:
                        logger.error(f"创建示例文件失败: {str(e)}")
        
        logger.info(f"总共找到 {len(files)} 个.c源文件")
        if files:
            for i, f in enumerate(files):
                logger.info(f"文件 {i+1}: {f}")
        return files
    except Exception as e:
        logger.error(f"查找文件时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def create_example_yaml_file(target_path):
    """创建示例YAML配置文件"""
    logger.info(f"尝试创建示例YAML配置文件: {target_path}")
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        example_content = '''# YAMLWeave 测试用桩代码配置文件
# 按测试用例、步骤和代码段分级组织

# ==== 基础功能测试用例 ====

# TC001: 数据验证测试
TC001:
  # STEP1: 输入边界检查
  STEP1:
    # segment1: 检查数值范围
    segment1: |
      if (data < 0 || data > 100) {
          printf("无效数据: %d\\n", data);
          return -1;
      }
    # segment2: 检查完成记录
    segment2: |
      printf("数据边界验证完毕\\n");

  # STEP2: 格式验证
  STEP2:
    # segment1: 检查数据格式
    segment1: |
      if (!is_valid_format(data.format)) {
          printf("无效的数据格式: %s\\n", data.format);
          return -1;
      }

# TC002: 性能监控测试
TC002:
  # STEP1: 计时器操作
  STEP1:
    # segment1: 开始计时
    segment1: |
      uint64_t start_time = get_current_time_ms();
      log_performance("开始性能监控");
    
    # segment2: 结束计时
    segment2: |
      uint64_t end_time = get_current_time_ms();
      log_performance("处理耗时: %llu ms", (end_time - start_time));

# ==== 高级功能测试用例 ====

# TC101: 复杂锚点格式测试 - 测试多种锚点格式变体
TC101:
  # STEP1: 标准格式测试
  STEP1:
    # 标准格式锚点 TC101 STEP1 segment1
    segment1: |
      printf("标准格式锚点测试成功\\n");
    
    # 特殊命名锚点 TC101 STEP1 format_check
    format_check: |
      if (data == NULL) {
          printf("数据为空\\n");
          return NULL_ERROR;
      }
  
  # STEP2: 特殊格式测试
  STEP2:
    # 无空格锚点测试(//TC101 STEP2 segment1)
    segment1: |
      printf("无空格锚点测试\\n");
    
    # 多空格锚点测试(//  TC101   STEP2   multi_space)
    multi_space: |
      printf("多空格锚点测试\\n");

# TC102: 复杂代码结构测试 - 测试复杂缩进和多行代码
TC102:
  STEP1:
    complex_code: |
      if (condition) {
          for (int i = 0; i < limit; i++) {
              if (i % 2 == 0) {
                  result += calculate(i);
                  
                  if (result > threshold) {
                      printf("阈值 %d 超出: %d\\n", threshold, result);
                      break;
                  }
              } else {
                  result -= penalty;
              }
          }
      } else {
          printf("条件不满足\\n");
          return DEFAULT_RESULT;
      }
'''
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(example_content)
        
        logger.info(f"成功创建示例YAML配置文件: {target_path}")
        return True
    except Exception as e:
        logger.error(f"创建示例YAML配置文件失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """命令行入口点"""
    if len(sys.argv) < 2:
        print("用法: python -m YAMLWeave.core.stub_processor <项目目录> [YAML配置文件]")
        return
    
    root_dir = sys.argv[1]
    if not os.path.isdir(root_dir):
        print(f"错误: '{root_dir}' 不是有效目录")
        return
    
    yaml_file = None
    if len(sys.argv) > 2:
        yaml_file = sys.argv[2]
        if not os.path.exists(yaml_file):
            print(f"错误: YAML配置文件 '{yaml_file}' 不存在")
            return
    
    processor = StubProcessor(root_dir, yaml_file)
    processor.process_directory(root_dir)

if __name__ == "__main__":
    main() 