#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI分析JSON数据生成器
支持接口调用和CLI工具两种模式
"""

import sys
import os
import json
import logging
from collections import defaultdict
from datetime import datetime

# 添加父目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))
try:
    from db_query import get_connection
except ImportError:
    # 如果无法导入数据库模块，提供一个模拟函数
    def get_connection():
        logger.warning("数据库连接模块未找到，使用模拟数据")
        return None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_ai_analysis_for_model(model_name):
    """
    为指定型号生成AI分析JSON数据
    
    Args:
        model_name: 型号名称，如 'SP0030-3Q-23-5QP'
        
    Returns:
        dict: AI分析格式的JSON数据
    """
    logger.info(f"开始生成型号 {model_name} 的AI分析数据")
    
    # 查询BOM数据
    bom_data = query_hierarchical_bom(model_name)
    if not bom_data:
        logger.error(f"未找到型号 {model_name} 的BOM数据")
        return None
    
    # 构建AI分析JSON结构
    ai_analysis = {
        "MODEL": model_name,
        "DESC": generate_model_description(model_name),
        "MPART": bom_data
    }
    
    return ai_analysis

def query_hierarchical_bom(model_name):
    """
    查询层级BOM数据
    
    Args:
        model_name: 型号名称
        
    Returns:
        dict: 按分类分组的层级BOM数据
    """
    connection = get_connection()
    if not connection:
        logger.error("数据库连接失败，返回示例数据")
        return create_sample_bom_data_for_model(model_name)
    
    try:
        import pymysql
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. 先查询该型号的level概况
            level_sql = """
            SELECT DISTINCT level 
            FROM mfg_bom 
            WHERE product_item_no = %s 
            ORDER BY level
            """
            cursor.execute(level_sql, (model_name,))
            level_results = cursor.fetchall()
            
            if not level_results:
                logger.warning(f"未找到型号 {model_name} 的BOM数据")
                return None
            
            levels = [int(row['level']) for row in level_results if row['level'] is not None]
            max_level = max(levels) if levels else 0
            
            logger.info(f"型号 {model_name} 包含层级: {levels}, 最大层级: {max_level}")
            
            # 2. 按层级逐层查询并构建结构
            return query_by_levels(cursor, model_name, levels)
            
    except Exception as e:
        logger.error(f"查询BOM数据失败: {e}")
        return None
    finally:
        connection.close()

def query_by_levels(cursor, model_name, levels):
    """
    按层级逐层查询并构建BOM结构
    
    Args:
        cursor: 数据库游标
        model_name: 型号名称
        levels: 层级列表
        
    Returns:
        dict: 按分类分组的层级BOM数据
    """
    all_parts = {}  # 存储所有零件 {part_no: part_data}
    part_id_counter = 1
    
    # 按层级从0开始逐层查询
    for level in sorted(levels):
        logger.info(f"查询层级 {level} 的零件...")
        
        level_sql = """
        SELECT item_no_c, item_name_c, qty, item_cls_c, 
               level, op, item_no_p, product_item_no
        FROM mfg_bom 
        WHERE product_item_no = %s AND level = %s AND item_type_c = '标准件'
        ORDER BY item_no_c
        """
        
        cursor.execute(level_sql, (model_name, str(level)))
        level_results = cursor.fetchall()
        
        logger.info(f"  层级 {level} 找到 {len(level_results)} 个零件")
        
        # 处理当前层级的零件
        for row in level_results:
            part_no = row['item_no_c']
            if not part_no:
                continue
            
            parent_no = row.get('item_no_p', '') or model_name
            
            # 创建唯一的零件实例ID (零件编号 + 父件编号 + 层级)
            unique_key = f"{part_no}_{parent_no}_{level}"
            
            # 检查是否已存在相同的零件实例
            if unique_key in all_parts:
                # 如果已存在，累加数量
                existing_part = all_parts[unique_key]
                current_qty = float(row['qty']) if row['qty'] else 0.0
                existing_part['MPART.BNUM'] += current_qty
                logger.info(f"    发现重复零件 {part_no}，数量累加: {existing_part['MPART.BNUM'] - current_qty} + {current_qty} = {existing_part['MPART.BNUM']}")
            else:
                # 如果不存在，创建新记录
                part_data = {
                    'MPART.NO': part_no,
                    'MPART.NAME': row['item_name_c'] or '',
                    'MPART.BNUM': float(row['qty']) if row['qty'] else 0.0,
                    'MPART.MFG': row['item_cls_c'] or '',
                    'MPART.LVL': int(level),
                    'MPART.PRNT': parent_no,
                    'MPART.OP': row['op'] or '',
                    'MPART.ID': part_id_counter,
                    'MPART.DESC': generate_part_description(part_no, row['item_name_c']),
                    'children': []
                }
                
                all_parts[unique_key] = part_data
                part_id_counter += 1
            
            # 如果不是顶级零件(level=0)，将其添加到父件的children中
            if level > 0:
                # 查找父件的所有可能实例
                parent_found = False
                for parent_key, parent_part in all_parts.items():
                    if parent_part['MPART.NO'] == parent_no:
                        parent_part['children'].append(part_data)
                        parent_found = True
                        logger.debug(f"    将 {part_no} 添加到父件 {parent_no} 的children中")
                        break
                
                if not parent_found:
                    logger.warning(f"    零件 {part_no} 的父件 {parent_no} 未找到")
    
    # 3. 按分类分组顶级零件（level=0的零件）
    grouped_data = defaultdict(list)
    level_0_parts = [part for part in all_parts.values() if part['MPART.LVL'] == 0]
    
    for part_data in level_0_parts:
        category = extract_category(part_data['MPART.NO'])
        grouped_data[category].append(part_data)
    
    # 统计信息
    total_parts = len(all_parts)
    total_with_children = sum(1 for part in all_parts.values() if part['children'])
    
    logger.info(f"构建层级结构完成:")
    logger.info(f"  总零件数: {total_parts}")
    logger.info(f"  顶级零件数: {len(level_0_parts)}")
    logger.info(f"  顶级分类: {len(grouped_data)}")
    logger.info(f"  有子件的零件: {total_with_children}")
    
    for category, parts in grouped_data.items():
        parts_with_children = sum(1 for part in parts if part['children'])
        total_children = sum(count_all_children(part) for part in parts)
        logger.info(f"  分类 {category}: {len(parts)} 个顶级零件，{parts_with_children} 个有直接子件，总子件数 {total_children}")
    
    return dict(grouped_data)

def count_all_children(part):
    """
    递归计算零件的所有子件数量
    
    Args:
        part: 零件数据
        
    Returns:
        int: 子件总数
    """
    count = len(part.get('children', []))
    for child in part.get('children', []):
        count += count_all_children(child)
    return count



def extract_category(part_no):
    """
    从零件编号中提取分类
    
    Args:
        part_no: 零件编号
        
    Returns:
        str: 分类名称
    """
    if not part_no:
        return 'UNKNOWN'
    
    # 处理常见的零件编号格式
    if '-' in part_no:
        parts = part_no.split('-')
        if parts[0].isdigit() and len(parts[0]) == 3:
            return parts[0]
    
    # 如果没有标准格式，尝试提取前缀
    import re
    match = re.match(r'^([A-Z]*\d+)', part_no)
    if match:
        return match.group(1)
    
    # 默认返回前6个字符作为分类
    return part_no[:6] if len(part_no) > 6 else part_no

def generate_model_description(model_name):
    """
    根据型号名称生成描述
    
    Args:
        model_name: 型号名称
        
    Returns:
        list: 描述列表
    """
    descriptions = []
    
    # 根据型号前缀生成基础描述
    if model_name.startswith('SP'):
        if '30' in model_name:
            descriptions.append("30K三相并网逆变器")
        elif '20' in model_name:
            descriptions.append("20K三相并网逆变器")
        elif '15' in model_name:
            descriptions.append("15K三相并网逆变器")
        else:
            descriptions.append("三相并网逆变器")
    elif model_name.startswith('TA'):
        descriptions.append("单相并网逆变器")
    elif model_name.startswith('HSP'):
        descriptions.append("混合储能逆变器")
    else:
        descriptions.append("逆变器产品")
    
    # 添加技术特征描述
    if 'Q' in model_name:
        descriptions.append("高效能版本")
    if 'P' in model_name:
        descriptions.append("标准版本")
    
    return descriptions

def generate_part_description(part_no, part_name):
    """
    生成零件描述
    
    Args:
        part_no: 零件编号
        part_name: 零件名称
        
    Returns:
        list: 描述列表
    """
    descriptions = []
    
    # 根据零件编号前缀生成描述
    if part_no.startswith('334-'):
        descriptions.append("组装件")
    elif part_no.startswith('311-'):
        descriptions.append("PCBA组件")
    elif part_no.startswith('532-'):
        descriptions.append("标签类")
    elif part_no.startswith('536-'):
        descriptions.append("包装材料")
    elif part_no.startswith('540-'):
        descriptions.append("文档类")
    elif part_no.startswith('B93'):
        descriptions.append("通讯模块")
    elif part_no.startswith('510-'):
        descriptions.append("标准件")
    elif part_no.startswith('500-'):
        descriptions.append("机械件")
    else:
        descriptions.append("标准零件")
    
    # 根据零件名称添加功能描述
    if part_name:
        name_lower = part_name.lower()
        if 'pcba' in name_lower:
            descriptions.append("电路板组件")
        elif 'label' in name_lower or '标签' in part_name:
            descriptions.append("标识标签")
        elif 'box' in name_lower or '纸箱' in part_name:
            descriptions.append("包装箱体")
        elif 'document' in name_lower or '文档' in part_name:
            descriptions.append("技术文档")
        elif 'fan' in name_lower or '风扇' in part_name:
            descriptions.append("散热组件")
        elif 'connector' in name_lower or '连接器' in part_name:
            descriptions.append("连接组件")
    
    return descriptions if descriptions else ["标准零件"]

def create_sample_bom_data_for_model(model_name):
    """
    为指定型号创建示例BOM数据（当数据库不可用时使用）
    
    Args:
        model_name: 型号名称
        
    Returns:
        dict: 示例BOM数据
    """
    logger.info(f"为型号 {model_name} 创建示例BOM数据")
    
    # 根据型号生成示例数据
    sample_data = {
        "334": [
            {
                "MPART.NO": "334-001-001",
                "MPART.NAME": f"{model_name}主机组装",
                "MPART.BNUM": 1.0,
                "MPART.MFG": "自制",
                "MPART.LVL": 0,
                "MPART.PRNT": model_name,
                "MPART.OP": "10",
                "MPART.ID": 1,
                "MPART.DESC": ["主机组装件"],
                "children": [
                    {
                        "MPART.NO": "311-001-001",
                        "MPART.NAME": "主控PCBA",
                        "MPART.BNUM": 1.0,
                        "MPART.MFG": "自制",
                        "MPART.LVL": 1,
                        "MPART.PRNT": "334-001-001",
                        "MPART.OP": "20",
                        "MPART.ID": 2,
                        "MPART.DESC": ["PCBA组件"],
                        "children": []
                    },
                    {
                        "MPART.NO": "500-001-001",
                        "MPART.NAME": "散热器",
                        "MPART.BNUM": 1.0,
                        "MPART.MFG": "外购",
                        "MPART.LVL": 1,
                        "MPART.PRNT": "334-001-001",
                        "MPART.OP": "30",
                        "MPART.ID": 3,
                        "MPART.DESC": ["散热组件"],
                        "children": []
                    }
                ]
            }
        ],
        "532": [
            {
                "MPART.NO": "532-001-001",
                "MPART.NAME": f"{model_name}产品标签",
                "MPART.BNUM": 1.0,
                "MPART.MFG": "外购",
                "MPART.LVL": 0,
                "MPART.PRNT": model_name,
                "MPART.OP": "40",
                "MPART.ID": 4,
                "MPART.DESC": ["标识标签"],
                "children": []
            }
        ],
        "540": [
            {
                "MPART.NO": "540-001-001",
                "MPART.NAME": f"{model_name}用户手册",
                "MPART.BNUM": 1.0,
                "MPART.MFG": "外购",
                "MPART.LVL": 0,
                "MPART.PRNT": model_name,
                "MPART.OP": "50",
                "MPART.ID": 5,
                "MPART.DESC": ["技术文档"],
                "children": []
            }
        ]
    }
    
    return sample_data

# ==================== 接口函数 ====================

def generate_ai_analysis_json(model_name, output_dir=None):
    """
    生成AI分析JSON数据 (供app.py调用的接口)
    
    Args:
        model_name: 型号名称，如 'SP0030-3Q-23-5QP'
        output_dir: 输出目录，默认为 'data/processed'
        
    Returns:
        dict: 包含生成结果的字典
        {
            'success': bool,
            'data': dict,  # AI分析数据
            'file_path': str,  # 保存的文件路径
            'stats': dict  # 统计信息
        }
    """
    try:
        logger.info(f"开始生成型号 {model_name} 的AI分析数据")
        
        # 生成AI分析数据
        ai_data = generate_ai_analysis_for_model(model_name)
        
        if not ai_data:
            return {
                'success': False,
                'error': f'未找到型号 {model_name} 的BOM数据',
                'data': None,
                'file_path': None,
                'stats': None
            }
        
        # 保存到文件
        if output_dir is None:
            output_dir = r"data\processed"
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{model_name}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ai_data, f, ensure_ascii=False, indent=2)
        
        # 统计信息
        total_parts = 0
        total_with_children = 0
        
        for category, parts in ai_data["MPART"].items():
            category_total = len(parts)
            category_with_children = sum(1 for part in parts if part.get('children'))
            total_parts += category_total
            total_with_children += category_with_children
        
        stats = {
            'categories': len(ai_data['MPART']),
            'total_parts': total_parts,
            'parts_with_children': total_with_children,
            'category_details': {
                category: {
                    'count': len(parts),
                    'with_children': sum(1 for part in parts if part.get('children'))
                }
                for category, parts in ai_data["MPART"].items()
            }
        }
        
        logger.info(f"AI分析数据生成成功: {stats['categories']}个分类, {stats['total_parts']}个零件")
        
        return {
            'success': True,
            'data': ai_data,
            'file_path': output_file,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"生成AI分析数据失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None,
            'file_path': None,
            'stats': None
        }

def get_model_ai_analysis(model_name):
    """
    获取型号的AI分析数据 (不保存文件，仅返回数据)
    
    Args:
        model_name: 型号名称
        
    Returns:
        dict: AI分析数据或None
    """
    try:
        return generate_ai_analysis_for_model(model_name)
    except Exception as e:
        logger.error(f"获取型号 {model_name} 的AI分析数据失败: {e}")
        return None

def batch_generate_ai_analysis(model_list, output_dir=None):
    """
    批量生成AI分析数据
    
    Args:
        model_list: 型号列表
        output_dir: 输出目录
        
    Returns:
        dict: 批量生成结果
    """
    results = []
    success_count = 0
    
    for model_name in model_list:
        result = generate_ai_analysis_json(model_name, output_dir)
        results.append({
            'model': model_name,
            **result
        })
        
        if result['success']:
            success_count += 1
    
    return {
        'total': len(model_list),
        'success': success_count,
        'failed': len(model_list) - success_count,
        'results': results
    }

# ==================== CLI工具函数 ====================

def save_ai_analysis_to_file(model_name, output_dir=None):
    """
    生成并保存AI分析数据到文件 (CLI工具用)
    
    Args:
        model_name: 型号名称
        output_dir: 输出目录
        
    Returns:
        bool: 是否成功
    """
    result = generate_ai_analysis_json(model_name, output_dir)
    
    if result['success']:
        print(f"✓ AI分析数据已保存到: {result['file_path']}")
        
        stats = result['stats']
        print(f"统计信息:")
        print(f"  分类数: {stats['categories']}")
        print(f"  零件数: {stats['total_parts']}")
        print(f"  有子件的零件: {stats['parts_with_children']}")
        
        print(f"\n分类详情:")
        for category, details in stats['category_details'].items():
            print(f"  {category}: {details['count']} 个零件，{details['with_children']} 个有子件")
        
        return True
    else:
        print(f"✗ 生成失败: {result['error']}")
        return False

def main():
    """
    CLI工具主函数
    """
    while True:
        print("\n=== AI分析数据生成工具 ===")
        print("1. 生成单个型号的AI分析数据")
        print("2. 批量生成AI分析数据")
        print("3. 查看型号的AI分析数据 (不保存)")
        print("4. 生成默认型号 (SP0030-3Q-23-5QP)")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-4): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
            
        elif choice == '1':
            model_name = input("请输入型号名称: ").strip()
            if model_name:
                output_dir = input("请输入输出目录 (默认: data/processed): ").strip()
                if not output_dir:
                    output_dir = None
                
                save_ai_analysis_to_file(model_name, output_dir)
            else:
                print("型号名称不能为空")
                
        elif choice == '2':
            models_input = input("请输入型号列表 (用逗号分隔): ").strip()
            if models_input:
                model_list = [m.strip() for m in models_input.split(',') if m.strip()]
                output_dir = input("请输入输出目录 (默认: data/processed): ").strip()
                if not output_dir:
                    output_dir = None
                
                print(f"\n开始批量生成 {len(model_list)} 个型号...")
                batch_result = batch_generate_ai_analysis(model_list, output_dir)
                
                print(f"\n批量生成完成:")
                print(f"  总计: {batch_result['total']} 个型号")
                print(f"  成功: {batch_result['success']} 个型号")
                print(f"  失败: {batch_result['failed']} 个型号")
                
                if batch_result['failed'] > 0:
                    print(f"\n失败的型号:")
                    for result in batch_result['results']:
                        if not result['success']:
                            print(f"  {result['model']}: {result['error']}")
            else:
                print("型号列表不能为空")
                
        elif choice == '3':
            model_name = input("请输入型号名称: ").strip()
            if model_name:
                ai_data = get_model_ai_analysis(model_name)
                if ai_data:
                    print(f"\n型号 {model_name} 的AI分析数据:")
                    print(f"  描述: {', '.join(ai_data['DESC'])}")
                    print(f"  分类数: {len(ai_data['MPART'])}")
                    
                    for category, parts in ai_data['MPART'].items():
                        parts_with_children = sum(1 for part in parts if part.get('children'))
                        print(f"  分类 {category}: {len(parts)} 个零件，{parts_with_children} 个有子件")
                else:
                    print("未找到数据")
            else:
                print("型号名称不能为空")
                
        elif choice == '4':
            print("生成默认型号: SP0030-00-23-5QP")
            save_ai_analysis_to_file("SP0030-00-23-5QP")
            
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()