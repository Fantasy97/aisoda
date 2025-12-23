import json
import argparse
import os
from docx import Document
from lxml import etree


class TableProcessor:
    """表格处理器 - 负责表格XML解析、结构识别和单元格数据处理"""
    
    def __init__(self):
        pass
    
    def extract_table_structure(self, table_element, table_obj):
        """解析表格XML结构，识别合并单元格和列关系"""
        try:
            # 获取表格的行数和列数
            rows = table_element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr')
            if not rows:
                return None
                
            # 分析表格结构
            structure_info = {
                'rows': len(rows),
                'columns': 0,
                'cells': [],
                'merge_info': []
            }
            
            # 计算最大列数
            max_cols = 0
            for row_idx, row in enumerate(rows):
                cells = row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
                col_count = 0
                for cell in cells:
                    # 检查gridSpan属性（水平合并）
                    grid_span = 1
                    tc_pr = cell.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr')
                    if tc_pr is not None:
                        grid_span_elem = tc_pr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridSpan')
                        if grid_span_elem is not None:
                            grid_span = int(grid_span_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '1'))
                    col_count += grid_span
                max_cols = max(max_cols, col_count)
            
            structure_info['columns'] = max_cols
            
            # 解析每个单元格的详细信息
            for row_idx, row in enumerate(rows):
                cells = row.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc')
                col_idx = 0
                
                for cell in cells:
                    cell_info = {
                        'row': row_idx,
                        'col': col_idx,
                        'content': '',
                        'grid_span': 1,
                        'v_merge': None,
                        'is_merged': False
                    }
                    
                    # 提取单元格内容
                    paragraphs = cell.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p')
                    content_parts = []
                    for p in paragraphs:
                        if p.text:
                            content_parts.append(p.text.strip())
                    cell_info['content'] = '\n'.join(content_parts) if content_parts else ''
                    
                    # 解析单元格属性
                    tc_pr = cell.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tcPr')
                    if tc_pr is not None:
                        # gridSpan (水平合并)
                        grid_span_elem = tc_pr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gridSpan')
                        if grid_span_elem is not None:
                            cell_info['grid_span'] = int(grid_span_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '1'))
                            if cell_info['grid_span'] > 1:
                                cell_info['is_merged'] = True
                        
                        # vMerge (垂直合并)
                        v_merge_elem = tc_pr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}vMerge')
                        if v_merge_elem is not None:
                            v_merge_val = v_merge_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            cell_info['v_merge'] = v_merge_val if v_merge_val else 'continue'
                            cell_info['is_merged'] = True
                    
                    structure_info['cells'].append(cell_info)
                    col_idx += cell_info['grid_span']
            
            return structure_info
            
        except Exception as e:
            print(f"Error parsing table structure: {e}")
            return None
        
    def detect_merged_cells(self, structure_info):
        """识别水平和垂直合并的单元格"""
        if not structure_info:
            return []
        
        merged_regions = []
        cells = structure_info['cells']
        
        # 创建一个网格来跟踪已处理的单元格
        grid = {}
        for cell in cells:
            grid[(cell['row'], cell['col'])] = cell
        
        # 检测水平合并
        for cell in cells:
            if cell['grid_span'] > 1:
                merged_regions.append({
                    'type': 'horizontal',
                    'start_row': cell['row'],
                    'end_row': cell['row'],
                    'start_col': cell['col'],
                    'end_col': cell['col'] + cell['grid_span'] - 1,
                    'content': cell['content']
                })
        
        # 检测垂直合并
        processed_v_merge = set()
        for cell in cells:
            if cell['v_merge'] == 'restart' and (cell['row'], cell['col']) not in processed_v_merge:
                # 找到垂直合并的结束位置
                end_row = cell['row']
                for r in range(cell['row'] + 1, structure_info['rows']):
                    next_cell = grid.get((r, cell['col']))
                    if next_cell and next_cell['v_merge'] == 'continue':
                        end_row = r
                        processed_v_merge.add((r, cell['col']))
                    else:
                        break
                
                if end_row > cell['row']:
                    merged_regions.append({
                        'type': 'vertical',
                        'start_row': cell['row'],
                        'end_row': end_row,
                        'start_col': cell['col'],
                        'end_col': cell['col'],
                        'content': cell['content']
                    })
                    processed_v_merge.add((cell['row'], cell['col']))
        
        return merged_regions
        
    def analyze_column_relationships(self, structure_info, processed_data):
        """分析表格纵列的组合关系"""
        if not structure_info or not processed_data:
            return []
        
        relationships = []
        merged_regions = self.detect_merged_cells(structure_info)
        cols = structure_info['columns']
        
        # 分析水平合并形成的列组合关系
        horizontal_merges = [r for r in merged_regions if r['type'] == 'horizontal']
        
        # 按行分组分析
        row_groups = {}
        for merge in horizontal_merges:
            row = merge['start_row']
            if row not in row_groups:
                row_groups[row] = []
            row_groups[row].append(merge)
        
        # 识别标题行的列组合
        for row_idx, merges in row_groups.items():
            for merge in merges:
                start_col = merge['start_col']
                end_col = merge['end_col']
                content = merge['content'].strip()
                
                # 判断关系类型
                relationship_type = "merged_header"
                if row_idx == 0:
                    relationship_type = "main_header"
                elif "年" in content or "时间" in content:
                    relationship_type = "time_group"
                elif "情况" in content or "信息" in content:
                    relationship_type = "info_group"
                elif len(content) > 10:
                    relationship_type = "description_group"
                
                relationships.append({
                    'columns': list(range(start_col, end_col + 1)),
                    'relationship': relationship_type,
                    'content': content,
                    'row': row_idx
                })
        
        # 去重和优化关系
        unique_relationships = []
        seen_columns = set()
        
        for rel in relationships:
            col_tuple = tuple(rel['columns'])
            if col_tuple not in seen_columns:
                unique_relationships.append(rel)
                seen_columns.add(col_tuple)
        
        return unique_relationships
    
    def deduplicate_merged_cells(self, table_data, structure_info):
        """去除合并单元格中的重复内容"""
        if not structure_info or not table_data:
            return table_data
        
        # 创建去重后的表格数据副本
        processed_data = [row[:] for row in table_data]  # 深拷贝
        
        # 获取合并区域信息
        merged_regions = self.detect_merged_cells(structure_info)
        
        # 对每个合并区域进行去重处理
        for region in merged_regions:
            start_row, end_row = region['start_row'], region['end_row']
            start_col, end_col = region['start_col'], region['end_col']
            
            # 保留左上角单元格的内容，其他位置置空或标记
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    if r < len(processed_data) and c < len(processed_data[r]):
                        if r == start_row and c == start_col:
                            # 保留原始内容
                            continue
                        else:
                            # 清空重复内容，但保留合并标记
                            processed_data[r][c] = ""
        
        return processed_data
        
    def build_cell_map(self, structure_info, processed_data, filter_empty_merged=True):
        """构建cell_map映射矩阵，标记合并状态和源位置"""
        if not structure_info:
            return []
        
        rows, cols = structure_info['rows'], structure_info['columns']
        cell_map = []
        
        # 初始化cell_map
        for r in range(rows):
            row_map = []
            for c in range(cols):
                row_map.append({
                    'row': r,
                    'col': c,
                    'content': '',
                    'is_merged': False,
                    'merge_source': None
                })
            cell_map.append(row_map)
        
        # 填充实际内容和合并信息
        merged_regions = self.detect_merged_cells(structure_info)
        
        # 先填充基础内容
        for r in range(min(rows, len(processed_data))):
            for c in range(min(cols, len(processed_data[r]))):
                cell_map[r][c]['content'] = processed_data[r][c]
        
        # 标记合并单元格
        for region in merged_regions:
            start_row, end_row = region['start_row'], region['end_row']
            start_col, end_col = region['start_col'], region['end_col']
            
            for r in range(start_row, end_row + 1):
                for c in range(start_col, end_col + 1):
                    if r < rows and c < cols:
                        if r == start_row and c == start_col:
                            # 源单元格
                            cell_map[r][c]['is_merged'] = True
                            cell_map[r][c]['content'] = region['content']
                        else:
                            # 合并的目标单元格
                            cell_map[r][c]['is_merged'] = True
                            cell_map[r][c]['merge_source'] = [start_row, start_col]
                            cell_map[r][c]['content'] = ""
        
        # 如果启用过滤，则过滤空的合并单元格
        if filter_empty_merged:
            cell_map = self.filter_empty_merged_cells(cell_map)
        
        return cell_map
        
    def filter_empty_merged_cells(self, cell_map):
        """
        过滤cellmap中满足以下条件的记录：
        - is_merged: true
        - content: ""（空内容）
        - merge_source: 不为null
        """
        if not cell_map:
            return cell_map
        
        filtered_cell_map = []
        
        for row in cell_map:
            filtered_row = []
            for cell in row:
                # 检查是否满足过滤条件
                should_filter = (
                    cell.get('is_merged', False) == True and
                    cell.get('content', '') == '' and
                    cell.get('merge_source') is not None
                )
                
                # 如果不满足过滤条件，保留该单元格
                if not should_filter:
                    filtered_row.append(cell)
            
            # 只有当行中还有单元格时才添加该行
            if filtered_row:
                filtered_cell_map.append(filtered_row)
        
        return filtered_cell_map


