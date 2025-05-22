#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAMLWeave 简化打包脚本
将项目打包为带时间戳的.exe文件，并输出到code同级目录
"""
import os
import sys
import subprocess
import datetime
import shutil
import logging
import platform
from pathlib import Path

# 基础配置
VERSION = "1.0.0"
APP_NAME = "YAMLWeave"
MAIN_SCRIPT = "main.py"

# 获取项目路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)  # code的上一级目录

# 日志配置
LOG_FILE = os.path.join(SCRIPT_DIR, f"packing_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_requirements():
    """检查并安装必要的依赖"""
    logger.info("检查必要的依赖...")
    try:
        import PyInstaller
        logger.info("PyInstaller已安装")
    except ImportError:
        logger.info("安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    try:
        import yaml
        logger.info("PyYAML已安装")
    except ImportError:
        logger.info("安装PyYAML...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])

def clean_old_files():
    """清理旧的打包文件和目录"""
    logger.info("清理旧文件...")
    # 清理build目录
    build_dir = os.path.join(SCRIPT_DIR, "build")
    if os.path.exists(build_dir):
        logger.info(f"删除build目录: {build_dir}")
        shutil.rmtree(build_dir, ignore_errors=True)
    
    # 清理dist目录
    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    if os.path.exists(dist_dir):
        logger.info(f"删除dist目录: {dist_dir}")
        shutil.rmtree(dist_dir, ignore_errors=True)
    
    # 清理.spec文件
    for file in os.listdir(SCRIPT_DIR):
        if file.endswith(".spec"):
            logger.info(f"删除spec文件: {file}")
            os.remove(os.path.join(SCRIPT_DIR, file))

    # 递归删除 __pycache__ 目录，避免旧的字节码被打包
    for root, dirs, _ in os.walk(PROJECT_DIR):
        for d in dirs:
            if d == "__pycache__":
                pycache_path = os.path.join(root, d)
                logger.info(f"删除__pycache__目录: {pycache_path}")
                shutil.rmtree(pycache_path, ignore_errors=True)

def generate_version():
    """生成带时间戳的版本号"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    version_with_timestamp = f"{VERSION}_{timestamp}"
    logger.info(f"生成版本号: {version_with_timestamp}")
    return version_with_timestamp

