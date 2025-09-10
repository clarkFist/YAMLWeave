"""
自定义异常类
定义所有与Auto Stub相关的异常
"""

class AutoStubError(Exception):
    """Auto Stub基础异常类"""
    pass

class FileIOError(AutoStubError):
    """文件IO相关异常"""
    pass

class EncodingError(FileIOError):
    """编码检测和处理相关异常"""
    pass

class StubParsingError(AutoStubError):
    """桩解析相关异常"""
    pass

class StubProcessingError(AutoStubError):
    """桩处理相关异常"""
    pass

class EnumHandlingError(StubProcessingError):
    """枚举处理相关异常"""
    pass

class CommentHandlingError(StubProcessingError):
    """注释处理相关异常"""
    pass

class FunctionHandlingError(StubProcessingError):
    """函数处理相关异常"""
    pass

class ConfigError(AutoStubError):
    """配置相关异常"""
    pass 