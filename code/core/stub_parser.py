"""
桩注释解析模块 (优化版)
支持从YAML配置文件加载桩代码和识别新格式锚点

本模块专注于解析文件中的锚点和桩代码，负责以下核心功能：
1. 识别文件中的锚点标识
2. 从YAML配置中获取对应的桩代码
3. 解析传统格式的注释
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

# 导入日志工具
try:
    from ..utils.logger import get_logger
except Exception:
    try:
        from utils.logger import get_logger
    except Exception:
        get_logger = None
        logger = logging.getLogger(__name__)

if get_logger:
    logger = get_logger(__name__)
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)

# 导入YAML处理器
# 为了在不同的运行环境(如PyInstaller打包后)都能正常导入，
# 这里尝试多种导入路径，并在失败时记录详细日志。
YamlStubHandler = None
try:
    # 优先尝试绝对导入，以兼容打包后的模块结构
    from code.handlers.yaml_handler import YamlStubHandler  # type: ignore
    logger.info("成功通过绝对路径导入YamlStubHandler")
except Exception as abs_err:
    logger.warning(f"绝对路径导入YamlStubHandler失败: {abs_err}")
    try:
        # 常规相对导入（源码运行时的路径）
        from ..handlers.yaml_handler import YamlStubHandler  # type: ignore
        logger.info("成功通过相对路径导入YamlStubHandler")
    except Exception as rel_err:
        logger.error(
            "无法导入YamlStubHandler，锚点与桩代码分离功能将不可用"
        )
        logger.error(f"详细错误: {rel_err}")
        YamlStubHandler = None

# 导入文件处理工具函数
try:
    from ..core.utils import read_file, write_file
except Exception:
    try:
        from code.core.utils import read_file, write_file
    except ImportError:
        try:
            # 尝试相对导入
            from .utils import read_file, write_file
        except ImportError:
            # 最后尝试直接导入
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            try:
                from utils import read_file, write_file
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

class StubParser:
    """
    增强的桩注释解析器，支持YAML配置和新格式锚点
    
    支持两种主要工作模式:
    1. 传统模式：识别注释中内嵌的代码字段
    2. 分离模式：识别锚点标识，从YAML配置文件中加载对应的桩代码
    """
    
    def __init__(self, yaml_handler: Optional[YamlStubHandler] = None):
        # 传统模式的正则表达式
        # 测试用例ID匹配模式 - 匹配符合"// TC001 STEP1:"格式的注释行
        self.test_case_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+):', re.IGNORECASE)
        
        # 单行代码匹配模式 - 匹配"// code: [代码内容]"格式
        self.single_line_code_pattern = re.compile(r'//\s*code:\s*(.*)')
        
        # 多行代码开始和结束标记
        self.multi_line_start = '/* code:'
        self.multi_line_end = '*/'
        
        # 新格式锚点匹配模式 - 匹配符合"// TC001 STEP1 segment1"格式的注释行
        self.anchor_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+\s+\w+).*', re.IGNORECASE)
        
        # YAML处理器
        self.yaml_handler = yaml_handler
    
    def set_yaml_handler(self, yaml_handler: YamlStubHandler):
        """
        设置YAML处理器
        
        Args:
            yaml_handler: YAML处理器实例
        """
        self.yaml_handler = yaml_handler
    
    def parse_file(self, file_path: str, content: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        解析文件中的桩注释
        
        支持两种模式：
        1. 传统模式：从注释的code字段中提取代码
        2. 分离模式：识别锚点，从YAML中加载代码
        
        Args:
            file_path: 文件路径
            content: 可选的文件内容，如果提供则不再读取文件
            
        Returns:
            List[Dict[str, Any]]: 解析出的桩点列表
        """
        # 读取文件内容
        if content is None:
            content, encoding = read_file(file_path)
            if content is None:
                logger.error(f"无法读取文件: {file_path}")
                return []
        
        lines = content.splitlines()
        
        # 优先使用新格式解析（锚点与桩代码分离机制）
        stub_points = self.parse_new_format(file_path, lines)
        
        # 如果没有找到新格式的锚点，或YAML处理器不可用，则尝试传统格式
        if not stub_points:
            logger.info(f"未找到新格式锚点，尝试传统格式解析: {file_path}")
            stub_points = self.parse_traditional_format(file_path, lines)
        
        logger.info(f"在文件 {file_path} 中找到 {len(stub_points)} 个桩点")
        return stub_points
    
    def parse_new_format(self, file_path: str, lines: List[str]) -> List[Dict[str, Any]]:
        """
        解析新格式的锚点标识，在锚点位置插入桩代码
        
        支持两种模式：
        1. 基于锚点匹配：识别文件中的"// TC001 STEP1 segment1"格式锚点，并在该位置插入对应代码
        2. 全局插入模式：当文件中没有锚点时，在文件开头插入所有YAML中定义的桩代码
        
        Args:
            file_path: 文件路径
            lines: 文件内容行列表
            
        Returns:
            List[Dict[str, Any]]: 解析出的桩点列表
        """
        if not self.yaml_handler:
            logger.warning("YAML处理器未配置，无法使用锚点与桩代码分离功能")
            return []
        
        logger.info(f"开始处理文件 {file_path}")
        
        # 获取YAML中定义的所有测试用例
        test_cases = self.yaml_handler.get_all_test_cases()
        logger.info(f"YAML配置中存在的测试用例: {test_cases}")
        
        stub_points = []
        
        # 首先在文件中查找锚点
        found_anchors = False
        for i, line in enumerate(lines):
            match = self.anchor_pattern.search(line)
            if match:
                found_anchors = True
                anchor_text = match.group(1).strip()
                logger.info(f"在文件 {file_path} 的第 {i+1} 行找到锚点: {anchor_text}")
                
                # 解析锚点标识
                try:
                    parts = anchor_text.split()
                    # 仅获取前三个部分作为TC_ID, STEP_ID和segment_ID，不管中间有多少空格
                    tc_parts = []
                    for part in parts:
                        if part.strip():  # 确保不是空字符串
                            tc_parts.append(part.strip())
                    
                    logger.debug(f"锚点解析结果: 原始文本='{anchor_text}', 解析部分={tc_parts}")
                    
                    # 确保至少有三个部分
                    if len(tc_parts) >= 3:
                        tc_id = tc_parts[0]
                        step_id = tc_parts[1]
                        segment_id = tc_parts[2]
                        
                        # 从YAML配置中获取对应的桩代码
                        code = self.yaml_handler.get_stub_code(tc_id, step_id, segment_id)
                        
                        if code:
                            logger.info(f"为锚点 {anchor_text} 找到桩代码")
                            # 添加到桩点列表，在锚点所在行的下一行插入
                            stub_points.append({
                                'test_case_id': anchor_text,
                                'code': code,
                                'line_number': i + 1,  # 在当前锚点行之后插入
                                'original_line': i,
                                'file': file_path,
                                'format': 'new'  # 标记为新格式
                            })
                        else:
                            logger.warning(f"未找到锚点 {anchor_text} 对应的桩代码")
                    else:
                        logger.warning(f"锚点 '{anchor_text}' 格式不正确, 无法解析出三个部分 (TC_ID, STEP_ID, segment_ID)")
                except Exception as e:
                    logger.error(f"解析锚点时发生错误: {anchor_text}, 错误: {e}")
        
        # 如果文件中没有找到锚点，则在文件开头一次性插入所有桩代码（保留原有行为）
        if not found_anchors:
            logger.info(f"文件 {file_path} 中未找到锚点，将在文件开头插入所有桩代码")
            # 在文件的最前面添加所有定义的测试用例的桩代码
            for tc_id in test_cases:
                # 获取该测试用例下的所有步骤
                steps = self.yaml_handler.get_steps_for_test_case(tc_id)
                
                for step_id in steps:
                    # 获取该步骤下的所有代码段
                    segments = self.yaml_handler.get_segments_for_step(tc_id, step_id)
                    
                    for segment_id in segments:
                        # 获取代码段内容
                        code = self.yaml_handler.get_stub_code(tc_id, step_id, segment_id)
                        
                        if code:
                            logger.info(f"为文件 {file_path} 准备插入桩代码: {tc_id} {step_id} {segment_id}")
                            
                            # 添加到桩点列表，在文件开头插入
                            stub_points.append({
                                'test_case_id': f"{tc_id} {step_id} {segment_id}",
                                'code': code,
                                'line_number': 1,  # 在文件开头插入
                                'original_line': 0,
                                'file': file_path,
                                'format': 'new'  # 标记为新格式
                            })
        
        logger.info(f"文件 {file_path} 将插入 {len(stub_points)} 个桩点")
        return stub_points
    
    def parse_traditional_format(self, file_path: str, lines: List[str]) -> List[Dict[str, Any]]:
        """
        解析传统格式的注释和code字段
        
        识别"// TC001 STEP1:"格式的注释和相关的code字段。
        
        Args:
            file_path: 文件路径
            lines: 文件内容行列表
            
        Returns:
            List[Dict[str, Any]]: 解析出的桩点列表
        """
        stub_points = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # 查找测试用例ID注释
            match = self.test_case_pattern.search(line)
            if match:
                test_case_id = match.group(1)
                code = None
                insert_line = i
                
                # 检查下一行是否包含code字段
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    
                    # 处理单行代码
                    code_match = self.single_line_code_pattern.search(next_line)
                    if code_match:
                        code = code_match.group(1)
                        insert_line = i + 1
                    
                    # 处理多行代码
                    elif self.multi_line_start in next_line:
                        code_lines = []
                        j = i + 2
                        while j < len(lines) and self.multi_line_end not in lines[j]:
                            code_lines.append(lines[j])
                            j += 1
                        
                        if code_lines:
                            code = '\n'.join(code_lines)
                            insert_line = j if j < len(lines) else i + 1
                
                if code:
                    logger.info(f"找到传统格式桩点: {test_case_id} (行 {i+1})")
                    stub_points.append({
                        'test_case_id': test_case_id,
                        'code': code,
                        'line_number': insert_line + 1,
                        'original_line': i,
                        'file': file_path,
                        'format': 'traditional'  # 标记为传统格式
                    })
            
            i += 1
        
        return stub_points
    
    def process_file(self, file_path: str, callback=None) -> Tuple[bool, str, int]:
        """
        处理单个文件，插入桩代码
        
        Args:
            file_path: 文件路径
            callback: 可选回调函数，用于报告处理进度
            
        Returns:
            Tuple[bool, str, int]: (成功/失败, 消息, 插入桩点数量)
        """
        try:
            # 读取文件内容
            content, encoding = read_file(file_path)
            if content is None:
                return False, f"无法读取文件: {file_path}", 0
            
            # 解析文件中的桩点
            stub_points = self.parse_file(file_path, content)
            
            if not stub_points:
                logger.info(f"文件中未找到需要插入的桩点: {file_path}")
                return True, "无需更新", 0
                
            # 按行号逆序排序，从后往前插入，避免行号变化
            stub_points.sort(key=lambda x: x['line_number'], reverse=True)
            
            # 分割内容为行
            lines = content.splitlines()
            total_lines = len(lines)
            
            # 插入桩代码
            for i, stub_point in enumerate(stub_points):
                # 调用进度回调
                if callback:
                    progress = int((i / len(stub_points)) * 100)
                    callback(progress, f"处理文件 {os.path.basename(file_path)}: 插入桩点 {i+1}/{len(stub_points)}")
                
                line_num = stub_point['line_number']
                line_num = min(line_num, total_lines)  # 确保不超出范围
                
                # 获取缩进级别
                indent = ''
                if line_num > 0 and line_num <= total_lines:
                    # 计算前导空格
                    current_line = lines[line_num - 1]
                    indent_match = re.match(r'^(\s*)', current_line)
                    if indent_match:
                        indent = indent_match.group(1)
                
                # 处理多行代码，为每行添加相同缩进和注释标记
                code_lines = stub_point['code'].splitlines()
                formatted_code = []
                for code_line in code_lines:
                    formatted_code.append(f"{indent}{code_line}  // 通过桩插入")
                
                # 在指定位置插入代码
                lines.insert(line_num, "\n".join(formatted_code))
            
            # 将处理后的内容写回文件
            new_content = "\n".join(lines)
            success = write_file(file_path, new_content, encoding)
            
            if success:
                return True, f"成功处理文件，插入了 {len(stub_points)} 个桩点", len(stub_points)
            else:
                return False, "写入文件失败", 0
                
        except Exception as e:
            error_msg = f"处理文件时出错: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return False, error_msg, 0 