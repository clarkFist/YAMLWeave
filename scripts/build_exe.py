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
import glob
from pathlib import Path

# 基础配置
VERSION = "1.0.0"
APP_NAME = "YAMLWeave"
MAIN_SCRIPT = "main.py"

# 获取项目路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)  # 仓库根目录
CODE_DIR = os.path.join(PROJECT_DIR, "code")  # 原code目录位置
MAIN_SCRIPT_PATH = os.path.join(CODE_DIR, MAIN_SCRIPT)
RUNTIME_HOOK = os.path.join(SCRIPT_DIR, "tkinter_env_hook.py")

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


def get_tcl_tk_paths():
    """尝试获取 Tcl/Tk 资源目录路径"""
    try:
        import tkinter
        tcl_lib = Path(tkinter.Tcl().eval('info library'))
        tk_ver = '.'.join(tkinter.Tcl().eval('info patchlevel').split('.')[:2])
        tk_lib = tcl_lib.parent / f"tk{tk_ver}"
        
        # 对于 Anaconda 环境，还需要获取 DLL 目录
        python_exe = Path(sys.executable)
        
        # 检查是否是 Anaconda 环境
        if 'anaconda' in str(python_exe).lower() or 'miniconda' in str(python_exe).lower():
            # Anaconda 环境中的 DLL 路径
            dll_dir = python_exe.parent / 'Library' / 'bin'
            logger.info(f"检测到 Anaconda 环境，DLL 目录: {dll_dir}")
        else:
            # 标准 Python 安装的 DLL 路径
            dll_dir = python_exe.parent / 'DLLs'
            
        return str(tcl_lib), str(tk_lib), str(dll_dir)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("无法获取 Tcl/Tk 路径: %s", exc)
        return None, None, None

def get_tkinter_binaries():
    """获取 tkinter 相关的二进制文件"""
    binaries = []
    try:
        _, _, dll_dir = get_tcl_tk_paths()
        if dll_dir and os.path.exists(dll_dir):
            # 查找所有 Tcl/Tk 相关的 DLL 文件
            dll_patterns = ['tcl*.dll', 'tk*.dll', '_tkinter*.pyd', 'tkinter*.dll']
            for pattern in dll_patterns:
                for dll_file in glob.glob(os.path.join(dll_dir, pattern)):
                    if os.path.isfile(dll_file):
                        binaries.append((dll_file, '.'))
                        logger.info(f"添加 DLL 文件: {dll_file}")
            
            # 检查 Python DLLs 目录
            python_exe = Path(sys.executable)
            python_dll_dir = python_exe.parent / 'DLLs'
            if python_dll_dir.exists():
                for dll_file in python_dll_dir.glob('_tkinter*.pyd'):
                    binaries.append((str(dll_file), '.'))
                    logger.info(f"添加 Python DLL: {dll_file}")
                    
        return binaries
    except Exception as exc:
        logger.warning("获取 tkinter 二进制文件失败: %s", exc)
        return []

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

    # 检查 tkinter 是否可用
    try:
        import tkinter  # noqa: F401
        logger.info("Tkinter 已安装")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Tkinter 无法导入: %s", e)
        logger.error(
            "请确认 Python 已包含 Tcl/Tk 组件。\n"
            "在 Windows 上可重新安装官方发行版，勾选 Tcl/Tk；"
            "在 Linux 上可安装 python3-tk 软件包。"
        )

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
    
    # 获取 Tcl/Tk 路径
    tcl_path, tk_path, dll_dir = get_tcl_tk_paths()
    tcl_data = f"        (r'{tcl_path}', 'tcl'),\n" if tcl_path else ""
    tk_data = f"        (r'{tk_path}', 'tk'),\n" if tk_path else ""
    
    # 获取 tkinter 相关的二进制文件
    tkinter_binaries = get_tkinter_binaries()
    binaries_str = ""
    if tkinter_binaries:
        for binary_file, dest in tkinter_binaries:
            binaries_str += f"        (r'{binary_file}', '{dest}'),\n"

    # 使用简单的相对路径，避免转义问题
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import sys
import os

PROJECT_ROOT = r"{PROJECT_DIR}"
CODE_DIR = os.path.join(PROJECT_ROOT, 'code')
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, CODE_DIR)

block_cipher = None

a = Analysis(
    [r"{MAIN_SCRIPT_PATH}"],
    pathex=[PROJECT_ROOT, CODE_DIR],
    binaries=[
{binaries_str}    ],
    datas=[
        (os.path.join(CODE_DIR, 'ui'), 'code/ui'),
        (os.path.join(CODE_DIR, 'core'), 'code/core'),
        (os.path.join(CODE_DIR, 'utils'), 'code/utils'),
        (os.path.join(CODE_DIR, 'handlers'), 'code/handlers'),
        (os.path.join(PROJECT_ROOT, '__init__.py'), '__init__.py'),
        (os.path.join(CODE_DIR, '__init__.py'), 'code/__init__.py'),
{tcl_data}{tk_data}    ],
    hiddenimports=[
    # ── 应用自身 ───────────────────────────────────────────────
    'code', 'code.ui', 'code.ui.app_ui', 'code.ui.app_controller',
    'code.core', 'code.core.stub_processor', 'code.core.stub_parser', 'code.core.utils',
    'code.utils', 'code.utils.logger', 'code.utils.exceptions',
    'code.handlers', 'code.handlers.comment_handler', 'code.handlers.yaml_handler',

    # ── 第三方 / 标准库 ───────────────────────────────────────
    'yaml',
    'tkinter', 'tkinter.filedialog', 'tkinter.messagebox',
    'tkinter.ttk', 'tkinter.scrolledtext', 'tkinter.font',
    'pathlib', 'datetime',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[r'{RUNTIME_HOOK}'],
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
    console=False,
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
        env = os.environ.copy()
        tcl_path, tk_path, dll_dir = get_tcl_tk_paths()
        if tcl_path:
            env['TCL_LIBRARY'] = tcl_path
        if tk_path:
            env['TK_LIBRARY'] = tk_path

        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            spec_file,
            "--clean",
            "--noconfirm"
        ], cwd=SCRIPT_DIR, env=env)
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

def open_output_dir(version):
    """在打包完成后打开输出目录"""
    output_dir = os.path.join(PROJECT_DIR, f"{APP_NAME}_{version}")
    logger.info(f"尝试打开目录: {output_dir}")
    try:
        if platform.system() == "Windows":
            os.startfile(output_dir)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", output_dir])
        else:
            subprocess.Popen(["xdg-open", output_dir])
        return True
    except Exception as e:
        logger.error(f"自动打开目录失败: {e}")
        return False

def validate_key_files():
    """验证关键Python文件的语法正确性"""
    logger.info("验证关键文件语法...")
    key_files = [
        os.path.join(CODE_DIR, "main.py"),
        os.path.join(CODE_DIR, "stub_processor.py"),
    ]

    # 检查core目录中的文件
    core_dir = os.path.join(CODE_DIR, "core")
    if os.path.exists(core_dir):
        for file in os.listdir(core_dir):
            if file.endswith(".py"):
                key_files.append(os.path.join(core_dir, file))
    
    # 检查handlers目录中的文件
    handlers_dir = os.path.join(CODE_DIR, "handlers")
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
        output_dir = os.path.join(PROJECT_DIR, f"{APP_NAME}_{version}")
        logger.info(f"打包结果位于: {output_dir}")

        # 打开输出目录以便用户查看生成的程序
        open_output_dir(version)
        
    except Exception as e:
        logger.error(f"打包过程中发生错误: {e}", exc_info=True)
        return

if __name__ == "__main__":
    main()
