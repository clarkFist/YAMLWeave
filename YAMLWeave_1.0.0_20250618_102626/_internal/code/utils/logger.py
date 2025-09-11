"""
日志配置模块
提供日志设置和获取功能
"""

import logging
import os
import sys
from datetime import datetime
import glob


def get_app_root():
    """Return base directory for logs depending on runtime environment."""
    if getattr(sys, "frozen", False):
        # Running inside bundled executable
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

# 日志格式
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 统一生成时间戳日志目录和文件
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
LOGS_DIR = os.path.join(get_app_root(), f"logs_{TIMESTAMP}")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "yamlweave.log")

class UILogHandler(logging.Handler):
    """将日志消息转发到UI的处理器"""

    def __init__(self, ui):
        super().__init__()
        self.ui = ui

    def emit(self, record):
        if not self.ui:
            return
        try:
            msg = record.getMessage()
            if record.levelno >= logging.ERROR:
                tag = "error"
            elif record.levelno >= logging.WARNING:
                tag = "warning"
            else:
                tag = "info"

            # 根据内容自动调整tag以便在UI中分色显示
            lower_msg = msg.lower()
            if "锚点" in msg or "anchor" in lower_msg:
                tag = "find"
            elif "用例" in msg:
                tag = "case"

            self.ui.log(f"[{record.levelname}] {msg}", tag=tag)
        except Exception:
            pass

def add_ui_handler(ui, level=logging.INFO):
    """向根日志器添加UI日志处理器"""
    handler = UILogHandler(ui)
    handler.setLevel(level)
    logging.getLogger().addHandler(handler)
    return handler

def setup_global_logger(level=logging.INFO):
    # 清除旧的handler
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    # 文件handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.root.addHandler(file_handler)
    logging.root.setLevel(level)
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logging.root.addHandler(console_handler)

def setup_logging(level='info', log_file=None, console=True):
    """
    设置日志系统
    
    Args:
        level: 日志级别，可选值: debug, info, warning, error, critical
        log_file: 日志文件名，如果为None则使用默认命名
        console: 是否输出到控制台
    
    Returns:
        logging.Logger: 根日志记录器
    """
    # 确保日志目录存在
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS.get(level.lower(), logging.INFO))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    # 添加文件处理器
    if log_file is None:
        log_file = LOG_FILE
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 添加控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name)

def log_exception(logger, exception, prefix_message=""):
    """
    记录异常信息
    
    Args:
        logger: 日志记录器
        exception: 异常对象
        prefix_message: 前缀消息
        
    Returns:
        str: 格式化的错误消息
    """
    if prefix_message:
        error_message = f"{prefix_message}: {str(exception)}"
    else:
        error_message = str(exception)
        
    logger.exception(error_message)
    return error_message

def log_operation_result(logger, operation_name, success, message=""):
    """
    记录操作结果
    
    Args:
        logger: 日志记录器
        operation_name: 操作名称
        success: 是否成功
        message: 附加消息
        
    Returns:
        str: 格式化的结果消息
    """
    result = "成功" if success else "失败"
    log_message = f"{operation_name} {result}"
    
    if message:
        log_message += f": {message}"
        
    if success:
        logger.info(log_message)
    else:
        logger.error(log_message)
        
    return log_message

def setup_file_logger():
    """设置文件日志器，返回日志文件路径"""
    import time
    import os
    
    # 创建logs目录（如果不存在）
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 日志文件命名规则：yamlweave_日期_时间.log
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"yamlweave_{timestamp}.log")
    
    # 配置文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # 详细的日志格式，包含更多上下文信息
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s'
    )
    file_handler.setFormatter(detailed_formatter)
    
    # 设置文件日志级别为DEBUG，记录所有详细信息
    file_handler.setLevel(logging.DEBUG)
    
    # 将处理器添加到根日志器
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    return log_file

