# YamlWeave项目架构设计文档

## 项目概述

YamlWeave是一个自动插桩工具，旨在简化C代码测试过程中的桩代码插入工作。该工具支持两种工作模式：

1. **传统模式**：从注释中直接提取代码字段
2. **分离模式**：从YAML配置中加载桩代码（锚点与桩代码分离）

分离模式的优势在于减少源代码污染，实现桩代码的集中管理和复用。

## 系统架构

YamlWeave采用模块化设计，主要包含以下几个核心模块：

1. **核心模块 (core)**：提供桩代码处理的核心逻辑
2. **处理器模块 (handlers)**：负责YAML配置和注释的处理
3. **工具模块 (utils)**：提供日志、文件操作等通用功能
4. **用户界面模块 (ui)**：提供图形用户界面
5. **命令行模块 (cli)**：提供命令行接口

各模块之间的关系如下图所示：

```
                  +-------------+
                  | YamlWeave   |
                  +-------------+
                         |
        +----------------+----------------+
        |                |                |
+-------v------+  +------v-------+  +-----v-------+
|    core      |  |   handlers   |  |     ui      |
+-------+------+  +------+-------+  +-----+-------+
        |                |                |
   +----+----+      +----+----+      +----+----+
   |         |      |         |      |         |
+--v--+  +---v--+ +-v---+  +--v---+ +-v---+ +--v--+
|stub_|  |stub_| |yaml_|  |comment|app_ui|app_|
|proc.|  |pars.| |hand.|  |_hand.| +-----+ |cont.|
+-----+  +-----+ +-----+  +------+         +-----+
```

## 主要模块详解

### 1. 核心模块 (core)

#### 1.1 stub_processor.py

**作用**: 负责桩代码处理的核心逻辑，协调其他组件工作，实现桩代码插入功能

**关键代码**:

```python
class StubProcessor:
    """
    桩处理器，支持"锚点与桩代码分离"机制
    
    此处理器实现了桩代码注入的两种核心机制：
    1. 传统模式：从注释中直接提取代码字段
    2. 分离模式：从YAML配置中加载桩代码（锚点与桩代码分离）
    
    分离模式的优势：
    - 减少源代码污染：源代码中仅保留锚点标识
    - 桩代码集中管理：所有桩代码在YAML配置文件中管理
    - 支持桩代码复用：同一桩代码可用于多处锚点
    """
    
    def __init__(self, yaml_file_path: Optional[str] = None):
        # 创建YAML处理器
        self.yaml_handler = None
        if YamlStubHandler:
            self.yaml_handler = YamlStubHandler(yaml_file_path)
        
        # 创建解析器和注释处理器
        self.parser = StubParser(self.yaml_handler)
        self.comment_handler = CommentHandler()
```

**主要功能**:

- 处理单个文件的插桩

```python
def process_file(self, file_path: str) -> Tuple[bool, str, int]:
    """处理单个文件，在文件开头插入所有YAML中定义的桩代码"""
    logger.info(f"开始处理文件: {file_path}")
    
    # 读取文件内容
    content, encoding = read_file(file_path)
    if content is None:
        return False, "无法读取文件内容", 0
    
    lines = content.splitlines()
    
    # 使用新格式解析，这将为文件生成所有YAML中定义的桩点
    stub_points = self.parser.parse_new_format(file_path, lines)
    
    # 插入所有桩点
    inserted_count = 0
    for stub in stub_points:
        # 实际的插入工作由CommentHandler完成
        if self.comment_handler.process_stub(lines, stub):
            inserted_count += 1
```

- 处理整个目录的插桩

```python
def process_directory(self, root_dir: str) -> Dict[str, Any]:
    """处理目录中的所有C文件"""
    logger.info(f"开始处理目录: {root_dir}")
    
    # 检查YAML配置文件是否设置（分离模式需要）
    if not self.yaml_handler or not self.yaml_file_path:
        logger.warning("未设置YAML配置文件，只能使用传统模式")
        return {"error": "未设置YAML配置文件"}
    
    # 查找所有C文件
    c_files = find_c_files(root_dir)
    
    # 处理每个文件
    results = {
        "total_files": len(c_files),
        "processed_files": 0,
        "successful_stubs": 0,
        "errors": []
    }
    
    for file_path in c_files:
        success, message, count = self.process_file(file_path)
        if success:
            results["processed_files"] += 1
            results["successful_stubs"] += count
        else:
            results["errors"].append({
                "file": file_path,
                "error": message
            })
```

#### 1.2 stub_parser.py

**作用**: 负责解析C代码中的注释和锚点，支持传统格式和新格式的桩代码识别

**关键代码**:

