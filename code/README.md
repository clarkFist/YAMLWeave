# YAMLWeave 打包说明

## 打包步骤

1. 确保已安装Python 3.7+环境
2. 运行打包脚本：`python ../scripts/build_exe.py`
3. 脚本将自动执行以下操作：
   - 检查代码中的语法错误并修复
   - 生成带时间戳的版本号
   - 创建PyInstaller配置文件
   - 执行PyInstaller打包
   - 复制示例文件到打包目录
   - 打开打包结果目录

## 注意事项

1. 打包前会自动检测并修复以下问题：
   - 缺少冒号的if语句
   - 模块导入路径问题
   - PyInstaller特殊处理需求

2. 打包过程会自动安装必要的依赖：
   - PyInstaller (打包工具)
   - PyYAML (YAML配置支持)

3. 打包结果位于 `dist/YAMLWeave_[版本号]` 目录下

4. 如果原代码有被修复，建议在打包前先验证修复后的代码能否正常运行

## 路径处理说明

YAMLWeave 工具采用了以下策略来处理打包后的路径问题：

1. 使用 `sys._MEIPASS` 获取PyInstaller打包后的应用根目录
2. 动态添加模块搜索路径，确保所有模块能被正确导入
3. 使用相对路径处理示例文件和配置
4. 提供多级回退机制，确保在不同环境下都能正常工作

## 目录结构

打包后的目录结构如下：

```
YAMLWeave_v1.0.0_YYYYMMDD_HHMMSS/
├── YAMLWeave.exe       # 主程序
├── ui/                 # UI模块
├── core/               # 核心模块
├── utils/              # 工具模块
├── handlers/           # 处理器模块
└── samples/            # 示例文件
    ├── examples/       # 示例代码
    └── example.yaml    # 示例配置
``` 