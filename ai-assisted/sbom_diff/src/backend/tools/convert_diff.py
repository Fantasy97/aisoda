import pandas as pd
import json
import os
import sys
from pathlib import Path

# BOM表格配置参数
BOM_CONFIG = {
    "sheet_keywords": ["BOM差异", "差异BOM"],
    "data_start_row": 3,  # 数据开始行（索引从0开始）
    "product_model_cell": (0, 0),  # 产品型号所在单元格(行,列)
    "base_bom_cell": (1, 1),  # 基准BOM所在单元格
    "target_bom_cell": (1, 7),  # 目标BOM所在单元格
    "base_bom_columns": {  # 基准BOM各字段所在列
        "MPART.NO": 1,
        "MPART.NAME": 0,
        "MBOM.BNUM": 4,
        "MBOM.SCGX": 5
    },
    "target_bom_columns": {  # 目标BOM各字段所在列
        "MPART.NO": 7,
        "MPART.NAME": 0,
        "MBOM.BNUM": 10,
        "MBOM.SCGX": 11
    },
    "description_column": 0  # 描述所在列
}

def excel_to_json(excel_file, config=BOM_CONFIG):
    """读取Excel文件中的BOM差异表并转换为JSON"""
    
    diff_output_dirs = {
        'TA': 'data/processed/diff/TA',
        'SP': 'data/processed/diff/SP'
    }
    
    for model, model_dir in diff_output_dirs.items():
        if model in excel_file:
            base_dir = Path(__file__).resolve().parents[3]
            output_path = base_dir / model_dir
            break
    
    try:
        # 读取所有sheet名称
        xls = pd.ExcelFile(excel_file)
        sheet_names = xls.sheet_names
        
        # 查找包含关键词的sheet
        target_sheet = None
        for sheet in sheet_names:
            if any(keyword in sheet for keyword in config["sheet_keywords"]):
                target_sheet = sheet
                break
        
        if not target_sheet:
            print(f"未找到BOM差异表sheet: {excel_file}")
            return None
            
        # 读取目标sheet
        df = pd.read_excel(excel_file, sheet_name=target_sheet, header=None)
        
        # 提取产品型号
        row, col = config["product_model_cell"]
        
        # 提取数据
        base_row, base_col = config["base_bom_cell"]
        target_row, target_col = config["target_bom_cell"]
        
        data = {
            "base_bom_model": str(df.iloc[base_row, base_col]).split("（")[0].strip(),
            "target_bom_model": str(df.iloc[target_row, target_col]).split("（")[0].strip(),
            "items": []
        }
        
        # 从配置的行开始提取物料数据
        for i in range(config["data_start_row"], len(df)):
            # 如果遇到空行或"差异BOM清单"行，停止处理
            desc_col = config["description_column"]
            if pd.isna(df.iloc[i, desc_col]) or "差异BOM清单" in str(df.iloc[i, desc_col]) or "子阶BOM建立" in str(df.iloc[i, desc_col]):
                break
                
            # 提取描述
            description = str(df.iloc[i, desc_col]) if not pd.isna(df.iloc[i, desc_col]) else ""
            
            # 跳过空行
            if description == "":
                continue
                
            # 构建物料项
            item = {
                "base_bom": {},
                "target_bom": {}
            }
            
            # 填充基准BOM数据
            for field, col in config["base_bom_columns"].items():
                item["base_bom"][field] = str(df.iloc[i, col]) if not pd.isna(df.iloc[i, col]) else ""
                
            # 填充目标BOM数据
            for field, col in config["target_bom_columns"].items():
                item["target_bom"][field] = str(df.iloc[i, col]) if not pd.isna(df.iloc[i, col]) else ""
                
            data["items"].append(item)
        
        if data and data.get("items"):
            table_name = data["base_bom_model"] + "_to_" + data["target_bom_model"]
            
            # 保存为JSON文件
            output_file = output_path / (table_name + ".json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"处理完成，结果已保存到 {output_file}")
            return table_name
        
        return None
    except Exception as e:
        print(f"处理文件 {excel_file} 时出错: {e}")
        return None

def process_directory(input_dir, output_dir, config=BOM_CONFIG):
    """处理目录中的所有Excel文件"""
    results = {}
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.xls') or file.endswith('.xlsx'):
                file_path = os.path.join(root, file)
                print(f"处理文件: {file}")
                
                data = excel_to_json(file_path, config)
                if data:
                    table_name = data["base_bom_model"] + "_to_" + data["target_bom_model"]
                    results[table_name] = data
                    
                    # 保存为JSON文件
                    output_file = output_path / (table_name + ".json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"处理完成，结果已保存到 {output_file}")
    
    return results

def main():
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = r"D:\code\sbom\data\差异库\原始\金牛差异表\TA0033-0U-30-5WP BOM建立申请单_V1.5.xls"
    
    # output_path = Path(r"D:\code\sbom\data\差异库\diff\diff_SP")
    # output_path.mkdir(parents=True, exist_ok=True)
    # output_file = output_path / "diff_SP.json"
    
    # if os.path.isdir(input_path):
    #     results = process_directory(input_path, output_path)
    # else:
        results = {Path(input_path).name: excel_to_json(input_path)}
    
    # 保存为JSON文件
    # with open(output_file, 'w', encoding='utf-8') as f:
    #     json.dump(results, f, ensure_ascii=False, indent=2)
    
    # print(f"处理完成，结果已保存到 {output_file}")

if __name__ == "__main__":
    main()