#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import sys
import argparse
from collections import defaultdict
from pathlib import Path

def convert_model(diff_file_path):
    """
    根据差异文件生成目标型号的JSON文件
    
    Args:
        diff_file_path: 差异文件路径，如 TA0033-00-20-5WP_to_TA0033-0U-30-5WP.json
        
    Returns:
        dict: {'success': bool, 'missing_files': list}
    """
    # 初始化操作统计
    stats = {
        '替换': 0,
        '删除': 0,
        '新增': 0,
        '未找到': [],
    }
    
    # 加载配置
    config = {
        "base_dir_name": "data",
        "base_model_dir": "processed/bom/TA",
        "parts_db_file": "all.json",
        "output_dir": "output",
        "file_extension": ".json",
        "new_part_type": "新增"
    }
    
    # 根据型号设置输出目录
    model_output_dirs = {
        'TA': 'processed/bom/TA',
        'SP': 'processed/bom/SP'
    }
    
    for model, model_dir in model_output_dirs.items():
        if model in diff_file_path:
            config['base_model_dir'] = model_dir
            config['output_dir'] = model_dir
            break
    
    # 获取项目根目录 (sbom_web)
    base_dir = Path(__file__).resolve().parents[3]
    if config["base_dir_name"]:
        # 如果base_dir_name是绝对路径，直接使用它
        if os.path.isabs(config["base_dir_name"]):
            base_dir = config["base_dir_name"]
        else:
            base_dir = os.path.join(base_dir, config["base_dir_name"])
    
    # 打印路径信息以便调试
    # print(f"基础路径: {base_dir}")
    # print(f"基础型号目录: {config['base_model_dir']}")
    # print(f"文件扩展名: {config['file_extension']}")
    # print(f"零件表路径: {os.path.join(base_dir, config['parts_db_file'])}")
    # print(f"输出目录: {config['output_dir']}")
    # print()
    
    # 1. 读取差异文件
    try:
        with open(diff_file_path, 'r', encoding='utf-8') as f:
            diff_data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取差异文件 {diff_file_path}，原因：{str(e)}")
        return {'success': False, 'missing_files': []}
    
    # 2. 提取基础型号和目标型号
    base_model = diff_data.get('base_bom_model')
    target_model = diff_data.get('target_bom_model')
    
    if not base_model or not target_model:
        print("错误：差异文件中未找到基础型号或目标型号")
        return {'success': False, 'missing_files': []}
    
    # 3. 在配置的基础型号目录下查找基础型号文件
    base_file_path = os.path.join(base_dir, config["base_model_dir"], f"{base_model}{config['file_extension']}")
    
    # 如果文件不存在，尝试使用.txt扩展名
    if not os.path.exists(base_file_path) and config['file_extension'] != '.txt':
        alt_file_path = os.path.join(base_dir, config["base_model_dir"], f"{base_model}.txt")
        if os.path.exists(alt_file_path):
            print(f"使用替代文件路径: {alt_file_path}")
            base_file_path = alt_file_path
    
    if not os.path.exists(base_file_path):
        print(f"错误：未找到基础型号文件 {base_file_path}")
        return {'success': False, 'missing_files': [base_file_path]}
    
    # 4. 读取基础型号文件
    try:
        with open(base_file_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取基础型号文件 {base_file_path}，原因：{str(e)}")
        return {'success': False, 'missing_files': [base_file_path]}
    
    # 5. 预处理差异文件，创建查找映射
    replacement_map = {}
    target_parts_info = {}  # 存储目标部件的详细信息
    
    for item in diff_data.get('items', []):
        base_part = item.get('base_bom', {}).get('MPART.NO')
        target_part = item.get('target_bom', {})
        target_part_no = target_part.get('MPART.NO')
        
        if base_part and target_part_no:
            if target_part_no == "/":
                replacement_map[base_part] = None
                stats['删除'] += 1
            else:
                replacement_map[base_part] = target_part_no
                target_parts_info[target_part_no] = target_part
                stats['替换'] += 1
    
    # 6. 读取零件表（只读取一次）
    parts_db = {}
    parts_db_path = os.path.join(base_dir, config["parts_db_file"])
    if os.path.exists(parts_db_path):
        try:
            with open(parts_db_path, 'r', encoding='utf-8') as f:
                parts_db_raw = json.load(f)
                
            # 将零件表转换为以部件号为键的字典，加速查找
            for category, parts in parts_db_raw.items():
                for part in parts:
                    part_no = part.get('MPART.NO')
                    if part_no:
                        parts_db[part_no] = part
        except Exception as e:
            print(f"警告：读取零件表时出错：{str(e)}")
    
    # 7. 根据映射关系修改基础数据
    new_data = defaultdict(list)
    all_base_parts = set()
    
    for category, parts in base_data.items():
        for part in parts:
            part_no = part.get('MPART.NO')
            all_base_parts.add(part_no)
            
            if part_no in replacement_map:
                if replacement_map[part_no] is None:
                    # 如果映射为None，跳过该部件（删除）
                    continue
                
                # 创建新部件，替换部件号
                new_part = part.copy()
                new_part_no = replacement_map[part_no]
                new_part['MPART.NO'] = new_part_no
                
                # 从零件表中查找新部件的详细信息
                if new_part_no in parts_db:
                    db_part = parts_db[new_part_no]
                    new_part['MPART.NAME'] = db_part.get('MPART.NAME', new_part.get('MPART.NAME', ''))
                    new_part['MBOM.BNUM'] = db_part.get('MBOM.BNUM', new_part.get('MBOM.BNUM', 1))
                    new_part['MPART.WLSX'] = db_part.get('MPART.WLSX', new_part.get('MPART.WLSX', ''))
                # 如果在零件表中没有找到，使用差异文件中的信息
                elif new_part_no in target_parts_info:
                    target_part = target_parts_info[new_part_no]
                    new_part['MPART.NAME'] = target_part.get('MPART.NAME', part.get('MPART.NAME', ''))
                    new_part['MBOM.BNUM'] = target_part.get('MBOM.BNUM', part.get('MBOM.BNUM', 1))
                    new_part['MPART.WLSX'] = config["new_part_type"]
                
                # 确定类别（可能与原类别不同）
                new_category = category
                if '-' in new_part_no:
                    potential_category = new_part_no.split('-')[0]
                    if potential_category:
                        new_category = potential_category
                
                new_data[new_category].append(new_part)
            else:
                # 如果没有映射关系，保持原样
                new_data[category].append(part)
    
    # 8. 添加差异文件中新增的部件
    for item in diff_data.get('items', []):
        base_part = item.get('base_bom', {})
        target_part = item.get('target_bom', {})
        
        # 如果基础部件为 "/"，且目标部件不为 "/"，表示需要添加新部件
        if base_part.get('MPART.NO') == "/" and target_part.get('MPART.NO') != "/":
            part_no = target_part.get('MPART.NO')
            if part_no:
                # 提取类别（部件号的前缀）
                category = part_no.split('-')[0] if '-' in part_no else part_no
                
                # 创建新部件
                new_part = {
                    'MPART.NO': part_no,
                    'MPART.NAME': target_part.get('MPART.NAME', ''),
                    'MBOM.BNUM': int(target_part.get('MBOM.BNUM', 1)) if target_part.get('MBOM.BNUM', '').isdigit() else target_part.get('MBOM.BNUM', 1),
                    'MPART.WLSX': config["new_part_type"]  
                }
                
                # 添加到相应类别
                new_data[category].append(new_part)
                stats['新增'] += 1
    
    # 9. 生成目标型号文件
    # 如果输出目录是绝对路径，直接使用它
    if os.path.isabs(config["output_dir"]):
        target_file_path = os.path.join(config["output_dir"], f"{target_model}{config['file_extension']}")
    else:
        target_file_path = os.path.join(base_dir, config["output_dir"], f"{target_model}{config['file_extension']}")
    
    print(f"目标型号文件路径: {target_file_path}")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
    
    try:
        with open(target_file_path, 'w', encoding='utf-8') as f:
            # 转换defaultdict为普通dict
            json.dump(dict(new_data), f, ensure_ascii=False, indent=4)
        print(f"成功生成目标型号文件：{target_file_path}")
        
        # 检查差异文件中的基础部件是否都在原始文件中找到
        for item in diff_data.get('items', []):
            base_part_no = item.get('base_bom', {}).get('MPART.NO')
            if base_part_no and base_part_no != "/" and base_part_no not in all_base_parts:
                stats['未找到'].append(base_part_no)
        
        # 输出操作统计
        print(f"\n操作统计：")
        print(f"  替换部件: {stats['替换']} 个")
        print(f"  删除部件: {stats['删除']} 个")
        print(f"  新增部件: {stats['新增']} 个")
        if stats['未找到']:
            print(f"  未在原始文件中找到的部件: {len(stats['未找到'])} 个")
            for part_no in stats['未找到']:
                print(f"    - {part_no}")
        else:
            print(f"  所有基础部件都在原始文件中找到")
        
        return {'success': True, 'missing_files': []}
    except Exception as e:
        print(f"错误：无法写入目标型号文件 {target_file_path}，原因：{str(e)}")
        return {'success': False, 'missing_files': []}

def generate_js_data(diff_file_path):
    """
    生成JavaScript格式的BOM变更数据
    
    Args:
        diff_file_path: 差异文件路径
        
    Returns:
        list: JavaScript格式的数据数组
    """
    config = {
        "base_dir_name": "data",
        "base_model_dir": "processed\TA\\bom",
        "parts_db_file": "all.json",
        "output_dir": "output",
        "file_extension": ".json",
        "new_part_type": "新增"
    }
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if config["base_dir_name"] and os.path.isabs(config["base_dir_name"]):
        base_dir = config["base_dir_name"]
    elif config["base_dir_name"]:
        base_dir = os.path.join(base_dir, config["base_dir_name"])
    
    # 读取差异文件
    try:
        with open(diff_file_path, 'r', encoding='utf-8') as f:
            diff_data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取差异文件 {diff_file_path}")
        return []
    
    # 读取基础型号文件
    base_model = diff_data.get('base_bom_model')
    if not base_model:
        return []
    
    base_file_path = os.path.join(base_dir, config["base_model_dir"], f"{base_model}{config['file_extension']}")
    if not os.path.exists(base_file_path) and config['file_extension'] != '.txt':
        alt_file_path = os.path.join(base_dir, config["base_model_dir"], f"{base_model}.txt")
        if os.path.exists(alt_file_path):
            base_file_path = alt_file_path
    
    try:
        with open(base_file_path, 'r', encoding='utf-8') as f:
            base_data = json.load(f)
    except Exception:
        return []
    
    # 读取零件表
    parts_db = {}
    parts_db_path = os.path.join(base_dir, config["parts_db_file"])
    if os.path.exists(parts_db_path):
        try:
            with open(parts_db_path, 'r', encoding='utf-8') as f:
                parts_db_raw = json.load(f)
            for category, parts in parts_db_raw.items():
                for part in parts:
                    part_no = part.get('MPART.NO')
                    if part_no:
                        parts_db[part_no] = part
        except Exception:
            pass
    
    # 创建基础部件映射
    base_parts_map = {}
    for category, parts in base_data.items():
        for part in parts:
            part_no = part.get('MPART.NO')
            if part_no:
                base_parts_map[part_no] = part
    
    js_data = []
    processed_parts = set()
    
    # 处理差异文件中的变更
    for item in diff_data.get('items', []):
        base_part = item.get('base_bom', {})
        target_part = item.get('target_bom', {})
        base_part_no = base_part.get('MPART.NO')
        target_part_no = target_part.get('MPART.NO')
        
        if base_part_no == "/" and target_part_no != "/":
            # 新增
            name = target_part.get('MPART.NAME', '')
            if target_part_no in parts_db:
                name = parts_db[target_part_no].get('MPART.NAME', name)
            
            js_data.append({
                'name': name,
                'status': '新增',
                'basePartNo': '',
                'baseQty': '',
                'genPartNo': target_part_no,
                'genQty': str(target_part.get('MBOM.BNUM', '1'))
            })
            processed_parts.add(target_part_no)
            
        elif base_part_no != "/" and target_part_no == "/":
            # 删除
            base_info = base_parts_map.get(base_part_no, {})
            js_data.append({
                'name': base_info.get('MPART.NAME', ''),
                'status': '删除',
                'basePartNo': base_part_no,
                'baseQty': str(base_info.get('MBOM.BNUM', '1')),
                'genPartNo': '',
                'genQty': ''
            })
            processed_parts.add(base_part_no)
            
        elif base_part_no != "/" and target_part_no != "/" and base_part_no != target_part_no:
            # 替换
            base_info = base_parts_map.get(base_part_no, {})
            name = target_part.get('MPART.NAME', base_info.get('MPART.NAME', ''))
            if target_part_no in parts_db:
                name = parts_db[target_part_no].get('MPART.NAME', name)
            
            js_data.append({
                'name': name,
                'status': '替换',
                'basePartNo': base_part_no,
                'baseQty': str(base_info.get('MBOM.BNUM', '1')),
                'genPartNo': target_part_no,
                'genQty': str(target_part.get('MBOM.BNUM', base_info.get('MBOM.BNUM', '1')))
            })
            processed_parts.add(base_part_no)
            processed_parts.add(target_part_no)
    
    # 添加不变的部件
    for part_no, part_info in base_parts_map.items():
        if part_no not in processed_parts:
            js_data.append({
                'name': part_info.get('MPART.NAME', ''),
                'status': '不变',
                'basePartNo': part_no,
                'baseQty': str(part_info.get('MBOM.BNUM', '1')),
                'genPartNo': part_no,
                'genQty': str(part_info.get('MBOM.BNUM', '1'))
            })
    
    return js_data

def main():
    # parser = argparse.ArgumentParser(description='根据差异文件生成目标型号的JSON文件')
    # parser.add_argument('diff_file', help='差异文件路径，如 TA0033-00-20-5WP_to_TA0033-0U-30-5WP.json')
    # parser.add_argument('--config', '-c', help='指定配置文件路径，默认使用项目根目录下的config.json')
    # parser.add_argument('--js-data', action='store_true', help='生成JavaScript格式的数据并输出到控制台')
    
    # args = parser.parse_args()
    
    diff_file = "d:/code/sbom/release/sbom_web/data/processed/diff/TA/TA0033-00-20-5WP_to_TA0033-0U-30-5WP.json"
    # if args.js_data:
    #     js_data = generate_js_data(args.diff_file)
    #     print("\nconst sampleData = [")
    #     for i, item in enumerate(js_data):
    #         comma = ',' if i < len(js_data) - 1 else ''
    #         print(f"    {{ name: '{item['name']}', status: '{item['status']}', basePartNo: '{item['basePartNo']}', baseQty: '{item['baseQty']}', genPartNo: '{item['genPartNo']}', genQty: '{item['genQty']}' }}{comma}")
    #     print("];")
    # else:
    convert_model(diff_file)

if __name__ == '__main__':
    main()
