#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave - C代码自动插桩工具
"""

__version__ = "1.0.0"
__author__ = "YAMLWeave Team"

# 导出主要模块 - 使用相对导入
try:
    # 从当前包内导入核心模块
    from .core.stub_processor import StubProcessor
    from .ui.app_ui import YAMLWeaveUI
    from .ui.app_controller import AppController
    
    # 调试日志
    import logging
    logging = logging.getLogger("yamlweave")
    logging.info("成功从code包导入核心模块")
except ImportError as e:
    # 记录导入错误
    import logging
    logging = logging.getLogger("yamlweave")
    logging.error(f"无法从code包导入核心模块: {str(e)}")
    
    # 尝试备用导入方式
    try:
        # 尝试直接导入
        from core.stub_processor import StubProcessor
        from ui.app_ui import YAMLWeaveUI
        from ui.app_controller import AppController
        
        logging.info("成功通过直接导入方式加载核心模块")
    except ImportError as e2:
        logging.error(f"备用导入方式也失败: {str(e2)}")
        # 引发异常以便上层处理
        raise

"""
YAMLWeave 包
自动插桩工具，用于根据配置或注释自动向代码中插入桩代码。

此包提供了一套完整的工具链，用于管理和插入代码桩。
可通过图形界面或命令行使用，也可作为库在其他Python程序中使用。
"""