def create_spec_file(version):
    """创建简化的PyInstaller规范文件"""
    logger.info("创建spec文件...")
    
    output_name = f"{APP_NAME}_{version}"
    spec_file_path = os.path.join(SCRIPT_DIR, f"{APP_NAME}_{version}.spec")
    
    # 使用简单的相对路径，避免转义问题
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
CODE_DIR = os.path.join(PROJECT_ROOT, 'code')
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, CODE_DIR)

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[PROJECT_ROOT, CODE_DIR],
    binaries=[],
    datas=[
        (os.path.join(CODE_DIR, 'ui'), 'code/ui'),
        (os.path.join(CODE_DIR, 'core'), 'code/core'),
        (os.path.join(CODE_DIR, 'utils'), 'code/utils'),
        (os.path.join(CODE_DIR, 'handlers'), 'code/handlers'),
        (os.path.join(PROJECT_ROOT, '__init__.py'), '__init__.py'),
        (os.path.join(CODE_DIR, '__init__.py'), 'code/__init__.py'),
    ],
    hiddenimports=[
        'code', 'code.ui', 'code.ui.app_ui', 'code.ui.app_controller',
        'code.core', 'code.core.stub_processor', 'code.core.stub_parser', 'code.core.utils',
        'code.utils', 'code.utils.logger', 'code.utils.exceptions',
        'code.handlers', 'code.handlers.comment_handler', 'code.handlers.yaml_handler',
        'yaml', 'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'pathlib', 'datetime'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{output_name}',
)
"""
    
    # 保存spec文件
    with open(spec_file_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    logger.info(f"Spec文件已创建: {spec_file_path}")
    return spec_file_path

def run_pyinstaller(spec_file):
    """运行PyInstaller打包程序"""
    logger.info("开始PyInstaller打包...")
    
    try:
        # 直接执行PyInstaller打包
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "PyInstaller", 
            spec_file,
            "--clean",
            "--noconfirm"
        ], cwd=SCRIPT_DIR)
        logger.info("PyInstaller打包成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"PyInstaller打包失败: {e}")
        return False

def verify_package(version):
    """验证打包结果是否完整"""
    logger.info("验证打包结果...")
    
    dist_dir = os.path.join(SCRIPT_DIR, "dist", f"{APP_NAME}_{version}")
    exe_file = os.path.join(dist_dir, f"{APP_NAME}.exe")
    
    # 检查.exe文件是否存在
    if not os.path.exists(exe_file):
        logger.error(f"缺少可执行文件: {exe_file}")
        return False
    
    logger.info("打包结果验证通过")
    return True

def move_to_parent_dir(version):
    """将打包结果移动到code同级目录"""
    logger.info("移动打包结果到code同级目录...")
    
    source_dir = os.path.join(SCRIPT_DIR, "dist", f"{APP_NAME}_{version}")
    target_dir = os.path.join(PROJECT_DIR, f"{APP_NAME}_{version}")
    
    try:
        # 如果目标目录已存在，先删除
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        # 移动目录
        shutil.move(source_dir, target_dir)
        logger.info(f"打包结果已移动到: {target_dir}")
        return True
    except Exception as e:
        logger.error(f"移动打包结果失败: {e}")
        return False

def cleanup():
    """清理临时文件和构建目录"""
    logger.info("清理临时文件...")
    
    try:
        # 清理build目录
        build_dir = os.path.join(SCRIPT_DIR, "build")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        
        # 清理dist目录
        dist_dir = os.path.join(SCRIPT_DIR, "dist")
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir)
        
        # 清理.spec文件
        for file in os.listdir(SCRIPT_DIR):
            if file.endswith(".spec"):
                os.remove(os.path.join(SCRIPT_DIR, file))
        
        logger.info("临时文件清理完成")
        return True
    except Exception as e:
        logger.error(f"清理临时文件失败: {e}")
        return False

def validate_key_files():
    """验证关键Python文件的语法正确性"""
    logger.info("验证关键文件语法...")
    key_files = [
        os.path.join(SCRIPT_DIR, "main.py"),
        os.path.join(SCRIPT_DIR, "stub_processor.py"),
    ]
    
    # 检查core目录中的文件
    core_dir = os.path.join(SCRIPT_DIR, "core")
    if os.path.exists(core_dir):
        for file in os.listdir(core_dir):
            if file.endswith(".py"):
                key_files.append(os.path.join(core_dir, file))
    
    # 检查handlers目录中的文件
    handlers_dir = os.path.join(SCRIPT_DIR, "handlers")
    if os.path.exists(handlers_dir):
        for file in os.listdir(handlers_dir):
            if file.endswith(".py"):
                key_files.append(os.path.join(handlers_dir, file))
    
    validation_passed = True
    for file in key_files:
        if os.path.exists(file):
            try:
                logger.info(f"验证文件: {file}")
                subprocess.check_call([sys.executable, "-m", "py_compile", file], stderr=subprocess.PIPE)
                logger.info(f"文件语法验证通过: {file}")
            except subprocess.CalledProcessError as e:
                logger.error(f"文件存在语法错误: {file}")
                logger.error(f"错误详情: {e}")
                validation_passed = False
        else:
            logger.warning(f"文件不存在，跳过: {file}")
    
    return validation_passed

def main():
    """主函数"""
    logger.info(f"开始打包 {APP_NAME}...")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"平台: {platform.platform()}")
    logger.info(f"项目目录: {PROJECT_DIR}")
    
    try:
        # 检查依赖
        check_requirements()
        
        # 清理旧文件
        clean_old_files()
        
        # 验证文件语法
        if not validate_key_files():
            logger.error("关键文件存在语法错误，中止打包")
            return
        
        # 生成版本号
        version = generate_version()
        
        # 创建spec文件
        spec_file = create_spec_file(version)
        
        # 运行PyInstaller
        if not run_pyinstaller(spec_file):
            logger.error("打包失败")
            return
        
        # 验证打包结果
        if not verify_package(version):
            logger.error("打包结果验证失败")
            return
        
        # 移动到父目录
        if not move_to_parent_dir(version):
            logger.error("移动打包结果失败")
            return
        
        # 清理临时文件
        cleanup()
        
        logger.info(f"{APP_NAME} {version} 打包完成!")
        logger.info(f"打包结果位于: {os.path.join(PROJECT_DIR, f'{APP_NAME}_{version}')}")
        
    except Exception as e:
        logger.error(f"打包过程中发生错误: {e}", exc_info=True)
        return

if __name__ == "__main__":
    main()