class EmptyCellAnalyzer:
    """空白单元格分析器 - 负责空白单元格关系分析"""
    
    def __init__(self):
        pass
    
    def analyze_empty_cell_relationships(self, cell_map):
        """
        分析cell_map中空内容单元格的关系
        为空内容单元格添加relationship数组，包含相关的上下文信息
        """
        if not cell_map:
            return cell_map
        
        # 创建按行列索引的快速查找字典
        position_map = {}
        for cell in cell_map:
            position_map[(cell['row'], cell['col'])] = cell
        
        # 为每个空内容单元格分析关系
        for cell in cell_map:
            if cell['content'].strip() == "":
                relationships = []
                
                # 1. 查找同行左边最近的非空内容
                left_content = self._find_left_content(cell, position_map)
                if left_content:
                    relationships.append(left_content)
                
                # 2. 向上查找该列的非空内容
                up_content = self._find_up_content(cell, position_map)
                if up_content:
                    relationships.append(up_content)
                
                # 3. 如果是连续空单元格，可能需要查找更远的上下文
                extended_context = self._find_extended_context(cell, position_map)
                for context in extended_context:
                    if context not in relationships:
                        relationships.append(context)
                
                # 添加relationship字段
                cell['relationship'] = relationships
        
        return cell_map
        
    def _find_left_content(self, cell, position_map):
        """查找同行左边最近的非空内容"""
        current_row = cell['row']
        current_col = cell['col']
        
        # 从当前列向左查找
        for col in range(current_col - 1, -1, -1):
            left_cell = position_map.get((current_row, col))
            if left_cell and left_cell['content'].strip():
                return left_cell['content'].strip()
        
        return None
        
    def _find_up_content(self, cell, position_map):
        """向上查找该列的非空内容"""
        current_row = cell['row']
        current_col = cell['col']
        
        # 从当前行向上查找
        for row in range(current_row - 1, -1, -1):
            up_cell = position_map.get((row, current_col))
            if up_cell and up_cell['content'].strip():
                return up_cell['content'].strip()
        
        return None
        
    def _find_extended_context(self, cell, position_map):
        """查找扩展的上下文信息，处理连续空单元格的情况"""
        contexts = []
        current_row = cell['row']
        current_col = cell['col']
        
        # 检查是否是连续空单元格的一部分
        consecutive_empty_cols = self._find_consecutive_empty_columns(cell, position_map)
        
        if len(consecutive_empty_cols) > 1:
            # 如果是连续空单元格，查找这个区域的边界上下文
            
            # 查找左边界的内容
            left_boundary_col = min(consecutive_empty_cols) - 1
            if left_boundary_col >= 0:
                left_boundary_cell = position_map.get((current_row, left_boundary_col))
                if left_boundary_cell and left_boundary_cell['content'].strip():
                    contexts.append(left_boundary_cell['content'].strip())
            
            # 查找右边界的内容
            right_boundary_col = max(consecutive_empty_cols) + 1
            right_boundary_cell = position_map.get((current_row, right_boundary_col))
            if right_boundary_cell and right_boundary_cell['content'].strip():
                contexts.append(right_boundary_cell['content'].strip())
            
            # 对于连续空单元格，查找每列向上的最近非空内容
            for col in consecutive_empty_cols:
                if col != current_col:  # 避免重复查找当前列
                    for row in range(current_row - 1, -1, -1):
                        up_cell = position_map.get((row, col))
                        if up_cell and up_cell['content'].strip():
                            content = up_cell['content'].strip()
                            if content not in contexts:
                                contexts.append(content)
                            break
        
        return contexts
        
    def _find_consecutive_empty_columns(self, cell, position_map):
        """查找当前行中连续的空单元格列"""
        current_row = cell['row']
        current_col = cell['col']
        consecutive_cols = [current_col]
        
        # 向左查找连续空单元格
        col = current_col - 1
        while col >= 0:
            left_cell = position_map.get((current_row, col))
            if left_cell and left_cell['content'].strip() == "":
                consecutive_cols.insert(0, col)
                col -= 1
            else:
                break
        
        # 向右查找连续空单元格
        col = current_col + 1
        while True:
            right_cell = position_map.get((current_row, col))
            if right_cell and right_cell['content'].strip() == "":
                consecutive_cols.append(col)
                col += 1
            else:
                break
        
        return consecutive_cols


