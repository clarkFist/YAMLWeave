"""
文件工具模块
提供文件处理的通用函数
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# 尝试相对或绝对导入日志与异常处理，以兼容不同的包结构
try:
    from .logger import get_logger
    from .exceptions import FileIOError
except Exception:
    try:
        from utils.logger import get_logger
        from utils.exceptions import FileIOError
    except Exception:
        get_logger = None
        class FileIOError(Exception):
            pass

logger = get_logger(__name__) if get_logger else logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.warning("使用基本日志配置")

def detect_encoding(file_path):
    """检测文件编码"""
    try:
        # 优先尝试相对导入
        from ..core.utils import detect_encoding as core_detect
        return core_detect(file_path)
    except Exception:
        try:
            from code.core.utils import detect_encoding as core_detect
            return core_detect(file_path)
        except Exception:
            # 如果导入失败，使用默认UTF-8编码
            logger.warning("无法导入编码检测模块，将使用默认UTF-8编码")
            return 'utf-8'

def read_file(file_path):
    """读取文件内容"""
    encoding = detect_encoding(file_path)
    try:
        from ..core.utils import read_file as core_read_file
        content = core_read_file(file_path)
        return content.splitlines(keepends=True)
    except Exception:
        try:
            from code.core.utils import read_file as core_read_file
            content = core_read_file(file_path)
            return content.splitlines(keepends=True)
        except Exception:
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
        from ..core.utils import write_file as core_write_file
        return core_write_file(file_path, ''.join(lines), encoding)
    except Exception:
        try:
            from code.core.utils import write_file as core_write_file
            return core_write_file(file_path, ''.join(lines), encoding)
        except Exception:
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