def save_execution_log(stats, project_dir, backup_dir=None, stubbed_dir=None):
    """
    保存执行日志到固定目录
    
    Args:
        stats: 统计信息字典
        project_dir: 项目目录
        backup_dir: 备份目录
        stubbed_dir: 插桩结果目录
        
    Returns:
        str: 执行日志文件路径
    """
    import time
    import os
    import json
    import tempfile
    import logging
    
    # 记录开始保存执行日志
    print(f"开始保存执行日志，项目目录: {project_dir}")
    logging.info(f"开始保存执行日志，项目目录: {project_dir}")
    
    # 创建带时间戳的日志目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = os.path.join(get_app_root(), f'logs_{timestamp}')
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建带时间戳的执行日志文件
    log_filename = f"execution_{timestamp}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    print(f"将保存执行日志到: {log_file_path}")
    
    # 组织执行结果信息
    execution_info = {
        "timestamp": timestamp,
        "project_directory": project_dir,
        "stats": stats,
        "backup_directory": backup_dir,
        "stubbed_directory": stubbed_dir
    }
    
    # 格式化结果信息
    result_lines = []
    result_lines.append(f"===== 执行日志：{timestamp} =====")
    result_lines.append(f"项目目录: {project_dir}")
    
    if backup_dir:
        result_lines.append(f"备份目录: {backup_dir}")
        
    if stubbed_dir:
        result_lines.append(f"插桩结果目录: {stubbed_dir}")
    
    result_lines.append("\n----- 执行统计 -----")
    
    if stats:
        scanned = stats.get('scanned_files', 0)
        updated = stats.get('updated_files', 0)
        inserted = stats.get('inserted_stubs', 0)
        failed = stats.get('failed_files', 0)
        
        result_lines.append(f"总扫描文件数: {scanned}")
        result_lines.append(f"更新的文件数: {updated}")
        result_lines.append(f"插入的桩点数: {inserted}")
        
        if failed > 0:
            result_lines.append(f"处理失败文件: {failed}")
        
        # 计算成功率
        if scanned > 0:
            update_rate = updated / scanned * 100
            result_lines.append(f"文件更新率: {update_rate:.1f}%")
        
        # 计算桩点插入效率
        if updated > 0:
            stub_per_file = inserted / updated
            result_lines.append(f"平均每文件桩点: {stub_per_file:.1f}")
    
    result_lines.append("=====================")
    
    # 写入执行日志文件
    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            # 写入格式化结果
            f.write('\n'.join(result_lines))
            f.write('\n\n')
            
            # 写入JSON格式数据供程序解析
            f.write("--- JSON数据 ---\n")
            f.write(json.dumps(execution_info, ensure_ascii=False, indent=2))
        
        print(f"执行日志已成功保存: {log_file_path}")
        logging.info(f"执行日志已成功保存: {log_file_path}")
        return log_file_path
    
    except Exception as e:
        error_msg = f"保存执行日志失败: {str(e)}"
        print(error_msg)
        logging.error(error_msg)
        
        # 尝试保存到临时目录作为备选
        try:
            temp_log_path = os.path.join(tempfile.gettempdir(), log_filename)
            print(f"尝试保存到临时目录: {temp_log_path}")
            
            with open(temp_log_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(result_lines))
                f.write('\n\n')
                f.write("--- JSON数据 ---\n")
                f.write(json.dumps(execution_info, ensure_ascii=False, indent=2))
            
            print(f"执行日志已保存到临时目录: {temp_log_path}")
            logging.info(f"执行日志已保存到临时目录: {temp_log_path}")
            return temp_log_path
        
        except Exception as inner_e:
            error_msg = f"保存到临时目录也失败: {str(inner_e)}"
            print(error_msg)
            logging.error(error_msg)
            return None

