#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Excel解析器
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src" / "backend"))

from tools.excel_parser import ExcelParser


def test_excel_parser():
    """测试Excel解析功能"""
    parser = ExcelParser()
    
    # 测试文件路径
    test_file = project_root / "tmp" / "EHS适用法律法规及其他要求清单-2025.4.11更新.xlsx"
    
    print("=" * 60)
    print("Excel解析器测试")
    print("=" * 60)
    print(f"测试文件: {test_file}")
    print()
    
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return
    
    # 测试解析
    print("开始解析Excel文件...")
    result = parser.parse_excel_to_law_format(str(test_file))
    
    if result['success']:
        print(f"✓ 解析成功!")
        print(f"  工作表名称: {result['sheet_name']}")
        print(f"  数据行数: {result['total_count']}")
        print(f"  错误数: {result['error_count']}")
        
        if result['errors']:
            print(f"\n错误列表:")
            for error in result['errors'][:5]:  # 只显示前5个错误
                print(f"  - {error}")
        
        if result['data']:
            print(f"\n前5条数据预览:")
            for i, law in enumerate(result['data'][:5], 1):
                print(f"\n  [{i}] {law['法律、法规、标准及其他要求']}")
                print(f"      施行日期: {law['施行（修改）日期']}")
                print(f"      获取途径: {law['获取途径']}")
    else:
        print(f"✗ 解析失败: {result['error']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_excel_parser()
