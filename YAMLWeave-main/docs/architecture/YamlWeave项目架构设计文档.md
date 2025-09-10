# YamlWeave项目架构设计文档

## 项目概述

YamlWeave是一个自动插桩工具，旨在简化C代码测试过程中的桩代码插入工作。该工具支持两种工作模式：

1. **传统模式**：从注释中直接提取代码字段
2. **分离模式**：从YAML配置中加载桩代码（锚点与桩代码分离）

分离模式的优势在于减少源代码污染，实现桩代码的集中管理和复用。

## 系统架构

YamlWeave采用模块化设计，主要包含以下几个核心模块：

1. **核心模块 (core)**：提供桩代码处理的核心逻辑和文件操作工具
2. **处理器模块 (handlers)**：负责YAML配置和注释的处理
3. **工具模块 (utils)**：提供日志、配置管理、异常处理等通用功能
4. **用户界面模块 (ui)**：提供图形用户界面和控制器
5. **主入口模块 (main.py)**：整合命令行和GUI功能的统一入口

各模块之间的关系如下图所示：

```
                    +-------------+
                    |   main.py   |
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
  |stub_|  |stub_| |yaml_|  |comment||app_ui||app_|
  |proc.|  |pars.| |hand.|  |_hand.| |     | |cont.|
  +-----+  +-----+ +-----+  +------+ +-----+ +-----+
     |         |      |                     |
  +--v--+  +---v--+   |               +-----v------+
  |utils|  |adapt.|   |               |rounded_    |
  +-----+  +-----+   |               |progressbar |
          |           |               +------------+
     +----v----+      |
     |  utils  |      |
     +----+----+      |
          |           |
     +----v----+------v----+
     | logger | file_utils |
     | config | exceptions |
     +--------+------------+
```

## 主要模块详解

### 1. 核心模块 (core)

#### 1.1 stub_processor.py

**作用**: 负责桩代码处理的核心逻辑，协调其他组件工作，实现桩代码插入功能，支持目录备份和结果管理

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
    
    def __init__(self, project_dir: Optional[str] = None, yaml_file_path: Optional[str] = None, ui=None):
        """
        初始化桩处理器
        
        Args:
            project_dir: 项目目录路径，可选
            yaml_file_path: YAML配置文件路径，可选
            ui: UI实例，用于进度显示和日志输出
        """
        # 初始化日志
        self.logger = logging.getLogger("yamlweave.core")
        
        # 初始化变量
        self.project_dir = project_dir
        self.yaml_file_path = yaml_file_path
        self.using_mocks = not (handlers_loaded and parser_loaded)
        self.ui = ui
        
        # 实例化处理器组件（包含错误恢复机制）
        try:
            # 初始化YAML处理器
            self.yaml_handler = YamlStubHandler(yaml_file_path)
            if yaml_file_path and os.path.exists(yaml_file_path):
                self.yaml_handler.load_yaml(yaml_file_path)
            
            # 初始化注释处理器
            self.comment_handler = CommentHandler()
            
            # 初始化解析器
            self.parser = StubParser(self.yaml_handler)
            
            self.logger.info("桩处理器组件初始化完成")
        except Exception as e:
            self.logger.error(f"初始化桩处理器组件失败: {str(e)}")
            self.using_mocks = True
            
            # 确保即使出错也有可用的组件
            self.yaml_handler = YamlStubHandler(yaml_file_path)
            self.comment_handler = CommentHandler()
            self.parser = StubParser(self.yaml_handler)
```

**主要功能**:

- 处理单个文件的插桩

```python
def process_file(self, file_path: str, callback=None) -> Tuple[bool, str, int]:
    """
    处理单个文件，插入桩代码
    
    Args:
        file_path: 文件路径
        callback: 可选回调函数，用于报告处理进度
        
    Returns:
        Tuple[bool, str, int]: (成功/失败, 消息, 插入桩点数量)
    """
    logger.info(f"处理文件: {file_path}")
    
    if self.using_mocks:
        logger.warning(f"使用模拟处理: {file_path}")
        return True, "成功 (模拟)", 0
    
    # 实际处理文件
    try:
        if not os.path.exists(file_path):
            return False, f"文件不存在: {file_path}", 0
        
        # 处理文件并返回结果
        success, message, count = self.parser.process_file(file_path, callback)
        
        if success:
            logger.info(f"文件处理成功: {file_path}, 插入了 {count} 个桩点")
        else:
            logger.warning(f"文件处理失败: {file_path}, {message}")
        
        return success, message, count
    except Exception as e:
        error_msg = f"处理文件时出错: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, 0
