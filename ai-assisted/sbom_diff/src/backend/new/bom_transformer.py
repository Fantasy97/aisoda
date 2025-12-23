#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOM转换器 - 根据差异文件生成新的BOM文件
支持接口调用和CLI工具两种模式
"""

import json
import os
import shutil
from typing import Dict, List, Any
import copy
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BOMTransformer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return {}
    
    def save_json(self, data: Dict[str, Any], file_path: str) -> bool:
        """保存JSON文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"文件保存成功: {file_path}")
            return True
        except Exception as e:
            print(f"保存文件失败 {file_path}: {e}")
            return False
    
    def find_item_by_part_no(self, bom_data: Dict[str, Any], part_no: str, parent_no: str = None) -> tuple:
        """在BOM数据中查找指定零件号的项目"""
        def search_in_items(items: List[Dict], level: int = 0) -> tuple:
            for i, item in enumerate(items):
                if item.get("MPART.NO") == part_no:
                    if parent_no is None or item.get("MPART.PRNT") == parent_no:
                        return items, i, item
                
                # 递归搜索子项
                if "children" in item and item["children"]:
                    result = search_in_items(item["children"], level + 1)
                    if result[0] is not None:
                        return result
            
            return None, -1, None
        
        # 在所有分类中搜索
        for category, items in bom_data.get("MPART", {}).items():
            result = search_in_items(items)
            if result[0] is not None:
                return result
        
        return None, -1, None 
   
    def apply_diff_changes(self, bom_data: Dict[str, Any], diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """应用差异变更到BOM数据"""
        result_data = copy.deepcopy(bom_data)
        
        # 更新模型信息
        target_model = diff_data["model_info"]["target_model"]
        result_data["MODEL"] = target_model
        
        # 处理主要差异项目
        for diff_item in diff_data.get("diff_items", []):
            base_bom = diff_item["base_bom"]
            target_bom = diff_item["target_bom"]
            part_no = base_bom["MPART.NO"]
            parent_no = base_bom["MPART.PRNT"]
            remark = target_bom.get("REMARK", "")
            
            print(f"处理零件: {part_no}, 操作: {remark}")
            
            if remark == "Add":
                # 添加新项目
                parent_no = target_bom["MPART.PRNT"]
                part_no = target_bom["MPART.NO"]
                
                # 根据零件号确定分类 (取前3位数字)
                category = extract_category(part_no)
                
                # 创建新的项目
                new_item = {
                    "MPART.NO": part_no,
                    "MPART.NAME": target_bom.get("MPART.NAME", "新增零件"),
                    "MPART.BNUM": target_bom["MPART.BNUM"],
                    "MPART.MFG": target_bom.get("MPART.MFG", "新增"),
                    "MPART.LVL": 0,
                    "MPART.PRNT": parent_no,
                    "MPART.OP": target_bom.get("MPART.OP", ""),
                    "MPART.ID": self.get_next_id(result_data),
                    "MPART.DESC": target_bom.get("MPART.DESC", ["新增零件"]),
                    "children": []
                }
                
                # 确保分类存在，如果不存在则创建
                if "MPART" not in result_data:
                    result_data["MPART"] = {}
                if category not in result_data["MPART"]:
                    result_data["MPART"][category] = []
                
                # 添加到对应分类
                result_data["MPART"][category].append(new_item)
                print(f"已添加零件: {part_no} 到分类: {category} (父件: {parent_no})")
                continue

            # 查找要修改的项目
            items_list, item_index, found_item = self.find_item_by_part_no(result_data, part_no, parent_no)

            if found_item is None:
                print(f"未找到零件: {part_no} (父件: {parent_no})")
                continue
            
            # 统一转换为小写进行比较，不区分大小写
            remark_lower = remark.lower() if remark else ""
            
            if remark_lower == "delete":
                # 删除项目
                if items_list and item_index >= 0:
                    items_list.pop(item_index)
                    print(f"已删除零件: {part_no}")
            
            elif remark_lower == "change":
                # 修改项目
                if items_list and item_index >= 0:
                    # 更新零件号
                    items_list[item_index]["MPART.NO"] = target_bom["MPART.NO"]
                    # 更新父件号
                    items_list[item_index]["MPART.PRNT"] = target_bom["MPART.PRNT"]
                    # 更新数量
                    items_list[item_index]["MPART.BNUM"] = target_bom["MPART.BNUM"]
                    print(f"已修改零件: {part_no} -> {target_bom['MPART.NO']}")
            
        
        # 处理子BOM项目 (添加新项目)
        for sub_item in diff_data.get("sub_bom_items", []):
            sub_remark = sub_item.get("REMARK", "").lower()
            if sub_remark == "add":
                parent_no = sub_item["MPART.PRNT"]
                
                # 查找父项目
                parent_items, parent_index, parent_item = self.find_item_by_part_no(result_data, parent_no)
                
                if parent_item is None:
                    print(f"未找到父项目: {parent_no}")
                    continue
                
                # 创建新的子项目
                new_item = {
                    "MPART.NO": sub_item["MPART.NO"],
                    "MPART.NAME": sub_item["MPART.NAME"],
                    "MPART.BNUM": sub_item["MPART.BNUM"],
                    "MPART.MFG": "子阶新增",  # 默认值
                    "MPART.LVL": parent_item["MPART.LVL"] + 1,
                    "MPART.PRNT": parent_no,
                    "MPART.OP": sub_item["MPART.OP"],
                    "MPART.ID": self.get_next_id(result_data),
                    "MPART.DESC": ["标准零件"],
                    "children": []
                }
                
                # 添加到父项目的children中
                if "children" not in parent_item:
                    parent_item["children"] = []
                parent_item["children"].append(new_item)
                print(f"已添加子项目: {sub_item['MPART.NO']} 到父项目: {parent_no}")
        
        # 更新所有MPART.LVL为0的项目的MPART.PRNT为新的模型号
        self.update_root_parent(result_data, target_model)
        
        return result_data
    
    def get_next_id(self, bom_data: Dict[str, Any]) -> int:
        """获取下一个可用的ID"""
        max_id = 0
        
        def find_max_id(items: List[Dict]):
            nonlocal max_id
            for item in items:
                if "MPART.ID" in item:
                    max_id = max(max_id, item["MPART.ID"])
                if "children" in item and item["children"]:
                    find_max_id(item["children"])
        
        for category, items in bom_data.get("MPART", {}).items():
            find_max_id(items)
        
        return max_id + 1
    
    def update_root_parent(self, bom_data: Dict[str, Any], new_model: str):
        """更新所有根级项目的父件号"""
        def update_items(items: List[Dict]):
            for item in items:
                if item.get("MPART.LVL") == 0:
                    item["MPART.PRNT"] = new_model
                if "children" in item and item["children"]:
                    update_items(item["children"])
        
        for category, items in bom_data.get("MPART", {}).items():
            update_items(items)
    
    def get_bom_stats(self, bom_data: Dict[str, Any], diff_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取BOM统计信息"""
        # 统计BOM数据
        total_parts = 0
        categories = len(bom_data.get("MPART", {}))
        
        for category, items in bom_data.get("MPART", {}).items():
            total_parts += len(items)
        
        # 统计操作数量
        delete_count = 0
        change_count = 0
        add_count = 0
        
        for diff_item in diff_data.get("diff_items", []):
            remark = diff_item["target_bom"].get("REMARK", "").lower()
            if remark == "delete":
                delete_count += 1
            elif remark == "change":
                change_count += 1
        
        for sub_item in diff_data.get("sub_bom_items", []):
            if sub_item.get("REMARK", "").lower() == "add":
                add_count += 1
        
        return {
            'target_model': diff_data["model_info"]["target_model"],
            'categories': categories,
            'total_parts': total_parts,
            'operations': {
                'delete': delete_count,
                'change': change_count,
                'add': add_count
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def transform_bom(self, base_file: str, diff_file: str, output_file: str) -> bool:
        """执行BOM转换"""
        print(f"开始BOM转换...")
        print(f"基础文件: {base_file}")
        print(f"差异文件: {diff_file}")
        print(f"输出文件: {output_file}")
        
        # 加载基础BOM文件
        base_bom = self.load_json(base_file)
        if not base_bom:
            print("加载基础BOM文件失败")
            return False
        
        # 加载差异文件
        diff_data = self.load_json(diff_file)
        if not diff_data:
            print("加载差异文件失败")
            return False
        
        # 应用变更
        result_bom = self.apply_diff_changes(base_bom, diff_data)
        
        # 保存结果
        return self.save_json(result_bom, output_file)

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

# ==================== 接口函数 ====================

def transform_bom_json(base_file, diff_file, output_file=None, tmp_dir=None):
    """
    BOM转换接口函数 (供app.py调用)
    
    Args:
        base_file: 基础BOM文件路径
        diff_file: 差异文件路径
        output_file: 输出文件路径，默认根据差异文件自动生成
        tmp_dir: 临时目录，默认为 'tmp'
        
    Returns:
        dict: 包含转换结果的字典
        {
            'success': bool,
            'data': dict,  # 转换后的BOM数据
            'file_path': str,  # 保存的文件路径
            'tmp_file_path': str,  # 临时文件路径
            'stats': dict  # 统计信息
        }
    """
    try:
        logger.info(f"开始BOM转换: {base_file} -> {output_file}")
        
        transformer = BOMTransformer()
        
        # 加载基础BOM文件
        base_bom = transformer.load_json(base_file)
        if not base_bom:
            return {
                'success': False,
                'error': f'加载基础BOM文件失败: {base_file}',
                'data': None,
                'file_path': None,
                'tmp_file_path': None,
                'stats': None
            }
        
        # 加载差异文件
        diff_data = transformer.load_json(diff_file)
        if not diff_data:
            return {
                'success': False,
                'error': f'加载差异文件失败: {diff_file}',
                'data': None,
                'file_path': None,
                'tmp_file_path': None,
                'stats': None
            }
        
        # 自动生成输出文件名
        if output_file is None:
            target_model = diff_data["model_info"]["target_model"]
            output_file = f"data/processed/{target_model}.json"
        
        # 设置临时目录
        if tmp_dir is None:
            tmp_dir = "tmp"
        
        # 生成临时文件路径
        target_model = diff_data["model_info"]["target_model"]
        tmp_file_path = os.path.join(tmp_dir, f"{target_model}.json")
        
        # 应用变更
        result_bom = transformer.apply_diff_changes(base_bom, diff_data)
        
        # 保存到临时目录
        os.makedirs(tmp_dir, exist_ok=True)
        if not transformer.save_json(result_bom, tmp_file_path):
            return {
                'success': False,
                'error': f'保存临时文件失败: {tmp_file_path}',
                'data': None,
                'file_path': None,
                'tmp_file_path': None,
                'stats': None
            }
        
        # 保存到最终目录
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        if not transformer.save_json(result_bom, output_file):
            return {
                'success': False,
                'error': f'保存最终文件失败: {output_file}',
                'data': None,
                'file_path': None,
                'tmp_file_path': tmp_file_path,
                'stats': None
            }
        
        # 统计信息
        stats = transformer.get_bom_stats(result_bom, diff_data)
        
        logger.info(f"BOM转换成功: {stats['total_parts']}个零件, {stats['categories']}个分类")
        
        return {
            'success': True,
            'data': result_bom,
            'file_path': output_file,
            'tmp_file_path': tmp_file_path,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"BOM转换失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None,
            'file_path': None,
            'tmp_file_path': None,
            'stats': None
        }

def get_bom_diff_preview(base_file, diff_file):
    """
    获取BOM差异预览 (不执行转换，仅返回预览信息)
    
    Args:
        base_file: 基础BOM文件路径
        diff_file: 差异文件路径
        
    Returns:
        dict: 差异预览信息
    """
    try:
        transformer = BOMTransformer()
        
        # 加载差异文件
        diff_data = transformer.load_json(diff_file)
        if not diff_data:
            return None
        
        preview = {
            'model_info': diff_data.get('model_info', {}),
            'diff_summary': {
                'delete_count': 0,
                'change_count': 0,
                'add_count': 0
            },
            'diff_items': [],
            'sub_bom_items': []
        }
        
        # 统计差异项目
        for diff_item in diff_data.get("diff_items", []):
            remark = diff_item["target_bom"].get("REMARK", "")
            remark_lower = remark.lower() if remark else ""
            if remark_lower == "delete":
                preview['diff_summary']['delete_count'] += 1
            elif remark_lower == "change":
                preview['diff_summary']['change_count'] += 1
            
            preview['diff_items'].append({
                'part_no': diff_item["base_bom"]["MPART.NO"],
                'part_name': diff_item["MPART.NAME"],
                'operation': remark,
                'base_bom': diff_item["base_bom"],
                'target_bom': diff_item["target_bom"]
            })
        
        # 统计子BOM项目
        for sub_item in diff_data.get("sub_bom_items", []):
            if sub_item.get("REMARK", "").lower() == "add":
                preview['diff_summary']['add_count'] += 1
                preview['sub_bom_items'].append(sub_item)
        
        return preview
        
    except Exception as e:
        logger.error(f"获取BOM差异预览失败: {e}")
        return None

def batch_transform_bom(transform_list, tmp_dir=None):
    """
    批量BOM转换
    
    Args:
        transform_list: 转换列表，每个元素包含 {'base_file', 'diff_file', 'output_file'}
        tmp_dir: 临时目录
        
    Returns:
        dict: 批量转换结果
    """
    results = []
    success_count = 0
    
    for transform_item in transform_list:
        base_file = transform_item['base_file']
        diff_file = transform_item['diff_file']
        output_file = transform_item.get('output_file')
        
        result = transform_bom_json(base_file, diff_file, output_file, tmp_dir)
        results.append({
            'base_file': base_file,
            'diff_file': diff_file,
            **result
        })
        
        if result['success']:
            success_count += 1
    
    return {
        'total': len(transform_list),
        'success': success_count,
        'failed': len(transform_list) - success_count,
        'results': results
    }

# ==================== CLI工具函数 ====================

def save_transformed_bom_to_file(base_file, diff_file, output_file=None, tmp_dir=None):
    """
    执行BOM转换并保存到文件 (CLI工具用)
    
    Args:
        base_file: 基础BOM文件路径
        diff_file: 差异文件路径
        output_file: 输出文件路径
        tmp_dir: 临时目录
        
    Returns:
        bool: 是否成功
    """
    result = transform_bom_json(base_file, diff_file, output_file, tmp_dir)
    
    if result['success']:
        print(f"✓ BOM转换成功!")
        print(f"  临时文件: {result['tmp_file_path']}")
        print(f"  最终文件: {result['file_path']}")
        
        stats = result['stats']
        print(f"\n转换统计:")
        print(f"  目标型号: {stats['target_model']}")
        print(f"  分类数: {stats['categories']}")
        print(f"  零件数: {stats['total_parts']}")
        print(f"  删除: {stats['operations']['delete']} 个")
        print(f"  修改: {stats['operations']['change']} 个")
        print(f"  添加: {stats['operations']['add']} 个")
        
        return True
    else:
        print(f"✗ BOM转换失败: {result['error']}")
        return False

def show_diff_preview(base_file, diff_file):
    """
    显示差异预览
    
    Args:
        base_file: 基础BOM文件路径
        diff_file: 差异文件路径
    """
    preview = get_bom_diff_preview(base_file, diff_file)
    
    if preview:
        model_info = preview['model_info']
        print(f"\n=== BOM差异预览 ===")
        print(f"基础型号: {model_info.get('base_model', 'N/A')}")
        print(f"目标型号: {model_info.get('target_model', 'N/A')}")
        print(f"标题: {model_info.get('title', 'N/A')}")
        
        summary = preview['diff_summary']
        print(f"\n操作统计:")
        print(f"  删除: {summary['delete_count']} 个零件")
        print(f"  修改: {summary['change_count']} 个零件")
        print(f"  添加: {summary['add_count']} 个零件")
        
        if preview['diff_items']:
            print(f"\n主要变更:")
            for item in preview['diff_items']:
                print(f"  {item['operation']}: {item['part_no']} - {item['part_name']}")
        
        if preview['sub_bom_items']:
            print(f"\n子BOM添加:")
            for item in preview['sub_bom_items']:
                print(f"  添加: {item['MPART.NO']} - {item['MPART.NAME']} (父件: {item['MPART.PRNT']})")
    else:
        print("获取差异预览失败")

def main():
    """
    CLI工具主函数
    """
    while True:
        print("\n=== BOM转换工具 ===")
        print("1. 执行BOM转换")
        print("2. 查看差异预览")
        print("3. 批量BOM转换")
        print("4. 默认转换 (SP0030-00-23-5QP -> SP0030-3Q-23-5QP)")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-4): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
            
        elif choice == '1':
            base_file = input("请输入基础BOM文件路径: ").strip()
            diff_file = input("请输入差异文件路径: ").strip()
            output_file = input("请输入输出文件路径 (可选): ").strip()
            tmp_dir = input("请输入临时目录 (默认: tmp): ").strip()
            
            if not base_file or not diff_file:
                print("基础BOM文件和差异文件路径不能为空")
                continue
            
            if not output_file:
                output_file = None
            if not tmp_dir:
                tmp_dir = None
            
            save_transformed_bom_to_file(base_file, diff_file, output_file, tmp_dir)
            
        elif choice == '2':
            base_file = input("请输入基础BOM文件路径: ").strip()
            diff_file = input("请输入差异文件路径: ").strip()
            
            if not base_file or not diff_file:
                print("基础BOM文件和差异文件路径不能为空")
                continue
            
            show_diff_preview(base_file, diff_file)
            
        elif choice == '3':
            print("批量转换功能 - 请准备包含转换配置的JSON文件")
            config_file = input("请输入配置文件路径: ").strip()
            
            if not config_file:
                print("配置文件路径不能为空")
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    transform_list = json.load(f)
                
                tmp_dir = input("请输入临时目录 (默认: tmp): ").strip()
                if not tmp_dir:
                    tmp_dir = None
                
                print(f"\n开始批量转换 {len(transform_list)} 个BOM...")
                batch_result = batch_transform_bom(transform_list, tmp_dir)
                
                print(f"\n批量转换完成:")
                print(f"  总计: {batch_result['total']} 个BOM")
                print(f"  成功: {batch_result['success']} 个BOM")
                print(f"  失败: {batch_result['failed']} 个BOM")
                
                if batch_result['failed'] > 0:
                    print(f"\n失败的转换:")
                    for result in batch_result['results']:
                        if not result['success']:
                            print(f"  {result['base_file']} -> {result['diff_file']}: {result['error']}")
                            
            except Exception as e:
                print(f"批量转换失败: {e}")
            
        elif choice == '4':
            print("执行默认转换...")
            base_file = "data/processed/SP0030-00-23-5QP.json"
            diff_file = "data/processed/SP0030-00-23-5QP_to_SP0030-3Q-23-5QP.json"
            save_transformed_bom_to_file(base_file, diff_file)
            
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()