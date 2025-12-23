#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PLM Excel BOM数据处理器
专门处理PLM导出的Excel BOM数据，转换为JSON格式
保持原始型号名称（如DE0030-3Q-20-52-00P）
"""

import pandas as pd
import json
import os
import logging
from collections import defaultdict
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlmExcelProcessor:
    """PLM Excel BOM数据处理器"""
    
    def __init__(self):
        self.part_id_counter = 1
        
    def process_plm_excel(self, excel_file_path, sheet_num=0, output_dir="data/tmp"):
        """
        处理PLM Excel文件中指定的sheet并生成JSON
        
        Args:
            excel_file_path: Excel文件路径
            sheet_num: 要处理的sheet索引号，默认为0（第一个sheet）
            output_dir: 输出目录
            
        Returns:
            dict: 处理结果
        """
        try:
            logger.info(f"开始处理PLM Excel文件: {excel_file_path}")
            
            # 读取Excel文件并提取sheet名称
            xl_file = pd.ExcelFile(excel_file_path)
            sheet_names = xl_file.sheet_names
            logger.info(f"Excel包含 {len(sheet_names)} 个sheet: {sheet_names}")
            
            # 验证sheet_num是否有效
            if sheet_num < 0 or sheet_num >= len(sheet_names):
                raise ValueError(f"sheet_num {sheet_num} 超出范围，有效范围: 0-{len(sheet_names)-1}")
            
            # 从指定sheet名称提取型号
            target_sheet_name = sheet_names[sheet_num]
            model_name = self._extract_model_from_sheet_name(target_sheet_name)
            logger.info(f"处理第 {sheet_num} 个sheet '{target_sheet_name}'，提取到型号: {model_name}")
            
            # 读取指定sheet的数据
            df = pd.read_excel(excel_file_path, sheet_name=target_sheet_name)
            logger.info(f"读取到 {len(df)} 行数据")
            
            # 数据预处理
            df = self._preprocess_data(df)
            
            # 设置输出文件路径
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{model_name}.json")
            
            # 构建BOM结构
            bom_structure = self._build_bom_structure(df, model_name)
            
            # 构建最终JSON结构
            json_data = {
                "MODEL": model_name,
                "DESC": self._generate_model_description(model_name),
                "MPART": bom_structure
            }
            
            # 保存JSON文件
            self._save_json_file(json_data, output_file)
            
            # 统计信息
            stats = self._calculate_stats(json_data)
            
            logger.info(f"处理完成: {stats['categories']}个分类, {stats['total_parts']}个零件")
            
            return {
                'success': True,
                'model_name': model_name,
                'data': json_data,
                'file_path': output_file,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_name': None,
                'data': None,
                'file_path': None,
                'stats': None
            }
    
    def _preprocess_data(self, df):
        """数据预处理"""
        # 清理列名
        df.columns = df.columns.str.strip()
        
        # 填充NaN值
        df = df.fillna('')
        
        # 过滤掉空的物料编码行
        df = df[df['物料编码'].astype(str).str.strip() != '']
        
        # 转换数据类型
        df['阶层'] = df['阶层'].astype(str).str.strip()
        df['用量'] = pd.to_numeric(df['用量'], errors='coerce').fillna(1.0)
        
        logger.info(f"预处理后剩余 {len(df)} 行有效数据")
        return df
    
    def _extract_model_from_sheet_name(self, sheet_name):
        """从sheet名称提取型号名称"""
        # 直接使用sheet名称作为型号，去除首尾空格
        model_name = str(sheet_name).strip()
        logger.info(f"使用sheet名称作为型号: {model_name}")
        return model_name
    
    def _extract_original_model_name(self, df):
        """提取原始型号名称（备用方法，从数据中提取）"""
        # 查找阶层为0的记录
        level_0_records = df[df['阶层'] == '0']
        if not level_0_records.empty:
            model_code = str(level_0_records.iloc[0]['物料编码']).strip()
            return model_code  # 直接返回原始型号，不做任何转换
        
        # 如果没有找到，返回默认值
        return "UNKNOWN_MODEL"
    
    def _build_bom_structure(self, df, model_name):
        """构建BOM结构"""
        all_parts = {}
        level_groups = defaultdict(list)
        
        # 添加层级数字，但保持原始顺序（不排序）
        df['level_num'] = df['阶层'].apply(self._parse_level)
        # 保持Excel中的原始顺序，这样父子关系才能正确建立
        df_sorted = df
        
        # 处理每个零件并建立层级关系
        parent_stack = []  # 用于跟踪父件的栈
        
        for _, row in df_sorted.iterrows():
            part_no = str(row['物料编码']).strip()
            if not part_no:
                continue
                
            level_num = int(row['level_num'])
            
            # 跳过主产品记录（level_num = -1，即阶层为'0'的记录）
            if level_num == -1:
                logger.info(f"跳过主产品记录: {part_no}")
                continue
            
            # 创建零件数据
            part_data = {
                'MPART.NO': part_no,
                'MPART.NAME': str(row['物料名称']).strip(),
                'MPART.BNUM': float(row['用量']) if row['用量'] else 1.0,
                'MPART.MFG': str(row['来料方式']).strip(),
                'MPART.LVL': level_num,
                'MPART.PRNT': model_name,  # 父件关系立即建立
                'MPART.OP': str(row['生产工序']).strip(),
                'MPART.ID': self.part_id_counter,
                'MPART.DESC': str(row['中文']).strip(),
                'children': []
            }
            
            self.part_id_counter += 1
            
            # 建立父子关系
            # 调整父件栈，移除层级大于等于当前层级的父件
            while parent_stack and parent_stack[-1]['level'] >= level_num:
                parent_stack.pop()
            
            # 如果有父件，建立关系
            if parent_stack:
                parent_part = parent_stack[-1]['part']
                part_data['MPART.PRNT'] = parent_part['MPART.NO']
                parent_part['children'].append(part_data)
            
            # 将当前零件加入父件栈
            parent_stack.append({
                'level': level_num,
                'part': part_data
            })
            
            # 存储零件
            unique_key = f"{part_no}_{level_num}_{self.part_id_counter}"
            all_parts[unique_key] = part_data
            level_groups[level_num].append(part_data)
        
        # 按分类分组顶级零件（只使用 level_num = 0 的第一级零件作为顶级）
        top_level_parts = level_groups.get(0, [])
        return self._group_by_category(top_level_parts)
    
    def _parse_level(self, level_str):
        """
        解析阶层字符串为数字
        转换规则：
        - '0' -> -1 (主产品，最顶级)
        - '.1' -> 0 (第一级子件)
        - '..2' -> 1 (第二级子件)
        - '...3' -> 2 (第三级子件)
        """
        level_str = str(level_str).strip()
        
        if level_str == '0':
            return -1  # 主产品为最顶级
        elif level_str.startswith('.'):
            # 点的数量减1作为层级
            dot_count = level_str.count('.')
            return dot_count - 1
        else:
            try:
                # 如果是纯数字，直接转换
                num = int(level_str)
                if num == 0:
                    return -1
                else:
                    return num - 1
            except:
                return 0
    
    def _establish_relationships(self, level_groups):
        """建立父子关系（已在处理过程中完成，此方法保留用于兼容性）"""
        # 父子关系已在零件处理过程中通过栈结构建立
        pass
    
    def _group_by_category(self, top_level_parts):
        """按分类分组顶级零件"""
        grouped_data = defaultdict(list)
        
        for part_data in top_level_parts:
            category = self._extract_category(part_data['MPART.NO'])
            grouped_data[category].append(part_data)
        
        return dict(grouped_data)
    
    def _extract_category(self, part_no):
        """从零件编号中提取分类"""
        if not part_no:
            return 'UNKNOWN'
        
        # 处理标准零件编号格式
        if '-' in part_no:
            parts = part_no.split('-')
            if len(parts) > 0:
                prefix = parts[0]
                if prefix.isdigit() and len(prefix) == 3:
                    return prefix
        
        # 提取前缀
        import re
        match = re.match(r'^([A-Z]*\d+)', part_no)
        if match:
            return match.group(1)
        
        # 默认分类
        return part_no[:6] if len(part_no) > 6 else part_no
    
    def _generate_model_description(self, model_name):
        """生成型号描述"""
        descriptions = []
        
        # 根据型号生成描述
        if '30' in model_name:
            descriptions.append("30K三相并网逆变器")
        elif '33' in model_name:
            descriptions.append("33K三相并网逆变器")
        elif '40' in model_name:
            descriptions.append("40K三相并网逆变器")
        elif '20' in model_name:
            descriptions.append("20K三相并网逆变器")
        else:
            descriptions.append("三相并网逆变器")
        
        if 'Q' in model_name:
            descriptions.append("高效能版本")
        if 'P' in model_name:
            descriptions.append("标准版本")
        
        return descriptions
    
    def _save_json_file(self, json_data, output_path):
        """保存JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON文件已保存到: {output_path}")
    
    def _calculate_stats(self, json_data):
        """计算统计信息"""
        total_parts = 0
        total_with_children = 0
        
        for category, parts in json_data["MPART"].items():
            category_total = len(parts)
            category_with_children = sum(1 for part in parts if part.get('children'))
            total_parts += category_total
            total_with_children += category_with_children
        
        return {
            'categories': len(json_data['MPART']),
            'total_parts': total_parts,
            'parts_with_children': total_with_children,
            'category_details': {
                category: {
                    'count': len(parts),
                    'with_children': sum(1 for part in parts if part.get('children'))
                }
                for category, parts in json_data["MPART"].items()
            }
        }
    
    def process_gbom_sheet(self, excel_file_path, sheet_num=0, output_dir="data/tmp"):
        """
        处理GBOM格式的sheet（包含中文名称、GBOM.BOMPST、MPART.NO等列）
        
        Args:
            excel_file_path: Excel文件路径
            sheet_num: 要处理的sheet索引号，默认为0（第一个sheet）
            output_dir: 输出目录
            
        Returns:
            dict: 处理结果
        """
        try:
            logger.info(f"开始处理GBOM格式Excel文件: {excel_file_path}")
            
            # 读取Excel文件并提取sheet名称
            xl_file = pd.ExcelFile(excel_file_path)
            sheet_names = xl_file.sheet_names
            logger.info(f"Excel包含 {len(sheet_names)} 个sheet: {sheet_names}")
            
            # 验证sheet_num是否有效
            if sheet_num < 0 or sheet_num >= len(sheet_names):
                raise ValueError(f"sheet_num {sheet_num} 超出范围，有效范围: 0-{len(sheet_names)-1}")
            
            # 从指定sheet名称提取型号
            target_sheet_name = sheet_names[sheet_num]
            model_name = self._extract_model_from_sheet_name(target_sheet_name)
            logger.info(f"处理第 {sheet_num} 个sheet '{target_sheet_name}'，提取到型号: {model_name}")
            
            # 读取指定sheet的数据
            df = pd.read_excel(excel_file_path, sheet_name=target_sheet_name)
            logger.info(f"读取到 {len(df)} 行数据")
            
            # GBOM格式数据预处理
            df = self._preprocess_gbom_data(df)
            
            # 如果预处理后没有有效数据，返回错误
            if len(df) == 0:
                return {
                    'success': False,
                    'error': '没有有效的GBOM数据',
                    'model_name': model_name,
                    'data': None,
                    'file_path': None,
                    'stats': None
                }
            
            # 设置输出文件路径
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{model_name}.json")
            
            # 构建GBOM结构
            gbom_structure = self._build_gbom_structure(df, model_name)
            
            # 构建最终JSON结构
            json_data = {
                "MODEL": model_name,
                "DESC": self._generate_model_description(model_name),
                "MPART": gbom_structure
            }
            
            # 保存JSON文件
            self._save_json_file(json_data, output_file)
            
            # 统计信息
            stats = self._calculate_stats(json_data)
            
            logger.info(f"GBOM处理完成: {stats['categories']}个分类, {stats['total_parts']}个零件")
            
            return {
                'success': True,
                'model_name': model_name,
                'data': json_data,
                'file_path': output_file,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"GBOM处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_name': None,
                'data': None,
                'file_path': None,
                'stats': None
            }
    
    def _preprocess_gbom_data(self, df):
        """GBOM格式数据预处理"""
        # 清理列名
        df.columns = df.columns.str.strip()
        
        # 填充NaN值
        df = df.fillna('')
        
        # 检查必要的列是否存在
        required_columns = ['MPART.NO', 'MPART.NAME', 'GBOM.BNUM']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 过滤掉空的MPART.NO行
        df = df[df['MPART.NO'].astype(str).str.strip() != '']
        
        # 转换数据类型
        df['GBOM.BNUM'] = pd.to_numeric(df['GBOM.BNUM'], errors='coerce').fillna(1.0)
        
        logger.info(f"GBOM预处理后剩余 {len(df)} 行有效数据")
        return df
    
    def _build_gbom_structure(self, df, model_name):
        """构建GBOM结构"""
        all_parts = {}
        
        # 处理每个零件
        for _, row in df.iterrows():
            part_no = str(row['MPART.NO']).strip()
            if not part_no:
                continue
            
            # 创建零件数据（按照你提供的格式）
            part_data = {
                'MPART.NO': str(row['MPART.NO']).strip(),
                'MPART.NAME': str(row['MPART.NAME']).strip(),
                'MPART.BNUM': float(row['GBOM.BNUM']) if row['GBOM.BNUM'] else 1.0,
                'MPART.MFG': "",
                'MPART.LVL': 0,
                'MPART.PRNT': model_name,  # 使用sheet名称作为父件
                'MPART.OP': "",
                'MPART.ID': self.part_id_counter,
                'MPART.DESC': self._get_chinese_description(row, part_no, str(row['MPART.NAME'])),
                'children': []
            }
            
            self.part_id_counter += 1
            
            # 存储零件
            unique_key = f"{part_no}_{self.part_id_counter}"
            all_parts[unique_key] = part_data
        
        # 按分类分组零件
        return self._group_gbom_by_category(all_parts.values())
    
    def _get_chinese_description(self, row, part_no, part_name):
        """
        获取中文描述，支持多个列名
        优先级：中文名称 > 中文备注 > 空字符串
        
        Args:
            row: 数据行
            part_no: 零件编号
            part_name: 零件名称
            
        Returns:
            list: 描述列表
        """
        # 检查中文名称列
        if '中文名称' in row and str(row['中文名称']).strip():
            return [str(row['中文名称']).strip()]
        
        # 检查中文备注列
        if '中文备注' in row and str(row['中文备注']).strip():
            return [str(row['中文备注']).strip()]
        
        # 如果都没有，返回空字符串
        return [""]
    
    def _group_gbom_by_category(self, parts):
        """按分类分组GBOM零件"""
        grouped_data = defaultdict(list)
        
        for part_data in parts:
            category = self._extract_category(part_data['MPART.NO'])
            grouped_data[category].append(part_data)
        
        return dict(grouped_data)
    
    def process_excel_with_auto_detection(self, excel_file_path, output_dir="data/tmp"):
        """
        自动检测Excel中所有sheet的格式并调用相应的处理函数
        
        Args:
            excel_file_path: Excel文件路径
            output_dir: 输出目录
            
        Returns:
            dict: 处理结果汇总
        """
        try:
            logger.info(f"开始自动检测处理Excel文件: {excel_file_path}")
            
            # 读取Excel文件并提取sheet名称
            xl_file = pd.ExcelFile(excel_file_path)
            sheet_names = xl_file.sheet_names
            logger.info(f"Excel包含 {len(sheet_names)} 个sheet: {sheet_names}")
            
            # 设置输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 处理结果汇总
            all_results = []
            success_count = 0
            plm_count = 0
            gbom_count = 0
            skip_count = 0
            
            # 检测并处理每个sheet
            for i, sheet_name in enumerate(sheet_names):
                logger.info(f"检测第 {i+1}/{len(sheet_names)} 个sheet: {sheet_name}")
                
                try:
                    # 检测sheet格式
                    sheet_format = self._detect_sheet_format(excel_file_path, sheet_name)
                    logger.info(f"Sheet '{sheet_name}' 检测为: {sheet_format}")
                    
                    if sheet_format == 'PLM':
                        # 使用PLM格式处理
                        result = self.process_plm_excel(excel_file_path, i, output_dir)
                        result['format'] = 'PLM'
                        plm_count += 1
                        
                    elif sheet_format == 'GBOM':
                        # 使用GBOM格式处理
                        result = self.process_gbom_sheet(excel_file_path, i, output_dir)
                        result['format'] = 'GBOM'
                        gbom_count += 1
                        
                    else:
                        # 跳过不支持的格式
                        result = {
                            'success': False,
                            'error': f'不支持的格式: {sheet_format}',
                            'model_name': sheet_name,
                            'format': sheet_format,
                            'file_path': None,
                            'stats': None
                        }
                        skip_count += 1
                    
                    result['sheet_name'] = sheet_name
                    result['sheet_index'] = i
                    all_results.append(result)
                    
                    if result['success']:
                        success_count += 1
                        
                except Exception as sheet_error:
                    logger.error(f"处理sheet '{sheet_name}' 失败: {sheet_error}")
                    all_results.append({
                        'sheet_name': sheet_name,
                        'sheet_index': i,
                        'model_name': sheet_name,
                        'success': False,
                        'error': str(sheet_error),
                        'format': 'UNKNOWN',
                        'file_path': None,
                        'stats': None
                    })
            
            # 汇总统计
            total_sheets = len(sheet_names)
            failed_count = total_sheets - success_count
            
            # 收集所有成功生成的JSON文件路径
            json_files = []
            for result in all_results:
                if result['success'] and result.get('file_path'):
                    json_files.append(result['file_path'])
            
            logger.info(f"自动检测处理完成: 总计{total_sheets}个sheet, 成功{success_count}个, PLM格式{plm_count}个, GBOM格式{gbom_count}个, 跳过{skip_count}个, 失败{failed_count}个")
            logger.info(f"生成的JSON文件: {json_files}")
            
            return {
                'success': success_count > 0,
                'total_sheets': total_sheets,
                'success_count': success_count,
                'failed_count': failed_count,
                'plm_count': plm_count,
                'gbom_count': gbom_count,
                'skip_count': skip_count,
                'json_files': json_files,  # 新增：所有生成的JSON文件路径数组
                'results': all_results,
                'error': None if success_count > 0 else '所有sheet都处理失败'
            }
            
        except Exception as e:
            logger.error(f"自动检测处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_sheets': 0,
                'success_count': 0,
                'failed_count': 0,
                'plm_count': 0,
                'gbom_count': 0,
                'skip_count': 0,
                'json_files': [],  # 新增：空的JSON文件路径数组
                'results': []
            }
    
    def _detect_sheet_format(self, excel_file_path, sheet_name):
        """
        检测sheet的格式类型
        
        Args:
            excel_file_path: Excel文件路径
            sheet_name: sheet名称
            
        Returns:
            str: 格式类型 ('PLM', 'GBOM', 'UNKNOWN')
        """
        try:
            # 读取sheet数据
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            
            if len(df) == 0:
                return 'EMPTY'
            
            # 获取列名
            columns = [str(col).strip() for col in df.columns]
            
            # 检测PLM格式特征
            plm_indicators = ['阶层', '物料编码', '物料名称', '用量']
            plm_score = sum(1 for col in plm_indicators if col in columns)
            
            # 检测GBOM格式特征
            gbom_indicators = ['MPART.NO', 'MPART.NAME', 'GBOM.BNUM']
            gbom_score = sum(1 for col in gbom_indicators if col in columns)
            
            # 检查是否有阶层列的特殊值
            has_hierarchy = False
            if '阶层' in columns:
                hierarchy_values = df['阶层'].astype(str).str.strip().unique()
                plm_hierarchy_patterns = ['0', '.1', '..2', '...3']
                if any(val in plm_hierarchy_patterns for val in hierarchy_values):
                    has_hierarchy = True
            
            logger.info(f"Sheet '{sheet_name}' 格式检测: PLM指标{plm_score}/{len(plm_indicators)}, GBOM指标{gbom_score}/{len(gbom_indicators)}, 层级结构{has_hierarchy}")
            
            # 判断格式
            if plm_score >= 3 and has_hierarchy:
                return 'PLM'
            elif gbom_score >= 3:
                return 'GBOM'
            elif plm_score >= 2:
                return 'PLM'  # 可能是PLM格式但缺少层级信息
            else:
                return 'UNKNOWN'
                
        except Exception as e:
            logger.error(f"检测sheet '{sheet_name}' 格式失败: {e}")
            return 'ERROR'

