#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件解析工具
用于解析EHS法律法规Excel文件
"""

import openpyxl
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime


class ExcelParser:
    """Excel文件解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_excel_file(self, file_path: str, sheet_index: int = 0) -> Dict:
        """
        解析Excel文件
        
        Args:
            file_path: Excel文件路径
            sheet_index: 工作表索引，默认为0（第一个工作表）
            
        Returns:
            包含解析结果的字典
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': f'文件不存在: {file_path}'
                }
            
            # 检查文件扩展名
            if file_path.suffix.lower() not in ['.xlsx', '.xls']:
                return {
                    'success': False,
                    'error': '不支持的文件格式，仅支持 .xlsx 和 .xls'
                }
            
            self.logger.info(f"开始解析Excel文件: {file_path}")
            
            # 加载工作簿
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            
            # 获取工作表
            if sheet_index >= len(workbook.sheetnames):
                return {
                    'success': False,
                    'error': f'工作表索引超出范围，文件共有 {len(workbook.sheetnames)} 个工作表'
                }
            
            sheet_name = workbook.sheetnames[sheet_index]
            worksheet = workbook[sheet_name]
            
            self.logger.info(f"正在解析工作表: {sheet_name}")
            
            # 解析数据
            data = []
            headers = []
            
            for row_idx, row in enumerate(worksheet.iter_rows(values_only=True), start=1):
                # 跳过空行
                if not any(row):
                    continue
                
                # 第一行作为表头
                if row_idx == 1:
                    headers = [str(cell) if cell is not None else f'Column{i}' 
                              for i, cell in enumerate(row)]
                    continue
                
                # 解析数据行
                row_data = {}
                for i, cell in enumerate(row):
                    if i < len(headers):
                        # 处理日期格式
                        if isinstance(cell, datetime):
                            cell_value = cell.strftime('%Y-%m-%d')
                        elif cell is None or str(cell).strip() == '' or str(cell).strip().upper() == '#N/A':
                            cell_value = ''
                        else:
                            cell_value = str(cell).strip()
                        
                        row_data[headers[i]] = cell_value
                
                # 只添加非空行
                if any(row_data.values()):
                    data.append(row_data)
            
            workbook.close()
            
            self.logger.info(f"解析完成，共 {len(data)} 行数据")
            
            return {
                'success': True,
                'data': data,
                'sheet_name': sheet_name,
                'total_sheets': len(workbook.sheetnames),
                'row_count': len(data),
                'headers': headers
            }
            
        except Exception as e:
            self.logger.error(f"解析Excel文件失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_excel_to_law_format(self, file_path: str, sheet_index: int = 0) -> Dict:
        """
        解析Excel文件并转换为法律法规格式
        
        Args:
            file_path: Excel文件路径
            sheet_index: 工作表索引
            
        Returns:
            包含法律法规数据的字典
        """
        result = self.parse_excel_file(file_path, sheet_index)
        
        if not result['success']:
            return result
        
        # 转换为法律法规格式
        laws = []
        errors = []
        
        for idx, row in enumerate(result['data'], start=1):
            try:
                # 映射字段（根据实际Excel列名调整）
                law_data = {
                    '序号': row.get('序号', '') or row.get('编号', '') or str(idx),
                    '法律、法规、标准及其他要求': row.get('法律、法规、标准及其他要求', '') or row.get('法律名称', '') or row.get('名称', ''),
                    '施行（修改）日期': self._normalize_date(row.get('施行（修改）日期', '') or row.get('施行日期', '') or row.get('日期', '')),
                    '颁布部门': row.get('颁布部门', '') or row.get('发布部门', ''),
                    '标准编号': row.get('标准编号', '') or row.get('编号', ''),
                    '适用条款': row.get('适用条款', '') or row.get('条款', ''),
                    '获取途径': row.get('获取途径', '') or row.get('来源', ''),
                    '网址': row.get('网址', '') or row.get('链接', '')
                }
                
                # 验证必填字段
                if not law_data['法律、法规、标准及其他要求']:
                    errors.append(f"第{idx}行：法律名称不能为空")
                    continue
                
                laws.append(law_data)
                
            except Exception as e:
                errors.append(f"第{idx}行：解析失败 - {str(e)}")
        
        return {
            'success': True,
            'data': laws,
            'sheet_name': result['sheet_name'],
            'total_count': len(laws),
            'error_count': len(errors),
            'errors': errors
        }
    
    def _normalize_date(self, date_str: str) -> str:
        """标准化日期格式为 YYYY-MM-DD"""
        if not date_str:
            return ''
        
        date_str = str(date_str).strip()
        
        # 移除时间部分
        date_str = date_str.replace(' 00:00:00', '').strip()
        
        # 处理 YYYY/M/D 格式
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                year, month, day = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 处理 YYYY-M-D 格式
        if '-' in date_str:
            parts = date_str.split('-')
            if len(parts) == 3:
                year, month, day = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return date_str


def main():
    """测试函数"""
    parser = ExcelParser()
    
    # 测试文件路径
    test_file = Path(__file__).parent.parent.parent.parent / "tmp" / "EHS适用法律法规及其他要求清单-2025.4.11更新.xlsx"
    
    if test_file.exists():
        print(f"测试文件: {test_file}")
        result = parser.parse_excel_to_law_format(str(test_file))
        
        if result['success']:
            print(f"✓ 解析成功")
            print(f"  工作表: {result['sheet_name']}")
            print(f"  数据行数: {result['total_count']}")
            print(f"  错误数: {result['error_count']}")
            
            if result['data']:
                print(f"\n前3条数据:")
                for i, law in enumerate(result['data'][:3], 1):
                    print(f"  {i}. {law['法律、法规、标准及其他要求']}")
        else:
            print(f"✗ 解析失败: {result['error']}")
    else:
        print(f"测试文件不存在: {test_file}")


if __name__ == "__main__":
    main()
