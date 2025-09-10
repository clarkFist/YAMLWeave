# YAMLWeave v1.1.0 功能增强说明文档

## 📋 概述

YAMLWeave v1.1.0版本在原有功能基础上进行了重要优化和增强，主要包括：
- 🔍 **增强的锚点缺失检测与提示**
- 📊 **改进的进度条显示模块**
- 🔄 **反向输出YAML功能**


---

## 🔍 功能一：增强的锚点缺失检测与提示

### 1.1 功能描述

改进了对YAML配置文件中缺失锚点的检测和提示机制，帮助用户快速定位和修复配置问题。

### 1.2 核心改进

#### 1.2.1 精确的缺失锚点统计
- **文件级别记录**：准确记录每个缺失锚点的文件路径和行号
- **锚点标识跟踪**：完整记录锚点的测试用例ID、步骤ID和代码段ID
- **数量统计**：实时统计缺失锚点的总数量

#### 1.2.2 增强的日志提示
- **分类显示**：将缺失信息按类型分类显示
- **详细定位**：提供精确的文件相对路径和行号信息
- **色彩区分**：使用不同颜色标签区分不同类型的提示信息

### 1.3 技术实现

#### 1.3.1 核心数据结构
```python
# 在 stub_parser.py 中
self.missing_anchors: List[Dict[str, Any]] = []

# 缺失锚点记录格式
missing_anchor = {
    'file': file_path,      # 文件绝对路径
    'line': line_number,    # 行号（从1开始）
    'anchor': anchor_text   # 完整锚点文本
}
```

#### 1.3.2 检测逻辑
```python
# 在处理每个锚点时进行检测
if not self.yaml_handler.get_stub_code(tc_id, step_id, segment_id):
    self.missing_anchors.append({
        'file': file_path, 
        'line': i + 1, 
        'anchor': anchor_text
    })
```

#### 1.3.3 统计与显示
```python
# 在 stub_processor.py 中
missing_list = getattr(self.parser, 'missing_anchors', [])
missing_count = len(missing_list)
result["missing_stubs"] = missing_count
result["missing_anchor_details"] = missing_list

# UI显示逻辑
if missing_count > 0:
    self.ui.log(f"[警告] 缺失桩代码锚点共 {missing_count} 个", tag="warning")
    for entry in missing_list:
        rel_file = os.path.relpath(entry.get('file', ''), root_dir)
        line = entry.get('line', '')
        anchor = entry.get('anchor', '')
        msg = f"{rel_file} 第 {line} 行: {anchor} 未在YAML中找到"
        self.ui.log(f"[缺失] {msg}", tag="missing")
```

### 1.4 用户体验改进

#### 1.4.1 状态栏提示
- 实时显示缺失锚点数量
- 处理完成后在状态栏显示汇总信息

#### 1.4.2 日志分类显示
- `[警告]` 标签：显示缺失锚点总数
- `[缺失]` 标签：显示具体的缺失锚点详情
- `[信息]` 标签：显示未找到锚点的文件列表

---

## 📊 功能二：改进的进度条显示模块

### 2.1 功能描述

进度条组件，提供了更加美观和实用的进度显示效果，增强了用户的操作反馈体验。

### 2.2 核心特性

#### 2.2.1 自定义圆角进度条
- **视觉效果**：采用圆角设计，提升界面美观度
- **颜色搭配**：使用浅色背景配深色填充，提升可读性
- **平滑动画**：进度更新时具有平滑的视觉效果

#### 2.2.2 多维度进度显示
- **百分比显示**：实时显示处理进度百分比
- **文件计数**：显示当前处理文件数/总文件数
- **状态文本**：同步显示当前处理状态

### 2.3 技术实现

#### 2.3.1 自定义进度条组件
```python
# 在 rounded_progressbar.py 中
class RoundedProgressBar(tk.Canvas):
    """自定义圆角进度条控件"""
    
    def __init__(self, master, width=300, height=10, 
                 bg_color="#DDDDDD", fg_color="#444444", radius=5):
        # 初始化参数
        self._width = width
        self._height = height
        self._radius = radius
        self._bg_color = bg_color  # 背景色
        self._fg_color = fg_color  # 前景色
        self._progress = 0
        
    def set(self, value: float):
        """设置进度值，取值范围0-100"""
        value = max(0.0, min(100.0, float(value)))
        self._progress = value
        bar_width = self._width * (self._progress / 100.0)
        # 更新进度条显示
```

#### 2.3.2 进度更新机制
```python
# 在 app_ui.py 中
def update_progress(self, value, status_text=None, current=None, total=None):
    """更新进度条和状态栏"""
    self.progress.set(value)
    if hasattr(self, "progress_bar") and hasattr(self.progress_bar, "set"):
        self.progress_bar.set(value)
    
    if current is not None and total is not None:
        percentage = f"{value}%" if value <= 100 else "100%"
        progress_text = f"{current}/{total} ({percentage})"
        self.update_status(progress_text)
```

