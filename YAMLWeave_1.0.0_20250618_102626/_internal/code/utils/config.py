"""
配置管理模块
处理YAMLWeave的配置加载和管理
"""

import os
import yaml
from typing import Dict, Any, List, Optional

# 尝试相对导入以兼容打包后的路径结构
try:
    from .logger import get_logger
    from .exceptions import ConfigError
except Exception:  # pragma: no cover - 回退到绝对导入
    try:
        from utils.logger import get_logger
        from utils.exceptions import ConfigError
    except Exception:
        import logging
        get_logger = lambda name=None: logging.getLogger(name)
        class ConfigError(Exception):
            pass

logger = get_logger(__name__)

# 配置字典
config = {}

# 默认配置文件路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "default.yaml")

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，如果为None则使用默认配置
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    global config
    
    # 首先加载默认配置
    try:
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"无法加载默认配置文件: {str(e)}")
        config = {}
    
    # 如果指定了配置文件，则覆盖默认配置
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f) or {}
                
            # 递归合并配置
            deep_merge(config, user_config)
        except Exception as e:
            print(f"无法加载用户配置文件: {str(e)}")
    
    return config

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归合并字典
    
    Args:
        base: 基础字典
        override: 覆盖字典
        
    Returns:
        Dict[str, Any]: 合并后的字典
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key: 配置键，可以是点分隔的路径，如 "logging.level"
        default: 默认值，如果配置不存在则返回此值
        
    Returns:
        Any: 配置值
    """
    if not config:
        load_config()
        
    parts = key.split('.')
    current = config
    
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
            
    return current

def set_config(key: str, value: Any) -> None:
    """
    设置配置值
    
    Args:
        key: 配置键，可以是点分隔的路径，如 "logging.level"
        value: 配置值
    """
    if not config:
        load_config()
        
    parts = key.split('.')
    current = config
    
    # 导航到最后一个部分前
    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        current = current[part]
        
    # 设置值
    current[parts[-1]] = value

def save_config(config_path: str) -> bool:
    """
    保存配置到文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        bool: 是否成功保存
    """
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {str(e)}")
        return False

# 默认配置
DEFAULT_CONFIG = {
    # 编码相关配置
    'encoding': {
        'default': 'utf-8',
        'fallback': ['utf-8', 'GBK', 'gb2312', 'ascii'],
        'confidence_threshold': 0.7
    },
    # 文件IO相关配置
    'file_io': {
        'max_read_size': 500000,  # 最大读取字节数
        'create_backup': True,    # 是否创建备份
        'temp_file_suffix': '.tmp', # 临时文件后缀
        'backup_file_suffix': '.bak' # 备份文件后缀
    },
    # 日志相关配置
    'logging': {
        'level': 'info',
        'console': True,
        'file': True
    },
    # UI相关配置
    'ui': {
        'title': '自动化桩工具',
        'default_mode': 'yaml'
    },
    # 处理器相关配置
    'handlers': {
        'max_workers': 4,  # 线程池最大工作线程数
        'default_indent': '    '  # 默认缩进
    }
}

class Config:
    """配置管理类"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化配置"""
        if self._initialized:
            return
            
        self._config = DEFAULT_CONFIG.copy()
        self._config_file = None
        self._initialized = True
        
    def load_config(self, config_file: Optional[str] = None) -> bool:
        """
        从文件加载配置
        
        Args:
            config_file: 配置文件路径，如果为None则尝试在默认位置查找
            
        Returns:
            bool: 是否成功加载配置
        """
        if config_file is None:
            # 尝试在默认位置查找配置文件
            config_paths = [
                os.path.join(os.path.expanduser('~'), '.yamlweave.yaml'),
                os.path.join(os.path.expanduser('~'), '.yamlweave.yml'),
                os.path.join(os.getcwd(), 'yamlweave.yaml'),
                os.path.join(os.getcwd(), 'yamlweave.yml'),
                os.path.join(os.path.dirname(__file__), '../..', 'yamlweave.yaml'),
                os.path.join(os.path.dirname(__file__), '../..', 'yamlweave.yml')
            ]
            
            for location in config_paths:
                if os.path.exists(location):
                    config_file = location
                    break
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    
                if user_config:
                    # 递归更新配置
                    self._update_config(self._config, user_config)
                    self._config_file = config_file
                    logger.info(f"已从文件加载配置: {config_file}")
                    return True
            except Exception as e:
                logger.warning(f"加载配置文件失败: {str(e)}")
        
        return False
    
    def _update_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        递归更新配置字典
        
        Args:
            target: 目标配置字典
            source: 源配置字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_config(target[key], value)
            else:
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键，使用点号分隔层级，如'encoding.default'
            default: 如果配置项不存在，返回的默认值
            
        Returns:
            Any: 配置值
        """
        try:
            value = self._config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键，使用点号分隔层级，如'encoding.default'
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_fallback_encodings(self) -> List[str]:
        """获取回退编码列表"""
        return self.get('encoding.fallback', ['utf-8', 'GBK'])
    
    def get_encoding_confidence_threshold(self) -> float:
        """获取编码检测置信度阈值"""
        return self.get('encoding.confidence_threshold', 0.7)
    
    def get_max_workers(self) -> int:
        """获取线程池最大工作线程数"""
        return self.get('handlers.max_workers', 4)
    
    def get_default_indent(self) -> str:
        """获取默认缩进"""
        return self.get('handlers.default_indent', '    ')
    
    def get_ui_title(self) -> str:
        """获取UI标题"""
        return self.get('ui.title', '自动化桩工具')
    
    def get_default_mode(self) -> str:
        """获取默认模式"""
        return self.get('ui.default_mode', 'yaml')
    
    def should_create_backup(self) -> bool:
        """是否创建备份"""
        return self.get('file_io.create_backup', True)
    
    def get_backup_suffix(self) -> str:
        """获取备份文件后缀"""
        return self.get('file_io.backup_file_suffix', '.bak')
    
    def get_temp_suffix(self) -> str:
        """获取临时文件后缀"""
        return self.get('file_io.temp_file_suffix', '.tmp')

# 全局配置实例
config = Config() 