```

- 处理整个目录的插桩（支持备份和结果目录管理）

```python
def process_directory(self, root_dir: str, callback=None) -> Dict[str, Any]:
    """
    处理目录中的所有文件
    
    Args:
        root_dir: 根目录路径
        callback: 可选回调函数，用于报告处理进度
        
    Returns:
        Dict[str, Any]: 处理结果统计信息
    """
    result = {
        "total_files": 0,
        "processed_files": 0,
        "successful_stubs": 0,
        "errors": [],
        "backup_dir": None,
        "stubbed_dir": None,
        "missing_stubs": 0
    }

    # 实际处理目录
    try:
        # 检查目录是否存在
        if not os.path.isdir(root_dir):
            result["errors"].append({"file": "N/A", "error": f"目录不存在: {root_dir}"})
            return result
        
        # 创建备份和结果目录（如果不存在）
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = getattr(self, 'backup_dir', f"{root_dir}_backup_{timestamp}")
        stubbed_dir = getattr(self, 'stubbed_dir', f"{root_dir}_stubbed_{timestamp}")
        
        # 保存目录信息
        self.backup_dir = backup_dir
        self.stubbed_dir = stubbed_dir
        
        # 将目录信息添加到结果中
        result["backup_dir"] = backup_dir
        result["stubbed_dir"] = stubbed_dir

        # 查找所有C文件
        c_files = find_c_files(root_dir)
        result["total_files"] = len(c_files)
        
        # 处理每个文件
        for i, file_path in enumerate(c_files):
            # 更新进度显示
            if hasattr(self, 'ui') and self.ui and hasattr(self.ui, "update_progress"):
                percentage = int((i / result["total_files"]) * 100) if result["total_files"] > 0 else 0
                current_file = os.path.basename(file_path)
                self.ui.root.after(0, self.ui.update_progress, percentage, f"处理: {current_file}", i, result["total_files"])
            
            # 处理文件
            success, message, count = self.process_file(file_path, callback)
            
            if success:
                result["processed_files"] += 1
                result["successful_stubs"] += count
            else:
                result["errors"].append({"file": file_path, "error": message})
```

#### 1.2 stub_parser.py

**作用**: 负责解析C代码中的注释和锚点，支持传统格式和新格式的桩代码识别，并提供缺失锚点统计

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
        # 测试用例ID匹配模式 - 匹配符合"// TC001 STEP1:"格式的注释行
        self.test_case_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+):', re.IGNORECASE)
        
        # 单行代码匹配模式 - 匹配"// code: [代码内容]"格式
        self.single_line_code_pattern = re.compile(r'//\s*code:\s*(.*)')
        
        # 多行代码开始和结束标记
        self.multi_line_start = '/* code:'
        self.multi_line_end = '*/'
        
        # 新格式锚点匹配模式 - 匹配符合"// TC001 STEP1 segment1"格式的注释行
        self.anchor_pattern = re.compile(r'//\s*(TC\d+\s+STEP\d+\s+\w+).*', re.IGNORECASE)
        
        # YAML处理器
        self.yaml_handler = yaml_handler

        # 用于统计缺失的桩代码锚点
        self.missing_anchors: List[Dict[str, Any]] = []

        # 用于记录未找到任何锚点的文件
        self.files_without_anchors: List[str] = []
```

#### 1.3 utils.py (core/utils.py)

**作用**: 提供核心文件操作功能，包括编码检测、文件读写等基础工具函数

**关键代码**:

