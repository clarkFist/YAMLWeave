"""
文件工具模块
提供文件处理的通用函数
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

try:
    from YAMLWeave.utils.logger import get_logger
    from YAMLWeave.utils.exceptions import FileIOError
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.warning("使用基本日志配置")

def detect_encoding(file_path):
    """检测文件编码"""
    try:
        # 尝试从core模块导入
        from YAMLWeave.core.encoding_utils import detect_file_encoding
        return detect_file_encoding(file_path)
    except ImportError:
        # 如果导入失败，使用默认UTF-8编码
        logger.warning("无法导入编码检测模块，将使用默认UTF-8编码")
        return 'utf-8'

def read_file(file_path):
    """读取文件内容"""
    encoding = detect_encoding(file_path)
    try:
        # 尝试从core模块导入
        from YAMLWeave.core.file_io import read_file_lines as core_read_file_lines
        return core_read_file_lines(file_path, encoding)
    except ImportError:
        # 如果导入失败，实现一个简单的读取函数
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.readlines()
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return []

def write_file(file_path, lines, encoding: Optional[str] = None):
    """写入文件内容

    Args:
        file_path: 文件路径
        lines: 要写入的内容列表
        encoding: 指定编码；为 ``None`` 时自动检测原文件编码
    """
    if encoding is None:
        encoding = detect_encoding(file_path) if os.path.exists(file_path) else 'utf-8'
    try:
        # 尝试从core模块导入
        from YAMLWeave.core.file_io import write_lines_to_file as core_write_lines_to_file
        return core_write_lines_to_file(file_path, lines, encoding)
    except ImportError:
        # 如果导入失败，实现一个简单的写入函数
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.writelines(lines)
            return True
        except Exception as e:
            logger.error(f"写入文件失败: {str(e)}")
            return False

def get_encoding(file_path: str) -> str:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 检测到的编码
    """
    return detect_encoding(file_path)

def read_file_lines(file_path: str, fallback_encodings: Optional[List[str]] = None) -> List[str]:
    """
    读取文件行列表，首先尝试使用自动检测的编码。
    如果读取失败，则依次使用 ``fallback_encodings`` 中的编码再次尝试。

    Args:
        file_path: 文件路径
        fallback_encodings: 回退编码列表

    Returns:
        List[str]: 文件行列表
    """
    if fallback_encodings is None:
        fallback_encodings = []

    encoding = detect_encoding(file_path)
    encodings_to_try = [encoding] + [e for e in fallback_encodings if e != encoding]

    for enc in encodings_to_try:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.readlines()
        except Exception as e:
            logger.warning(f"使用编码 {enc} 读取文件失败: {e}")

    logger.error(f"无法读取文件: {file_path}")
    return []

def read_file_lines_with_fallback_encoding(file_path: str, fallback_encodings: Optional[List[str]] = None) -> List[str]:
    """
    读取文件行列表，与 :func:`read_file_lines` 行为相同。
    提供此函数是为了兼容旧代码。

    Args:
        file_path: 文件路径
        fallback_encodings: 回退编码列表，当自动检测失败时依次尝试这些编码

    Returns:
        List[str]: 文件行列表
    """
    return read_file_lines(file_path, fallback_encodings)

def write_lines_to_file(file_path: str, lines: List[str], encoding: str = 'utf-8') -> bool:
    """
    将行列表写入文件
    
    Args:
        file_path: 文件路径
        lines: 要写入的行列表
        encoding: 编码方式，传递给 :func:`write_file`
    
    Returns:
        bool: 是否写入成功
    """