# ==================== 便捷函数 ====================

def process_plm_excel_file(excel_file_path, sheet_num=0, output_dir="data/tmp"):
    """
    处理单个PLM Excel文件中指定的sheet
    
    Args:
        excel_file_path: Excel文件路径
        sheet_num: 要处理的sheet索引号，默认为0（第一个sheet）
        output_dir: 输出目录
        
    Returns:
        dict: 处理结果
    """
    processor = PlmExcelProcessor()
    return processor.process_plm_excel(excel_file_path, sheet_num, output_dir)

def process_gbom_excel_file(excel_file_path, sheet_num=0, output_dir="data/tmp"):
    """
    处理GBOM格式的Excel文件中指定的sheet
    
    Args:
        excel_file_path: Excel文件路径
        sheet_num: 要处理的sheet索引号，默认为0（第一个sheet）
        output_dir: 输出目录
        
    Returns:
        dict: 处理结果
    """
    processor = PlmExcelProcessor()
    return processor.process_gbom_sheet(excel_file_path, sheet_num, output_dir)

def process_excel_auto_detect(excel_file_path, output_dir="data/tmp"):
    """
    自动检测Excel中所有sheet的格式并调用相应的处理函数
    
    Args:
        excel_file_path: Excel文件路径
        output_dir: 输出目录
        
    Returns:
        dict: 处理结果汇总
    """
    processor = PlmExcelProcessor()
    return processor.process_excel_with_auto_detection(excel_file_path, output_dir)