```python
def detect_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(min(1024 * 1024, os.path.getsize(file_path)))
        
        import chardet
        result = chardet.detect(raw_data)
        encoding = result['encoding'] or 'utf-8'
        confidence = result['confidence']
        logger.info(f"检测到文件 {file_path} 编码: {encoding}, 置信度: {confidence}")
        
        # 常见编码修正
        if encoding.lower() in ('gb2312', 'gbk'):
            return 'gb18030'
        return encoding
    except Exception as e:
        logger.error(f"检测文件 {file_path} 编码失败: {str(e)}")
        return 'utf-8'

def read_file(file_path):
    """读取文件内容，自动处理编码"""
    # 尝试的编码列表
    encodings_to_try = []
    
    # 首先尝试检测编码
    detected_encoding = detect_encoding(file_path)
    encodings_to_try.append(detected_encoding)
    
    # 添加其他常用编码
    for enc in ['utf-8', 'gb18030', 'gbk', 'latin1']:
        if enc != detected_encoding:
            encodings_to_try.append(enc)
    
    # 尝试使用不同的编码读取文件
    for encoding in encodings_to_try:
        try:
            logger.info(f"尝试使用编码 {encoding} 读取文件 {file_path}")
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
                logger.info(f"使用编码 {encoding} 成功读取文件 {file_path}")
                return content, encoding
        except UnicodeDecodeError:
            logger.warning(f"使用编码 {encoding} 读取文件 {file_path} 失败")
            continue
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败: {str(e)}")
            break
    
    # 如果所有编码都失败，使用二进制模式读取并返回
    try:
        logger.warning(f"所有编码尝试失败，以二进制模式读取文件 {file_path}")
        with open(file_path, 'rb') as f:
            binary_content = f.read()
            # 将二进制内容转换为字符串，替换不可解码的字节
            text_content = binary_content.decode('utf-8', errors='replace')
            return text_content, 'utf-8'
    except Exception as e:
        logger.error(f"以二进制模式读取文件 {file_path} 失败: {str(e)}")
        return None, None

def write_file(file_path, content, encoding=None):
    """写入文件内容，使用原始编码"""
    if not encoding:
        # 如果未指定编码，尝试检测原文件编码
        if os.path.exists(file_path):
            encoding = detect_encoding(file_path)
        else:
            encoding = 'utf-8'
    
    try:
        # 为处理后的文件添加后缀
        stub_file_path = file_path + ".stub"
        
        # 写入处理后的文件
        with open(stub_file_path, 'w', encoding=encoding, errors='replace') as f:
            f.write(content)
        logger.info(f"成功写入处理后文件: {stub_file_path}")
        
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {str(e)}")
        return False
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

**作用**: 负责YAML配置文件的加载、解析和管理，支持桩代码的查询和获取，包含复杂的编码处理和错误恢复机制

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
        segment2: |
          log_info("输入数据验证完毕");
    ```
    
    YAML中的'|'符号表示"字面块标量"（literal block scalar），它会保留文本中的所有换行符和缩进，
    使桩代码的格式在配置文件中保持原样，便于阅读和维护。
    
    特点：
    - 支持多种编码自动检测和处理
    - 包含错误恢复机制，当YAML解析失败时自动生成默认配置
    - 支持路径自动查找和文件创建
    """
    
    def __init__(self, yaml_file_path: Optional[str] = None):
        """
        初始化YAML桩代码处理器
        
        Args:
            yaml_file_path: YAML配置文件路径，可选
        """
        self.yaml_file_path = yaml_file_path
        self.stub_data = {}
        
        if yaml_file_path and os.path.exists(yaml_file_path):
            self.load_yaml(yaml_file_path)
```

**主要功能**:

- 加载YAML配置文件，处理编码问题和错误恢复

```python
def load_yaml(self, yaml_file_path: str) -> bool:
    """
    加载YAML配置文件
    
    Args:
        yaml_file_path: YAML配置文件路径
        
    Returns:
        bool: 加载成功返回True，否则返回False
    """
    try:
        # 规范化路径
        yaml_file_path = os.path.normpath(yaml_file_path)
        logger.info(f"尝试加载YAML配置文件: {yaml_file_path}")
        
        # 特殊处理auto.yaml文件
        if not os.path.exists(yaml_file_path):
            # 尝试在当前目录和上级目录中查找auto.yaml
            simple_name = os.path.basename(yaml_file_path)
            if simple_name.lower() in ('auto.yaml', 'auto.yml'):
                # 尝试当前目录
                if os.path.exists(simple_name):
                    yaml_file_path = simple_name
                    logger.info(f"在当前目录找到: {yaml_file_path}")
                else:
                    # 尝试向上级目录中寻找
                    curr_dir = os.getcwd()
                    parent_dir = os.path.dirname(curr_dir)
                    test_path = os.path.join(parent_dir, simple_name)
                    if os.path.exists(test_path):
                        yaml_file_path = test_path
                        logger.info(f"在上级目录找到: {yaml_file_path}")
        
        # 检查路径是否含有空格并处理
        if " " in yaml_file_path:
            logger.info(f"路径中含有空格，尝试特殊处理")
            quoted_path = f'"{yaml_file_path}"'
            logger.info(f"引号包装路径: {quoted_path}")
            
            # 尝试替换空格为短横线
            no_spaces_path = yaml_file_path.replace(" ", "-")
            logger.info(f"替换空格后的路径: {no_spaces_path}")
            if os.path.exists(no_spaces_path):
                yaml_file_path = no_spaces_path
                logger.info(f"使用替换空格后的路径: {yaml_file_path}")
        
        if not os.path.exists(yaml_file_path):
            logger.error(f"YAML配置文件不存在: {yaml_file_path}")
            
            # 尝试解决路径问题，包括创建示例文件
            try:
                # 特殊处理/tests - insert/目录
                if 'tests - insert' in yaml_file_path:
                    alt_path = yaml_file_path.replace('tests - insert', 'tests-insert')
                    logger.info(f"尝试替换目录名中的空格: {alt_path}")
                    if os.path.exists(alt_path):
                        yaml_file_path = alt_path
                        logger.info(f"使用替换空格后的路径: {yaml_file_path}")
                        return self._read_and_process_yaml(yaml_file_path)
                
                # 列出父目录内容以辅助诊断
                parent_dir = os.path.dirname(yaml_file_path)
                logger.info(f"检查父目录内容: {parent_dir}")
                if os.path.exists(parent_dir):
                    files = os.listdir(parent_dir)
                    logger.info(f"父目录文件列表: {files}")
                    
                    # 查找任何yaml文件
                    for file in files:
                        if file.lower().endswith(('.yaml', '.yml')):
                            full_path = os.path.join(parent_dir, file)
                            logger.info(f"找到YAML文件: {full_path}")
                            yaml_file_path = full_path
                            return self._read_and_process_yaml(yaml_file_path)
                
                # 尝试创建示例YAML文件
                try:
                    from YAMLWeave.core.stub_processor import create_example_yaml_file
                    example_yaml_path = create_example_yaml_file(yaml_file_path)
                    logger.info(f"已创建示例YAML配置文件: {example_yaml_path}")
                    return {}
                except ImportError:
                    logger.error("无法创建示例YAML配置文件")
                    return {}
                
            except Exception as e:
                logger.error(f"尝试解决路径问题失败: {str(e)}")
                return False
        
        return self._read_and_process_yaml(yaml_file_path)
        
    except Exception as e:
        logger.error(f"加载YAML配置文件失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # 最终尝试：创建基本YAML文件
        try:
            from YAMLWeave.core.stub_processor import create_example_yaml_file
            if create_example_yaml_file('auto.yaml'):
                logger.info(f"最终尝试：已创建auto.yaml")
                self.stub_data = {
                    'TC001': {
                        'STEP1': {
                            'segment1': 'printf("自动生成的桩代码\\n");'  # 单行代码直接使用字符串
                        }
                    }
                }
                self.yaml_file_path = 'auto.yaml'
                return True
        except Exception as e3:
            logger.error(f"最终尝试失败: {str(e3)}")
            
        self.stub_data = {}
        return False
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

**作用**: 提供全面的日志记录功能，支持UI日志集成、文件日志、执行日志管理等

**关键代码**:

```python
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
    # 创建带时间戳的日志目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = os.path.join(get_app_root(), f'logs_{timestamp}')
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建带时间戳的执行日志文件
    log_filename = f"execution_{timestamp}.log"
    log_file_path = os.path.join(log_dir, log_filename)
    
    # 组织执行结果信息
    execution_info = {
        "timestamp": timestamp,
        "project_directory": project_dir,
        "stats": stats,
        "backup_directory": backup_dir,
        "stubbed_directory": stubbed_dir
    }
    
    # 格式化结果信息并写入文件
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
        
        return log_file_path
    except Exception as e:
        error_msg = f"保存执行日志失败: {str(e)}"
        logging.error(error_msg)
        return None
```

#### 3.2 file_utils.py

**作用**: 提供高级文件操作功能，包括文件搜索、路径处理等

**关键功能**:
- 支持多种文件类型的搜索
- 递归目录遍历
- 文件编码处理
- 路径规范化

#### 3.3 config.py

**作用**: 提供配置管理功能，支持YAML和JSON格式的配置文件读取和保存

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
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        return yaml.safe_load(f) or {}
                    else:
                        return json.load(f) or {}
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")
        return {}
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                    yaml.dump(self.config, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
```

#### 3.4 exceptions.py

**作用**: 定义项目专用的异常类，提供更精确的错误处理

**关键功能**:
- 定义YAMLWeave相关的自定义异常
- 提供异常分类和错误代码
- 支持异常链和上下文信息

### 4. 用户界面模块 (ui)

#### 4.1 app_ui.py

**作用**: 提供现代化图形用户界面，支持丰富的用户交互操作，包括进度显示、日志管理、状态监控等

**关键代码**:

```python
class YAMLWeaveUI:
    """YAMLWeave工具的图形用户界面"""
    
    def __init__(self, root):
        """
        初始化UI界面
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title("YAMLWeave - C代码插桩工具")
        self.root.geometry("900x700")

        # 使用ttk主题并设置基础样式，使界面更专业
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass
        default_font = ("Segoe UI", 10)
        self.style.configure("TLabel", font=default_font)
        self.style.configure("TButton", font=default_font)
        self.style.configure("TEntry", font=default_font)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                   "data", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"设置图标失败: {str(e)}")
        
        # 创建变量
        self.project_dir = tk.StringVar()
        self.yaml_file = tk.StringVar()
        self.status = tk.StringVar(value="就绪")
        self.progress = tk.IntVar(value=0)
        
        # 回调函数
        self.process_callback = None
        self.reverse_callback = None
        
        # 创建UI组件
        self._create_widgets()
        self._configure_tags()
        
        # 初始化已处理行数
        self.processed_lines = 0
        
        # 结束初始化日志
        self.log("[初始化] YAMLWeave界面初始化完成", tag="info")
        self.log("[提示] 请设置项目目录和YAML配置文件，然后点击\"扫描并插入\"", tag="info")
