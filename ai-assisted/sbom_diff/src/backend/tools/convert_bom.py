import pandas as pd
import json
import argparse
import os
from pathlib import Path

def group_parts_by_first_prefix(input_file, start_sheet=0):
    
    bom_output_dirs = {
        '金牛': 'data/processed/bom/TA',
        '时珍': 'data/processed/bom/SP'
    }
    
    for model, model_dir in bom_output_dirs.items():
        if model in input_file:
            base_dir = Path(__file__).resolve().parents[3]
            output_dir = base_dir / model_dir
            break

    # 读取Excel文件中的所有工作表名称
    xls = pd.ExcelFile(input_file, engine='openpyxl')
    all_sheets = xls.sheet_names
    
    # 从指定的sheet开始处理
    for sheet in all_sheets[start_sheet:]:
            
        # 读取当前工作表的数据
        df = pd.read_excel(xls, sheet_name=sheet)

        # 确保只保留你需要的列
        df = df[['MPART.NO', 'MPART.NAME', 'MBOM.BNUM', 'MPART.WLSX']]

        # 创建分组字典
        grouped = {}

        for _, row in df.iterrows():
            part_no = row['MPART.NO']
            part_name = row['MPART.NAME']
            part_bnum = row['MBOM.BNUM']
            part_wlsx = row['MPART.WLSX']

            # 按第一个 '-' 分割，取第一部分
            prefix = part_no.split('-')[0]

            # 构造要保存的数据项
            item = {
                "MPART.NO": part_no,
                "MPART.NAME": part_name,
                "MBOM.BNUM": part_bnum,
                "MPART.WLSX": part_wlsx
            }

            # 放入对应的组中
            if prefix not in grouped:
                grouped[prefix] = []
            grouped[prefix].append(item)

        # 写入JSON文件
        output_file = output_dir / (sheet + ".json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(grouped, f, ensure_ascii=False, indent=4)

        print(f"✅ 已按第一个 '-' 前缀分组并保存到: {output_file}")
    
    return True
        

def main():
    # if len(sys.argv) < 2:
    #     print("用法: python convert_bom.py <Excel文件路径> [输出目录] [起始表索引]")
    #     print("示例1: python convert_bom.py input.xlsx  # 输出到当前目录")
    #     print("示例2: python convert_bom.py input.xlsx output  # 输出到output目录")
    #     print("示例3: python convert_bom.py input.xlsx output 2  # 从第3个表开始处理")
    #     return
    
    input_file = "D:\code\sbom\data\\bom库\原始\金牛.xlsx"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"错误：输入文件 {input_file} 不存在")
        return
    
    start_sheet = 3
    group_parts_by_first_prefix(input_file, start_sheet=start_sheet)

if __name__ == "__main__":
    import sys
    main()