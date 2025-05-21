"""
注释处理器模块
处理传统模式下C代码注释中的桩代码提取
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any

try:
    from YAMLWeave.utils.logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)
    logger.warning("使用基本日志配置")

class CommentHandler:
    """处理桩代码插入，支持两种锚点格式"""
    
    def __init__(self):
        # 传统格式 - 测试用例ID匹配模式 (如 TC001 STEP1:)
        self.test_case_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+):', re.IGNORECASE)
        
        # 新格式 - 锚点匹配模式 (如 TC001 STEP1 segment1)
        # 使用更宽松的模式，允许锚点后有其他文本
        self.anchor_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+\s+\w+).*', re.IGNORECASE)
    
    def find_comment_insertion_point(self, lines: List[str], stub_info: Dict[str, Any]) -> Tuple[int, bool]:
        """
        查找注释或锚点的插入点
        
        支持两种格式：
        1. 传统格式：// TC001 STEP1: 描述
        2. 新格式：直接在文件开头插入所有桩代码
        
        Args:
            lines: 文件内容行列表
            stub_info: 桩信息
            
        Returns:
            Tuple[int, bool]: (插入行号, 是否找到)
        """
        test_case_id = stub_info.get('test_case_id')
        if not test_case_id:
            logger.warning("缺少测试用例ID或锚点，无法查找插入点")
            return -1, False
        
        # 确定使用哪种模式
        format_type = stub_info.get('format', 'traditional')
        
        if format_type == 'new':
            # 新格式：使用预设的插入点
            insertion_point = stub_info.get('line_number', 1)
            logger.info(f"使用预设插入点: 行 {insertion_point}")
            return insertion_point, True
        else:
            # 传统格式：查找注释和code字段
            for i, line in enumerate(lines):
                match = self.test_case_pattern.search(line)
                parts = test_case_id.split()
                if match and match.group(1).lower() == parts[0].lower() + " " + parts[1].lower():
                    # 找到匹配的测试用例ID
                    logger.info(f"找到匹配的注释: '{line.strip()}' (行 {i+1})")
                    
                    # 确定插入位置 - 在注释行之后
                    # 如果下一行包含code字段，则在code字段之后插入
                    if i + 1 < len(lines) and '// code:' in lines[i + 1]:
                        return i + 2, True
                    elif i + 1 < len(lines) and '/* code:' in lines[i + 1]:
                        # 对于多行注释，需要找到结束位置
                        j = i + 2
                        while j < len(lines) and '*/' not in lines[j]:
                            j += 1
                        if j < len(lines):  # 找到了结束位置
                            return j + 1, True
                        else:
                            return i + 1, True  # 未找到结束位置，使用默认位置
                    else:
                        return i + 1, True  # 没有code字段，直接在注释行后插入
        
        logger.warning(f"未找到匹配的锚点或注释: {test_case_id}")
        return -1, False
    
    def insert_code(self, lines: List[str], insertion_point: int, code: str) -> bool:
        """
        在指定位置插入代码
        
        为每行非空插入代码添加"// 通过桩插入"标记。
        
        Args:
            lines: 文件内容行列表
            insertion_point: 插入位置
            code: 要插入的代码
            
        Returns:
            bool: 插入成功返回True，否则返回False
        """
        if insertion_point < 0 or insertion_point > len(lines):
            logger.error(f"无效的插入位置: {insertion_point}")
            return False
        
        # 拆分代码为多行，并添加标记
        # 对于每一行非空代码，添加"// 通过桩插入"标记
        code_lines = code.splitlines()
        marked_code = []
        for line in code_lines:
            if line.strip():
                marked_code.append(f"{line}  // 通过桩插入")
            else:
                marked_code.append(line)
        
        # 在指定位置插入代码
        for i, code_line in enumerate(marked_code):
            lines.insert(insertion_point + i, code_line)
        
        logger.info(f"在行 {insertion_point} 后插入了 {len(marked_code)} 行代码")
        return True
    
    def process_stub(self, lines: List[str], stub_info: Dict[str, Any]) -> bool:
        """
        处理单个桩
        
        支持两种格式：
        1. 传统格式：从注释中提取code字段
        2. 新格式：使用锚点，从YAML中加载代码
        
        Args:
            lines: 文件内容行列表
            stub_info: 桩信息，包含test_case_id和code等关键信息
            
        Returns:
            bool: 处理成功返回True，否则返回False
        """
        # 添加详细日志
        logger.info(f"处理桩点: {stub_info['test_case_id']}, 格式: {stub_info.get('format', 'unknown')}")
        
        # 对于新格式，直接在锚点行下方插入代码
        if stub_info.get('format') == 'new':
            line_number = stub_info.get('line_number', 0)
            if 0 <= line_number < len(lines):
                logger.info(f"在行 {line_number} 处插入桩代码，锚点标识: {stub_info['test_case_id']}")
                return self.insert_code(lines, line_number, stub_info['code'])
            else:
                logger.error(f"无效的行号: {line_number}, 文件总行数: {len(lines)}")
                return False
        
        # 对于传统格式，查找注释并在其后插入
        # 查找插入点
        insertion_point, found = self.find_comment_insertion_point(lines, stub_info)
        if not found:
            logger.warning(f"未找到插入点: {stub_info['test_case_id']}")
            return False
        
        logger.info(f"在行 {insertion_point} 处插入桩代码")
        # 插入代码 - 为每行代码添加"// 通过桩插入"标记
        return self.insert_code(lines, insertion_point, stub_info['code']) 