```

#### 4.2 rounded_progressbar.py

**作用**: 提供自定义圆角进度条组件，增强界面美观性

**关键功能**:
- 绘制圆角矩形进度条
- 支持自定义颜色和尺寸
- 平滑的进度更新动画

#### 4.3 app_controller.py

**作用**: 连接UI和核心处理逻辑，实现用户操作的响应和处理，包含适配器模式和错误恢复机制

**关键代码**:

```python
class StubProcessorAdapter:
    """
    适配器类，为StubProcessor提供兼容接口，确保无论导入哪个版本的StubProcessor都能正常工作
    """
    
    def __init__(self, processor):
        """
        初始化适配器
        
        Args:
            processor: 原始StubProcessor实例
        """
        self.processor = processor
        self.logger = logging.getLogger('yamlweave')
        self.ui = None  # 添加UI属性
        
        # 检查处理器属性，打印详细诊断信息
        self.logger.info("创建StubProcessor适配器")
        self.logger.info(f"处理器类型: {type(processor).__name__}")
        
        # 检查关键方法是否存在
        if hasattr(processor, 'process_files'):
            self.logger.info("处理器具有process_files方法")
        elif hasattr(processor, 'process_directory'):
            self.logger.info("处理器具有process_directory方法")
        else:
            self.logger.warning("处理器既没有process_files也没有process_directory方法，可能需要修复")

