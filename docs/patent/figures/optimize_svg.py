#!/usr/bin/env python3
"""
SVG线条连接优化脚本
优化PlantUML生成的SVG图中线条连接不完整的问题
"""

import re
import sys

def optimize_svg_lines(svg_content):
    """
    优化SVG中的线条连接

    主要优化:
    1. 添加 shape-rendering="geometricPrecision" 提高渲染精度
    2. 为所有line元素添加 stroke-linecap="round" 和 stroke-linejoin="round"
    3. 为所有polygon添加 stroke-linejoin="miter" 确保箭头完整连接
    """

    # 1. 确保SVG根元素有 shape-rendering 属性
    if 'shape-rendering="geometricPrecision"' not in svg_content:
        svg_content = re.sub(
            r'(<svg[^>]*)(>)',
            r'\1 shape-rendering="geometricPrecision"\2',
            svg_content,
            count=1
        )

    # 2. 优化所有line元素 - 添加圆角端点和连接
    def enhance_line(match):
        line_tag = match.group(0)
        if 'stroke-linecap' not in line_tag:
            line_tag = line_tag.replace(
                'style="stroke:#181818;stroke-width:1;"',
                'style="stroke:#181818;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round;"'
            )
        return line_tag

    svg_content = re.sub(
        r'<line[^>]*style="stroke:#181818;stroke-width:1;"[^>]*/>',
        enhance_line,
        svg_content
    )

    # 3. 优化所有polygon箭头 - 添加miter连接确保尖角完整
    def enhance_polygon(match):
        polygon_tag = match.group(0)
        if 'stroke-linejoin' not in polygon_tag:
            polygon_tag = polygon_tag.replace(
                'style="stroke:#181818;stroke-width:1;"',
                'style="stroke:#181818;stroke-width:1;stroke-linejoin:miter;"'
            )
        return polygon_tag

    svg_content = re.sub(
        r'<polygon[^>]*fill="#181818"[^>]*style="stroke:#181818;stroke-width:1;"[^>]*/>',
        enhance_polygon,
        svg_content
    )

    return svg_content


if __name__ == '__main__':
    input_file = '/Users/fistclark/Desktop/YAMLWeave/docs/patent/figures/svg/fig02_anchor_identification_process.svg'

    # 读取SVG文件
    with open(input_file, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # 优化SVG
    optimized_content = optimize_svg_lines(svg_content)

    # 写回文件
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(optimized_content)

    print(f"✓ SVG优化完成: {input_file}")
    print("主要改进:")
    print("  - 添加了 shape-rendering='geometricPrecision' 提高渲染精度")
    print("  - 所有连接线使用圆角端点 (stroke-linecap:round)")
    print("  - 所有连接线使用圆角连接 (stroke-linejoin:round)")
    print("  - 所有箭头使用尖角连接 (stroke-linejoin:miter)")
