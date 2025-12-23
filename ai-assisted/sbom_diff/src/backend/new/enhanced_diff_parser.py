#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
增强版差异表解析器
基于新的数据结构设计，解析Excel差异表并生成标准JSON格式
支持CLI工具和API调用两种模式
"""

import sys
import os
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import re
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DiffItem:
    """差异项数据结构"""
    MPART_NAME: str = ""        # 差异物料名称
    BASE_MPART_NO: str = ""     # 基准BOM差异料号
    BASE_MPART_PRNT: str = ""   # 基准BOM其上阶料号
    BASE_MPART_BNUM: int = 0    # 基准BOM数量
    BASE_MPART_OP: str = ""     # 基准BOM工位
    BASE_REMARK: str = ""       # 基准BOM备注
    
    TARGET_MPART_NO: str = ""   # 目标BOM差异料号
    TARGET_MPART_PRNT: str = "" # 目标BOM其上阶料号
    TARGET_MPART_BNUM: int = 0  # 目标BOM数量
    TARGET_MPART_OP: str = ""   # 目标BOM工位
    TARGET_REMARK: str = ""     # 目标BOM备注
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "MPART.NAME": self.MPART_NAME,
            "base_bom": {
                "MPART.NO": self.BASE_MPART_NO,
                "MPART.PRNT": self.BASE_MPART_PRNT,
                "MPART.BNUM": self.BASE_MPART_BNUM,
                "MPART.OP": self.BASE_MPART_OP,
                "REMARK": self.BASE_REMARK
            },
            "target_bom": {
                "MPART.NO": self.TARGET_MPART_NO,
                "MPART.PRNT": self.TARGET_MPART_PRNT,
                "MPART.BNUM": self.TARGET_MPART_BNUM,
                "MPART.OP": self.TARGET_MPART_OP,
                "REMARK": self.TARGET_REMARK
            }
        }


@dataclass
class SubBomItem:
    """子阶BOM项数据结构"""
    MPART_NAME: str = ""        # 物料名称
    MPART_NO: str = ""          # 子阶料号
    MPART_PRNT: str = ""        # 上阶料号
    MPART_BNUM: int = 0         # 数量
    MPART_OP: str = ""          # 工位
    REMARK: str = ""            # 备注
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "MPART.NAME": self.MPART_NAME,
            "MPART.NO": self.MPART_NO,
            "MPART.PRNT": self.MPART_PRNT,
            "MPART.BNUM": self.MPART_BNUM,
            "MPART.OP": self.MPART_OP,
            "REMARK": self.REMARK
        }


class EnhancedDiffParser:
    """增强版差异表解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.column_mapping = {
            # 差异表列映射
            "diff_excel": {
                "差异物料名称": "MPART.NAME",
                "差异料号": "MPART.NO", 
                "其上阶料号": "MPART.PRNT",
                "数量": "MPART.BNUM",
                "工位": "MPART.OP",
                "备注": "REMARK"
            },
            # 子阶BOM列映射
            "sub_bom": {
                "物料名称": "MPART.NAME",
                "子阶料号": "MPART.NO",
                "上阶料号": "MPART.PRNT", 
                "数量": "MPART.BNUM",
                "工位": "MPART.OP",
                "备注": "REMARK"
            }
        }
    
    def parse_excel_file(self, excel_file_path: str) -> Dict[str, Any]:
        """
        解析Excel差异文件
        
        Args:
            excel_file_path: Excel文件路径
            
        Returns:
            解析结果字典
        """
        try:
            logger.info(f"开始解析Excel文件: {excel_file_path}")
            
            # 读取Excel文件
            xls = pd.ExcelFile(excel_file_path)
            
            # 查找BOM差异表sheet
            diff_sheet_name = self._find_diff_sheet(xls.sheet_names)
            if not diff_sheet_name:
                raise ValueError("未找到BOM差异表sheet")
            
            # 读取差异表数据
            df = pd.read_excel(excel_file_path, sheet_name=diff_sheet_name, header=None)
            
            # 解析差异表
            result = self._parse_diff_sheet(df)
            
            logger.info("Excel文件解析完成")
            return result
            
        except Exception as e:
            logger.error(f"解析Excel文件失败: {e}")
            raise
    
    def _find_diff_sheet(self, sheet_names: List[str]) -> Optional[str]:
        """查找BOM差异表sheet"""
        keywords = ["BOM差异表", "差异表", "BOM差异", "差异BOM"]
        
        for sheet_name in sheet_names:
            for keyword in keywords:
                if keyword in sheet_name:
                    return sheet_name
        
        return None
    
    def _parse_diff_sheet(self, df: pd.DataFrame) -> Dict[str, Any]:
        """解析差异表sheet"""
        logger.info("解析BOM差异表数据")
        
        # 提取基本信息
        model_info = self._extract_model_info(df)
        
        # 查找数据区域
        diff_start_row, diff_end_row = self._find_diff_data_range(df)
        sub_bom_start_row, sub_bom_end_row = self._find_sub_bom_data_range(df)
        
        # 解析差异数据
        diff_items = []
        if diff_start_row is not None and diff_end_row is not None:
            diff_items = self._parse_diff_data(df, diff_start_row, diff_end_row)
        
        # 解析子阶BOM数据
        sub_bom_items = []
        if sub_bom_start_row is not None and sub_bom_end_row is not None:
            sub_bom_items = self._parse_sub_bom_data(df, sub_bom_start_row, sub_bom_end_row)
        
        # 构建结果
        result = {
            "model_info": model_info,
            "diff_items": [item.to_dict() for item in diff_items],
            "sub_bom_items": [item.to_dict() for item in sub_bom_items],
            "statistics": {
                "diff_count": len(diff_items),
                "sub_bom_count": len(sub_bom_items)
            }
        }
        
        return result
    
    def _extract_model_info(self, df: pd.DataFrame) -> Dict[str, str]:
        """提取型号信息"""
        model_info = {
            "base_model": "",
            "target_model": "",
            "title": ""
        }
        
        # 查找标题行（第一行）
        if len(df) > 0:
            title_cell = str(df.iloc[0, 0]) if not pd.isna(df.iloc[0, 0]) else ""
            model_info["title"] = title_cell
            
            # 从标题中提取目标型号
            match = re.search(r'([A-Z]+\d+[A-Z0-9\-]+)', title_cell)
            if match is None:
                match = re.search(r'(\S+)\s+机种', title_cell)
            if match:
                model_info["target_model"] = match.group(1)
        
        # 查找Base BOM型号（第二行）
        if len(df) > 1:
            for col in range(df.shape[1]):
                cell_value = str(df.iloc[1, col]) if not pd.isna(df.iloc[1, col]) else ""
                if "Base BOM" in cell_value:
                    # 提取Base BOM型号
                    match = re.search(r'([A-Z]+\d+[A-Z0-9\-]+)', cell_value)
                    if match:
                        model_info["base_model"] = match.group(1)
                    break
        
        logger.info(f"提取到型号信息: {model_info}")
        return model_info
    
    def _find_diff_data_range(self, df: pd.DataFrame) -> Tuple[Optional[int], Optional[int]]:
        """查找差异数据范围"""
        start_row = None
        end_row = None
        
        # 查找差异数据开始行（包含"差异物料名称"的行）
        for i in range(len(df)):
            for col in range(df.shape[1]):
                cell_value = str(df.iloc[i, col]) if not pd.isna(df.iloc[i, col]) else ""
                if "差异物料名称" in cell_value:
                    start_row = i + 1  # 数据从下一行开始
                    break
            if start_row is not None:
                break
        
        if start_row is None:
            return None, None
        
        # 查找差异数据结束行（遇到空行或"子阶BOM建立"）
        for i in range(start_row, len(df)):
            # 检查是否为空行
            row_empty = True
            for col in range(df.shape[1]):
                if not pd.isna(df.iloc[i, col]) and str(df.iloc[i, col]).strip():
                    row_empty = False
                    break
            
            # 检查是否包含"子阶BOM建立"
            contains_sub_bom = False
            for col in range(df.shape[1]):
                cell_value = str(df.iloc[i, col]) if not pd.isna(df.iloc[i, col]) else ""
                if "子阶BOM建立" in cell_value:
                    contains_sub_bom = True
                    break
            
            if row_empty or contains_sub_bom:
                end_row = i
                break
        
        if end_row is None:
            end_row = len(df)
        
        logger.info(f"差异数据范围: {start_row} - {end_row}")
        return start_row, end_row
    
    def _find_sub_bom_data_range(self, df: pd.DataFrame) -> Tuple[Optional[int], Optional[int]]:
        """查找子阶BOM数据范围"""
        start_row = None
        end_row = None
        
        # 查找子阶BOM数据开始行（包含"物料名称"且在"子阶BOM建立"之后的行）
        sub_bom_found = False
        for i in range(len(df)):
            for col in range(df.shape[1]):
                cell_value = str(df.iloc[i, col]) if not pd.isna(df.iloc[i, col]) else ""
                if "子阶BOM建立" in cell_value:
                    sub_bom_found = True
                elif sub_bom_found and "物料名称" in cell_value:
                    start_row = i + 1  # 数据从下一行开始
                    break
            if start_row is not None:
                break
        
        if start_row is None:
            return None, None
        
        # 查找子阶BOM数据结束行（遇到连续空行或文件结束）
        empty_count = 0
        for i in range(start_row, len(df)):
            # 检查是否为空行
            row_empty = True
            for col in range(df.shape[1]):
                if not pd.isna(df.iloc[i, col]) and str(df.iloc[i, col]).strip():
                    row_empty = False
                    break
            
            if row_empty:
                empty_count += 1
                if empty_count >= 2:  # 连续2个空行则结束
                    end_row = i - empty_count + 1
                    break
            else:
                empty_count = 0
        
        if end_row is None:
            end_row = len(df)
        
        logger.info(f"子阶BOM数据范围: {start_row} - {end_row}")
        return start_row, end_row
    
    def _parse_diff_data(self, df: pd.DataFrame, start_row: int, end_row: int) -> List[DiffItem]:
        """解析差异数据"""
        diff_items = []
        
        for i in range(start_row, end_row):
            # 检查是否为有效数据行
            if self._is_empty_row(df, i):
                continue
            
            try:
                item = DiffItem()
                
                # 解析物料名称（第0列）
                item.MPART_NAME = self._get_cell_value(df, i, 0)
                
                # 解析基准BOM数据（列1-6）
                item.BASE_MPART_NO = self._get_cell_value(df, i, 1)
                item.BASE_MPART_PRNT = self._get_cell_value(df, i, 2)
                # 跳过位置号（列3）
                item.BASE_MPART_BNUM = self._get_int_value(df, i, 4)
                item.BASE_MPART_OP = self._get_cell_value(df, i, 5)
                item.BASE_REMARK = self._get_cell_value(df, i, 6)
                
                # 解析目标BOM数据（列7-12）
                item.TARGET_MPART_NO = self._get_cell_value(df, i, 7)
                item.TARGET_MPART_PRNT = self._get_cell_value(df, i, 8)
                # 跳过位置号（列9）
                item.TARGET_MPART_BNUM = self._get_int_value(df, i, 10)
                item.TARGET_MPART_OP = self._get_cell_value(df, i, 11)
                item.TARGET_REMARK = self._get_cell_value(df, i, 12)
                
                # 只添加有效的差异项
                if item.MPART_NAME or item.BASE_MPART_NO or item.TARGET_MPART_NO:
                    diff_items.append(item)
                    
            except Exception as e:
                logger.warning(f"解析第{i+1}行差异数据时出错: {e}")
                continue
        
        logger.info(f"解析到 {len(diff_items)} 个差异项")
        return diff_items
    
    def _parse_sub_bom_data(self, df: pd.DataFrame, start_row: int, end_row: int) -> List[SubBomItem]:
        """解析子阶BOM数据"""
        sub_bom_items = []
        last_parent = ""  # 记录上一个有效的父件编号，用于处理合并单元格
        
        for i in range(start_row, end_row):
            # 检查是否为有效数据行
            if self._is_empty_row(df, i):
                continue
            
            try:
                item = SubBomItem()
                
                # 解析子阶BOM数据
                item.MPART_NAME = self._get_cell_value(df, i, 0)
                item.MPART_NO = self._get_cell_value(df, i, 1)
                item.MPART_PRNT = self._get_cell_value(df, i, 2)
                # 跳过位置号（列3）
                item.MPART_BNUM = self._get_int_value(df, i, 4)
                item.MPART_OP = self._get_cell_value(df, i, 5)
                item.REMARK = self._get_cell_value(df, i, 6)
                
                # 处理合并单元格导致的空白父件问题
                if not item.MPART_PRNT and last_parent:
                    item.MPART_PRNT = last_parent
                    logger.debug(f"第{i+1}行继承上一行的父件: {last_parent}")
                elif item.MPART_PRNT:
                    # 更新最后一个有效的父件编号
                    last_parent = item.MPART_PRNT
                
                # 设置默认REMARK为"Add"（如果为空）
                if not item.REMARK:
                    item.REMARK = "Add"
                
                # 只添加有效的子阶BOM项
                # if item.MPART_NAME and item.MPART_NO:
                if item.MPART_NO:
                    sub_bom_items.append(item)
                    logger.debug(f"添加子阶BOM项: {item.MPART_NAME} ({item.MPART_NO}) -> 父件: {item.MPART_PRNT}")
                    
            except Exception as e:
                logger.warning(f"解析第{i+1}行子阶BOM数据时出错: {e}")
                continue
        
        logger.info(f"解析到 {len(sub_bom_items)} 个子阶BOM项")
        return sub_bom_items
    
    def _is_empty_row(self, df: pd.DataFrame, row: int) -> bool:
        """检查是否为空行"""
        for col in range(df.shape[1]):
            if not pd.isna(df.iloc[row, col]) and str(df.iloc[row, col]).strip():
                return False
        return True
    
    def _get_cell_value(self, df: pd.DataFrame, row: int, col: int) -> str:
        """获取单元格字符串值"""
        if col >= df.shape[1]:
            return ""
        
        value = df.iloc[row, col]
        if pd.isna(value):
            return ""
        
        return str(value).strip()
    
    def _get_int_value(self, df: pd.DataFrame, row: int, col: int) -> int:
        """获取单元格整数值"""
        value_str = self._get_cell_value(df, row, col)
        if not value_str:
            return 0
        
        try:
            # 尝试转换为整数
            return int(float(value_str))
        except (ValueError, TypeError):
            return 0
    
    def save_result(self, result: Dict[str, Any], output_path: str = None) -> str:
        """
        保存解析结果到JSON文件
        
        Args:
            result: 解析结果
            output_path: 输出路径（可选，如果不提供则自动生成）
            
        Returns:
            实际保存的文件路径
        """
        try:
            # 如果没有提供输出路径，则自动生成
            if not output_path:
                output_path = self._generate_output_path(result)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 保存JSON文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"解析结果已保存到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"保存解析结果失败: {e}")
            raise
    
    def _generate_output_path(self, result: Dict[str, Any]) -> str:
        """生成输出文件路径"""
        model_info = result.get("model_info", {})
        base_model = model_info.get("base_model", "")
        target_model = model_info.get("target_model", "")
        
        if not base_model or not target_model:
            raise ValueError("无法生成输出路径：缺少基准型号或目标型号信息")
        
        # 确定型号类型
        model_type = self._extract_model_type(target_model)
        
        # 生成文件名
        filename = f"{base_model}_to_{target_model}.json"
        
        # 生成完整路径
        base_dir = Path(__file__).resolve().parents[3]  # 回到项目根目录
        output_dir = base_dir / "data" / "processed"
        output_path = output_dir / filename
        
        return str(output_path)
    
    def _extract_model_type(self, model_name: str) -> str:
        """提取型号类型"""
        if not model_name:
            return "UNKNOWN"
        
        # 提取型号前缀
        match = re.match(r'^([A-Z]+)', model_name)
        if match:
            prefix = match.group(1)
            if prefix in ['TA', 'SP', 'HSP']:
                return prefix
        
        # 默认返回前两个字符
        return model_name[:2] if len(model_name) >= 2 else model_name