class AppController:
    """
    应用控制器，连接UI和核心处理
    """
    
    def __init__(self, ui=None):
        # 实例变量初始化 - 首先设置UI属性
        self.ui = ui
        
        # 日志系统初始化
        self.setup_logging()
        
        # 记录处理器初始化
        try:
            # 创建StubProcessor实例并包装到适配器中
            raw_processor = StubProcessor(ui=self.ui)
            self.processor = StubProcessorAdapter(raw_processor)
            
            # 设置UI引用
            if self.ui and self.processor:
                self.processor.ui = self.ui
                # 设置内部处理器的UI引用
                if hasattr(self.processor, 'processor') and hasattr(self.processor.processor, 'ui'):
                    self.processor.processor.ui = self.ui
                    self.log_info("初始化时设置了处理器的UI引用")
            
            if not found_real_processor:
                self.log_warning("使用模拟的StubProcessor实现，功能将受限")
            else:
                self.log_info("成功初始化StubProcessor")
        except Exception as e:
            self.log_error(f"初始化处理器失败: {str(e)}")
            self.processor = None
        
        # UI回调设置
        if self.ui is not None:
            try:
                self.ui.set_process_callback(self.process_directory)
                self.ui.set_reverse_callback(self.export_yaml)
                self.log_info("成功设置处理回调")
            except Exception as e:
                self.log_error(f"设置UI回调失败: {str(e)}")
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

### 5. 主入口模块 (main.py)

#### 5.1 main.py

**作用**: 提供统一的程序入口，支持GUI模式和命令行模式，包含完整的环境设置和示例文件生成功能

**关键代码**:

