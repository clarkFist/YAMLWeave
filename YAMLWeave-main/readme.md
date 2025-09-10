# YAMLWeave - C代码自动插桩工具

## 📋 目录

- [简介](#简介)
- [功能特点](#功能特点)
- [安装与使用](#安装与使用)
- [工作模式](#工作模式)
- [多文件应用场景](#多文件应用场景)
- [常见问题](#常见问题)
- [程序结构说明](#程序结构说明)
- [版本信息](#版本信息)

---

## 📖 简介
YAMLWeave是一款专用于C代码自动插桩的工具，提供两种工作模式，帮助开发人员快速实现代码测试和调试。

## ✨ 功能特点

- 🚀 **双模式支持**：传统模式和分离模式，满足不同场景需求
- 📝 **YAML配置**：支持通过YAML文件集中管理桩代码
- 🔄 **多文件支持**：支持跨文件的测试用例组织
- 🎯 **精确插桩**：基于锚点标识的精确代码插入
- 📊 **实时反馈**：提供详细的处理日志和结果报告
- ⚠️ **缺失提示**：在日志结尾汇总缺失的桩代码锚点，并以弹窗或状态栏提示数量
- 🛠 **零依赖**：无需安装Python或其他依赖项

---

## 🚀 安装与使用

### 系统要求
- Windows 10/11 操作系统
- 至少100MB可用磁盘空间
- 管理员权限（首次运行时）

### 安装步骤

1. 下载最新版本的YAMLWeave压缩包
2. 解压到任意目录
3. 双击`YAMLWeave_v*.exe`启动程序

### 快速上手

1. **启动工具**：双击`YAMLWeave_v*.exe`程序启动
2. **选择项目**：点击"浏览"按钮，选择要进行插桩的项目目录
3. **选择配置**：
   - 分离模式：选择YAML配置文件（必选）
   - 传统模式：可不选择YAML配置文件
4. **执行插桩**：点击"扫描并插入"按钮开始自动插桩操作
5. **查看结果**：在日志窗口实时查看处理进度和结果

---

## 💻 工作模式

### 传统模式

在C代码注释中直接嵌入桩代码，适合快速测试和少量插桩场景。

**操作步骤：**
1. 在源代码中添加特定格式的注释
2. 运行YAMLWeave工具，选择项目目录
3. 点击"扫描并插入"按钮执行插桩

**代码示例：**

```c
void validate_data(int data) {
    // TC001 STEP1: 数据边界检查
    // code: if (data < 0 || data > 100) { printf("无效数据: %d\n", data); return ERROR_VALUE; }
    
    process_data(data);
}
```

**插入后：**

```c
void validate_data(int data) {
    // TC001 STEP1: 数据边界检查
    // code: if (data < 0 || data > 100) { printf("无效数据: %d\n", data); return ERROR_VALUE; }
    if (data < 0 || data > 100) { printf("无效数据: %d\n", data); return ERROR_VALUE; }  // 通过桩插入
    
    process_data(data);
}
```

### 分离模式

桩代码与源代码完全解耦，源代码中仅保留锚点标识，所有桩代码统一在YAML配置文件中管理。

**操作步骤：**
1. 在源代码中添加锚点标识
2. 创建YAML配置文件，定义对应的桩代码
3. 运行YAMLWeave工具，选择项目目录和YAML配置文件
4. 点击"扫描并插入"按钮执行插桩

**C代码锚点：**

```c
void validate_data(int data) {
    // TC001 STEP1 segment1
    
    process_data(data);
}
```

**YAML配置：**

```yaml
TC001:
  STEP1:
    segment1: |
      if (data < 0 || data > 100) {
          printf("无效数据: %d\n", data);
          return ERROR_VALUE;
      }
```

**插入后：**

```c
void validate_data(int data) {
    // TC001 STEP1 segment1
    if (data < 0 || data > 100) {  // 通过桩插入
        printf("无效数据: %d\n", data);  // 通过桩插入
        return ERROR_VALUE;  // 通过桩插入
    }  // 通过桩插入
    
    process_data(data);
}
```

---

## 🔄 多文件应用场景

YAMLWeave支持在**多个文件**中组织测试用例，实现更复杂的测试流程：

- 同一测试用例ID可以**跨文件**重用
- 不同步骤ID可以分布在**不同文件**中
- 特别适合测试**完整功能流程**

### 多文件示例

以下示例展示如何在多个文件中实现一个完整的测试用例流程：

#### 文件1: module1/input_validation.c

```c
int validate_input(char* input, int length) {
    // TC001 STEP1 validate_input
    
    printf("模块1: 验证输入数据 (长度=%d)\n", length);
    return 1; // 默认返回有效
}
```

#### 文件2: module2/data_processing.c

```c
void process_data(char* data) {
    // TC001 STEP2 process_data
    
    printf("模块2: 处理数据\n");
}
```

#### 文件3: module3/status_check.c

```c
int check_system_status() {
    // TC001 STEP3 check_status
    
    printf("模块3: 检查系统状态\n");
    return 1; // 默认返回正常
}
```

#### YAML配置文件: test_cases.yaml

```yaml
# 完整测试用例流程 - 跨多个文件
TC001:
  # 步骤1: 输入验证 (在module1/input_validation.c)
  STEP1:
    validate_input: |
      if (input == NULL || length <= 0) {
          printf("模块1: 检测到无效输入参数\n");
          return 0;
      }
      
      printf("模块1: 输入验证通过\n");
  
  # 步骤2: 数据处理 (在module2/data_processing.c)
  STEP2:
    process_data: |
      if (data == NULL) {
          printf("模块2: 数据为空，无法处理\n");
          return;
      }
      
      printf("模块2: 开始数据转换\n");
      // 处理数据的代码...
  
  # 步骤3: 状态检查 (在module3/status_check.c)
  STEP3:
    check_status: |
      int status_code = get_system_status();
      if (status_code != STATUS_OK) {
          printf("模块3: 系统状态异常 (状态码: %d)\n", status_code);
          return 0;
      }
      
      printf("模块3: 系统状态正常\n");
```

---

## ❓ 常见问题

### Q1: 如何处理插桩后的代码回滚？
A: 工具会自动备份原始文件，可以通过日志窗口的"恢复"按钮进行回滚。

### Q2: 支持哪些C代码版本？
A: 支持C89/C90、C99和C11标准的代码。

### Q3: 如何处理大型项目的插桩？
A: 建议使用分离模式，通过YAML配置文件统一管理桩代码。

### Q4: 是否支持批量处理？
A: 是的，工具支持批量处理多个文件和目录。

### Q5: 如果源文件中没有锚点会怎样？
A: 从 v1.1 起，工具不会再在文件开头插入所有桩代码，而是仅在日志中提示该文件未找到锚点。

### Q6: 打包时报 "_tkinter" 无法加载怎么办？
A: 该错误通常是 Python 缺少 Tcl/Tk 组件导致。请确认所用的 Python 环境已安装并配置
   Tkinter：
   - Windows 用户可重新运行官方安装包并勾选 *Tcl/Tk and IDLE*；
   - Linux 用户可安装 `python3-tk` (或同名) 软件包。

---

## 📁 程序结构说明

打包后的应用程序包含以下内容：

```
YAMLWeave_v1.0.0_20250514/
├── YAMLWeave_v1.0.0_20250514.exe  # 主程序可执行文件
├── readme.md                      # 使用说明文档
├── logs/                          # 日志目录
└── _internal/                     # 程序依赖目录
```

> **注意**：不要删除或修改`_internal`目录中的文件，这会导致程序无法正常运行。

### _internal目录说明

`_internal`目录包含应用程序运行所需的所有依赖项：

- Python解释器和运行时库
- 应用程序核心代码模块(core, ui, utils等)
- 所有第三方依赖库

---

## ℹ️ 版本信息

详细版本信息可在应用程序的版本信息文件(`version.txt`)中查看。

---

## 📝 更新日志

### v1.0.0 (2025-05-14)
- 初始版本发布
- 支持传统模式和分离模式
- 实现多文件插桩功能
- 添加YAML配置文件支持