#### 2.3.3 处理器集成
```python
# 在 stub_processor.py 中
if hasattr(self, 'ui') and self.ui and hasattr(self.ui, "update_progress"):
    percentage = int((i + 1) / len(c_files) * 100)
    self.ui.root.after(0, self.ui.update_progress, 
                      percentage, f"处理文件 {i+1}/{len(c_files)}", 
                      i+1, len(c_files))
```

### 2.4 界面效果

#### 2.4.1 颜色方案
- **背景色**：`#DDDDDD`（浅灰色）
- **填充色**：`#444444`（深灰色）
- **半径**：`5px`（圆角效果）

#### 2.4.2 显示信息
- 进度百分比（0-100%）
- 当前文件数/总文件数
- 处理状态文本

---

## 🔄 功能三：全新的反向输出YAML功能

### 3.1 功能描述

全新的反向输出功能，能够从已经插入桩代码的C文件中提取桩代码，并生成标准的YAML配置文件，实现了从代码到配置的逆向工程。

### 3.2 核心特性

#### 3.2.1 智能代码提取
- **桩代码识别**：自动识别已插入的桩代码
- **锚点解析**：解析桩代码对应的锚点信息
- **代码分组**：按测试用例ID、步骤ID和代码段ID进行分组

#### 3.2.2 标准YAML格式输出
- **块字符串格式**：使用`|`符号保持代码格式
- **层级结构**：保持TC → STEP → SEGMENT的层级关系
- **UTF-8编码**：确保中文注释的正确显示

### 3.3 技术实现

#### 3.3.1 桩代码提取逻辑
```python
# 在 stub_processor.py 中
def extract_to_yaml(self, root_dir: str, output_file: str) -> bool:
    """根据已插入的桩代码生成YAML配置"""
    try:
        stub_dict: Dict[str, Dict[str, Dict[str, str]]] = {}
        c_files = find_c_files(root_dir)
        
        for file_path in c_files:
            stubs = self.parser.extract_stubs_from_file(file_path)
            for entry in stubs:
                tc = entry['test_case_id']
                step = entry['step_id']
                seg = entry['segment_id']
                code = entry['code']
                stub_dict.setdefault(tc, {}).setdefault(step, {})[seg] = code
```

#### 3.3.2 YAML格式化处理
```python
# 自定义YAML字符串格式
class LiteralStr(str):
    """用于在YAML中以块字符串形式表示代码"""

def literal_representer(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

yaml.add_representer(LiteralStr, literal_representer, Dumper=yaml.SafeDumper)

# 格式化输出
formatted_dict: Dict[str, Dict[str, Dict[str, LiteralStr]]] = {}
for tc_id, steps in stub_dict.items():
    formatted_dict[tc_id] = {}
    for step_id, segments in steps.items():
        formatted_dict[tc_id][step_id] = {
            seg_id: LiteralStr(code)
            for seg_id, code in segments.items()
        }
```

#### 3.3.3 UI集成
```python
# 在 app_ui.py 中
def _reverse_extract(self):
    """反向提取YAML配置"""
    project_dir = self.project_dir.get()
    if not project_dir or not os.path.isdir(project_dir):
        messagebox.showwarning("输入错误", "请选择有效项目目录")
        return

    output_path = filedialog.asksaveasfilename(
        defaultextension=".yaml",
        filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*.*")],
        initialfile="reversed.yaml",
    )
    
    if self.reverse_callback:
        self.reverse_callback(project_dir, output_path)
```

### 3.4 输出示例

#### 3.4.1 输入C代码
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

#### 3.4.2 输出YAML配置
```yaml
TC001:
  STEP1:
    segment1: |
      if (data < 0 || data > 100) {
          printf("无效数据: %d\n", data);
          return ERROR_VALUE;
      }
```

---


---

## 🚀 使用指南

### 5.1 锚点缺失检测

1. **启动工具**：运行YAMLWeave
2. **选择项目**：选择包含锚点的项目目录
3. **选择配置**：选择YAML配置文件
4. **执行检测**：点击"扫描并插入"按钮
5. **查看结果**：在日志窗口查看缺失锚点的详细信息

### 5.2 进度监控

1. **观察进度条**：实时查看处理进度
2. **查看状态栏**：了解当前处理状态
3. **监控日志**：查看详细的处理日志

### 5.3 反向输出YAML

1. **选择项目**：选择包含已插入桩代码的项目
2. **点击按钮**：点击"反向生成YAML"按钮
3. **选择输出**：选择YAML文件保存位置
4. **完成导出**：等待导出完成并查看结果

