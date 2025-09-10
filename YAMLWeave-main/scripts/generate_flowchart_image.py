#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成YAMLWeave插桩逻辑流程图图片
使用此脚本将Mermaid图表转换为PNG图片文件

使用方法：
1. 安装依赖：pip install mermaid-py
2. 运行脚本：python generate_flowchart_image.py

注意：需要安装Node.js和mermaid-cli
npm install -g @mermaid-js/mermaid-cli
"""

import os
import sys
import subprocess
import tempfile

def create_mermaid_file():
    """创建Mermaid图表内容"""
    mermaid_content = '''flowchart TD
    A[程序启动] --> B["初始化StubProcessor<br/>• 设置项目目录<br/>• 加载YAML配置文件"]
    
    B --> C["调用process_directory()<br/>遍历项目目录"]
    
    C --> D["find_c_files(root_dir)<br/>查找所有.c文件"]
    
    D --> E{"是否找到.c文件?"}
    E -->|否| F["创建示例文件<br/>sample.c"]
    E -->|是| G["开始处理文件列表"]
    F --> G
    
    G --> H["遍历每个.c文件<br/>调用process_file()"]
    
    H --> I["StubParser.parse_file()<br/>解析文件内容"]
    
    I --> J["优先尝试新格式解析<br/>parse_new_format()"]
    
    J --> K["逐行扫描文件<br/>查找锚点标识"]
    
    K --> L{"找到锚点<br/>// TC001 STEP1 segment1?"}
    
    L -->|是| M["解析锚点格式<br/>提取TC_ID, STEP_ID, segment_ID"]
    L -->|否| N["记录无锚点文件<br/>files_without_anchors"]
    
    M --> O["YamlStubHandler.get_stub_code()<br/>查询YAML配置"]
    
    O --> P{"在YAML中找到<br/>对应桩代码?"}
    
    P -->|是| Q["添加到桩点列表<br/>记录插入行号和代码"]
    P -->|否| R["记录缺失锚点<br/>missing_anchors"]
    
    Q --> S["继续扫描下一行"]
    R --> S
    N --> T["尝试传统格式解析<br/>parse_traditional_format()"]
    
    T --> U["查找// TC001 STEP1:格式<br/>和code:字段"]
    
    U --> V{"找到传统格式?"}
    V -->|是| W["提取内嵌代码"]
    V -->|否| X["返回无桩点"]
    
    W --> Y["桩点按行号逆序排序<br/>从后往前插入"]
    S --> Y
    X --> AA["处理下一个文件"]
    
    Y --> Z["插入桩代码到文件<br/>• 计算缩进<br/>• 写入.stub文件"]
    
    Z --> AB["创建备份和结果目录<br/>• backup_YYYYMMDD_HHMMSS<br/>• stubbed_YYYYMMDD_HHMMSS"]
    
    AB --> AC["复制.stub文件到结果目录<br/>重命名为原文件名"]
    
    AC --> AA
    
    AA --> AD{"还有文件需要处理?"}
    AD -->|是| H
    AD -->|否| AE["生成处理统计报告<br/>• 总文件数<br/>• 处理文件数<br/>• 插入桩点数<br/>• 缺失桩点数"]
    
    AE --> AF["完成插桩处理"]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style O fill:#fff3e0
    style P fill:#e8f5e8
    style Q fill:#e8f5e8
    style R fill:#ffebee
    style AF fill:#e1f5fe'''
    
    return mermaid_content

def check_mermaid_cli():
    """检查是否安装了mermaid-cli"""
    try:
        result = subprocess.run(['mmdc', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"找到Mermaid CLI版本: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("未找到mermaid-cli，请先安装：")
        print("npm install -g @mermaid-js/mermaid-cli")
        return False

def generate_image_with_cli(mermaid_content, output_path):
    """使用mermaid-cli生成图片"""
    print("使用mermaid-cli生成图片...")
    
    # 创建临时mermaid文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
        f.write(mermaid_content)
        temp_mmd_path = f.name
    
    try:
        # 使用mmdc命令生成PNG图片
        cmd = [
            'mmdc',
            '-i', temp_mmd_path,
            '-o', output_path,
            '-t', 'default',
            '--width', '1400',
            '--height', '1000',
            '--backgroundColor', 'white'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"成功生成图片: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"生成图片失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_mmd_path)
        except:
            pass

def generate_image_with_kroki():
    """使用Kroki在线服务生成图片"""
    print("使用Kroki在线服务生成图片...")
    try:
        import requests
        import base64
        import zlib
        
        mermaid_content = create_mermaid_file()
        
        # 压缩和编码
        compressed = zlib.compress(mermaid_content.encode('utf-8'))
        encoded = base64.urlsafe_b64encode(compressed).decode('ascii')
        
        # 请求Kroki服务
        url = f"https://kroki.io/mermaid/png/{encoded}"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            output_path = "YAMLWeave插桩逻辑流程图.png"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"成功生成图片: {output_path}")
            return True
        else:
            print(f"请求失败，状态码: {response.status_code}")
            return False
            
    except ImportError:
        print("需要安装requests库: pip install requests")
        return False
    except Exception as e:
        print(f"生成图片失败: {e}")
        return False

def main():
    """主函数"""
    print("YAMLWeave插桩逻辑流程图生成器")
    print("=" * 50)
    
    # 获取项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    output_path = os.path.join(project_dir, "YAMLWeave插桩逻辑流程图.png")
    
    mermaid_content = create_mermaid_file()
    
    # 方法1：尝试使用mermaid-cli
    if check_mermaid_cli():
        if generate_image_with_cli(mermaid_content, output_path):
            return
    
    # 方法2：尝试使用在线服务
    print("\n尝试使用在线服务生成图片...")
    if generate_image_with_kroki():
        return
    
    # 方法3：提供替代方案
    print("\n无法自动生成图片，请尝试以下替代方案：")
    print("1. 安装mermaid-cli后重新运行：")
    print("   npm install -g @mermaid-js/mermaid-cli")
    print()
    print("2. 使用在线编辑器：")
    print("   访问 https://mermaid.live")
    print("   复制以下Mermaid代码并导出为PNG：")
    print("-" * 30)
    print(mermaid_content)
    print("-" * 30)
    print()
    print("3. 使用HTML文件：")
    print("   在浏览器中打开 插桩逻辑流程图.html")
    print("   右键流程图选择'将图像另存为'")

if __name__ == "__main__":
    main() 