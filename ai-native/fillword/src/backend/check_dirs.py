#!/usr/bin/env python3
"""
检查目录结构脚本
"""

import os
from pathlib import Path

def check_directories():
    """检查项目目录结构"""
    print("🔍 检查项目目录结构")
    print("=" * 40)
    
    # 当前目录
    current_dir = Path.cwd()
    print(f"📁 当前目录: {current_dir}")
    
    # 检查相对路径
    paths_to_check = [
        "../../data/input",
        "../../data/processed", 
        "../../data/output",
        "tools/config.json",
        "tools/example_data.json"
    ]
    
    for path in paths_to_check:
        full_path = Path(path).resolve()
        exists = full_path.exists()
        status = "✅" if exists else "❌"
        print(f"{status} {path} -> {full_path}")
        
        # 如果是目录且存在，列出内容
        if exists and full_path.is_dir():
            try:
                files = list(full_path.iterdir())
                if files:
                    print(f"   📄 包含 {len(files)} 个文件/目录")
                    for file in files[:5]:  # 只显示前5个
                        print(f"      - {file.name}")
                    if len(files) > 5:
                        print(f"      ... 还有 {len(files) - 5} 个文件")
                else:
                    print("   📄 空目录")
            except PermissionError:
                print("   ❌ 无权限访问")
    
    print("\n🎯 目录用途说明:")
    print("   - data/input: 上传的输入文件（Word文档）")
    print("   - data/processed: 中间处理文件（JSON数据）")
    print("   - data/output: 最终输出文件（Word文档、HTML报告）")

if __name__ == '__main__':
    check_directories()