```python
class StubParser:
    """
    增强的桩注释解析器，支持YAML配置和新格式锚点
    
    支持两种主要工作模式:
    1. 传统模式：识别注释中内嵌的代码字段
    2. 分离模式：识别锚点标识，从YAML配置文件中加载对应的桩代码
    """
    
    def __init__(self, yaml_handler: Optional[YamlStubHandler] = None):
        # 传统模式的正则表达式
        self.test_case_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+):', re.IGNORECASE)
        self.single_line_code_pattern = re.compile(r'//\s*code:\s*(.*)')
        
        # 新格式锚点匹配模式
        self.anchor_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+\s+\w+).*', re.IGNORECASE)
        
        # YAML处理器
        self.yaml_handler = yaml_handler
```

**主要功能**:

- 解析新格式的锚点

```python
def parse_new_format(self, file_path: str, lines: List[str]) -> List[Dict[str, Any]]:
    """解析新格式的锚点标识，在锚点位置插入桩代码"""
    if not self.yaml_handler:
        logger.warning("YAML处理器未配置，无法使用锚点与桩代码分离功能")
        return []
    
    stub_points = []
    
    # 在文件中查找锚点
    for i, line in enumerate(lines):
        match = self.anchor_pattern.search(line)
        if match:
            anchor_text = match.group(1).strip()
            
            # 解析锚点标识
            parts = anchor_text.split()
            if len(parts) >= 3:
                tc_id = parts[0]
                step_id = parts[1]
                segment_id = parts[2]
                
                # 从YAML配置中获取对应的桩代码
                code = self.yaml_handler.get_stub_code(tc_id, step_id, segment_id)
                
                if code:
                    # 添加到桩点列表，在锚点所在行的下一行插入
                    stub_points.append({
                        'test_case_id': anchor_text,
                        'code': code,
                        'line_number': i + 1,  # 在当前锚点行之后插入
                        'original_line': i,
                        'file': file_path,
                        'format': 'new'  # 标记为新格式
                    })
```

- 解析传统格式的注释和code字段

```python
def parse_traditional_format(self, file_path: str, lines: List[str]) -> List[Dict[str, Any]]:
    """解析传统格式的注释和code字段"""
    stub_points = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 查找测试用例ID注释
        match = self.test_case_pattern.search(line)
        if match:
            test_case_id = match.group(1)
            
            # 检查下一行是否包含code字段
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                
                # 处理单行代码
                code_match = self.single_line_code_pattern.search(next_line)
                if code_match:
                    code = code_match.group(1)
                    # 处理代码...
```

- 文件编码检测功能

```python
def detect_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(min(1024 * 1024, os.path.getsize(file_path)))
        
        import chardet
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        
        # 常见编码修正
        if encoding.lower() in ('gb2312', 'gbk'):
            return 'gb18030'
        return encoding
    except Exception as e:
        logger.error(f"检测文件 {file_path} 编码失败: {str(e)}")
        return 'utf-8'
```

### 2. 处理器模块 (handlers)

#### 2.1 yaml_handler.py

**作用**: 负责YAML配置文件的加载、解析和管理，支持桩代码的查询和获取

**关键代码**:

```python
class YamlStubHandler:
    """
    YAML桩代码处理器
    
    管理和解析YAML格式的桩代码配置文件，使用YAML块字符格式：
    
    ```yaml
    TC001:
      STEP1:
        segment1: |
          if (data < 0 || data > 100) {
              printf("无效数据: %d\n", data);
              return;
          }
    ```
    
    YAML中的 '|' 符号表示"字面块标量"（literal block scalar），它会保留文本中的所有换行符和缩进，
    使桩代码的格式在配置文件中保持原样，便于阅读和维护。
    """
    
    def __init__(self, yaml_file_path: Optional[str] = None):
        self.yaml_file_path = yaml_file_path
        self.stub_data = {}
        
        if yaml_file_path and os.path.exists(yaml_file_path):
            self.load_yaml(yaml_file_path)
```

**主要功能**:

- 加载YAML配置文件，处理编码问题

```python
def load_yaml(self, yaml_file_path: str) -> bool:
    """加载YAML配置文件"""
    try:
        # 规范化路径
        yaml_file_path = os.path.normpath(yaml_file_path)
        logger.info(f"尝试加载YAML配置文件: {yaml_file_path}")
        
        # 各种路径和编码处理...
        
        return self._read_and_process_yaml(yaml_file_path)
    except Exception as e:
        logger.error(f"加载YAML配置文件失败: {str(e)}")
        # 错误恢复处理...
```

- 获取特定锚点对应的桩代码