def batch_process_plm_files(excel_files, output_dir="data/tmp"):
    """
    批量处理PLM Excel文件
    
    Args:
        excel_files: Excel文件路径列表
        output_dir: 输出目录
        
    Returns:
        dict: 批量处理结果
    """
    results = []
    success_count = 0
    
    for excel_file in excel_files:
        result = process_plm_excel_file(excel_file, 0, output_dir)
        results.append({
            'excel_file': excel_file,
            **result
        })
        
        if result['success']:
            success_count += 1
    
    return {
        'total': len(excel_files),
        'success': success_count,
        'failed': len(excel_files) - success_count,
        'results': results
    }

# ==================== CLI工具 ====================

def main():
    """CLI工具主函数"""
    print("=== PLM Excel BOM数据处理工具 ===")
    
    # 默认处理tmp目录下的所有Excel文件
    tmp_dir = "tmp"
    result = process_excel_auto_detect(r'D:\code\sbom\release\sbom_diff\tmp\PLM新建BOM——DE0040-3Q-20-52-00P 20250825.xlsx')

    if result['success']:
        print(f"成功处理: {result['json_files']}")
        print(f"PLM格式: {result['plm_count']}")
        print(f"GBOM格式: {result['gbom_count']}")

if __name__ == "__main__":
    main()