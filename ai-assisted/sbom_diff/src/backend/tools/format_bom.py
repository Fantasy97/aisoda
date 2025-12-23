import json
import pandas as pd

def json_to_excel(json_file_path, output_excel_path=None):
    """
    将JSON文件转换为Excel文件，只保留MPART.NO和MBOM.BNUM两列
    """
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取所有项目的数据
    all_items = []
    for category, items in data.items():
        if isinstance(items, list):
            for item in items:
                all_items.append({
                    'MPART.NO': item.get('MPART.NO', ''),
                    'MBOM.BNUM': item.get('MBOM.BNUM', '')
                })
    
    # 创建DataFrame
    df = pd.DataFrame(all_items)
    
    # 如果没有指定输出路径，使用临时文件
    if output_excel_path is None:
        import tempfile
        import os
        temp_dir = tempfile.gettempdir()
        filename = os.path.basename(json_file_path).replace('.json', '.xlsx')
        output_excel_path = os.path.join(temp_dir, filename)
    elif not output_excel_path.endswith('.xlsx'):
        output_excel_path += '.xlsx'
    
    # 保存为Excel文件
    df.to_excel(output_excel_path, index=False, engine='openpyxl')
    print(f"转换完成！Excel文件已保存到: {output_excel_path}")
    return output_excel_path

if __name__ == "__main__":
    # 使用示例
    json_file = "D:\code\sbom\\release\sbom_web\data\processed\\bom\SP\SP0005-78-03-33P.json"
    output_file = "D:\code\sbom\\release\sbom_web\data\output\SP0005-78-03-33P.xlsx"
    
    try:
        json_to_excel(json_file, output_file)
    except Exception as e:
        print(f"转换失败: {e}")