class WordParser:
    """Word文档解析器主类 - 协调各个组件完成解析任务"""
    
    def __init__(self):
        self.table_processor = TableProcessor()
        self.empty_analyzer = EmptyCellAnalyzer()
    
    def extract_full_document(self, docx_path, output_path=None):
        """
        完整文档信息提取API
        
        Args:
            docx_path: Word文档路径
            output_path: 输出文件路径，默认为positioned_content.json
            
        Returns:
            dict: 完整的文档结构信息
        """
        if output_path is None:
            # 确保输出目录存在
            processed_dir = "../../data/processed"
            os.makedirs(processed_dir, exist_ok=True)
            output_path = os.path.join(processed_dir, "positioned_content.json")
        
        try:
            # 调用内部解析方法
            result = self._extract_and_process_docx(docx_path, output_path)
            
            # 验证基本结构
            assert 'document_structure' in result, "缺少document_structure字段"
            
            # 统计各类元素
            paragraphs = [item for item in result['document_structure'] if item['type'] == 'paragraph']
            tables = [item for item in result['document_structure'] if item['type'] == 'table']
            
            print(f"✓ 成功解析文档")
            print(f"  - 段落数量: {len(paragraphs)}")
            print(f"  - 表格数量: {len(tables)}")
            
            # 验证增强功能
            enhanced_tables = [t for t in tables if 'structure' in t and t['structure'] is not None]
            print(f"  - 增强解析的表格: {len(enhanced_tables)}")
            
            # 验证合并单元格检测
            total_merged_cells = 0
            for table in enhanced_tables:
                if 'cell_map' in table['structure']:
                    for row in table['structure']['cell_map']:
                        for cell in row:
                            if cell['is_merged']:
                                total_merged_cells += 1
            
            print(f"  - 检测到的合并单元格: {total_merged_cells}")
            
            # 验证列关系分析
            total_relationships = sum(len(t['structure']['column_relationships']) for t in enhanced_tables if 'column_relationships' in t['structure'])
            print(f"  - 识别的列关系: {total_relationships}")
            
            return result
            
        except Exception as e:
            print(f"✗ 文档解析失败: {e}")
            raise
        
    def extract_empty_cells(self, docx_path, output_path=None):
        """
        空白单元格分析API(重构自原test_simplified_parser函数)
        
        Args:
            docx_path: Word文档路径  
            output_path: 输出文件路径，默认为empty_cells_simplified.json
            
        Returns:
            list: 空白单元格及其关系信息
        """
        if output_path is None:
            # 确保输出目录存在
            processed_dir = "../../data/processed"
            os.makedirs(processed_dir, exist_ok=True)
            output_path = os.path.join(processed_dir, "empty_cells_simplified.json")
        
        try:
            # 首先进行完整文档解析
            processed_dir = "../../data/processed"
            os.makedirs(processed_dir, exist_ok=True)
            positioned_content_path = os.path.join(processed_dir, "positioned_content.json")
            full_result = self._extract_and_process_docx(docx_path, positioned_content_path)
            
            # 存储所有结果
            analysis_results = {
                "summary": {
                    "total_tables": 0,
                    "tables_with_empty_cells": 0,
                    "total_empty_cells": 0
                },
                "tables": []
            }
            
            for item in full_result['document_structure']:
                if item['type'] == 'table':
                    table_index = item['table_index']
                    cell_map = []
                    
                    # 将嵌套的cell_map转换为平坦的列表
                    for row_data in item['structure']['cell_map']:
                        for cell in row_data:
                            cell_map.append(cell)
                    
                    # 分析空单元格关系
                    result = self.empty_analyzer.analyze_empty_cell_relationships(cell_map)
                    
                    # 统计空单元格
                    empty_cells_with_relationships = [cell for cell in result if 'relationship' in cell]
                    
                    table_result = {
                        "table_index": table_index,
                        "total_cells": len(cell_map),
                        "empty_cells_count": len(empty_cells_with_relationships),
                        "empty_cells": empty_cells_with_relationships
                    }
                    
                    analysis_results["tables"].append(table_result)
                    analysis_results["summary"]["total_tables"] += 1
                    
                    if empty_cells_with_relationships:
                        analysis_results["summary"]["tables_with_empty_cells"] += 1
                        analysis_results["summary"]["total_empty_cells"] += len(empty_cells_with_relationships)
            
            # 输出完整的JSON结果
            output_json = json.dumps(analysis_results, ensure_ascii=False, indent=2)
            print(output_json)
            
            # 同时保存到文件
            processed_dir = "../../data/processed"
            os.makedirs(processed_dir, exist_ok=True)
            analysis_result_path = os.path.join(processed_dir, 'empty_cells_analysis_result.json')
            with open(analysis_result_path, 'w', encoding='utf-8') as f:
                f.write(output_json)
            
            # 创建简化版本：仅包含空单元格的基本信息
            simplified_empty_cells = []
            
            for table in analysis_results["tables"]:
                for empty_cell in table["empty_cells"]:
                    simplified_cell = {
                        "row": empty_cell["row"],
                        "col": empty_cell["col"], 
                        "content": empty_cell["content"],
                        "relationship": empty_cell["relationship"]
                    }
                    simplified_empty_cells.append(simplified_cell)
            
            # 输出简化版JSON
            simplified_json = json.dumps(simplified_empty_cells, ensure_ascii=False, indent=2)
            
            # 保存简化版到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(simplified_json)
            
            print(f"\n=== 简化版输出已保存到 {output_path} ===")
            print(f"总共 {len(simplified_empty_cells)} 个空单元格")
            
            return simplified_empty_cells
            
        except Exception as e:
            print(f"✗ 空白单元格分析失败: {e}")
            raise
    
    def convert_doc_to_docx(self, doc_path, docx_path=None):
        """
        将.doc文件转换为.docx格式
        
        Args:
            doc_path: 输入的.doc文件路径
            docx_path: 输出的.docx文件路径，默认为同名.docx文件
            
        Returns:
            str: 转换后的.docx文件路径
        """
        import os
        
        if not os.path.exists(doc_path):
            raise FileNotFoundError(f".doc文件不存在: {doc_path}")
        
        if not doc_path.lower().endswith('.doc'):
            raise ValueError("输入文件必须是.doc格式")
        
        if docx_path is None:
            # 生成默认的.docx文件名
            base_name = os.path.splitext(doc_path)[0]
            docx_path = base_name + '.docx'
        
        try:
            # 尝试使用win32com进行转换（Windows环境）
            try:
                import win32com.client
                
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                
                # 打开.doc文件
                doc = word.Documents.Open(os.path.abspath(doc_path))
                
                # 保存为.docx格式
                doc.SaveAs2(os.path.abspath(docx_path), FileFormat=16)  # 16 = docx格式
                doc.Close()
                word.Quit()
                
                print(f"✓ 成功转换: {doc_path} -> {docx_path}")
                return docx_path
                
            except ImportError:
                # 如果win32com不可用，提供替代方案提示
                raise Exception(
                    "无法导入win32com模块。请安装pywin32包或手动将.doc文件转换为.docx格式。\n"
                    "安装命令: pip install pywin32"
                )
                
        except Exception as e:
            print(f"✗ 文档转换失败: {e}")
            raise
        
    def _extract_and_process_docx(self, docx_path, output_file):
        """
        内部方法：完整文档解析逻辑（重构自原extract_and_process_docx函数）
        
        Args:
            docx_path: Word文档路径
            output_file: 输出JSON文件路径
        
        Returns:
            dict: 解析结果字典
        
        Raises:
            FileNotFoundError: 文档文件不存在
            Exception: 其他解析错误
        """
        try:
            doc = Document(docx_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Word文档文件不存在: {docx_path}")
        except Exception as e:
            raise Exception(f"无法打开Word文档: {e}")
        
        try:
            # 提取body元素信息
            body = doc._element.body
            body_elements = []
            for element in body:
                body_elements.append({
                    "tag": element.tag,
                    "text": element.text if hasattr(element, 'text') else ""
                })
        except Exception as e:
            print(f"警告: 提取文档结构时出错: {e}")
            body_elements = []
        
        try:
            # 提取表格数据和结构信息
            tables = []
            table_structures = []
            table_elements = body.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl') if body is not None else []
            
            for i, table in enumerate(doc.tables):
                try:
                    # 提取基础表格内容
                    table_data = []
                    for row in table.rows:
                        row_data = [cell.text.strip() for cell in row.cells]
                        table_data.append(row_data)
                    tables.append(table_data)
                    
                    # 提取表格结构信息
                    if i < len(table_elements):
                        structure = self.table_processor.extract_table_structure(table_elements[i], table)
                        table_structures.append(structure)
                    else:
                        table_structures.append(None)
                except Exception as e:
                    print(f"警告: 处理表格 {i} 时出错: {e}")
                    tables.append([])
                    table_structures.append(None)
        except Exception as e:
            print(f"警告: 提取表格数据时出错: {e}")
            tables = []
            table_structures = []
        
        # 处理位置信息
        ordered_content = []
        paragraph_index = 0
        table_index = 0
        
        for i, element in enumerate(body_elements):
            if element['tag'].endswith('}p') and element['text'] and element['text'].strip():
                ordered_content.append({
                    'type': 'paragraph',
                    'position': i,
                    'content': element['text'].strip(),
                    'paragraph_index': paragraph_index
                })
                paragraph_index += 1
            elif element['tag'].endswith('}tbl'):
                # 获取基础表格内容和结构信息
                raw_content = tables[table_index] if table_index < len(tables) else None
                structure_info = table_structures[table_index] if table_index < len(table_structures) else None
                
                # 创建增强的表格项
                table_item = {
                    'type': 'table',
                    'position': i,
                    'table_index': table_index
                }
                
                # 如果有结构信息，添加增强功能
                if structure_info and raw_content:
                    try:
                        # 去重处理
                        processed_content = self.table_processor.deduplicate_merged_cells(raw_content, structure_info)
                        
                        # 构建cell_map（默认启用过滤）
                        cell_map = self.table_processor.build_cell_map(structure_info, processed_content, filter_empty_merged=True)
                        
                        # 分析列关系
                        column_relationships = self.table_processor.analyze_column_relationships(structure_info, processed_content)
                        
                        # 添加增强的结构信息
                        table_item['structure'] = {
                            'rows': structure_info['rows'],
                            'columns': structure_info['columns'],
                            'cell_map': cell_map,
                            'column_relationships': column_relationships
                        }
                    except Exception as e:
                        print(f"警告: 处理表格 {table_index} 的结构信息时出错: {e}")
                        # 降级到基础功能
                        table_item['processed_content'] = raw_content
                        table_item['structure'] = None
                
                ordered_content.append(table_item)
                table_index += 1
        
        result = {'document_structure': ordered_content}
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告: 保存输出文件时出错: {e}")
            raise
        
        return result


def create_cli_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='Word文档解析工具 - 提供完整文档解析和空白单元格分析功能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 完整文档提取
  python word_parser.py --mode full --input document.docx --output result.json
  
  # 空白单元格分析  
  python word_parser.py --mode empty --input document.docx --output empty_cells.json
  
  # 同时执行两种分析
  python word_parser.py --mode both --input document.docx
  
  # 使用默认输出文件名
  python word_parser.py --mode full --input document.docx
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['full', 'empty', 'both'],
        required=True,
        help='解析模式: full=完整文档解析, empty=空白单元格分析, both=两种分析都执行'
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入的Word文档路径 (.docx格式)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='输出文件路径 (可选，默认使用标准文件名)'
    )
    
    parser.add_argument(
        '--convert',
        action='store_true',
        help='如果输入是.doc文件，自动转换为.docx格式'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出信息'
    )
    
    return parser