```python
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
        
        # 创建示例C文件...
        # （包含完整的示例文件创建逻辑）
        
    except Exception as e:
        logger.error(f"创建示例文件失败: {str(e)}")

def main():
    """主函数，启动GUI或命令行模式"""
    try:
        # 检查命令行参数，确定是否启动GUI
        if len(sys.argv) > 1:
            # 有命令行参数，启动命令行模式
            run_command_line_mode()
        else:
            # 无命令行参数，启动GUI模式
            run_gui_mode()
    except Exception as e:
        logger.error(f"程序启动失败: {str(e)}")
        sys.exit(1)

def run_gui_mode():
    """运行GUI模式"""
    try:
        # 创建Tkinter根窗口
        root = tk.Tk()
        
        # 创建UI实例
        ui = YAMLWeaveUI(root)
        
        # 创建控制器
        controller = AppController(ui)
        
        # 启动GUI主循环
        root.mainloop()
        
    except Exception as e:
        logger.error(f"GUI模式启动失败: {str(e)}")
        messagebox.showerror("启动错误", f"GUI模式启动失败: {str(e)}")

def run_command_line_mode():
    """运行命令行模式"""
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="YAMLWeave - C代码插桩工具")
    parser.add_argument("project_dir", help="项目目录路径")
    parser.add_argument("-y", "--yaml", help="YAML配置文件路径")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出详细日志")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"启动YAMLWeave工具 - 命令行模式")
    logger.info(f"项目目录: {args.project_dir}")
    
    # 创建处理器并执行处理
    try:
        processor = StubProcessor(args.project_dir, args.yaml)
        if args.yaml:
            processor.set_yaml_file(args.yaml)
        
        result = processor.process_directory(args.project_dir)
        
        # 输出结果
        print(f"处理完成:")
        print(f"  总文件数: {result.get('total_files', 0)}")
        print(f"  处理文件数: {result.get('processed_files', 0)}")
        print(f"  插入桩点数: {result.get('successful_stubs', 0)}")
        
        if result.get('errors'):
            print(f"  错误数: {len(result['errors'])}")
            
    except Exception as e:
        logger.error(f"命令行模式执行失败: {str(e)}")
        sys.exit(1)
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

YamlWeave项目采用高度模块化的设计架构，实现了C代码自动插桩的完整解决方案。项目具有以下主要特点和优势：

### 架构特点

1. **模块化设计**：各模块功能明确分离，易于维护和扩展
   - **核心模块**：提供插桩处理的核心逻辑和文件操作
   - **处理器模块**：负责YAML配置和注释的专业化处理
   - **工具模块**：提供日志、配置、异常处理等基础设施
   - **用户界面模块**：提供现代化的图形界面和交互体验
   - **主入口模块**：统一GUI和CLI的程序入口

2. **适配器模式**：通过`StubProcessorAdapter`确保不同版本处理器的兼容性

3. **错误恢复机制**：在各个层面都包含了完善的错误处理和恢复逻辑

### 功能特色

1. **双模式支持**：
   - **传统模式**：基于代码注释直接插桩，适合简单场景
   - **分离模式**：基于YAML配置的锚点插桩，实现代码与桩代码分离

2. **智能文件处理**：
   - 自动编码检测和多编码支持
   - 备份目录和结果目录的自动管理
   - 支持批量文件处理和进度跟踪

3. **丰富的用户界面**：
   - 现代化的图形界面设计
   - 实时进度显示和状态监控
   - 多彩日志显示和分类管理
   - 自定义圆角进度条组件

4. **全面的日志系统**：
   - 支持文件日志和UI日志的统一管理
   - 执行日志的持久化存储
   - 缺失锚点的详细统计和报告

### 技术优势

1. **高兼容性**：支持PyInstaller打包，兼容Windows和Linux系统

2. **健壮性**：包含多层错误处理机制，确保程序稳定运行

3. **可扩展性**：模块化设计便于功能扩展和维护

4. **易用性**：提供GUI和CLI两种使用方式，满足不同用户需求

5. **专业性**：针对C代码插桩的专业化设计，支持复杂的插桩场景

### 设计优势

1. **代码分离**：实现了桩代码与源代码的完全分离，保持代码清晰
2. **集中管理**：通过YAML配置实现桩代码的集中管理和复用
3. **用户友好**：现代化的界面设计和详细的操作反馈
4. **维护便利**：完善的日志系统和错误诊断机制
5. **性能优化**：支持多文件并行处理和实时进度反馈

YamlWeave项目成功地将复杂的C代码插桩需求转化为简单易用的工具，为嵌入式软件开发和测试提供了强有力的支持。通过先进的架构设计和丰富的功能特性，该工具能够显著提高开发效率并降低测试成本。 