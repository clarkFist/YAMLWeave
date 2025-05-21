#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave 主入口模块
支持两种模式：基于注释的传统插桩和基于YAML配置的锚点插桩

本模块是YAMLWeave工具的主入口，实现了note.md中描述的功能：
1. 传统模式 - 基于代码注释插桩:

原始代码:
```c
void process_data(int data) {
    // TC001 STEP1: 数据边界检查
    // code: if (data < 0 || data > 100) { log_error("无效数据: %d", data); return; }
    perform_data_processing(data);
}
```

插入后的代码:
```c
void process_data(int data) {
    // TC001 STEP1: 数据边界检查
    // code: if (data < 0 || data > 100) { log_error("无效数据: %d", data); return; }
    if (data < 0 || data > 100) {  // 通过桩插入
        log_error("无效数据: %d", data);  // 通过桩插入
        return;  // 通过桩插入
    }  // 通过桩插入
    perform_data_processing(data);
}
```

2. 分离模式 - 基于锚点与YAML配置的插桩:

YAML配置:
```yaml
TC001:
  STEP1:
    segment1:
      - if (data < 0 || data > 100) {
      - "    log_error(\"无效数据: %d\", data);"
      - "    return;"
      - }
```

原始代码:
```c
void process_data(int data) {
    // TC001 STEP1 segment1
    perform_data_processing(data);
}
```

插入后的代码:
```c
void process_data(int data) {
    // TC001 STEP1 segment1
    if (data < 0 || data > 100) {  // 通过桩插入
        log_error("无效数据: %d", data);  // 通过桩插入
        return;  // 通过桩插入
    }  // 通过桩插入
    perform_data_processing(data);
}
```

"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import importlib.util
import site
import inspect
import logging
from pathlib import Path
import tempfile
import uuid
import datetime
import shutil
from utils.logger import setup_global_logger
import glob

setup_global_logger()

# 获取应用根目录的函数
def get_application_root():
    """
    获取应用程序根目录，支持普通运行和PyInstaller打包后的场景
    
    返回:
        str: 应用程序根目录的绝对路径
    """
    # PyInstaller打包后，_MEIPASS变量包含应用程序的根目录
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的路径
        return sys._MEIPASS
    
    # 普通Python运行 - 获取当前文件所在目录的父目录（项目根目录）
    current_file = os.path.abspath(inspect.getfile(inspect.currentframe()))
    code_dir = os.path.dirname(current_file)
    return os.path.dirname(code_dir)  # 返回code目录的父目录作为项目根目录

# 设置应用根目录
APP_ROOT = get_application_root()

# 配置模块导入路径
def setup_import_paths():
    """
    配置模块导入路径，确保能够正确导入项目模块
    无论是直接运行还是打包后运行
    """
    # 将项目根目录添加到Python路径
    if APP_ROOT not in sys.path:
        sys.path.insert(0, APP_ROOT)
    
    # 将code目录添加到Python路径（如果存在）
    code_dir = os.path.join(APP_ROOT, "code")
    if os.path.isdir(code_dir) and code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    
    # 打印当前应用根目录和sys.path (调试用)
    print(f"应用根目录: {APP_ROOT}")
    print(f"sys.path: {sys.path}")

# 设置导入路径
setup_import_paths()

# 配置日志记录器
def setup_logger():
    """配置并返回日志记录器"""
    try:
        # 创建日志记录器
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # 配置控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(console_handler)
        
        print(f"日志将写入: {APP_ROOT}")
        return logger
    except Exception as e:
        # 最小日志配置
        print(f"创建日志记录器时出错: {str(e)}")
        try:
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
        except:
            pass
            
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
        logger.warning(f"使用基本日志配置，原因: {str(e)}")
        return logger

# 设置日志记录器
logger = setup_logger()

# 尝试导入核心模块
try:
    # 使用相对导入方式
    from code.core.stub_processor import StubProcessor
    from code.ui.app_ui import YAMLWeaveUI
    from code.ui.app_controller import AppController
    
    logger.info("成功导入核心模块")
except ImportError as e:
    logger.error(f"导入核心模块失败: {str(e)}")
    # 尝试调整路径后导入
    try:
        # 尝试导入绝对路径
        sys.path.insert(0, os.path.join(APP_ROOT, "code"))
        from code.core.stub_processor import StubProcessor
        from code.ui.app_ui import YAMLWeaveUI
        from code.ui.app_controller import AppController
        
        logger.info("成功通过调整路径导入核心模块")
    except Exception as inner_e:
        logger.error(f"调整路径后导入核心模块仍然失败: {str(inner_e)}")
        messagebox.showerror("导入错误", "无法导入核心处理模块，请确保项目结构完整")
        sys.exit(1)