def main():
    """CLI主入口函数"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    try:
        import os
        
        # 验证输入文件
        if not os.path.exists(args.input):
            print(f"✗ 错误: 输入文件不存在: {args.input}")
            return 1
        
        # 处理文件格式转换
        input_file = args.input
        if args.input.lower().endswith('.doc'):
            if args.convert:
                print(f"正在转换 .doc 文件为 .docx 格式...")
                word_parser = WordParser()
                try:
                    input_file = word_parser.convert_doc_to_docx(args.input)
                except Exception as e:
                    print(f"✗ 文件转换失败: {e}")
                    return 1
            else:
                print(f"✗ 错误: 输入文件是 .doc 格式，请使用 --convert 参数自动转换，或手动转换为 .docx 格式")
                return 1
        elif not args.input.lower().endswith('.docx'):
            print(f"✗ 错误: 不支持的文件格式。请使用 .docx 文件")
            return 1
        
        # 创建解析器实例
        word_parser = WordParser()
        
        print(f"=== Word文档解析工具 ===")
        print(f"输入文件: {input_file}")
        print(f"解析模式: {args.mode}")
        
        # 执行解析
        if args.mode == 'full':
            if args.output:
                output_path = args.output
            else:
                processed_dir = "../../data/processed"
                os.makedirs(processed_dir, exist_ok=True)
                output_path = os.path.join(processed_dir, "positioned_content.json")
            print(f"输出文件: {output_path}")
            print("\n开始完整文档解析...")
            
            result = word_parser.extract_full_document(input_file, output_path)
            print(f"✓ 完整文档解析完成，结果已保存到: {output_path}")
            
        elif args.mode == 'empty':
            if args.output:
                output_path = args.output
            else:
                processed_dir = "../../data/processed"
                os.makedirs(processed_dir, exist_ok=True)
                output_path = os.path.join(processed_dir, "empty_cells_simplified.json")
            print(f"输出文件: {output_path}")
            print("\n开始空白单元格分析...")
            
            result = word_parser.extract_empty_cells(input_file, output_path)
            print(f"✓ 空白单元格分析完成，结果已保存到: {output_path}")
            
        elif args.mode == 'both':
            processed_dir = "../../data/processed"
            os.makedirs(processed_dir, exist_ok=True)
            positioned_path = os.path.join(processed_dir, "positioned_content.json")
            empty_path = os.path.join(processed_dir, "empty_cells_simplified.json")
            print(f"输出文件: {positioned_path}, {empty_path}")
            print("\n开始完整文档解析...")
            
            full_result = word_parser.extract_full_document(input_file, positioned_path)
            print(f"✓ 完整文档解析完成，结果已保存到: {positioned_path}")
            
            print("\n开始空白单元格分析...")
            empty_result = word_parser.extract_empty_cells(input_file, empty_path)
            print(f"✓ 空白单元格分析完成，结果已保存到: {empty_path}")
        
        print("\n=== 解析完成 ===")
        return 0
        
    except KeyboardInterrupt:
        print("\n✗ 用户中断操作")
        return 1
    except Exception as e:
        print(f"✗ 解析过程中发生错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()