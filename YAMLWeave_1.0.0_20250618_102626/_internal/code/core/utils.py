#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave Core 模块 - utils
提供通用工具函数，主要用于文件处理和编码识别
"""

import os
import logging

try:
    from ..utils.logger import get_logger
except Exception:
    try:
        from utils.logger import get_logger
    except Exception:
        get_logger = None

logger = get_logger(__name__) if get_logger else logging.getLogger(__name__)
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(handler)

def detect_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(min(1024 * 1024, os.path.getsize(file_path)))
        
        import chardet
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        confidence = result['confidence']
        logger.info(f"检测到文件 {file_path} 编码: {encoding}, 置信度: {confidence}")
        
        # 常见编码修正
        if encoding.lower() in ('gb2312', 'gbk'):
            return 'gb18030'
        return encoding
    except Exception as e:
        logger.error(f"检测文件 {file_path} 编码失败: {str(e)}")
        return 'utf-8'

def read_file(file_path):
    """读取文件内容，自动处理编码"""
    # 尝试的编码列表
    encodings_to_try = []
    
    # 首先尝试检测编码
    detected_encoding = detect_encoding(file_path)
    encodings_to_try.append(detected_encoding)
    
    # 添加其他常用编码
    for enc in ['utf-8', 'gb18030', 'gbk', 'latin1']:
        if enc != detected_encoding:
            encodings_to_try.append(enc)
    
    # 尝试使用不同的编码读取文件
    for encoding in encodings_to_try:
        try:
            logger.info(f"尝试使用编码 {encoding} 读取文件 {file_path}")
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                logger.info(f"使用编码 {encoding} 成功读取文件 {file_path}")
                return content, encoding
        except UnicodeDecodeError:
            logger.warning(f"使用编码 {encoding} 读取文件 {file_path} 失败")
            continue
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            break
    
    # 如果所有编码都失败，使用二进制模式读取并返回
    try:
        logger.warning(f"所有编码尝试失败，以二进制模式读取文件 {file_path}")
        with open(file_path, 'rb') as f:
            binary_content = f.read()
            # 将二进制内容转换为字符串，替换不可解码的字节
            text_content = binary_content.decode('utf-8', errors='replace')
            return text_content, 'utf-8'
    except Exception as e:
        logger.error(f"以二进制模式读取文件 {file_path} 失败: {str(e)}")
        return None, None

def write_file(file_path, content, encoding=None):
    """写入文件内容，使用原始编码"""
    if not encoding:
        # 如果未指定编码，尝试检测原文件编码
        if os.path.exists(file_path):
            encoding = detect_encoding(file_path)
        else:
            encoding = 'utf-8'
    
    try:
        # 不再创建.bak备份文件
        # 所有处理后的文件都会保存到不同的目录，原始文件保持不变
        # 如果需要使用原始文件进行比较，可以使用_backup_目录中的文件
        
        # 为处理后的文件添加后缀
        stub_file_path = file_path + ".stub"
        
        # 写入处理后的文件
        with open(stub_file_path, 'w', encoding=encoding, errors='replace') as f:
            f.write(content)
        logger.info(f"成功写入处理后文件: {stub_file_path}")
        
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {str(e)}")
        return False 