```python
def get_stub_code(self, test_case_id: str, step_id: str, segment_id: str) -> Optional[str]:
    """获取特定锚点对应的桩代码"""
    try:
        # 检查测试用例是否存在
        if test_case_id not in self.stub_data:
            logger.warning(f"未找到测试用例: {test_case_id}")
            return None
        
        # 检查步骤是否存在
        if step_id not in self.stub_data[test_case_id]:
            logger.warning(f"未找到步骤: {test_case_id} {step_id}")
            return None
        
        # 检查代码段是否存在
        if segment_id not in self.stub_data[test_case_id][step_id]:
            logger.warning(f"未找到代码段: {test_case_id} {step_id} {segment_id}")
            return None
        
        # 获取代码段内容
        code_content = self.stub_data[test_case_id][step_id][segment_id]
        return code_content  # 使用块字符格式存储的代码字符串
```

- 获取测试用例和步骤信息

```python
def get_all_test_cases(self) -> List[str]:
    """获取所有测试用例ID"""
    if not isinstance(self.stub_data, dict):
        return []
    return list(self.stub_data.keys())

def get_steps_for_test_case(self, test_case_id: str) -> List[str]:
    """获取特定测试用例的所有步骤"""
    if not isinstance(self.stub_data, dict) or test_case_id not in self.stub_data:
        return []
    return list(self.stub_data[test_case_id].keys())

def get_segments_for_step(self, test_case_id: str, step_id: str) -> List[str]:
    """获取特定步骤的所有代码段"""
    if not isinstance(self.stub_data, dict) or test_case_id not in self.stub_data:
        return []
    if not isinstance(self.stub_data[test_case_id], dict) or step_id not in self.stub_data[test_case_id]:
        return []
    return list(self.stub_data[test_case_id][step_id].keys())
```

#### 2.2 comment_handler.py

**作用**: 负责处理C代码中的注释和锚点，实现桩代码的插入

**关键代码**:

```python
class CommentHandler:
    """处理桩代码插入，支持两种锚点格式"""
    
    def __init__(self):
        # 传统格式 - 测试用例ID匹配模式 (如 TC001 STEP1:)
        self.test_case_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+):', re.IGNORECASE)
        
        # 新格式 - 锚点匹配模式 (如 TC001 STEP1 segment1)
        self.anchor_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+\s+\w+).*', re.IGNORECASE)
```

**主要功能**:

- 查找桩代码插入点

```python
def find_comment_insertion_point(self, lines: List[str], stub_info: Dict[str, Any]) -> Tuple[int, bool]:
    """查找注释或锚点的插入点"""
    test_case_id = stub_info.get('test_case_id')
    
    # 确定使用哪种模式
    format_type = stub_info.get('format', 'traditional')
    
    if format_type == 'new':
        # 新格式：使用预设的插入点
        insertion_point = stub_info.get('line_number', 1)
        return insertion_point, True
    else:
        # 传统格式：查找注释和code字段
        for i, line in enumerate(lines):
            match = self.test_case_pattern.search(line)
            parts = test_case_id.split()
            if match and match.group(1).lower() == parts[0].lower() + " " + parts[1].lower():
                # 找到匹配的测试用例ID
                # 确定插入位置 - 在注释行之后
```

- 插入桩代码

```python
def insert_code(self, lines: List[str], insertion_point: int, code: str) -> bool:
    """在指定位置插入代码"""
    # 拆分代码为多行，并添加标记
    # 对于每一行非空代码，添加"// 通过桩插入"标记
    code_lines = code.splitlines()
    marked_code = []
    for line in code_lines:
        if line.strip():
            marked_code.append(f"{line}  // 通过桩插入")
        else:
            marked_code.append(line)
    
    # 在指定位置插入代码
    for i, code_line in enumerate(marked_code):
        lines.insert(insertion_point + i, code_line)
```

### 3. 工具模块 (utils)

#### 3.1 logger.py

**作用**: 提供日志记录功能，支持不同级别的日志输出

**关键代码**:

```python
def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取指定名称的日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 设置控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s [%(name)s]: %(message)s'))
    logger.addHandler(console_handler)
    
    # 设置文件日志处理器
    try:
        os.makedirs('logs', exist_ok=True)
        file_handler = logging.FileHandler(os.path.join('logs', 'YamlWeave.log'), encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s [%(name)s]: %(message)s'))
        logger.addHandler(file_handler)
    except Exception:
        pass
    
    return logger
```

#### 3.2 file_utils.py

**作用**: 提供文件操作相关的工具函数

**关键代码**:

```python
def read_file_with_encoding(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """使用指定编码读取文件内容"""
    try:
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {str(e)}")
        return None

def write_file_with_encoding(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """使用指定编码写入文件内容"""
    try:
        with open(file_path, 'w', encoding=encoding, errors='replace') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {str(e)}")
        return False
```

#### 3.3 config.py