def parse_diff_file(excel_file_path: str, output_path: str = None) -> Tuple[Dict[str, Any], str]:
    """
    解析差异文件的便捷函数
    
    Args:
        excel_file_path: Excel文件路径
        output_path: 输出JSON文件路径（可选，如果不提供则自动生成）
        
    Returns:
        (解析结果字典, 实际保存的文件路径)
    """
    parser = EnhancedDiffParser()
    result = parser.parse_excel_file(excel_file_path)
    
    # 保存结果并返回实际路径
    actual_output_path = parser.save_result(result, output_path)
    
    return result, actual_output_path


# BOMGenerator 功能已集成到其他模块中，这里不需要导入
# 如果需要BOM生成功能，请使用 simple_ai_generator 和 bom_transformer 模块


# ==================== API接口函数 ====================

def parse_diff_excel(excel_file_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    解析Excel差异文件 (供API调用的接口)
    
    Args:
        excel_file_path: Excel文件路径
        output_dir: 输出目录，默认为 'data/processed'
        
    Returns:
        dict: 包含解析结果的字典
        {
            'success': bool,
            'data': dict,  # 解析数据
            'file_path': str,  # 保存的文件路径
            'stats': dict  # 统计信息
        }
    """
    try:
        logger.info(f"开始解析Excel差异文件: {excel_file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(excel_file_path):
            return {
                'success': False,
                'error': f'文件不存在: {excel_file_path}',
                'data': None,
                'file_path': None,
                'stats': None
            }
        
        # 解析差异文件
        parser = EnhancedDiffParser()
        result = parser.parse_excel_file(excel_file_path)
        
        # 生成输出路径
        if output_dir is None:
            output_dir = "data/processed"
        
        model_info = result.get("model_info", {})
        base_model = model_info.get("base_model", "")
        target_model = model_info.get("target_model", "")
        
        if base_model and target_model:
            filename = f"{base_model}_to_{target_model}.json"
        else:
            # 如果无法提取型号，使用时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diff_result_{timestamp}.json"
        
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, filename)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 统计信息
        stats = {
            'base_model': base_model,
            'target_model': target_model,
            'diff_count': result['statistics']['diff_count'],
            'sub_bom_count': result['statistics']['sub_bom_count'],
            'total_changes': result['statistics']['diff_count'] + result['statistics']['sub_bom_count'],
            'parse_time': datetime.now().isoformat()
        }
        
        logger.info(f"差异文件解析成功: {stats['diff_count']}个差异项, {stats['sub_bom_count']}个子阶BOM项")
        
        return {
            'success': True,
            'data': result,
            'file_path': output_file,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"解析Excel差异文件失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None,
            'file_path': None,
            'stats': None
        }

def get_diff_analysis(excel_file_path: str) -> Optional[Dict[str, Any]]:
    """
    获取差异分析数据 (不保存文件，仅返回数据)
    
    Args:
        excel_file_path: Excel文件路径
        
    Returns:
        dict: 差异分析数据或None
    """
    try:
        parser = EnhancedDiffParser()
        return parser.parse_excel_file(excel_file_path)
    except Exception as e:
        logger.error(f"获取差异分析数据失败: {e}")
        return None

def batch_parse_diff_files(file_list: List[str], output_dir: str = None) -> Dict[str, Any]:
    """
    批量解析差异文件
    
    Args:
        file_list: Excel文件路径列表
        output_dir: 输出目录
        
    Returns:
        dict: 批量解析结果
    """
    results = []
    success_count = 0
    
    for excel_file in file_list:
        result = parse_diff_excel(excel_file, output_dir)
        results.append({
            'file': excel_file,
            **result
        })
        
        if result['success']:
            success_count += 1
    
    return {
        'total': len(file_list),
        'success': success_count,
        'failed': len(file_list) - success_count,
        'results': results
    }

def validate_excel_file(excel_file_path: str) -> Dict[str, Any]:
    """
    验证Excel文件格式和内容
    
    Args:
        excel_file_path: Excel文件路径
        
    Returns:
        dict: 验证结果
    """
    try:
        # 检查文件存在性
        if not os.path.exists(excel_file_path):
            return {
                'valid': False,
                'error': '文件不存在',
                'details': []
            }
        
        # 检查文件格式
        if not excel_file_path.lower().endswith(('.xlsx', '.xls')):
            return {
                'valid': False,
                'error': '不支持的文件格式',
                'details': ['仅支持 .xlsx 和 .xls 格式']
            }
        
        # 尝试读取Excel文件
        try:
            xls = pd.ExcelFile(excel_file_path)
            sheet_names = xls.sheet_names
        except Exception as e:
            return {
                'valid': False,
                'error': '无法读取Excel文件',
                'details': [str(e)]
            }
        
        # 检查是否包含差异表sheet
        parser = EnhancedDiffParser()
        diff_sheet = parser._find_diff_sheet(sheet_names)
        
        details = []
        if diff_sheet:
            details.append(f"找到差异表sheet: {diff_sheet}")
        else:
            details.append("未找到标准的差异表sheet")
        
        details.append(f"包含sheet: {', '.join(sheet_names)}")
        
        return {
            'valid': diff_sheet is not None,
            'error': None if diff_sheet else '未找到差异表sheet',
            'details': details,
            'sheet_names': sheet_names,
            'diff_sheet': diff_sheet
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'验证过程出错: {str(e)}',
            'details': []
        }

# ==================== CLI工具函数 ====================

def save_diff_analysis_to_file(excel_file_path: str, output_dir: str = None) -> bool:
    """
    解析并保存差异分析数据到文件 (CLI工具用)
    
    Args:
        excel_file_path: Excel文件路径
        output_dir: 输出目录
        
    Returns:
        bool: 是否成功
    """
    result = parse_diff_excel(excel_file_path, output_dir)
    
    if result['success']:
        print(f"✓ 差异分析数据已保存到: {result['file_path']}")
        
        stats = result['stats']
        print(f"解析统计:")
        print(f"  基准型号: {stats['base_model']}")
        print(f"  目标型号: {stats['target_model']}")
        print(f"  差异项数: {stats['diff_count']}")
        print(f"  子阶BOM项数: {stats['sub_bom_count']}")
        print(f"  总变更数: {stats['total_changes']}")
        
        # 显示详细差异信息
        data = result['data']
        if data['diff_items']:
            print(f"\n差异项详情:")
            for i, item in enumerate(data['diff_items'][:5], 1):  # 只显示前5个
                print(f"  {i}. {item['MPART.NAME']}")
                base_no = item['base_bom']['MPART.NO']
                target_no = item['target_bom']['MPART.NO']
                if base_no != target_no:
                    print(f"     料号变更: {base_no} → {target_no}")
                base_qty = item['base_bom']['MPART.BNUM']
                target_qty = item['target_bom']['MPART.BNUM']
                if base_qty != target_qty:
                    print(f"     数量变更: {base_qty} → {target_qty}")
            
            if len(data['diff_items']) > 5:
                print(f"  ... 还有 {len(data['diff_items']) - 5} 个差异项")
        
        if data['sub_bom_items']:
            print(f"\n新增子阶BOM项:")
            for i, item in enumerate(data['sub_bom_items'][:5], 1):  # 只显示前5个
                print(f"  {i}. {item['MPART.NAME']} ({item['MPART.NO']})")
            
            if len(data['sub_bom_items']) > 5:
                print(f"  ... 还有 {len(data['sub_bom_items']) - 5} 个子阶BOM项")
        
        return True
    else:
        print(f"✗ 解析失败: {result['error']}")
        return False

def validate_and_show_excel_info(excel_file_path: str) -> bool:
    """
    验证并显示Excel文件信息
    
    Args:
        excel_file_path: Excel文件路径
        
    Returns:
        bool: 是否有效
    """
    print(f"验证Excel文件: {excel_file_path}")
    
    validation = validate_excel_file(excel_file_path)
    
    if validation['valid']:
        print("✓ 文件验证通过")
        print(f"  差异表sheet: {validation['diff_sheet']}")
        print(f"  所有sheet: {', '.join(validation['sheet_names'])}")
        return True
    else:
        print(f"✗ 文件验证失败: {validation['error']}")
        if validation['details']:
            for detail in validation['details']:
                print(f"  - {detail}")
        return False

def main():
    """
    CLI工具主函数
    """
    while True:
        print("\n=== 增强版差异表解析器 ===")
        print("1. 解析单个Excel差异文件")
        print("2. 批量解析Excel差异文件")
        print("3. 验证Excel文件格式")
        print("4. 查看差异分析数据 (不保存)")
        print("5. 解析测试文件")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-5): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
            
        elif choice == '1':
            excel_file = input("请输入Excel文件路径: ").strip()
            if excel_file:
                output_dir = input("请输入输出目录 (默认: data/processed): ").strip()
                if not output_dir:
                    output_dir = None
                
                save_diff_analysis_to_file(excel_file, output_dir)
            else:
                print("文件路径不能为空")
                
        elif choice == '2':
            files_input = input("请输入Excel文件路径列表 (用逗号分隔): ").strip()
            if files_input:
                file_list = [f.strip() for f in files_input.split(',') if f.strip()]
                output_dir = input("请输入输出目录 (默认: data/processed): ").strip()
                if not output_dir:
                    output_dir = None
                
                print(f"\n开始批量解析 {len(file_list)} 个文件...")
                batch_result = batch_parse_diff_files(file_list, output_dir)
                
                print(f"\n批量解析完成:")
                print(f"  总计: {batch_result['total']} 个文件")
                print(f"  成功: {batch_result['success']} 个文件")
                print(f"  失败: {batch_result['failed']} 个文件")
                
                if batch_result['failed'] > 0:
                    print(f"\n失败的文件:")
                    for result in batch_result['results']:
                        if not result['success']:
                            print(f"  {os.path.basename(result['file'])}: {result['error']}")
            else:
                print("文件列表不能为空")
                
        elif choice == '3':
            excel_file = input("请输入Excel文件路径: ").strip()
            if excel_file:
                validate_and_show_excel_info(excel_file)
            else:
                print("文件路径不能为空")
                
        elif choice == '4':
            excel_file = input("请输入Excel文件路径: ").strip()
            if excel_file:
                diff_data = get_diff_analysis(excel_file)
                if diff_data:
                    model_info = diff_data['model_info']
                    stats = diff_data['statistics']
                    
                    print(f"\n差异分析结果:")
                    print(f"  标题: {model_info['title']}")
                    print(f"  基准型号: {model_info['base_model']}")
                    print(f"  目标型号: {model_info['target_model']}")
                    print(f"  差异项数: {stats['diff_count']}")
                    print(f"  子阶BOM项数: {stats['sub_bom_count']}")
                else:
                    print("解析失败或无数据")
            else:
                print("文件路径不能为空")
                
        elif choice == '5':
            test_files = [
                "data/input/SP0030-3Q-23-5QP BOM建立申请单 20240704.xls"
            ]
            
            print("尝试解析测试文件:")
            for test_file in test_files:
                print(f"\n测试文件: {test_file}")
                if os.path.exists(test_file):
                    save_diff_analysis_to_file(test_file)
                else:
                    print(f"  文件不存在: {test_file}")
            
        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    # 如果直接运行此脚本，启动CLI工具
    main()