def get_execution_logs():
    """
    获取执行日志历史记录
    
    Returns:
        list: 执行日志文件列表，按时间降序排序
    """
    import os
    import json
    import time
    import tempfile
    import logging
    import glob
    from datetime import datetime
    
    log_files = []
    
    # 获取应用根目录
    app_root = get_app_root()
    
    # 尝试多个可能的执行日志目录位置
    possible_dirs = [
        # 主执行日志目录
        os.path.join(app_root, "execution_logs"),
        # 临时目录中的备份位置
        os.path.join(tempfile.gettempdir(), "yamlweave_logs"),
        # 直接临时目录（用于单个文件）
        tempfile.gettempdir()
    ]
    
    # 添加带时间戳的logs_YYYYMMDD_HHMMSS目录
    logs_timestamp_dirs = glob.glob(os.path.join(app_root, "logs_*"))
    possible_dirs.extend(logs_timestamp_dirs)
    
    for logs_dir in possible_dirs:
        try:
            if not os.path.exists(logs_dir):
                logging.info(f"日志目录不存在: {logs_dir}")
                continue
                
            logging.info(f"扫描日志目录: {logs_dir}")
            print(f"扫描日志目录: {logs_dir}")
            
            # 遍历执行日志目录中的所有日志文件
            for filename in os.listdir(logs_dir):
                # 只识别execution_*.log格式的执行日志文件
                if filename.startswith("execution_") and filename.endswith(".log"):
                    try:
                        file_path = os.path.join(logs_dir, filename)
                        
                        # 获取文件修改时间
                        file_mtime = os.path.getmtime(file_path)
                        file_mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_mtime))
                        
                        # 尝试从文件内容中解析执行信息
                        execution_info = {}
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                # 查找JSON数据部分
                                json_start = content.find("--- JSON数据 ---")
                                if json_start > 0:
                                    json_data = content[json_start + len("--- JSON数据 ---"):].strip()
                                    try:
                                        # 防止JSON数据不完整
                                        execution_info = json.loads(json_data)
                                    except json.JSONDecodeError as json_err:
                                        logging.warning(f"JSON解析错误: {file_path}, 尝试修复...")
                                        # 尝试找到有效的JSON部分
                                        try:
                                            # 检查是否有额外内容
                                            valid_json = json_data.split('\n\n')[0].strip()
                                            execution_info = json.loads(valid_json)
                                            logging.info(f"成功修复并解析JSON: {file_path}")
                                        except Exception:
                                            logging.warning(f"无法修复JSON: {file_path}, 使用基本信息")
                                            execution_info = {
                                                "timestamp": file_mtime_str,
                                                "project_directory": "未知",
                                                "stats": {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0}
                                            }
                        except Exception as e:
                            # 如果无法解析JSON，使用基本信息
                            logging.warning(f"无法解析日志文件JSON: {file_path}, 错误: {str(e)}")
                        
                        # 创建日志文件记录
                        log_record = {
                            "file_path": file_path,
                            "file_name": filename,
                            "modified_time": file_mtime,
                            "modified_time_str": file_mtime_str,
                            "execution_info": execution_info
                        }
                        
                        log_files.append(log_record)
                        
                    except Exception as e:
                        logging.warning(f"处理日志文件时出错: {filename}, 错误: {str(e)}")
                        continue
        except Exception as e:
            logging.warning(f"无法访问日志目录: {logs_dir}, 错误: {str(e)}")
            continue
    
    if log_files:
        logging.info(f"找到 {len(log_files)} 个执行日志文件")
        print(f"找到 {len(log_files)} 个执行日志文件")
    else:
        logging.warning("未找到任何执行日志文件")
        print("未找到任何执行日志文件")
    
    # 按修改时间降序排序
    log_files.sort(key=lambda x: x["modified_time"], reverse=True)
    
    return log_files

def get_execution_log_stats():
    """
    获取执行日志统计信息
    
    Returns:
        dict: 执行日志统计信息，包括总日志数、最新日志时间等
    """
    log_files = get_execution_logs()
    
    if not log_files:
        return {
            "total_logs": 0,
            "latest_log": None,
            "total_processed_files": 0,
            "total_inserted_stubs": 0
        }
    
    # 统计插桩文件总数和桩点总数
    total_processed_files = 0
    total_inserted_stubs = 0
    
    for log in log_files:
        execution_info = log.get("execution_info", {})
        stats = execution_info.get("stats", {})
        
        # 安全获取统计值并累加
        try:
            updated_files = stats.get("updated_files", 0)
            if updated_files and isinstance(updated_files, (int, float)):
                total_processed_files += int(updated_files)
                
            inserted_stubs = stats.get("inserted_stubs", 0)
            if inserted_stubs and isinstance(inserted_stubs, (int, float)):
                total_inserted_stubs += int(inserted_stubs)
        except (TypeError, ValueError):
            # 忽略无法处理的值
            pass
    
    return {
        "total_logs": len(log_files),
        "latest_log": log_files[0] if log_files else None,
        "total_processed_files": total_processed_files,
        "total_inserted_stubs": total_inserted_stubs
    }

def get_latest_execution_log_content():
    """
    获取最近执行日志的内容
    
    Returns:
        str: 最近执行日志的文本内容，如果没有则返回None
    """
    logs = get_execution_logs()
    if not logs:
        return None
    
    latest_log = logs[0]
    log_path = latest_log.get("file_path")
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        logging.error(f"读取最近执行日志失败: {str(e)}")
        return None

def get_execution_log_content(log_index=0):
    """
    获取指定索引的执行日志内容
    
    Args:
        log_index: 日志索引，0表示最新的日志
        
    Returns:
        tuple: (日志内容, 日志记录)，如果没有则返回(None, None)
    """
    logs = get_execution_logs()
    if not logs or log_index >= len(logs):
        return None, None
    
    log_record = logs[log_index]
    log_path = log_record.get("file_path")
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, log_record
    except Exception as e:
        logging.error(f"读取执行日志失败: {str(e)}")
        return None, log_record 