**作用**: 提供配置管理功能，支持读取和保存配置

**关键代码**:

```python
class ConfigManager:
    """配置管理器，负责加载和保存配置"""
    
    def __init__(self, config_file: str = 'config.yaml'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")
        return {}
```

### 4. 用户界面模块 (ui)

#### 4.1 app_ui.py

**作用**: 提供图形用户界面，支持用户交互操作

**关键代码**:

```python
class AutoStubUI:
    """YamlWeave工具的图形用户界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("YamlWeave 桩代码自动插入工具")
        
        # 设置窗口大小和位置
        window_width = 800
        window_height = 600
        self.root.geometry(f"{window_width}x{window_height}")
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建界面组件
        self._create_path_section()
        self._create_options_section()
        self._create_action_buttons()
        self._create_log_section()
```

#### 4.2 app_controller.py

**作用**: 连接UI和核心处理逻辑，实现用户操作的响应和处理

**关键代码**:

```python
class AppController:
    """应用控制器，连接UI和核心处理"""
    
    def __init__(self, ui=None):
        # 日志系统初始化
        self.log_file = setup_file_logger()
        
        # 记录处理器初始化
        self.processor = StubProcessor()
        
        # UI日志记录器初始化
        self.logger = UILogger(ui)
        
        # UI回调设置
        if ui:
            ui.set_process_callback(self.process_directory)
        
        self.ui = ui
```

**主要功能**:

```python
def process_directory(self, root_dir, yaml_file=None):
    """处理目录"""
    if not root_dir or not os.path.isdir(root_dir):
        self.logger.error(f"无效的目录路径: {root_dir}")
        return
    
    # 更新状态
    if self.ui:
        self.ui.update_status("正在处理...")
    
    # 创建并启动处理线程
    thread = threading.Thread(
        target=self._process_directory_thread,
        args=(root_dir, yaml_file)
    )
    thread.daemon = True
    thread.start()
```

### 5. 命令行模块 (cli)

#### 5.1 cli/main.py

**作用**: 提供命令行接口，实现命令行参数解析和程序执行逻辑

**关键代码**:

```python
def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="YamlWeave 桩代码自动插入工具")
    
    parser.add_argument("project_dir", help="项目目录路径")
    parser.add_argument("-y", "--yaml", help="YAML配置文件路径")
    parser.add_argument("-m", "--mode", choices=["traditional", "yaml"], default="yaml",
                        help="工作模式: traditional(传统模式) 或 yaml(分离模式)")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    
    return parser.parse_args()

def run_cli():
    """运行命令行模式"""
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = get_logger("YamlWeave_cli", level=log_level)
    
    logger.info(f"启动YamlWeave工具 - 命令行模式")
    logger.info(f"项目目录: {args.project_dir}")
    
    # 创建处理器
    processor = StubProcessor()
    
    # 根据工作模式进行处理
    if args.mode == "yaml":
        if args.yaml:
            logger.info(f"使用YAML配置: {args.yaml}")
            processor.set_yaml_file(args.yaml)
    
    # 处理目录
    result = processor.process_directory(args.project_dir)
```

## 工作流程

YamlWeave工具的主要工作流程如下：

1. **初始化**：加载配置和初始化处理器
2. **配置设置**：设置YAML配置文件（分离模式）
3. **文件扫描**：扫描指定目录下的所有C文件
4. **桩点识别**：解析文件中的锚点或传统注释
5. **桩代码获取**：从YAML配置或注释中获取桩代码
6. **桩代码插入**：在锚点位置插入对应的桩代码
7. **结果汇总**：统计处理结果并输出日志

## 主要功能特点

1. **锚点与桩代码分离**：支持在源代码中仅保留锚点标识，桩代码由YAML配置文件管理
2. **自动编码检测**：自动检测文件编码，支持多种编码格式
3. **友好的用户界面**：提供图形界面和命令行两种使用方式
4. **详细的日志记录**：记录处理过程中的各项信息，便于问题定位
5. **健壮的错误处理**：处理各种异常情况，确保工具的稳定运行

## 设计优势

1. **模块化设计**：各模块功能明确，易于维护和扩展
2. **高度可配置**：支持多种工作模式和配置选项
3. **代码复用**：通过YAML配置实现桩代码的复用
4. **减少代码污染**：源代码中仅保留锚点标识，保持代码清晰
5. **多平台支持**：兼容Windows和Linux等多种操作系统

## 总结

YamlWeave项目采用模块化设计，实现了桩代码自动插入的功能。通过支持传统模式和分离模式两种工作方式，满足不同使用场景的需求。项目提供了图形界面和命令行两种使用方式，结合详细的日志记录和健壮的错误处理，保证了工具的易用性和稳定性。 