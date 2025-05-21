# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_tk_files

# 获取项目根目录的绝对路径
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# 获取code目录的绝对路径
CODE_DIR = os.path.join(PROJECT_ROOT, 'code')

# 确保code目录在Python路径中
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, CODE_DIR)

# 收集 Tkinter/TTK 所需的资源文件，确保打包后的界面样式完整
tk_datas = collect_tk_files()

a = Analysis(
    [os.path.join(CODE_DIR, 'main.py')],
    pathex=[PROJECT_ROOT, CODE_DIR],
    binaries=[],
    datas=tk_datas + [
        (os.path.join(CODE_DIR, 'ui'), 'code/ui'),  # 使用相对结构
        (os.path.join(CODE_DIR, 'core'), 'code/core'),
        (os.path.join(CODE_DIR, 'utils'), 'code/utils'),
        (os.path.join(CODE_DIR, 'handlers'), 'code/handlers'),
        (os.path.join(PROJECT_ROOT, 'samples'), 'samples'),
        (os.path.join(PROJECT_ROOT, '__init__.py'), '__init__.py'),  # 包含项目根目录的__init__.py
        (os.path.join(CODE_DIR, '__init__.py'), 'code/__init__.py'),  # 包含code目录的__init__.py
    ],
    hiddenimports=[
        'code', 'code.ui', 'code.ui.app_ui', 'code.ui.app_controller', 
        'code.core', 'code.core.stub_processor', 'code.core.stub_parser', 'code.core.utils',
        'code.utils', 'code.utils.logger', 'code.utils.exceptions',
        'code.handlers', 'code.handlers.comment_handler', 'code.handlers.yaml_handler',
        'yaml', 'tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'pathlib', 'datetime'
    ],
    hookspath=[],
    hooksconfig={},
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
    name='YAMLWeave',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 设为True以便在出错时显示控制台输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(PROJECT_ROOT, 'yamlweave_icon.ico')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='YAMLWeave',
)