except Exception as e:
    logger.error(f"导入核心模块失败: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())
    messagebox.showerror("导入错误", f"导入核心模块时发生错误: {str(e)}")
    sys.exit(1)

def show_message(message):
    """显示简单的消息对话框，同时记录日志"""
    logger.info(f"显示消息: {message}")
    try:
        messagebox.showinfo("YAMLWeave", message)
    except Exception as e:
        logger.error(f"显示消息对话框失败: {str(e)}")
        print(f"[YAMLWeave] {message}")

def ensure_data_directory():
    """确保数据目录存在，包括示例和配置文件"""
    try:
        # 获取应用根目录
        logger.info(f"应用根目录: {APP_ROOT}")
        
        # 创建示例目录
        samples_dir = os.path.join(APP_ROOT, "samples")
        try:
            os.makedirs(samples_dir, exist_ok=True)
            logger.info(f"确保示例目录存在: {samples_dir}")
        except Exception as e:
            logger.warning(f"创建示例目录失败: {samples_dir}, 错误: {str(e)}")
            # 尝试在临时目录创建
            samples_dir = os.path.join(tempfile.gettempdir(), "yamlweave_samples")
            os.makedirs(samples_dir, exist_ok=True)
            logger.info(f"在临时目录创建示例目录: {samples_dir}")
        
        # 返回目录路径供后续使用
        return {
            "samples_dir": samples_dir
        }
    except Exception as e:
        logger.error(f"创建数据目录失败: {str(e)}")
        # 记录详细错误
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        
        # 回退到临时目录
        fallback_dir = os.path.join(tempfile.gettempdir(), "yamlweave_samples")
        logger.warning(f"回退到临时目录: {fallback_dir}")
        return {
            "samples_dir": fallback_dir
        }

def create_example_files(dirs):
    """创建基础示例文件和配置"""
    try:
        samples_dir = dirs["samples_dir"]
        
        # 创建基础示例子目录，直接在samples_dir下创建module1和module2
        module1_dir = os.path.join(samples_dir, "module1")
        module2_dir = os.path.join(samples_dir, "module2")
        
        created_dirs = []
        for module_dir in [module1_dir, module2_dir]:
            try:
                os.makedirs(module_dir, exist_ok=True)
                created_dirs.append(module_dir)
                logger.info(f"确保模块目录存在: {module_dir}")
            except Exception as e:
                logger.warning(f"创建目录失败: {module_dir}, 错误: {str(e)}")
        
        if not created_dirs:
            logger.error("所有示例目录创建都失败，将尝试继续但可能会有问题")
        
        # 创建module1中的示例文件
        demo1_1_file = os.path.join(module1_dir, "Demo1.1.c")
        if not os.path.exists(demo1_1_file):
            try:
                with open(demo1_1_file, "w", encoding="utf-8") as f:
                    f.write('''/**
 * 模块1示例文件1
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/**
 * 模块1函数1: 数据验证与边界检查
 */
int validate_data(int value) {
    // TC001 STEP1 segment1
    
    printf("验证数据: %d\\n", value);
    
    // TC101 STEP1 segment1
    
    // TC201 STEP1 benchmark_start
    
    return value > 0 ? 1 : 0;
}

/**
 * 模块1函数2: 数据处理与转换
 */
void process_data(int data) {
    // TC001 STEP2 segment1
    
    printf("处理数据: %d\\n", data);
    
    // TC102 STEP1 format_check
    
    // TC102 STEP1 segment1
    
    // TC102 STEP1 check_business_rules
}

/**
 * 模块1函数3: 系统初始化与资源分配
 */
int initialize_system(void* config) {
    // TC101 STEP1 log_init
    
    // TC101 STEP1 segment2
    
    printf("系统初始化中...\\n");
    return 0;
}
''')
                logger.info(f"创建示例文件: {demo1_1_file}")
            except Exception as e:
                logger.error(f"创建示例文件失败: {demo1_1_file}, 错误: {str(e)}")
        
        # 创建module1中的第二个示例文件
        demo1_2_file = os.path.join(module1_dir, "Demo1.2.c")
        if not os.path.exists(demo1_2_file):
            try:
                with open(demo1_2_file, "w", encoding="utf-8") as f:
                    f.write('''/**
 * 模块1示例文件2
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <string.h>

/**
 * 模块1函数3: 消息处理
 */
void process_message(const char* message) {
    // TC001 STEP3 segment1
    
    printf("处理消息: %s\\n", message);
    
    // TC102 STEP2 segment1
    
    // TC102 STEP2 verify_permissions
    
    // TC102 STEP2 after_verification
}

/**
 * 模块1函数4: 系统状态检查
 */
int check_system_status() {
    // TC001 STEP4 segment1
    
    printf("检查系统状态...\\n");
    
    // TC103 STEP1 segment1
    
    // TC103 STEP1 close_connections
    
    // TC103 STEP1 rollback
    
    return 1;
}

/**
 * 模块1函数5: 错误处理与报告
 */
void handle_error(int error_code, const char* error_description, const char* error_details) {
    // TC103 STEP2 log_error
    
    // TC103 STEP2 segment2
    
    // TC103 STEP2 completed
    
    printf("处理错误: %d, %s\\n", error_code, error_description);
}
''')
                logger.info(f"创建示例文件: {demo1_2_file}")
            except Exception as e:
                logger.error(f"创建示例文件失败: {demo1_2_file}, 错误: {str(e)}")
                
        # 创建module2中的示例文件
        demo2_1_file = os.path.join(module2_dir, "Demo2.1.c")
        if not os.path.exists(demo2_1_file):
            try:
                with open(demo2_1_file, "w", encoding="utf-8") as f:
                    f.write('''/**
 * 模块2示例文件1
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <stdlib.h>

/**
 * 模块2函数1: 初始化模块
 */
void init_module() {
    // TC002 STEP1 segment1
    
    printf("初始化模块2...\\n");
    
    // TC101 STEP2 network_init
    
    // TC101 STEP2 before_db_init
    
    // TC101 STEP2 segment3
}

/**
 * 模块2函数2: 释放资源
 */
void release_resources() {
    // TC002 STEP2 segment1
    
    printf("释放模块2资源...\\n");
    
    // TC202 STEP1 test_min_max
    
    // TC202 STEP1 test_special_chars
}

/**
 * 模块2函数3: 性能测试与基准测量
 */
void performance_test(int iterations) {
    // TC201 STEP1 benchmark_start
    
    printf("性能测试中...\\n");
    
    // TC203 STEP1 complex_structures
    
    // TC201 STEP1 benchmark_end
}
''')
                logger.info(f"创建示例文件: {demo2_1_file}")
            except Exception as e:
                logger.error(f"创建示例文件失败: {demo2_1_file}, 错误: {str(e)}")
        
        # 创建module2中的第二个示例文件
        demo2_2_file = os.path.join(module2_dir, "Demo2.2.c")
        if not os.path.exists(demo2_2_file):
            try:
                with open(demo2_2_file, "w", encoding="utf-8") as f:
                    f.write('''/**
 * 模块2示例文件2
 * 用于测试多文件场景下的插桩功能
 */

#include <stdio.h>
#include <math.h>

/**
 * 模块2函数3: 处理原始数据
 */
float process_raw_data(int raw_data) {
    // TC002 STEP3 segment1
    
    printf("处理原始数据: %d\\n", raw_data);
    return (float)raw_data * 1.5f;
}

/**
 * 模块2函数4: 验证结果
 */
int verify_result(float result, float expected) {
    // TC002 STEP4 segment1
    
    printf("验证结果: 实际 %.2f vs 期望 %.2f\\n", result, expected);
    
    // TC202 STEP1 test_min_max
    
    return fabs(result - expected) < (expected * 0.05f) ? 1 : 0;
}

/**
 * 模块2函数5: 复杂数据处理
 */
void process_complex_data(void* data_array, int array_size) {
    // TC203 STEP1 complex_structures
    
    printf("处理复杂数据结构...\\n");
}
''')
                logger.info(f"创建示例文件: {demo2_2_file}")
            except Exception as e:
                logger.error(f"创建示例文件失败: {demo2_2_file}, 错误: {str(e)}")
        
        # 为多文件测试创建YAML配置文件
        basic_yaml_content = '''# YAMLWeave 基础测试配置\n# 用于验证在多个文件场景下成功插入代码\n\n# 模块1 测试用例\nTC001:\n  STEP1:\n    segment1: |\n      if (value < 0) {\n          printf("模块1-文件1: 检测到无效值 %d\\n", value);\n          return 0;\n      }\n  STEP2:\n    segment1: |\n      int processed_data = data * 2;\n      printf("模块1-文件1: 数据已处理为 %d\\n", processed_data);\n  STEP3:\n    segment1: |\n      printf("模块1-文件2: 开始处理消息 '%s'\\n", message);\n      if (message == NULL || *message == '\\0') {\n          printf("模块1-文件2: 无效消息!\\n");\n          return;\n      }\n  STEP4:\n    segment1: |\n      int system_status = 1;\n      if (system_status != 1) {\n          printf("模块1-文件2: 系统状态异常\\n");\n          return 0;\n      }\n\n# 模块2 测试用例\nTC002:\n  STEP1:\n    segment1: |\n      static int initialized = 0;\n      if (initialized) {\n          printf("模块2-文件1: 已经初始化过了\\n");\n          return;\n      }\n      initialized = 1;\n  STEP2:\n    segment1: |\n      static int resources_released = 0;\n      if (resources_released) {\n          printf("模块2-文件1: 资源已释放\\n");\n          return;\n      }\n      resources_released = 1;\n  STEP3:\n    segment1: |\n      if (raw_data < 0) {\n          printf("模块2-文件2: 无效原始数据 %d\\n", raw_data);\n          return 0.0f;\n      }\n  STEP4:\n    segment1: |\n      float diff = result - expected;\n      float tolerance = expected * 0.05f;\n      printf("模块2-文件2: 差异 %.2f, 容差 %.2f\\n", diff, tolerance);'''
        
        return {
            "example_project_path": samples_dir,
            "simple_examples_dir": samples_dir,  # 将simple_examples_dir直接指向samples_dir
            "simple_yaml_path": "",
            "basic_yaml_content": basic_yaml_content
        }
    except Exception as e:
        logger.error(f"创建示例文件时出错: {str(e)}")
        # 返回最小必要的结果，防止后续代码崩溃
        return {
            "example_project_path": dirs["samples_dir"],
            "simple_examples_dir": dirs["samples_dir"],  # 将simple_examples_dir直接指向samples_dir
            "simple_yaml_path": "",
            "basic_yaml_content": ""
        }

def create_advanced_test_cases(dirs):
    """创建更全面的测试用例配置，覆盖所有测试功能点"""
    samples_dir = dirs["samples_dir"]
    logger.info(f"开始创建高级测试用例: {samples_dir}")
    
    # 创建高级测试YAML配置内容
    advanced_yaml_content = '''# YAMLWeave 高级测试配置文件
# 演示不同命名风格的segment，包括序号型和功能描述型

# ====== 系统初始化测试 ======

# TC101: 初始化测试 - 混合使用不同命名风格
TC101:
  # STEP1: 系统初始化
  STEP1:
    # 序号型命名
    segment1: |
      if (config == NULL) {
          printf("错误: 配置为空\\n");
          return INIT_ERROR_NULL_CONFIG;
      }
      printf("配置检查通过\\n");
    
    # 功能描述型命名
    log_init: |
      int log_status = init_log_system(config->log_level);
      if (log_status != SUCCESS) {
          printf("警告: 日志系统初始化失败 (状态码: %d)\\n", log_status);
      } else {
          log_message(LOG_INFO, "日志系统已初始化");
      }
    
    # 序号型命名
    segment2: |
      system_context = (SystemContext*)malloc(sizeof(SystemContext));
      if (system_context == NULL) {
          log_message(LOG_ERROR, "致命错误: 无法分配系统上下文内存");
          return INIT_ERROR_MEMORY_ALLOC;
      }
      memset(system_context, 0, sizeof(SystemContext));
  
  # STEP2: 模块初始化
  STEP2:
    # 功能描述型命名
    network_init: |
      system_context->network_handle = network_initialize(config->net_params);
      if (system_context->network_handle == NULL) {
          log_message(LOG_ERROR, "网络模块初始化失败");
          return INIT_ERROR_NETWORK;
      }
      log_message(LOG_INFO, "网络模块已初始化");
    
    # 位置型命名
    before_db_init: |
      log_message(LOG_INFO, "准备初始化数据库连接...");
      if (config->db_host == NULL) {
          log_message(LOG_ERROR, "数据库主机未配置");
          return INIT_ERROR_DATABASE_CONFIG;
      }
    
    # 序号型命名
    segment3: |
      DatabaseConfig db_config;
      db_config.host = config->db_host;
      db_config.port = config->db_port;
      db_config.username = config->db_user;
      db_config.password = config->db_password;
      
      system_context->db_handle = database_connect(&db_config);
      if (system_context->db_handle == NULL) {
          log_message(LOG_ERROR, "数据库模块初始化失败");
          return INIT_ERROR_DATABASE;
      }
      log_message(LOG_INFO, "数据库模块已初始化");

# ====== 数据验证测试 ======

# TC102: 数据验证测试 - 混合使用不同命名风格
TC102:
  # STEP1: 输入数据验证
  STEP1:
    # 功能描述型命名
    format_check: |
      if (data == NULL || data->format != DATA_FORMAT_V1) {
          log_message(LOG_ERROR, "数据格式无效");
          return VALIDATION_ERROR_FORMAT;
      }
    
    # 序号型命名
    segment1: |
      uint32_t calculated_checksum = calculate_checksum(data->buffer, data->length);
      if (calculated_checksum != data->checksum) {
          log_message(LOG_WARNING, "数据校验和不匹配: 期望 %u, 实际 %u", 
                     data->checksum, calculated_checksum);
          return VALIDATION_ERROR_CHECKSUM;
      }
    
    # 组合型命名
    check_business_rules: |
      if (data->timestamp < get_system_time() - MAX_DATA_AGE) {
          log_message(LOG_WARNING, "数据已过期");
          return VALIDATION_ERROR_EXPIRED;
      }
      
      if (data->value < MIN_ACCEPTABLE_VALUE || data->value > MAX_ACCEPTABLE_VALUE) {
          log_message(LOG_WARNING, "数据值超出可接受范围: %f", data->value);
          return VALIDATION_ERROR_VALUE_RANGE;
      }

  # STEP2: 权限验证
  STEP2:
    # 序号型命名
    segment1: |
      UserContext* user = get_current_user();
      if (user == NULL) {
          log_message(LOG_ERROR, "未找到用户上下文");
          return VALIDATION_ERROR_NO_USER;
      }
    
    # 功能描述型命名
    verify_permissions: |
      if ((user->permissions & PERMISSION_DATA_WRITE) == 0) {
          log_message(LOG_WARNING, "用户 %s 没有数据写入权限", user->username);
          return VALIDATION_ERROR_PERMISSION;
      }
      log_message(LOG_INFO, "用户 %s 权限验证通过", user->username);
    
    # 后处理命名
    after_verification: |
      log_message(LOG_INFO, "验证完成，更新用户访问时间戳");
      user->last_access_time = get_system_time();

# ====== 错误处理测试 ======

# TC103: 错误处理测试 - 混合使用不同命名风格
TC103:
  # STEP1: 资源清理
  STEP1:
    # 序号型命名
    segment1: |
      if (resource != NULL) {
          if (resource->buffer != NULL) {
              free(resource->buffer);
              resource->buffer = NULL;
          }
          free(resource);
          resource = NULL;
      }
    
    # 功能描述型命名
    close_connections: |
      if (connection_is_open(conn)) {
          log_message(LOG_INFO, "关闭连接...");
          int close_status = connection_close(conn);
          if (close_status != SUCCESS) {
              log_message(LOG_WARNING, "关闭连接时出错: %d", close_status);
              return close_status;
          }
      }
    
    # 动作型命名
    rollback: |
      if (transaction_is_active(transaction)) {
          log_message(LOG_INFO, "回滚事务...");
          int rollback_status = transaction_rollback(transaction);
          if (rollback_status != SUCCESS) {
              log_message(LOG_ERROR, "事务回滚失败: %d", rollback_status);
              // 即使回滚失败也继续处理
          }
      }

  # STEP2: 错误报告
  STEP2:
    # 功能描述型命名
    log_error: |
      log_message(LOG_ERROR, "操作失败: %s (错误码: %d)", error_description, error_code);
      if (error_details != NULL) {
          log_message(LOG_DEBUG, "错误详情: %s", error_details);
      }
    
    # 序号型命名
    segment2: |
      if (error_code >= CRITICAL_ERROR_THRESHOLD) {
          send_admin_notification("系统错误", error_description);
          log_message(LOG_INFO, "已发送管理员通知");
      }
    
    # 状态型命名
    completed: |
      log_message(LOG_INFO, "错误处理流程已完成");
      return ERROR_HANDLED;

# ====== 性能与边界测试 ======

# TC201: 性能测试 - 测试桩代码对性能的影响
TC201:
  # STEP1: 性能基准测试
  STEP1:
    benchmark_start: |
      clock_t start_time = clock();
      long long iteration_counter = 0;
      printf("性能测试开始\\n");
    
    benchmark_end: |
      clock_t end_time = clock();
      double elapsed_seconds = (double)(end_time - start_time) / CLOCKS_PER_SEC;
      printf("性能测试完成: 耗时 %.6f 秒, 迭代次数 %lld\\n", elapsed_seconds, iteration_counter);
      printf("每秒处理 %.2f 次操作\\n", iteration_counter / elapsed_seconds);

# TC202: 边界测试 - 测试各种边界情况
TC202:
  # STEP1: 边界值测试
  STEP1:
    test_min_max: |
      // 测试整型边界值
      if (value == INT_MIN || value == INT_MAX) {
          printf("检测到整型边界值: %d\\n", value);
          return BOUNDARY_CASE;
      }
      
      // 测试浮点数边界值
      if (fabs(double_value) < 1e-10 || fabs(double_value) > 1e10) {
          printf("检测到浮点数边界值: %e\\n", double_value);
          return BOUNDARY_CASE;
      }
    
    test_special_chars: |
      // 测试特殊字符输入
      if (strchr(input, '\\\\') || strchr(input, '\\"') || strchr(input, '\\'')) {
          printf("检测到特殊字符输入\\n");
          // 对特殊字符进行转义处理
          char* escaped = escape_string(input);
          printf("转义后: %s\\n", escaped);
          free(escaped);
      }

# TC203: 复杂代码段测试 - 测试多级缩进和循环
TC203:
  STEP1:
    complex_structures: |
      // 多级嵌套的数据结构和控制流测试
      for (int i = 0; i < array_size; i++) {
          if (data_array[i].type == TYPE_COMPOSITE) {
              CompositeData* composite = (CompositeData*)data_array[i].data;
              
              for (int j = 0; j < composite->child_count; j++) {
                  ChildData* child = &composite->children[j];
                  
                  if (child->flags & FLAG_REQUIRES_PROCESSING) {
                      switch (child->category) {
                          case CATEGORY_A:
                              process_category_a(child);
                              break;
                          case CATEGORY_B:
                              if (child->priority > HIGH_PRIORITY) {
                                  process_high_priority_b(child);
                              } else {
                                  process_normal_priority_b(child);
                              }
                              break;
                          default:
                              log_message(LOG_WARNING, "未知类别: %d", child->category);
                              continue;
                      }
                      
                      // 统计处理结果
                      processed_count++;
                      total_size += child->size;
                  }
              }
          }
      }
      
      printf("处理完成: %d 项, 总大小: %lu 字节\\n", processed_count, total_size);'''
    
    # 返回高级测试YAML内容
    return advanced_yaml_content

def create_combined_yaml(dirs, basic_content, advanced_content):
    """创建合并的YAML配置文件，包含基础测试和高级测试的所有用例"""
    try:
        samples_dir = dirs["samples_dir"]
        combined_yaml_file = os.path.join(samples_dir, "all_tests.yaml")
        
        # 确保内容不为None
        basic_content = basic_content or "# 基础测试内容创建失败"
        advanced_content = advanced_content or "# 高级测试用例创建失败"
        
        try:
            with open(combined_yaml_file, "w", encoding="utf-8") as f:
                f.write('''# YAMLWeave 综合测试配置文件
# 包含所有基础测试和高级测试用例
# ---------------------------------------

# =========== 基础测试用例 ===========
''')
                f.write(basic_content)
                f.write('''

# =========== 高级测试用例 ===========
''')
                f.write(advanced_content)
            
            logger.info(f"创建综合测试YAML配置: {combined_yaml_file}")
        except Exception as e:
            logger.error(f"写入综合测试YAML配置失败: {str(e)}")
            # 尝试在临时目录创建
            import tempfile
            temp_dir = tempfile.gettempdir()
            combined_yaml_file = os.path.join(temp_dir, "yamlweave_all_tests.yaml")
            try:
                with open(combined_yaml_file, "w", encoding="utf-8") as f:
                    f.write('''# YAMLWeave 临时综合测试配置文件
# 包含所有基础测试和高级测试用例
# ---------------------------------------

''')
                    f.write(basic_content)
                    f.write('''

# =========== 高级测试用例 ===========
''')
                    f.write(advanced_content)
                logger.info(f"在临时目录创建综合测试YAML配置: {combined_yaml_file}")
            except Exception as inner_e:
                logger.error(f"在临时目录创建综合测试YAML配置也失败: {str(inner_e)}")
                # 回退到使用内存中的临时路径
                combined_yaml_file = ""
        
        return combined_yaml_file
    except Exception as e:
        logger.error(f"创建合并YAML配置文件时出错: {str(e)}")
        return ""  # 返回空字符串，表示没有创建成功

def create_fallback_controller(ui_instance):
    """
    创建后备控制器类，在无法加载原始AppController时使用
    提供与原始控制器相同的基本功能
    """
    logger.info("创建后备AppController类...")    
    
    class FallbackAppController:
        """
        后备控制器实现，提供基本的文件处理和插桩功能
        在无法导入原始AppController时使用
        """
        def __init__(self, ui):
            self.ui = ui
            self.processor = None
            
            # 添加锚点存储
            self.anchors_found = 0
            self.anchor_details = []
            
            # 设置进程回调函数
            ui.set_process_callback(self.process_files)
            logger.info("后备AppController已初始化")
            
            # 尝试导入StubProcessor
            try:
                # 尝试多种可能的导入路径
                stub_processor_module = None
                import_paths = [
                    "core.stub_processor",
                    "code.core.stub_processor",
                    "YAMLWeave.core.stub_processor",
                    "stub_processor"  # 添加直接导入路径
                ]
                
                for path in import_paths:
                    try:
                        logger.info(f"尝试从{path}导入StubProcessor")
                        __import__(path)
                        stub_processor_module = sys.modules[path]
                        logger.info(f"成功从{path}导入模块")
                        # 设置控制器级别为完整功能
                        self.controller_level = 0
                        break
                    except ImportError as e:
                        logger.warning(f"从{path}导入失败: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"从{path}导入时发生非导入错误: {str(e)}")
                        continue
                
                if stub_processor_module and hasattr(stub_processor_module, "StubProcessor"):
                    self.StubProcessor = stub_processor_module.StubProcessor
                    logger.info("成功导入StubProcessor类")
                else:
                    # 如果无法导入，尝试手动查找文件
                    logger.warning("无法通过常规方式导入StubProcessor，尝试手动查找文件...")
                    search_paths = [
                        APP_ROOT,
                        os.path.dirname(APP_ROOT),
                        os.path.join(APP_ROOT, "code"),
                        os.path.join(APP_ROOT, "core"),
                        os.path.join(APP_ROOT, "code", "core"),
                        os.path.join(os.path.abspath(os.curdir), "code", "core")  # 添加当前工作目录
                    ]
                    
                    if hasattr(sys, '_MEIPASS'):
                        search_paths.append(sys._MEIPASS)
                        search_paths.append(os.path.join(sys._MEIPASS, "core"))
                    
                    stub_processor_file = None
                    for path in search_paths:
                        if os.path.exists(path):
                            logger.info(f"搜索路径: {path}")
                            file_candidates = [
                                "stub_processor.py", 
                                "core/stub_processor.py", 
                                "core\\stub_processor.py", 
                                "code/core/stub_processor.py", 
                                "code\\core\\stub_processor.py"
                            ]
                            for filename in file_candidates:
                                filepath = os.path.join(path, filename)
                                if os.path.exists(filepath):
                                    stub_processor_file = filepath
                                    logger.info(f"找到StubProcessor文件: {stub_processor_file}")
                                    break
                            if stub_processor_file:
                                break
                    
                    if stub_processor_file:
                        # 手动导入StubProcessor类
                        try:
                            spec = importlib.util.spec_from_file_location("stub_processor", stub_processor_file)
                            if spec:
                                stub_processor_module = importlib.util.module_from_spec(spec)
                                sys.modules["stub_processor"] = stub_processor_module
                                spec.loader.exec_module(stub_processor_module)
                                
                                if hasattr(stub_processor_module, "StubProcessor"):
                                    self.StubProcessor = stub_processor_module.StubProcessor
                                    logger.info("成功从文件路径导入StubProcessor类")
                                    # 设置控制器级别为降级功能
                                    self.controller_level = 1
                                else:
                                    logger.error(f"在模块中找不到StubProcessor类: {stub_processor_file}")
                                    self.create_minimal_stub_processor()
                                    # 设置控制器级别为最小功能
                                    self.controller_level = 2
                            else:
                                logger.error(f"无法为模块创建spec: {stub_processor_file}")
                                self.create_minimal_stub_processor()
                                # 设置控制器级别为最小功能
                                self.controller_level = 2
                        except Exception as e:
                            logger.error(f"导入StubProcessor类失败: {str(e)}")
                            logger.error(f"详细错误: {traceback.format_exc()}")
                            self.create_minimal_stub_processor()
                            # 设置控制器级别为最小功能
                            self.controller_level = 2
                    else:
                        logger.error("无法找到stub_processor.py文件，创建最简实现")
                        self.create_minimal_stub_processor()
                        # 设置控制器级别为最小功能
                        self.controller_level = 2
            except Exception as e:
                logger.error(f"导入StubProcessor时出错: {str(e)}")
                logger.error(f"详细错误: {traceback.format_exc()}")
                # 如果导入失败，创建一个最小化的StubProcessor实现
                self.create_minimal_stub_processor()
                # 设置控制器级别为最小功能
                self.controller_level = 2
            
            # 记录控制器级别信息
            levels = ["完整功能", "降级功能", "最小功能"]
            logger.info(f"控制器功能级别: {levels[self.controller_level]}")
            if self.ui:
                self.ui.root.after(0, self.ui.log, f"[系统] 初始化控制器功能级别: {levels[self.controller_level]}")
        
        def create_minimal_stub_processor(self):
            """
            创建最小化的StubProcessor类实现，提供基本功能
            """
            logger.info("创建最小化StubProcessor实现...")
            
            try:
                # 首先尝试导入我们创建的最小化StubProcessor
                try:
                    from code.minimal_stub_processor import MinimalStubProcessor
                    logger.info("成功从code.minimal_stub_processor导入MinimalStubProcessor类")
                    return MinimalStubProcessor
                except ImportError:
                    # 尝试其他导入路径
                    try:
                        import sys
                        import os
                        module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
                        if module_path not in sys.path:
                            sys.path.append(module_path)
                        
                        # 尝试从不同路径导入
                        try:
                            from minimal_stub_processor import MinimalStubProcessor
                            logger.info("从minimal_stub_processor导入MinimalStubProcessor类")
                            return MinimalStubProcessor
                        except ImportError:
                            logger.warning("无法从minimal_stub_processor导入")
                            # 继续使用内联定义
                    except Exception as path_error:
                        logger.warning(f"调整路径失败: {str(path_error)}")
                        # 继续使用内联定义
            except Exception as e:
                logger.warning(f"导入外部MinimalStubProcessor类失败: {str(e)}")
                # 继续使用内联定义
            
            # 如果外部导入失败，使用内联定义
            logger.info("使用内联定义的MinimalStubProcessor类")
            
            class MinimalStubProcessor:
                def __init__(self, project_dir=None, yaml_file=None, ui=None):
                    self.project_dir = project_dir
                    self.yaml_file = yaml_file
                    self.yaml_config = {}
                    self.stats = {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0, "failed_files": 0}
                    self.ui = ui
                    
                    # 添加备份和输出目录属性
                    self.backup_dir = None
                    self.output_dir = None
                    
                    if yaml_file and os.path.exists(yaml_file):
                        try:
                            import yaml
                            with open(yaml_file, 'r', encoding='utf-8') as f:
                                self.yaml_config = yaml.safe_load(f) or {}
                                if not self.yaml_config:
                                    logger.warning(f"YAML配置文件为空或格式不正确: {yaml_file}")
                                    if self.ui:
                                        self.ui.root.after(0, self.ui.log, f"[警告] YAML配置为空或格式不正确: {yaml_file}")
                        except ImportError:
                            logger.error("无法导入yaml模块，YAML配置将不可用")
                            if self.ui:
                                self.ui.root.after(0, self.ui.log, "[错误] 无法导入yaml模块，YAML配置将不可用")
                        except Exception as e:
                            logger.error(f"加载YAML配置失败: {str(e)}")
                            if self.ui:
                                self.ui.root.after(0, self.ui.log, f"[错误] 加载YAML配置失败: {str(e)}")
                
                def process_single_file(self, content, file_path, callback=None):
                    """
                    处理单个文件内容，执行桩代码插入
                    返回处理后的文件内容
                    
                    参数:
                        content: 文件内容
                        file_path: 文件路径
                        callback: 可选回调函数，用于报告处理进度
                    """
                    try:
                        logger.info(f"处理文件内容: {file_path}")
                        if self.ui:
                            self.ui.log(f"[处理] 正在处理: {os.path.basename(file_path)}")
                        
                        # 保存当前处理的文件路径和内容，供钩子函数使用
                        self.current_file = file_path
                        self.current_content = content
                        
                        # 存储原始内容以便检查是否有变化
                        original_content = content
                        updated_content = content
                        lines = content.splitlines()
                        
                        # 计数器-用于跟踪修改过的行数
                        inserted_stubs = 0
                        
                        # 处理每一行
                        i = 0
                        total_lines = len(lines)
                        while i < total_lines:
                            # 设置当前处理的行号，用于钩子函数和拦截函数
                            self.current_line = i + 1
                            
                            # 调用进度回调
                            if callback:
                                progress = int((i / total_lines) * 100)
                                callback(progress, f"处理文件 {os.path.basename(file_path)}: {i+1}/{total_lines} 行")
                            
                            line = lines[i]
                            
                            # 搜索注释中的锚点
                            # 样式1: // TC001 STEP1 segment1 
                            # 样式2: // TC001 STEP1: 数据边界检查
                            # 样式3: // TC001 STEP1 format_check
                            anchor_match = None
                            
                            if "//" in line and "TC" in line and "STEP" in line:
                                # 尝试匹配锚点模式
                                comment_part = line.split("//")[1].strip()
                                parts = comment_part.split()
                                
                                # 直接输出调试信息到控制台
                                print(f"\n==== MinimalStubProcessor检测到锚点 ====")
                                print(f"文件: {os.path.basename(file_path)}")
                                print(f"行号: {i+1}")
                                print(f"内容: {line.strip()}")
                                print(f"Parts: {parts}")
                                print("=====================================\n")
                                
                                if len(parts) >= 3 and parts[0].startswith("TC") and parts[1].startswith("STEP"):
                                    tc_id = parts[0].upper()
                                    step_id = parts[1].upper()
                                    segment_id = parts[2].lower()
                                    
                                    # 直接输出锚点信息到控制台
                                    print(f"\n==== 确认锚点 ====")
                                    print(f"文件: {os.path.basename(file_path)}")
                                    print(f"行号: {i+1}")
                                    print(f"锚点: {tc_id} {step_id} {segment_id}")
                                    print("=================\n")
                                    
                                    # 使用钩子函数 - 如果控制器注入了hook
                                    if hasattr(self, 'anchor_hook'):
                                        try:
                                            self.anchor_hook(os.path.basename(file_path), i+1, tc_id, step_id, segment_id)
                                        except Exception as e:
                                            print(f"调用锚点钩子失败: {str(e)}")
                                            import traceback
                                            print(traceback.format_exc())
                                    
                                    # 直接输出锚点信息到UI
                                    if self.ui:
                                        try:
                                            anchor_message = f"[锚点] 在文件 {os.path.basename(file_path)} 的第 {i+1} 行找到锚点: {tc_id} {step_id} {segment_id}"
                                            
                                            # 直接尝试多种方式将信息输出到UI
                                            
                                            # 方法1: 直接调用log方法
                                            self.ui.log(anchor_message, tag="find")
                                            self.ui.log(f"[代码] {line.strip()}", tag="info")
                                            
                                            # 方法2: 直接操作Text控件
                                            if hasattr(self.ui, 'log_text'):
                                                import tkinter as tk
                                                import datetime
                                                timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
                                                self.ui.log_text.insert(tk.END, timestamp, "info")
                                                self.ui.log_text.insert(tk.END, anchor_message + "\n", "find")
                                                self.ui.log_text.see(tk.END)
                                                self.ui.log_text.update_idletasks()
                                            
                                            # 方法3: 使用after方法
                                            if hasattr(self.ui, 'root'):
                                                try:
                                                    self.ui.root.after(100, lambda: self.ui.log(f"[锚点后续] {tc_id} {step_id} {segment_id} @ {os.path.basename(file_path)}:{i+1}", tag="find"))
                                                except Exception as e:
                                                    print(f"使用after方法失败: {str(e)}")
                                        except Exception as e:
                                            print(f"UI日志输出失败: {str(e)}")
                                            import traceback
                                            print(traceback.format_exc())
                                    
                                    anchor_match = {
                                        "tc_id": tc_id,
                                        "step_id": step_id,
                                        "segment_id": segment_id
                                    }
                                    
                                    logger.info(f"找到锚点: {tc_id} {step_id} {segment_id}")
                            
                            # 如果找到锚点，尝试插入代码
                            if anchor_match:
                                tc_id = anchor_match["tc_id"]
                                step_id = anchor_match["step_id"]
                                segment_id = anchor_match["segment_id"]
                                
                                # 1. 首先检查YAML配置
                                if self.yaml_config and tc_id in self.yaml_config:
                                    tc_config = self.yaml_config[tc_id]
                                    
                                    # 查找对应步骤
                                    if step_id in tc_config:
                                        step_config = tc_config[step_id]
                                        
                                        # 查找对应段
                                        stub_code = None
                                        if segment_id and segment_id in step_config:
                                            stub_code = step_config[segment_id]
                                            # 输出锚点信息到UI - 确保锚点信息被直接输出
                                            if self.ui:
                                                try:
                                                    filename = os.path.basename(file_path)
                                                    print(f"检测YAML配置锚点: {tc_id} {step_id} {segment_id} 行号: {i+1}")
                                                    anchor_message = f"[锚点] 在文件 {filename} 的第 {i+1} 行找到YAML配置锚点: {tc_id} {step_id} {segment_id}"
                                                    self.ui.log(anchor_message, tag="find")
                                                    # 显示代码内容
                                                    if i < len(lines):
                                                        self.ui.log(f"[代码] {lines[i].strip()}", tag="info")
                                                except Exception as e:
                                                    print(f"输出YAML配置锚点信息失败: {str(e)}")
                                        
                                        if stub_code:
                                            # 插入桩代码
                                            indent = len(line) - len(line.lstrip())
                                            indent_str = " " * indent
                                            
                                            # 准备插入的代码行
                                            code_lines = []
                                            for code_line in stub_code.splitlines():
                                                # 为每行添加插桩注释
                                                code_lines.append(f"{code_line}  // 通过桩插入")
                                            
                                            # 插入代码行
                                            lines.insert(i + 1, "")  # 空行
                                            for idx, code_line in enumerate(code_lines):
                                                lines.insert(i + 1 + idx, f"{indent_str}{code_line}")
                                            
                                            # 更新插入统计
                                            inserted_stubs += 1
                                            self.stats["inserted_stubs"] += 1
                                            logger.info(f"从YAML插入桩代码: {tc_id} {step_id} {segment_id}")
                                            
                                            # 输出插桩信息到UI
                                            if self.ui:
                                                insertion_message = f"[插桩] 在文件 {os.path.basename(file_path)} 第 {i+1} 行插入 {tc_id} {step_id} {segment_id} 桩代码 ({len(code_lines)}行)"
                                                self.ui.log(insertion_message, tag="insert")
                                                
                                                # 强化插桩信息显示
                                                print(f"\n===== 插入桩代码信息 =====")
                                                print(f"文件: {os.path.basename(file_path)}")
                                                print(f"行号: {i+1}")
                                                print(f"锚点: {tc_id} {step_id} {segment_id}")
                                                print(f"插入行数: {len(code_lines)}")
                                                print("========================")
                                                
                                                # 尝试多种方式确保显示
                                                try:
                                                    # 方式1: 使用强制显示格式
                                                    enhanced_insertion = f"[插桩强制显示] {tc_id} {step_id} {segment_id} 在文件 {os.path.basename(file_path)}:{i+1} 插入{len(code_lines)}行"
                                                    self.ui.log(enhanced_insertion, tag="insert")
                                                    
                                                    # 方式2: 使用after方法
                                                    if hasattr(self.ui, 'root'):
                                                        self.ui.root.after(30, lambda: self.ui.log(f"[插桩确认] {tc_id} {step_id} {segment_id} @ {os.path.basename(file_path)}:{i+1}", tag="insert"))
                                                except Exception as e:
                                                    print(f"增强插桩显示失败: {str(e)}")
                                                
                                                # 最多显示3行代码预览
                                                preview_lines = code_lines[:3] if len(code_lines) > 3 else code_lines
                                                for idx, preview in enumerate(preview_lines):
                                                    self.ui.log(f"[代码] {' '*4}{preview}", tag="info")
                                                if len(code_lines) > 3:
                                                    self.ui.log(f"[代码] {' '*4}...还有 {len(code_lines)-3} 行未显示...", tag="info")
                                
                                # 2. 如果YAML配置不存在，则查找下一行是否包含code注释
                                code_line = None
                                if i + 1 < len(lines):
                                    next_line = lines[i + 1]
                                    if "//" in next_line and "code:" in next_line.lower():
                                        code_part = next_line.split("code:")[1].strip()
                                        code_line = code_part
                                
                                if code_line:
                                    # 获取缩进
                                    indent = len(line) - len(line.lstrip())
                                    indent_str = " " * indent
                                    
                                    # 处理代码行 (可能有多个语句用分号分隔)
                                    statements = code_line.split(";")
                                    code_lines = []
                                    
                                    for stmt in statements:
                                        stmt = stmt.strip()
                                        if stmt:  # 忽略空语句
                                            if stmt.endswith("}"):  # 处理包含 } 的语句
                                                # 分离 } 和前面的代码
                                                if stmt != "}":
                                                    before_brace = stmt[:stmt.rfind("}")].strip()
                                                    if before_brace:
                                                        code_lines.append(f"{before_brace};  // 通过桩插入")
                                                    code_lines.append("}  // 通过桩插入")
                                                else:
                                                    code_lines.append("}  // 通过桩插入")
                                            else:
                                                code_lines.append(f"{stmt};  // 通过桩插入")
                                    
                                    # 插入代码行
                                    for idx, code_line in enumerate(code_lines):
                                        lines.insert(i + 2 + idx, f"{indent_str}{code_line}")
                                    
                                    # 更新插入统计
                                    inserted_stubs += 1
                                    self.stats["inserted_stubs"] += 1
                                    logger.info(f"从注释插入桩代码: {tc_id} {step_id}")
                                    
                                    # 输出插桩信息到UI
                                    if self.ui:
                                        self.ui.log(f"[插桩] 在文件 {os.path.basename(file_path)} 第 {i+1} 行插入注释桩代码 ({len(code_lines)}行)", tag="insert")
                                        # 最多显示3行代码预览
                                        preview_lines = code_lines[:3] if len(code_lines) > 3 else code_lines
                                        for idx, preview in enumerate(preview_lines):
                                            self.ui.log(f"[代码] {' '*4}{preview}", tag="info")
                                        if len(code_lines) > 3:
                                            self.ui.log(f"[代码] {' '*4}...还有 {len(code_lines)-3} 行未显示...", tag="info")
                                    
                                    # 跳过刚插入的行
                                    i += len(code_lines) + 1
                                    continue
                            
                            i += 1
                        
                        # 检查是否需要更新文件
                        if inserted_stubs > 0:
                            # 构建更新后的内容
                            updated_content = "\n".join(lines)
                            
                            if self.ui:
                                self.ui.root.after(0, self.ui.log, f"[插桩] {os.path.basename(file_path)}: 已插入 {inserted_stubs} 个桩点")
                            
                            return updated_content
                        else:
                            logger.info(f"文件无需更新: {file_path}")
                            return content
                    except Exception as e:
                        error_msg = f"处理文件内容失败: {file_path}, 错误: {str(e)}"
                        logger.error(error_msg)
                        if self.ui:
                            self.ui.root.after(0, self.ui.log, f"[错误] {error_msg}")
                        # 重新引发异常，让上层处理
                        raise
                
                def process_files(self, project_dir=None, yaml_file=None):
                    """处理文件的主方法（线程安全进度条更新）"""
                    try:
                        # 调试信息 - 输出实例信息
                        print("\n=== DEBUG FALLBACK CONTROLLER ===")
                        print(f"FallbackAppController.process_files 被调用: {self.__class__.__name__}")
                        print(f"self.processor 类型: {type(self.processor).__name__ if self.processor else '无'}")
                        print(f"project_dir: {project_dir}")
                        print(f"yaml_file: {yaml_file}")
                        print(f"UI对象存在: {self.ui is not None}")
                        if self.ui:
                            print(f"UI对象ID: {id(self.ui)}")
                        
                        # 更新实例属性
                        if project_dir:
                            self.project_dir = project_dir
                        if yaml_file:
                            self.yaml_file = yaml_file
                            
                        # 创建备份目录和输出目录
                        if self.project_dir and os.path.exists(self.project_dir):
                            try:
                                import datetime
                                now = datetime.datetime.now()
                                timestamp = now.strftime("%Y%m%d_%H%M%S")
                                project_name = os.path.basename(self.project_dir.rstrip("/\\"))
                                
                                # 创建备份目录
                                backup_dir_name = f"{project_name}_backup_{timestamp}"
                                backup_dir = os.path.join(os.path.dirname(self.project_dir), backup_dir_name)
                                
                                # 创建输出目录
                                output_dir_name = f"{project_name}_stubbed_{timestamp}"
                                output_dir = os.path.join(os.path.dirname(self.project_dir), output_dir_name)
                                
                                # 保存目录路径
                                self.backup_dir = backup_dir
                                self.output_dir = output_dir
                                
                                # 创建备份目录
                                os.makedirs(backup_dir, exist_ok=True)
                                
                                # 创建输出目录
                                os.makedirs(output_dir, exist_ok=True)
                                
                                # 记录日志
                                if self.ui:
                                    self.ui.log(f"[信息] 已创建备份目录: {backup_dir_name}", tag="file")
                                    self.ui.log(f"[信息] 已创建输出目录: {output_dir_name}", tag="file")
                            except Exception as e:
                                print(f"创建备份和输出目录失败: {str(e)}")
                                import traceback
                                print(traceback.format_exc())
                        
                        # 清空锚点列表
                        self.anchors_found = 0
                        self.anchor_details = []
                        
                        # 记录UI日志
                        if self.ui:
                            self.ui.log("[信息] 开始处理目录: " + str(project_dir))
                            if yaml_file:
                                self.ui.log("[信息] 使用YAML配置: " + str(yaml_file))
                            self.ui.log("[信息] 设置UI引用给处理器")
                            self.ui.log("[信息] 开始处理过程 - 将显示所有锚点信息", tag="header")
                        
                        # 创建处理器实例(如果还没有)
                        if self.processor is None and hasattr(self, 'StubProcessor'):
                            print("创建新的StubProcessor实例")
                            
                            # 创建处理器时直接传入UI对象
                            print(f"传递UI对象: {self.ui}")
                            print(f"UI对象类型: {type(self.ui).__name__}")
                            
                            try:
                                self.processor = self.StubProcessor(project_dir, yaml_file, self.ui)
                                print(f"StubProcessor实例创建成功")
                                print(f"处理器UI对象: {self.processor.ui}")
                                print(f"处理器UI对象类型: {type(self.processor.ui).__name__ if self.processor.ui else '无UI'}")
                            except Exception as e:
                                print(f"StubProcessor实例创建失败: {str(e)}")
                                import traceback
                                print(traceback.format_exc())
                            
                            # 确保处理器的UI对象正确设置
                            if hasattr(self.processor, 'ui') and not self.processor.ui:
                                print("处理器UI对象未设置，手动设置")
                                self.processor.ui = self.ui
                            
                            print(f"新创建的处理器UI对象ID: {id(self.processor.ui) if hasattr(self.processor, 'ui') and self.processor.ui else '无'}")
                            
                            # 直接输出一条测试日志，检查UI引用是否正常
                            if hasattr(self.processor, 'ui') and self.processor.ui:
                                try:
                                    self.processor.ui.log("[信息] StubProcessor实例成功创建并设置UI引用", tag="info")
                                except Exception as e:
                                    print(f"测试UI日志输出失败: {str(e)}")
                            
                            # 更新处理器实例
                            if self.processor:
                                if project_dir:
                                    self.processor.project_dir = project_dir
                                if yaml_file:
                                    self.processor.yaml_file = yaml_file
                                
                                # 设置拦截函数
                                original_find_stub_code = None
                                if hasattr(self.processor, 'find_stub_code'):
                                    original_find_stub_code = self.processor.find_stub_code
                                    
                                    # 定义拦截函数
                                    def intercepted_find_stub_code(tc_id, step_id, segment_id):
                                        # 直接向UI输出锚点信息
                                        if self.ui:
                                            filename = os.path.basename(self.processor.current_file) if hasattr(self.processor, 'current_file') else "未知文件"
                                            line_num = self.processor.current_line if hasattr(self.processor, 'current_line') else 0
                                            self.ui.log(f"[锚点] 在文件 {filename} 的第 {line_num} 行找到锚点: {tc_id} {step_id} {segment_id}", tag="find")
                                            
                                            # 尝试获取当前行的代码内容
                                            try:
                                                if hasattr(self.processor, 'current_content') and self.processor.current_content:
                                                    lines = self.processor.current_content.splitlines()
                                                    if 0 <= line_num-1 < len(lines):
                                                        code_line = lines[line_num-1].strip()
                                                        self.ui.log(f"[代码] {code_line}", tag="info")
                                            except Exception as e:
                                                print(f"获取代码内容失败: {str(e)}")
                                        # 调用原始方法
                                        return original_find_stub_code(tc_id, step_id, segment_id)
                                    
                                    # 替换方法
                                    self.processor.find_stub_code = intercepted_find_stub_code
                                    print("已设置锚点拦截函数")
                                
                                # 确保UI引用正确设置
                                if hasattr(self.processor, 'ui'):
                                    # 调试信息 - 输出处理器信息
                                    print(f"处理器UI属性类型: {type(self.processor.ui).__name__ if hasattr(self.processor, 'ui') else '无'}")
                                    print(f"修改前UI对象ID: {id(self.processor.ui) if hasattr(self.processor, 'ui') and self.processor.ui else '无'}")
                                    
                                    # 强制设置UI - 确保使用我们的UI实例
                                    self.processor.ui = self.ui
                                    
                                    # 检查设置后UI对象
                                    print(f"修改后UI对象ID: {id(self.processor.ui) if hasattr(self.processor, 'ui') and self.processor.ui else '无'}")
                                    self.ui.log("[信息] 已设置内部处理器的UI引用")
                                else:
                                    print("警告: 处理器没有ui属性")
                                    # 尝试添加ui属性
                                    setattr(self.processor, 'ui', self.ui)
                                    print(f"添加ui属性后: {hasattr(self.processor, 'ui')}")
                                
                                # 添加辅助方法，确保锚点信息直接输出到UI
                                def display_anchor(filename, line_num, tc_id, step_id, segment_id):
                                    if self.ui:
                                        try:
                                            message = f"[锚点] 在文件 {filename} 的第 {line_num} 行找到锚点: {tc_id} {step_id} {segment_id}"
                                            self.ui.log(message, tag="find")
                                            # 尝试获取当前文件处理实例中的代码内容
                                            if hasattr(self.processor, 'current_content') and self.processor.current_content:
                                                lines = self.processor.current_content.splitlines()
                                                if 0 <= line_num-1 < len(lines):
                                                    code_line = lines[line_num-1].strip()
                                                    self.ui.log(f"[代码] {code_line}", tag="info")
                                            return True
                                        except Exception as e:
                                            print(f"显示锚点信息失败: {str(e)}")
                                    return False
                                
                                # 添加辅助方法到处理器
                                self.processor.display_anchor = display_anchor
                                
                                # 添加测试用例详情解析和展示功能
                                def parse_test_case_info(yaml_file):
                                    """解析YAML配置中的测试用例详细信息"""
                                    test_case_info = {}
                                    if not yaml_file or not os.path.exists(yaml_file):
                                        return test_case_info
                                    
                                    try:
                                        import yaml
                                        with open(yaml_file, 'r', encoding='utf-8') as f:
                                            yaml_content = yaml.safe_load(f)
                                            if not yaml_content:
                                                return test_case_info
                                            
                                            # 解析每个测试用例
                                            for tc_id, tc_data in yaml_content.items():
                                                # 获取测试用例描述（如果有）
                                                tc_desc = ""
                                                if isinstance(tc_data, dict):
                                                    # 查找注释行
                                                    with open(yaml_file, 'r', encoding='utf-8') as f_lines:
                                                        yaml_lines = f_lines.readlines()
                                                        for i, line in enumerate(yaml_lines):
                                                            if tc_id in line and line.strip().startswith(tc_id + ":"):
                                                                # 查找上方的注释行
                                                                for j in range(i-1, max(0, i-5), -1):
                                                                    if yaml_lines[j].strip().startswith("#"):
                                                                        tc_desc = yaml_lines[j].strip("# \n")
                                                                        break
                                                
                                                # 收集步骤和段信息
                                                steps = {}
                                                step_count = 0
                                                segment_count = 0
                                                code_lines = 0
                                                
                                                if isinstance(tc_data, dict):
                                                    for step_id, step_data in tc_data.items():
                                                        step_count += 1
                                                        segments = {}
                                                        
                                                        if isinstance(step_data, dict):
                                                            for segment_id, segment_code in step_data.items():
                                                                segment_count += 1
                                                                if isinstance(segment_code, str):
                                                                    segment_lines = len(segment_code.splitlines())
                                                                    code_lines += segment_lines
                                                                    segments[segment_id] = {
                                                                        'code': segment_code,
                                                                        'line_count': segment_lines
                                                                    }
                                                        
                                                        steps[step_id] = segments
                                                
                                                test_case_info[tc_id] = {
                                                    'description': tc_desc,
                                                    'steps': steps,
                                                    'step_count': step_count,
                                                    'segment_count': segment_count,
                                                    'code_lines': code_lines
                                                }
                                        
                                        print(f"已解析测试用例: {len(test_case_info)} 个")
                                        return test_case_info
                                    except Exception as e:
                                        print(f"解析测试用例信息失败: {str(e)}")
                                        import traceback
                                        print(traceback.format_exc())
                                        return {}
                                
                                # 收集测试用例分类信息
                                def categorize_test_cases(test_case_info):
                                    """对测试用例进行分类"""
                                    categories = {
                                        'basic': [],  # 基础测试 TC00x
                                        'init': [],   # 初始化测试 TC10x
                                        'validate': [], # 验证测试 TC20x 
                                        'feature': [], # 功能测试 TC30x-TC89x
                                        'performance': [], # 性能测试 TC90x
                                        'other': []   # 其他测试
                                    }
                                    
                                    for tc_id, tc_data in test_case_info.items():
                                        if tc_id.startswith('TC00'):
                                            categories['basic'].append(tc_id)
                                        elif tc_id.startswith('TC10'):
                                            categories['init'].append(tc_id) 
                                        elif tc_id.startswith('TC20'):
                                            categories['validate'].append(tc_id)
                                        elif tc_id.startswith('TC9'):
                                            categories['performance'].append(tc_id)
                                        elif tc_id.startswith('TC'):
                                            categories['feature'].append(tc_id)
                                        else:
                                            categories['other'].append(tc_id)
                                    
                                    return categories
                                
                                # 执行处理前添加直接UI输出测试
                                if self.ui:
                                    self.ui.log("[信息] 准备处理文件...", tag="header")
                                    
                                    # 解析并显示测试用例详情
                                    if yaml_file and os.path.exists(yaml_file):
                                        self.ui.log(f"[信息] 分析YAML配置文件: {os.path.basename(yaml_file)}", tag="info")
                                        test_case_info = parse_test_case_info(yaml_file)
                                        
                                        if test_case_info:
                                            # 测试用例总体统计
                                            total_tc = len(test_case_info)
                                            total_steps = sum(tc['step_count'] for tc in test_case_info.values())
                                            total_segments = sum(tc['segment_count'] for tc in test_case_info.values())
                                            total_code_lines = sum(tc['code_lines'] for tc in test_case_info.values())
                                            
                                            # 显示测试用例分类统计
                                            categories = categorize_test_cases(test_case_info)
                                            self.ui.log(f"[信息] ===== 测试用例分析 =====", tag="header")
                                            self.ui.log(f"[用例] 共加载测试用例: {total_tc} 个，步骤: {total_steps} 个，桩点: {total_segments} 个", tag="stats")
                                            self.ui.log(f"[用例] 总代码行数: {total_code_lines} 行", tag="stats")
                                            
                                            # 按分类显示测试用例
                                            category_names = {
                                                'basic': '基础测试',
                                                'init': '初始化测试',
                                                'validate': '验证测试',
                                                'feature': '功能测试',
                                                'performance': '性能测试',
                                                'other': '其他测试'
                                            }
                                            
                                            for cat, tc_list in categories.items():
                                                if tc_list:
                                                    self.ui.log(f"[用例] {category_names[cat]}: {len(tc_list)} 个", tag="info")
                                                    # 最多显示5个用例ID
                                                    if len(tc_list) <= 5:
                                                        for tc_id in tc_list:
                                                            desc = test_case_info[tc_id]['description']
                                                            desc_text = f" - {desc}" if desc else ""
                                                            self.ui.log(f"[用例]   {tc_id}{desc_text}", tag="find")
                                                    else:
                                                        for tc_id in tc_list[:3]:
                                                            desc = test_case_info[tc_id]['description']
                                                            desc_text = f" - {desc}" if desc else ""
                                                            self.ui.log(f"[用例]   {tc_id}{desc_text}", tag="find")
                                                        self.ui.log(f"[用例]   ...还有 {len(tc_list)-3} 个未显示...", tag="info")
                                            
                                            # 保存测试用例信息，以便后续使用
                                            self.test_case_info = test_case_info
                                            self.test_case_categories = categories
                                        else:
                                            self.ui.log("[警告] 无法从YAML文件中提取测试用例信息", tag="warning")
                                    
                                    self.ui.log("[信息] 开始扫描锚点和插入桩代码", tag="info")
                                
                                # 定义处理文件过程中的回调函数来提供实时锚点信息
                                def file_callback(filepath, updated):
                                    print(f"文件回调: {os.path.basename(filepath)} 已更新: {updated}")
                                    # 直接通过UI输出
                                    if self.ui:
                                        self.ui.log(f"[文件] 处理: {os.path.basename(filepath)}", tag="file")

                                # 定义锚点检测钩子函数 - 这将被插入到处理器中
                                def anchor_hook(filename, line_number, tc_id, step_id, segment_id):
                                    """处理检测到的锚点"""
                                    # 直接输出到控制台
                                    print(f"\n==== 锚点检测到 ====")
                                    print(f"文件: {filename}")
                                    print(f"行号: {line_number}")
                                    print(f"锚点: {tc_id} {step_id} {segment_id}")
                                    print("===================\n")
                                    
                                    self.anchors_found += 1
                                    self.anchor_details.append({
                                        'filename': filename, 
                                        'line': line_number, 
                                        'tc_id': tc_id, 
                                        'step_id': step_id, 
                                        'segment_id': segment_id
                                    })
                                    
                                    # 立即输出锚点信息
                                    if self.ui:
                                        try:
                                            # 强制直接写入而不使用UI对象的log方法
                                            anchor_message = f"[锚点] 在文件 {filename} 的第 {line_number} 行找到锚点: {tc_id} {step_id} {segment_id}"
                                            # 首先尝试直接插入到Text控件
                                            if hasattr(self.ui, 'log_text'):
                                                import tkinter as tk
                                                import datetime
                                                timestamp = datetime.datetime.now().strftime("[%H:%M:%S] ")
                                                self.ui.log_text.insert(tk.END, timestamp + anchor_message + "\n", "find")
                                                self.ui.log_text.see(tk.END)
                                                self.ui.log_text.update_idletasks()
                                            # 再尝试使用UI对象的log方法
                                            self.ui.log(anchor_message, tag="find")
                                            
                                            # 增强: 显示对应的用例详细信息和桩代码预览
                                            if hasattr(self, 'test_case_info') and tc_id in self.test_case_info:
                                                tc_info = self.test_case_info[tc_id]
                                                
                                                # 显示用例描述
                                                if tc_info['description']:
                                                    self.ui.log(f"[用例] {tc_id} 描述: {tc_info['description']}", tag="info")
                                                
                                                # 检查是否有对应的桩代码
                                                if step_id in tc_info['steps'] and segment_id in tc_info['steps'][step_id]:
                                                    segment_info = tc_info['steps'][step_id][segment_id]
                                                    code = segment_info['code']
                                                    lines = segment_info['line_count']
                                                    
                                                    # 显示桩代码信息
                                                    self.ui.log(f"[桩点] 将插入 {lines} 行代码", tag="info")
                                                    
                                                    # 显示代码预览（最多显示5行）
                                                    code_lines = code.splitlines()
                                                    preview_lines = code_lines[:min(5, len(code_lines))]
                                                    for i, line in enumerate(preview_lines):
                                                        self.ui.log(f"[代码] {i+1}: {line}", tag="code")
                                                    
                                                    # 如果代码超过5行，显示省略信息
                                                    if len(code_lines) > 5:
                                                        self.ui.log(f"[代码] ... 还有 {len(code_lines) - 5} 行未显示 ...", tag="code")
                                                else:
                                                    # 如果在YAML中找不到对应的桩代码，给出警告
                                                    self.ui.log(f"[警告] 在YAML配置中找不到对应的桩代码: {tc_id}.{step_id}.{segment_id}", tag="warning")
                                        except Exception as e:
                                            print(f"锚点输出失败: {str(e)}")
                                            import traceback
                                            print(traceback.format_exc())

                                # 设置钩子函数
                                if self.processor:
                                    # 注入钩子函数到处理器
                                    setattr(self.processor, 'anchor_hook', anchor_hook)
                                    setattr(self.processor, 'file_callback', file_callback)
                                
                                # 执行处理
                                print(f"调用 processor.process_files() 方法: {type(self.processor.process_files).__name__}")
                                print("=== DEBUG FALLBACK CONTROLLER END ===\n")
                                
                                result = self.processor.process_files()
                                
                                # 输出锚点统计
                                if self.anchors_found > 0 and self.ui:
                                    self.ui.log(f"\n[信息] ----- 锚点详细信息 ----- (共找到 {self.anchors_found} 个锚点)", tag="header")
                                    for i, detail in enumerate(self.anchor_details[:10]):  # 最多显示10个锚点
                                        self.ui.log(f"[锚点] 锚点 {i+1}: 文件 {detail['filename']} 第 {detail['line']} 行: {detail['tc_id']} {detail['step_id']} {detail['segment_id']}", tag="find")
                                    if len(self.anchor_details) > 10:
                                        self.ui.log(f"[锚点] ...还有 {len(self.anchor_details) - 10} 个锚点未显示...", tag="info")
                                
                                # 输出处理结果
                                if self.ui:
                                    # 确保UI更新
                                    self.ui.root.after(0, self.ui.update_status, "处理完成")
                                    self.ui.log("\n[信息] ===== 处理完成 =====", tag="header")
                                    self.ui.log("[信息] 所有文件处理完毕", tag="info")
                                    
                                    # 增强的统计分析
                                    if hasattr(self.processor, 'stats'):
                                        stats = self.processor.stats
                                        scanned_files = stats.get("scanned_files", 0)
                                        updated_files = stats.get("updated_files", 0)
                                        inserted_stubs = stats.get("inserted_stubs", 0)
                                        failed_files = stats.get("failed_files", 0)
                                        
                                        # 输出基础统计信息
                                        self.ui.log(f"[信息] 文件总数: {scanned_files}", tag="stats")
                                        self.ui.log(f"[信息] 处理成功文件: {updated_files}", tag="stats")
                                        self.ui.log(f"[信息] 成功插入桩点: {inserted_stubs}", tag="stats")
                                        
                                        if failed_files > 0:
                                            self.ui.log(f"[警告] 处理失败文件: {failed_files}", tag="warning")
                                        
                                        # 计算并显示成功率
                                        if scanned_files > 0:
                                            file_success_rate = round((updated_files / scanned_files) * 100, 2)
                                            self.ui.log(f"[信息] 文件处理成功率: {file_success_rate}%", tag="stats")
                                        
                                        # 添加用例覆盖分析
                                        if hasattr(self, 'test_case_info') and hasattr(self, 'anchor_details'):
                                            # 统计插桩锚点的测试用例和步骤
                                            anchored_tc_ids = set()
                                            anchored_steps = set()
                                            for detail in self.anchor_details:
                                                anchored_tc_ids.add(detail['tc_id'])
                                                anchored_steps.add(f"{detail['tc_id']}.{detail['step_id']}")
                                            
                                            # 统计YAML配置中的测试用例和步骤
                                            yaml_tc_ids = set(self.test_case_info.keys())
                                            yaml_steps = set()
                                            for tc_id, tc_info in self.test_case_info.items():
                                                for step_id in tc_info['steps'].keys():
                                                    yaml_steps.add(f"{tc_id}.{step_id}")
                                            
                                            # 计算覆盖率
                                            if yaml_tc_ids:
                                                tc_coverage = round((len(anchored_tc_ids) / len(yaml_tc_ids)) * 100, 2)
                                                self.ui.log(f"[用例] 测试用例覆盖率: {len(anchored_tc_ids)}/{len(yaml_tc_ids)} ({tc_coverage}%)", tag="stats")
                                                
                                                # 特别关注未覆盖的用例
                                                uncovered_tcs = yaml_tc_ids - anchored_tc_ids
                                                if uncovered_tcs:
                                                    self.ui.log(f"[用例] 未覆盖的测试用例: {len(uncovered_tcs)} 个", tag="info")
                                                    # 最多显示5个未覆盖的用例
                                                    for i, tc_id in enumerate(list(uncovered_tcs)[:5]):
                                                        desc = self.test_case_info[tc_id]['description']
                                                        desc_text = f" - {desc}" if desc else ""
                                                        self.ui.log(f"[用例]   未覆盖: {tc_id}{desc_text}", tag="warning")
                                                    if len(uncovered_tcs) > 5:
                                                        self.ui.log(f"[用例]   ...还有 {len(uncovered_tcs) - 5} 个未覆盖的用例未显示...", tag="info")
                                            
                                            if yaml_steps:
                                                step_coverage = round((len(anchored_steps) / len(yaml_steps)) * 100, 2)
                                                self.ui.log(f"[用例] 测试步骤覆盖率: {len(anchored_steps)}/{len(yaml_steps)} ({step_coverage}%)", tag="stats")
                                    
                                    # 显示备份和结果目录信息
                                    if hasattr(self.processor, 'backup_dir') and self.processor.backup_dir:
                                        self.ui.log(f"[信息] 原始项目备份目录: {self.processor.backup_dir}", tag="file")
                                        # 简化路径只显示目录名
                                        backup_dirname = os.path.basename(self.processor.backup_dir)
                                        self.ui.log(f"[信息] 原始项目备份在: {backup_dirname}", tag="file")
                                    
                                    if hasattr(self.processor, 'output_dir') and self.processor.output_dir:
                                        self.ui.log(f"[信息] 处理结果目录: {self.processor.output_dir}", tag="file")
                                        # 简化路径只显示目录名
                                        output_dirname = os.path.basename(self.processor.output_dir)
                                        self.ui.log(f"[信息] 处理结果保存在: {output_dirname}", tag="file")
                                    
                                    # 最终完成消息
                                    self.ui.log("[成功] 插桩操作已成功完成", tag="success")
                                return result
                            else:
                                error_msg = "处理器实例未创建，无法处理文件"
                                print(f"错误: {error_msg}")
                                if self.ui:
                                    self.ui.log(f"[错误] {error_msg}", tag="error")
                                return False, error_msg, {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0, "failed_files": 0}
                        else:
                            error_msg = "处理器实例未创建，无法处理文件"
                            print(f"错误: {error_msg}")
                            if self.ui:
                                self.ui.log(f"[错误] {error_msg}", tag="error")
                            return False, error_msg, {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0, "failed_files": 0}
                    except Exception as e:
                        logger.error(f"处理文件时出错: {str(e)}")
                        print(f"异常: {str(e)}")
                        import traceback
                        print(traceback.format_exc())
                        if self.ui:
                            self.ui.log(f"[错误] 处理文件时出错: {str(e)}", tag="error")
                            self.ui.update_status("处理失败")
                        return False, str(e), {"scanned_files": 0, "updated_files": 0, "inserted_stubs": 0, "failed_files": 0}
    
    # 创建控制器实例并返回
    return FallbackAppController(ui_instance)

def main():
    """
    主函数 - 启动UI界面
    
    实现了note.md中描述的工具操作流程:
    1. 启动YAMLWeave工具
    2. 选择项目路径及YAML配置路径
    3. 点击"扫描并插入"执行插桩
    
    支持两种工作模式：
    - 传统模式：直接从注释中提取code字段
    - 分离模式：从YAML配置文件中加载桩代码（锚点与桩代码分离）
    """
    try:
        logger.info("启动YAMLWeave应用")
        
        # 设置工作目录为应用根目录，防止路径问题
        os.chdir(APP_ROOT)
        logger.info(f"设置工作目录: {APP_ROOT}")
        
        # 打印环境信息，帮助诊断问题
        logger.info(f"操作系统: {sys.platform}")
        logger.info(f"Python版本: {sys.version}")
        logger.info(f"当前工作目录: {os.getcwd()}")
        logger.info(f"应用根目录: {APP_ROOT}")
        logger.info(f"sys.path: {sys.path}")
        
        # 确保必要的目录存在
        dirs = ensure_data_directory()
        
        # 创建示例文件
        examples = create_example_files(dirs)
        
        # 创建高级测试用例
        try:
            advanced_yaml_content = create_advanced_test_cases(dirs)
            logger.info("成功创建高级测试用例")
        except Exception as e:
            logger.error(f"创建高级测试用例失败: {str(e)}")
            # 提供一个默认的高级测试用例结果
            advanced_yaml_content = "# 高级测试用例创建失败"
        
        # 创建合并的YAML配置文件
        try:
            combined_yaml_file = create_combined_yaml(
                dirs, 
                examples.get("basic_yaml_content", ""), 
                advanced_yaml_content
            )
            logger.info(f"成功创建合并的YAML配置文件: {combined_yaml_file}")
        except Exception as e:
            logger.error(f"创建合并的YAML配置文件失败: {str(e)}")
            # 提供一个默认的合并YAML配置文件，防止后续代码崩溃
            combined_yaml_file = examples.get("simple_yaml_path", "")
        
        # 创建Tkinter根窗口
        root = tk.Tk()
        logger.info("成功创建Tkinter根窗口")
        
        # 创建UI界面
        YAMLWeaveUI_loaded = False
        AppController_loaded = False
        app_ui = None
        controller = None
        
        try:
            logger.info("开始创建UI实例...")
            
            # 尝试导入YAMLWeaveUI类 - 更加健壮的方法
            try:
                from code.ui.app_ui import YAMLWeaveUI
                from code.ui.app_controller import AppController
                logger.info("成功通过直接导入方式加载UI组件")
                YAMLWeaveUI_loaded = True
                AppController_loaded = True
            except ImportError as e:
                logger.warning(f"直接导入UI组件失败: {str(e)}")
            
            # 尝试方法2: 绝对路径导入
            if not YAMLWeaveUI_loaded:
                try:
                    from code.ui.app_ui import YAMLWeaveUI
                    from code.ui.app_controller import AppController
                    logger.info("成功通过绝对路径导入方式加载UI组件")
                    YAMLWeaveUI_loaded = True
                    AppController_loaded = True
                except ImportError as e:
                    logger.warning(f"绝对路径导入UI组件失败: {str(e)}")
            
            # 尝试方法3: 手动查找文件并导入
            if not YAMLWeaveUI_loaded:
                try:
                    # 查找app_ui.py文件
                    search_paths = [
                        APP_ROOT,
                        os.path.dirname(APP_ROOT),
                        os.path.join(APP_ROOT, "code"),
                        os.path.join(APP_ROOT, "ui"),
                        os.path.join(os.path.dirname(APP_ROOT), "code"),
                        os.path.join(os.path.dirname(APP_ROOT), "code", "ui"),
                    ]
                    
                    if hasattr(sys, '_MEIPASS'):
                        search_paths.append(sys._MEIPASS)
                        search_paths.append(os.path.join(sys._MEIPASS, "ui"))
                    
                    # 查找UI文件
                    YAMLWeaveUI = None
                    for path in search_paths:
                        logger.info(f"搜索UI文件: {path}")
                        if os.path.exists(path):
                            # 尝试多种文件名匹配
                            for filename in ["app_ui.py", "ui/app_ui.py", "ui\\app_ui.py", "code/ui/app_ui.py", "code\\ui\\app_ui.py"]:
                                filepath = os.path.join(path, filename)
                                if os.path.exists(filepath):
                                    YAMLWeaveUI = filepath
                                    logger.info(f"找到UI文件: {YAMLWeaveUI}")
                                    break
                            if YAMLWeaveUI:
                                break
                    
                    if YAMLWeaveUI:
                        # 保存原始文件路径
                        yaml_weave_ui_path = YAMLWeaveUI
                        
                        # 手动导入UI类
                        spec = importlib.util.spec_from_file_location("app_ui", YAMLWeaveUI)
                        if not spec:
                            logger.error(f"无法为模块创建spec: {YAMLWeaveUI}")
                            raise ImportError(f"无法为模块创建spec: {YAMLWeaveUI}")
                        
                        app_ui_module = importlib.util.module_from_spec(spec)
                        sys.modules["app_ui"] = app_ui_module
                        spec.loader.exec_module(app_ui_module)
                        
                        if hasattr(app_ui_module, "YAMLWeaveUI"):
                            YAMLWeaveUI = getattr(app_ui_module, "YAMLWeaveUI")
                            logger.info("成功从文件路径导入YAMLWeaveUI类")
                            YAMLWeaveUI_loaded = True
                        else:
                            raise AttributeError(f"在模块中找不到YAMLWeaveUI类: {yaml_weave_ui_path}")
                        
                        # 尝试加载控制器
                        controller_path = yaml_weave_ui_path.replace("app_ui.py", "app_controller.py")
                        if os.path.exists(controller_path):
                            try:
                                spec = importlib.util.spec_from_file_location("app_controller", controller_path)
                                if not spec:
                                    logger.error(f"无法为模块创建spec: {controller_path}")
                                    raise ImportError(f"无法为模块创建spec: {controller_path}")
                                
                                app_controller_module = importlib.util.module_from_spec(spec)
                                sys.modules["app_controller"] = app_controller_module
                                spec.loader.exec_module(app_controller_module)
                                
                                if hasattr(app_controller_module, "AppController"):
                                    AppController = getattr(app_controller_module, "AppController")
                                    logger.info("成功从文件路径导入AppController类")
                                    AppController_loaded = True
                                else:
                                    logger.warning(f"在模块中找不到AppController类: {controller_path}")
                            except Exception as e:
                                logger.warning(f"加载控制器失败: {str(e)}")
                        else:
                            logger.warning(f"未找到控制器文件: {controller_path}")
                    else:
                        logger.error("无法找到app_ui.py文件")
                except Exception as e:
                    logger.error(f"手动加载UI组件失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # 检查是否成功加载UI类
            if not YAMLWeaveUI_loaded:
                raise ImportError("无法加载YAMLWeaveUI类，无法启动应用")
            
            # 创建UI实例
            app_ui = YAMLWeaveUI(root)
            logger.info("成功创建UI实例")
            
            # 创建控制器并连接UI
            if AppController_loaded:
                try:
                    controller = AppController(app_ui)
                    logger.info("成功创建控制器实例")
                except Exception as e:
                    logger.error(f"创建控制器实例失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 如果控制器创建失败，标记为未加载
                    AppController_loaded = False
            
            if not AppController_loaded:
                try:
                    # 使用后备控制器
                    logger.info("尝试使用后备控制器...")
                    controller = create_fallback_controller(app_ui)
                    logger.info("成功创建后备控制器实例")
                    app_ui.log("[信息] 使用后备控制器运行 - 完全支持所有功能")
                except Exception as e:
                    logger.error(f"创建后备控制器失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 如果后备控制器创建失败，标记为未加载
                    AppController_loaded = False
            
            # 自动填充示例文件路径
            example_project_path = examples.get("example_project_path", "")
            simple_examples_dir = examples.get("simple_examples_dir", "")
            simple_yaml_path = examples.get("simple_yaml_path", "")
            
            if app_ui is not None and os.path.exists(example_project_path):
                # 使用合并的YAML配置
                try:
                    app_ui.project_dir.set(example_project_path)
                    app_ui.yaml_file.set(combined_yaml_file)  # 使用合并的YAML配置
                    app_ui.log("[信息] 已自动填入测试用例路径")
                    app_ui.log(f"[信息] 测试用例目录: {example_project_path}")
                    app_ui.log(f"[信息] 测试用例目录: {simple_examples_dir}")
                    app_ui.log("[信息] 已使用综合测试配置文件，包含所有测试用例")
                    app_ui.log("[信息] 您可以直接点击\"扫描并插入\"按钮体验工具功能")
                    app_ui.log("[信息] 或者选择自己的项目目录和YAML配置文件")
                    
                    # 添加备份功能介绍
                    app_ui.log("[信息] ========================================", tag="header")
                    app_ui.log("[信息] 项目备份功能已启用:", tag="header")
                    app_ui.log("[信息] 1. 在处理项目前自动创建整个项目的备份", tag="info")
                    app_ui.log("[信息] 2. 插桩后的文件保存在新目录中", tag="info")
                    app_ui.log("[信息] 3. 原始项目保持不变", tag="info")
                    app_ui.log("[信息] 4. 备份目录名: 项目目录名_backup_时间戳", tag="info")
                    app_ui.log("[信息] 5. 插桩结果目录名: 项目目录名_stubbed_时间戳", tag="info")
                    app_ui.log("[信息] ========================================", tag="header")
                    
                    # 显示执行日志历史统计
                    try:
                        from code.utils.logger import get_execution_log_stats
                        
                        # 获取历史日志统计信息
                        log_stats = get_execution_log_stats()
                        total_logs = log_stats.get("total_logs", 0)
                        
                        if total_logs > 0:
                            app_ui.log("[信息] ========================================", tag="header")
                            app_ui.log("[信息] 执行日志历史统计:", tag="header")
                            app_ui.log(f"[信息] 总执行次数: {total_logs} 次", tag="stats")
                            
                            total_processed_files = log_stats.get("total_processed_files", 0)
                            total_inserted_stubs = log_stats.get("total_inserted_stubs", 0)
                            
                            if total_processed_files > 0:
                                app_ui.log(f"[信息] 总处理文件数: {total_processed_files} 个", tag="stats")
                            
                            if total_inserted_stubs > 0:
                                app_ui.log(f"[信息] 总插入桩点数: {total_inserted_stubs} 个", tag="stats")
                            
                            latest_log = log_stats.get("latest_log")
                            if latest_log:
                                app_ui.log(f"[信息] 最近执行时间: {latest_log.get('modified_time_str', '未知')}", tag="info")
                            
                            # 显示日志目录位置
                            # 常规执行日志目录
                            exec_logs_dir = os.path.join(APP_ROOT, "execution_logs")
                            app_ui.log(f"[信息] 执行日志保存在: {exec_logs_dir}", tag="file")
                            
                            # 带时间戳的日志目录检测
                            timestamp_logs = glob.glob(os.path.join(APP_ROOT, "logs_*"))
                            if timestamp_logs:
                                app_ui.log("[信息] 时间戳日志目录:", tag="info")
                                # 只显示最新的3个时间戳日志目录
                                timestamp_logs.sort(key=os.path.getmtime, reverse=True)
                                for i, log_dir in enumerate(timestamp_logs[:3]):
                                    app_ui.log(f"[信息] - {os.path.basename(log_dir)}", tag="file")
                                    # 检查是否有主日志文件
                                    main_log = os.path.join(log_dir, "yamlweave.log")
                                    if os.path.exists(main_log):
                                        app_ui.log(f"[信息]   * 主日志文件: yamlweave.log", tag="info")
                                
                                # 如果有更多，显示总数
                                if len(timestamp_logs) > 3:
                                    app_ui.log(f"[信息] - ...等 {len(timestamp_logs)} 个目录", tag="info")
                            
                            app_ui.log("[信息] ========================================", tag="header")
                    except Exception as log_stats_error:
                        logger.error(f"获取执行日志统计信息失败: {str(log_stats_error)}")
                    
                    # 弹出提示对话框
                    root.after(1000, lambda: messagebox.showinfo(
                        "YAMLWeave测试用例",
                        "已自动加载测试用例路径：\n\n"
                        f"测试用例目录：{example_project_path}\n\n"
                        f"综合测试配置：{combined_yaml_file}\n\n"
                        "已创建测试配置文件，包含所有测试用例。\n\n"
                        "点击\"扫描并插入\"按钮开始处理:\n"
                        "1. 首先会创建整个项目目录的备份\n"
                        "2. 然后在新目录中创建插桩后的文件\n"
                        "3. 原始项目目录保持不变\n"
                        "4. 执行日志将保存在固定目录中"
                    ))
                except Exception as e:
                    logger.error(f"自动填充示例文件路径失败: {str(e)}")
            else:
                logger.warning("无法找到示例项目目录，无法自动填充示例文件路径")
            
            # 启动主循环
            logger.info("进入主循环")
            root.mainloop()
            
            logger.info("应用正常退出")
        except NameError as e:
            logger.error(f"名称错误 - 无法找到类定义: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            show_message(f"UI初始化出错: 无法找到所需的类定义\n{str(e)}")
        except Exception as e:
            logger.error(f"UI初始化或运行出错: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            show_message(f"UI初始化或运行出错:\n{str(e)}")
        
    except Exception as e:
        logger.error(f"应用运行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        show_message(f"应用运行出错:\n{str(e)}")
    finally:
        logger.info("应用结束")


if __name__ == "__main__":
    main() 