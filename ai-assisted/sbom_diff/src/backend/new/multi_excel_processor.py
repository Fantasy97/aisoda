#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
多Excel文件批量处理器
支持上传多个Excel文件，自动检测3种sheet类型（PLM、GBOM、差异文件）并处理
"""

import os
import pandas as pd
import json
import logging
import uuid
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date

# 配置日志（需要在导入其他模块之前配置）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入数据库连接模块
# 添加 tools 目录到路径，用于导入 db_query
# 方法1：相对路径（从 src/backend/new 到 src/backend/tools）
tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
# 方法2：绝对路径（从项目根目录）
project_root = Path(__file__).resolve().parents[3]  # src/backend/new -> 项目根目录
tools_path_abs = os.path.join(str(project_root), 'src', 'backend', 'tools')

# 添加到 sys.path（如果不存在）
for path in [tools_path, tools_path_abs]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)
        logger.debug(f"已添加路径到 sys.path: {path}")

try:
    from db_query import get_connection
    logger.info(f"成功导入 db_query 模块")
    logger.info(f"tools_path: {tools_path}")
    logger.info(f"tools_path_abs: {tools_path_abs}")
except ImportError as e:
    # 如果无法导入数据库模块，提供一个模拟函数
    logger.error(f"无法导入 db_query 模块: {e}")
    logger.error(f"sys.path 中的相关路径: {[p for p in sys.path if 'tools' in p or 'backend' in p]}")
    def get_connection():
        logger.warning("数据库连接模块未找到，将跳过数据库保存")
        return None

# 导入现有处理模块
# 优先尝试从 new 导入（用于 app_new.py，它在 src/backend/ 目录下运行）
# 然后尝试从 src.backend.new 导入（用于测试环境，从项目根目录运行）
try:
    from new.plm_excel_processor import process_excel_auto_detect
    from new.enhanced_diff_parser import parse_diff_excel, validate_excel_file as validate_diff_file
    from new.simple_ai_generator import generate_ai_analysis_json
    from new.bom_transformer import transform_bom_json
except ImportError:
    try:
        from src.backend.new.plm_excel_processor import process_excel_auto_detect
        from src.backend.new.enhanced_diff_parser import parse_diff_excel, validate_excel_file as validate_diff_file
        from src.backend.new.simple_ai_generator import generate_ai_analysis_json
        from src.backend.new.bom_transformer import transform_bom_json
    except ImportError:
        # 最后尝试相对导入（作为包的一部分使用时）
        from .plm_excel_processor import process_excel_auto_detect
        from .enhanced_diff_parser import parse_diff_excel, validate_excel_file as validate_diff_file
        from .simple_ai_generator import generate_ai_analysis_json
        from .bom_transformer import transform_bom_json


class MultiExcelProcessor:
    """多Excel文件批量处理器"""
    
    def __init__(self, worker_id: str = "250000"):
        """
        初始化处理器
        
        Args:
            worker_id: 工号，默认为 "250000"
        """
        self.part_id_counter = 1
        self.worker_id = worker_id
    
    def _create_output_directory(self, base_output_dir: str = "data/tmp") -> str:
        """
        创建以工号+时间命名的输出目录
        
        Args:
            base_output_dir: 基础输出目录
            
        Returns:
            str: 新创建的输出目录路径（绝对路径）
        """
        # 生成时间戳（格式：YYYYMMDD_HHMMSS）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建目录名：工号_时间戳
        dir_name = f"{self.worker_id}_{timestamp}"
        
        # 构建完整路径（如果是相对路径，转换为绝对路径）
        if os.path.isabs(base_output_dir):
            output_dir = os.path.join(base_output_dir, dir_name)
        else:
            # 相对路径，需要找到项目根目录
            current_dir = Path(__file__).resolve().parents[3]  # 从 src/backend/new 回到项目根目录
            output_dir = os.path.join(str(current_dir), base_output_dir, dir_name)
        
        # 创建目录
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"创建输出目录: {output_dir}")
        
        return output_dir
    
    def _get_relative_path(self, absolute_path: str) -> str:
        """
        将绝对路径转换为相对路径（相对于项目根目录）
        
        Args:
            absolute_path: 绝对路径
            
        Returns:
            str: 相对路径（使用正斜杠）
        """
        try:
            # 获取项目根目录（从当前文件位置推导）
            project_root = Path(__file__).resolve().parents[3]  # src/backend/new -> 项目根目录
            
            # 转换为相对路径
            relative_path = os.path.relpath(absolute_path, str(project_root))
            
            # 转换为正斜杠格式（跨平台兼容）
            relative_path = relative_path.replace('\\', '/')
            
            return relative_path
        except Exception as e:
            logger.warning(f"转换相对路径失败: {e}, 使用原始路径")
            # 如果转换失败，尝试提取 data/tmp 之后的部分
            if 'data' in absolute_path or 'tmp' in absolute_path:
                parts = absolute_path.replace('\\', '/').split('/')
                try:
                    data_index = parts.index('data') if 'data' in parts else parts.index('tmp')
                    return '/'.join(parts[data_index:])
                except:
                    pass
            return absolute_path.replace('\\', '/')
    
    def _add_type_suffix_to_file(self, file_path: str, file_type: str, format_type: str = None) -> str:
        """
        在文件名末尾添加类型标识
        
        Args:
            file_path: 原始文件路径
            file_type: 文件类型 ('DIFF', 'PLM_GBOM')
            format_type: 格式类型 ('PLM', 'GBOM')，仅当 file_type 为 'PLM_GBOM' 时使用
            
        Returns:
            str: 重命名后的文件路径
        """
        if not file_path or not os.path.exists(file_path):
            return file_path
        
        try:
            # 获取目录和文件名
            dir_path = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            # 分离文件名和扩展名
            name, ext = os.path.splitext(filename)
            
            # 确定类型后缀
            if file_type == 'DIFF':
                type_suffix = '_DIFF'
            elif file_type == 'PLM_GBOM':
                # 根据格式类型添加后缀
                if format_type == 'PLM':
                    type_suffix = '_PLM'
                elif format_type == 'GBOM':
                    type_suffix = '_GBOM'
                else:
                    type_suffix = '_PLMGBOM'  # 默认后缀
            else:
                type_suffix = ''
            
            # 检查文件名是否已经包含类型后缀，避免重复添加
            if name.endswith('_DIFF') or name.endswith('_PLM') or name.endswith('_GBOM') or name.endswith('_PLMGBOM'):
                return file_path
            
            # 构建新文件名
            new_filename = f"{name}{type_suffix}{ext}"
            new_file_path = os.path.join(dir_path, new_filename)
            
            # 重命名文件
            if new_file_path != file_path:
                os.rename(file_path, new_file_path)
                logger.info(f"文件已重命名: {filename} -> {new_filename}")
            
            return new_file_path
            
        except Exception as e:
            logger.warning(f"重命名文件失败 '{file_path}': {e}")
            return file_path
    
    def _save_to_database(self, output_dir: str, file_count: int, success_count: int, 
                         worker_id: str, json_files: List[str]) -> Optional[str]:
        """
        保存处理记录到数据库 sbom_design 表
        
        Args:
            output_dir: 输出目录路径（相对路径）
            file_count: 处理的文件总数
            success_count: 成功处理的文件数
            worker_id: 工号
            json_files: 生成的JSON文件列表
            
        Returns:
            str: 插入记录的 design_id，失败返回 None
        """
        logger.info(f"开始保存数据库记录: output_dir={output_dir}, file_count={file_count}, success_count={success_count}, worker_id={worker_id}")
        
        try:
            connection = get_connection()
            if not connection:
                logger.error("数据库连接失败：get_connection() 返回 None")
                return None
            
            logger.info("数据库连接成功")
            
            import pymysql
            
            # 生成唯一的 design_id（使用 UUID）
            design_id = f"SBOM_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4()).upper()}"
            
            # 生成设计名称（基于目录名和时间）
            dir_name = os.path.basename(output_dir.rstrip(os.sep))
            design_name = f"批量处理_{dir_name}"
            
            # 构建设计信息 JSON
            design_info = {
                "worker_id": worker_id,
                "output_dir": output_dir,
                "total_files": file_count,
                "success_count": success_count,
                "json_file_count": len(json_files),
                "process_time": datetime.now().isoformat(),
                "json_files": json_files[:10]  # 只保存前10个文件路径，避免JSON过大
            }
            
            # 将相对路径转换为正斜杠格式（用于跨平台兼容）
            bom_path = output_dir.replace('\\', '/')
            
            logger.info(f"准备插入数据库记录: design_id={design_id}, bom_path={bom_path}")
            
            with connection.cursor() as cursor:
                # 插入记录到 sbom_design 表
                sql = """
                INSERT INTO sbom_design (
                    usr_id, deleted, create_time, updater, update_time,
                    design_id, design_name, design_type, design_status,
                    design_info, bom_path
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s
                )
                """
                
                now = datetime.now()
                # 假设 worker_id 可以转换为整数，如果不能，使用默认值 1
                try:
                    usr_id = int(worker_id) if worker_id.isdigit() else 1
                except:
                    usr_id = 1
                
                values = (
                    usr_id,              # usr_id
                    '0',                 # deleted (默认未删除)
                    now,                 # create_time
                    usr_id,              # updater (同 usr_id)
                    now,                 # update_time
                    design_id,           # design_id (唯一标识)
                    design_name,         # design_name
                    'BATCH_PROCESS',     # design_type
                    'DRFAT',        # design_status
                    json.dumps(design_info, ensure_ascii=False),  # design_info (JSON格式)
                    bom_path             # bom_path (相对路径)
                )
                
                logger.info(f"执行SQL插入: design_id={design_id}")
                logger.debug(f"SQL参数: usr_id={usr_id}, design_name={design_name}, bom_path={bom_path}")
                
                cursor.execute(sql, values)
                affected_rows = cursor.rowcount
                logger.info(f"SQL执行成功，影响行数: {affected_rows}")
                
                connection.commit()
                logger.info(f"事务提交成功")
                
                logger.info(f"成功保存处理记录到数据库: design_id={design_id}, bom_path={bom_path}")
                return design_id
                
        except Exception as e:
            logger.error(f"保存数据库记录失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            if 'connection' in locals() and connection:
                try:
                    connection.rollback()
                    logger.info("已回滚事务")
                except Exception as rollback_error:
                    logger.error(f"回滚失败: {rollback_error}")
            return None
        finally:
            if 'connection' in locals() and connection:
                try:
                    connection.close()
                    logger.info("数据库连接已关闭")
                except Exception as close_error:
                    logger.error(f"关闭连接失败: {close_error}")
        
    def detect_file_type(self, excel_file_path: str) -> str:
        """
        检测Excel文件的类型
        
        Args:
            excel_file_path: Excel文件路径
            
        Returns:
            str: 文件类型 ('DIFF', 'PLM_GBOM', 'UNKNOWN')
        """
        try:
            # 先检查是否为差异文件
            validation_result = validate_diff_file(excel_file_path)
            
            # 如果验证通过且有差异表sheet，则为差异文件
            if validation_result.get('valid') and validation_result.get('diff_sheet'):
                logger.info(f"文件 '{os.path.basename(excel_file_path)}' 检测为差异文件")
                return 'DIFF'
            
            # 读取Excel文件，检查是否包含PLM或GBOM格式的sheet
            xl_file = pd.ExcelFile(excel_file_path)
            sheet_names = xl_file.sheet_names
            
            # 检查是否有PLM或GBOM格式的sheet
            has_plm_or_gbom = False
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                    if len(df) == 0:
                        continue
                    
                    columns = [str(col).strip() for col in df.columns]
                    
                    # 检测PLM格式特征
                    plm_indicators = ['阶层', '物料编码', '物料名称', '用量']
                    plm_score = sum(1 for col in plm_indicators if col in columns)
                    
                    # 检测GBOM格式特征
                    gbom_indicators = ['MPART.NO', 'MPART.NAME', 'GBOM.BNUM']
                    gbom_score = sum(1 for col in gbom_indicators if col in columns)
                    
                    if plm_score >= 3 or gbom_score >= 3:
                        has_plm_or_gbom = True
                        break
                except Exception as e:
                    logger.warning(f"检测sheet '{sheet_name}' 时出错: {e}")
                    continue
            
            if has_plm_or_gbom:
                logger.info(f"文件 '{os.path.basename(excel_file_path)}' 检测为PLM/GBOM文件")
                return 'PLM_GBOM'
            else:
                logger.warning(f"文件 '{os.path.basename(excel_file_path)}' 无法识别类型")
                return 'UNKNOWN'
                
        except Exception as e:
            logger.error(f"检测文件类型失败: {e}")
            return 'UNKNOWN'
    
    def _process_diff_file_complete(self, excel_file_path: str, output_dir: str = "data/tmp") -> Dict[str, Any]:
        """
        完整处理差异文件流程（参考 app_new.py 的 api_process_diff_and_generate_new）
        
        Args:
            excel_file_path: Excel差异文件路径
            output_dir: 输出目录
            
        Returns:
            dict: 完整的处理结果
        """
        try:
            logger.info("步骤1: 解析差异文件...")
            # 步骤1：解析差异文件
            diff_result = parse_diff_excel(
                excel_file_path=excel_file_path,
                output_dir=output_dir
            )
            
            if not diff_result.get('success'):
                return {
                    'success': False,
                    'error': f'差异文件解析失败: {diff_result.get("error", "未知错误")}',
                    'file_type': 'DIFF',
                    'step': 'enhanced_diff_parser',
                    'excel_file': excel_file_path,
                    'excel_filename': os.path.basename(excel_file_path),
                    'file_path': None,
                    'files': []
                }
            
            diff_file_path = diff_result.get('file_path')
            stats = diff_result.get('stats', {})
            base_model = stats.get('base_model')
            target_model = stats.get('target_model')
            
            if not base_model or not target_model:
                return {
                    'success': False,
                    'error': '无法从差异文件中提取基准型号和目标型号',
                    'file_type': 'DIFF',
                    'excel_file': excel_file_path,
                    'excel_filename': os.path.basename(excel_file_path),
                    'file_path': None,
                    'files': []
                }
            
            logger.info(f"差异文件解析成功: {base_model} -> {target_model}")
            
            # 为差异文件添加类型后缀
            if diff_file_path:
                diff_file_path = self._add_type_suffix_to_file(diff_file_path, 'DIFF')
            
            # 步骤2：生成基础模型的AI分析数据
            logger.info(f"步骤2: 生成基础模型AI分析数据: {base_model}")
            base_ai_result = generate_ai_analysis_json(
                model_name=base_model,
                output_dir=output_dir
            )
            
            if not base_ai_result.get('success'):
                return {
                    'success': False,
                    'error': f'基础模型AI分析生成失败: {base_ai_result.get("error", "未知错误")}',
                    'file_type': 'DIFF',
                    'step': 'simple_ai_generator',
                    'model': base_model,
                    'excel_file': excel_file_path,
                    'excel_filename': os.path.basename(excel_file_path),
                    'file_path': diff_file_path,
                    'files': [diff_file_path] if diff_file_path else []
                }
            
            base_bom_file = base_ai_result.get('file_path')
            logger.info(f"基础模型AI分析生成成功: {base_bom_file}")
            
            # 为基础BOM文件添加类型后缀
            if base_bom_file:
                base_bom_file = self._add_type_suffix_to_file(base_bom_file, 'DIFF')
            
            # 步骤3：BOM转换
            logger.info("步骤3: 执行BOM转换...")
            target_bom_file = os.path.join(output_dir, f"{target_model}.json")
            transform_result = transform_bom_json(
                base_file=base_bom_file,
                diff_file=diff_file_path,
                output_file=target_bom_file,
                tmp_dir=output_dir
            )
            
            if not transform_result.get('success'):
                return {
                    'success': False,
                    'error': f'BOM转换失败: {transform_result.get("error", "未知错误")}',
                    'file_type': 'DIFF',
                    'step': 'bom_transformer',
                    'excel_file': excel_file_path,
                    'excel_filename': os.path.basename(excel_file_path),
                    'file_path': diff_file_path,
                    'files': [diff_file_path] if diff_file_path else [],
                    'base_bom_file': base_bom_file
                }
            
            target_bom_file = transform_result.get('file_path')
            # 为目标BOM文件添加类型后缀
            if target_bom_file:
                target_bom_file = self._add_type_suffix_to_file(target_bom_file, 'DIFF')
            logger.info(f"BOM转换成功: {target_bom_file}")
            
            # 步骤4：生成BOM对比数据（可选，用于前端展示）
            comparison_results = []
            try:
                logger.info("步骤4: 生成BOM对比数据...")
                with open(base_bom_file, 'r', encoding='utf-8') as f:
                    base_bom_data = json.load(f)
                with open(target_bom_file, 'r', encoding='utf-8') as f:
                    target_bom_data = json.load(f)
                
                # 处理对比数据 - 提取所有零件信息
                base_map, target_map = {}, {}
                
                # 处理基础BOM数据
                for category, items in base_bom_data.get('MPART', {}).items():
                    if isinstance(items, list):
                        for item in items:
                            code = item.get('MPART.NO')
                            if code:
                                base_map[code] = {
                                    'name': item.get('MPART.NAME', ''),
                                    'quantity': item.get('MPART.BNUM', 0)
                                }
                
                # 处理目标BOM数据
                for category, items in target_bom_data.get('MPART', {}).items():
                    if isinstance(items, list):
                        for item in items:
                            code = item.get('MPART.NO')
                            if code:
                                target_map[code] = {
                                    'name': item.get('MPART.NAME', ''),
                                    'quantity': item.get('MPART.BNUM', 0)
                                }
                
                # 生成对比结果
                all_codes = sorted(set(list(base_map.keys()) + list(target_map.keys())))
                
                for index, code in enumerate(all_codes):
                    base_item = base_map.get(code, {'name': '', 'quantity': 0})
                    target_item = target_map.get(code, {'name': '', 'quantity': 0})
                    
                    comparison_results.append({
                        'seq': index + 1,
                        'code': code,
                        'name': base_item['name'] or target_item['name'],
                        'baseQuantity': base_item['quantity'],
                        'targetQuantity': target_item['quantity'],
                        'status': 'changed' if base_item['quantity'] != target_item['quantity'] else 'unchanged'
                    })
                
                logger.info(f"BOM对比完成，共对比 {len(comparison_results)} 个零件")
                
            except Exception as e:
                logger.warning(f"BOM对比失败（不影响主流程）: {e}")
                comparison_results = []
            
            # 汇总所有生成的文件
            all_files = []
            if diff_file_path:
                all_files.append(diff_file_path)
            if base_bom_file:
                all_files.append(base_bom_file)
            if target_bom_file:
                all_files.append(target_bom_file)
            
            # 构建完整的返回结果
            result = {
                'success': True,
                'file_type': 'DIFF',
                'excel_file': excel_file_path,
                'excel_filename': os.path.basename(excel_file_path),
                'file_path': target_bom_file,  # 主要输出文件
                'files': all_files,  # 所有生成的文件
                'base_model': base_model,
                'target_model': target_model,
                'processing_steps': {
                    'enhanced_diff_parser': {
                        'status': 'success',
                        'file_path': diff_file_path,
                        'stats': diff_result.get('stats', {})
                    },
                    'simple_ai_generator': {
                        'status': 'success',
                        'file_path': base_bom_file,
                        'stats': base_ai_result.get('stats', {})
                    },
                    'bom_transformer': {
                        'status': 'success',
                        'file_path': target_bom_file,
                        'tmp_file_path': transform_result.get('tmp_file_path'),
                        'stats': transform_result.get('stats', {})
                    }
                },
                'comparison': comparison_results,
                'statistics': {
                    'diff_items': diff_result.get('stats', {}).get('diff_count', 0),
                    'sub_bom_items': diff_result.get('stats', {}).get('sub_bom_count', 0),
                    'base_bom_parts': base_ai_result.get('stats', {}).get('total_parts', 0),
                    'target_bom_parts': transform_result.get('stats', {}).get('total_parts', 0),
                    'comparison_items': len(comparison_results)
                }
            }
            
            logger.info("差异文件完整处理流程完成")
            return result
            
        except Exception as e:
            logger.error(f"处理差异文件完整流程失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'处理差异文件失败: {str(e)}',
                'file_type': 'DIFF',
                'excel_file': excel_file_path,
                'excel_filename': os.path.basename(excel_file_path),
                'file_path': None,
                'files': []
            }
    
    def process_single_file(self, excel_file_path: str, output_dir: str = "data/tmp") -> Dict[str, Any]:
        """
        处理单个Excel文件
        
        Args:
            excel_file_path: Excel文件路径
            output_dir: 输出目录
            
        Returns:
            dict: 处理结果
        """
        try:
            logger.info(f"开始处理文件: {os.path.basename(excel_file_path)}")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 检测文件类型
            file_type = self.detect_file_type(excel_file_path)
            
            if file_type == 'DIFF':
                # 处理差异文件 - 完整流程（参考 app_new.py）
                result = self._process_diff_file_complete(excel_file_path, output_dir)
                
            elif file_type == 'PLM_GBOM':
                # 处理PLM/GBOM文件（自动检测sheet格式）
                result = process_excel_auto_detect(
                    excel_file_path=excel_file_path,
                    output_dir=output_dir
                )
                result['file_type'] = 'PLM_GBOM'
                
                # 调整返回格式以统一结构
                if result.get('success'):
                    # 从results中提取文件路径，并为每个文件添加类型后缀
                    json_files = result.get('json_files', [])
                    results_list = result.get('results', [])
                    
                    # 为每个生成的文件添加类型后缀
                    renamed_files = []
                    for i, json_file in enumerate(json_files):
                        if json_file and os.path.exists(json_file):
                            # 从results中获取对应的格式类型
                            format_type = None
                            if i < len(results_list):
                                format_type = results_list[i].get('format', None)
                            
                            renamed_file = self._add_type_suffix_to_file(json_file, 'PLM_GBOM', format_type)
                            renamed_files.append(renamed_file)
                        else:
                            renamed_files.append(json_file)
                    
                    result['file_path'] = renamed_files[0] if renamed_files else None
                    result['files'] = renamed_files
                    result['json_files'] = renamed_files  # 同时更新 json_files
                else:
                    result['file_path'] = None
                    result['files'] = []
                    
            else:
                # 未知类型文件
                result = {
                    'success': False,
                    'error': f'无法识别的文件类型: {file_type}',
                    'file_type': file_type,
                    'file_path': None,
                    'files': []
                }
            
            # 添加文件名和路径信息
            result['excel_file'] = excel_file_path
            result['excel_filename'] = os.path.basename(excel_file_path)
            
            logger.info(f"文件处理完成: {os.path.basename(excel_file_path)}, 成功: {result.get('success', False)}")
            
            return result
            
        except Exception as e:
            logger.error(f"处理文件失败 '{excel_file_path}': {e}")
            return {
                'success': False,
                'error': str(e),
                'file_type': 'UNKNOWN',
                'excel_file': excel_file_path,
                'excel_filename': os.path.basename(excel_file_path),
                'file_path': None,
                'files': []
            }
    
    def process_multiple_files(self, excel_file_paths: List[str], output_dir: str = "data/tmp", create_subdir: bool = True) -> Dict[str, Any]:
        """
        批量处理多个Excel文件
        
        Args:
            excel_file_paths: Excel文件路径列表
            output_dir: 基础输出目录
            create_subdir: 是否创建工号+时间的子目录，默认为 True
            
        Returns:
            dict: 批量处理结果汇总
        """
        try:
            logger.info(f"开始批量处理 {len(excel_file_paths)} 个文件")
            
            # 创建工号+时间的输出目录
            if create_subdir:
                actual_output_dir = self._create_output_directory(output_dir)
            else:
                actual_output_dir = output_dir
                os.makedirs(actual_output_dir, exist_ok=True)
            
            logger.info(f"输出目录: {actual_output_dir}")
            
            # 处理结果汇总
            all_results = []
            success_count = 0
            failed_count = 0
            diff_count = 0
            plm_gbom_count = 0
            unknown_count = 0
            
            # 所有生成的JSON文件路径
            all_json_files = []
            
            # 逐个处理文件
            for i, file_path in enumerate(excel_file_paths, 1):
                logger.info(f"处理文件 {i}/{len(excel_file_paths)}: {os.path.basename(file_path)}")
                
                try:
                    # 检查文件是否存在
                    if not os.path.exists(file_path):
                        result = {
                            'success': False,
                            'error': '文件不存在',
                            'file_type': 'UNKNOWN',
                            'excel_file': file_path,
                            'excel_filename': os.path.basename(file_path),
                            'file_path': None,
                            'files': []
                        }
                        failed_count += 1
                        unknown_count += 1
                    else:
                        # 处理文件（使用实际输出目录）
                        result = self.process_single_file(file_path, actual_output_dir)
                        
                        # 统计成功和失败
                        if result.get('success'):
                            success_count += 1
                            
                            # 收集生成的JSON文件
                            file_type = result.get('file_type', 'UNKNOWN')
                            if file_type == 'DIFF':
                                diff_count += 1
                                # 差异文件生成一个JSON文件
                                if result.get('file_path'):
                                    all_json_files.append(result['file_path'])
                            elif file_type == 'PLM_GBOM':
                                # PLM/GBOM文件可能生成多个JSON文件
                                files = result.get('files', [])
                                if files:
                                    # 如果files列表存在且不为空，计数所有文件
                                    plm_gbom_count += len(files)
                                    all_json_files.extend(files)
                                elif result.get('file_path'):
                                    # 如果files为空但file_path存在，计数1个文件
                                    plm_gbom_count += 1
                                    all_json_files.append(result['file_path'])
                        else:
                            failed_count += 1
                            file_type = result.get('file_type', 'UNKNOWN')
                            if file_type == 'UNKNOWN':
                                unknown_count += 1
                            
                    all_results.append(result)
                    
                except Exception as e:
                    logger.error(f"处理文件 '{file_path}' 时发生异常: {e}")
                    all_results.append({
                        'success': False,
                        'error': str(e),
                        'file_type': 'UNKNOWN',
                        'excel_file': file_path,
                        'excel_filename': os.path.basename(file_path),
                        'file_path': None,
                        'files': []
                    })
                    failed_count += 1
                    unknown_count += 1
            
            # 汇总统计
            total_files = len(excel_file_paths)
            
            logger.info(f"批量处理完成: 总计{total_files}个文件, 成功{success_count}个, 失败{failed_count}个")
            logger.info(f"文件类型统计: 差异文件{diff_count}个, PLM/GBOM文件{plm_gbom_count}个, 未知类型{unknown_count}个")
            logger.info(f"生成JSON文件共 {len(all_json_files)} 个")
            logger.info(f"所有文件已输出到目录: {actual_output_dir}")
            
            # 将绝对路径转换为相对路径（相对于项目根目录）
            relative_output_dir = self._get_relative_path(actual_output_dir)
            logger.info(f"相对路径: {relative_output_dir}")
            
            # 保存到数据库
            logger.info("="*80)
            logger.info("开始保存数据库记录...")
            design_id = self._save_to_database(
                output_dir=relative_output_dir,
                file_count=total_files,
                success_count=success_count,
                worker_id=self.worker_id,
                json_files=all_json_files
            )
            if design_id:
                logger.info(f"✅ 数据库记录保存成功: design_id={design_id}")
            else:
                logger.warning(f"⚠️  数据库记录保存失败")
            logger.info("="*80)
            
            return {
                'success': success_count > 0,
                'total_files': total_files,
                'success_count': success_count,
                'failed_count': failed_count,
                'diff_count': diff_count,
                'plm_gbom_count': plm_gbom_count,
                'unknown_count': unknown_count,
                'excel_file_paths': excel_file_paths,
                'json_files': all_json_files,  # 所有生成的JSON文件路径
                'output_dir': actual_output_dir,  # 绝对路径
                'output_dir_relative': relative_output_dir,  # 相对路径
                'design_id': design_id,  # 数据库记录ID
                'results': all_results,
                'error': None if success_count > 0 else '所有文件都处理失败'
            }
            
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_files': len(excel_file_paths) if excel_file_paths else 0,
                'success_count': 0,
                'failed_count': len(excel_file_paths) if excel_file_paths else 0,
                'diff_count': 0,
                'plm_gbom_count': 0,
                'unknown_count': 0,
                'json_files': [],
                'results': []
            }


# ==================== 便捷函数 ====================

def process_multiple_excel_files(excel_file_paths: List[str], output_dir: str = "data/tmp", worker_id: str = "250000", create_subdir: bool = True) -> Dict[str, Any]:
    """
    批量处理多个Excel文件
    
    Args:
        excel_file_paths: Excel文件路径列表
        output_dir: 基础输出目录
        worker_id: 工号，默认为 "250000"
        create_subdir: 是否创建工号+时间的子目录，默认为 True
        
    Returns:
        dict: 批量处理结果汇总
    """
    processor = MultiExcelProcessor(worker_id=worker_id)
    return processor.process_multiple_files(excel_file_paths, output_dir, create_subdir=create_subdir)


def process_single_excel_file(excel_file_path: str, output_dir: str = "data/tmp", worker_id: str = "250000") -> Dict[str, Any]:
    """
    处理单个Excel文件
    
    Args:
        excel_file_path: Excel文件路径
        output_dir: 输出目录
        worker_id: 工号，默认为 "250000"
        
    Returns:
        dict: 处理结果
    """
    processor = MultiExcelProcessor(worker_id=worker_id)
    return processor.process_single_file(excel_file_path, output_dir)


# ==================== CLI工具 ====================

def main():
    """CLI工具主函数"""
    print("=== 多Excel文件批量处理器 ===")
    print("支持自动检测3种sheet类型: PLM、GBOM、差异文件")
    
    # 测试文件列表
    test_files = [
        # 可以在这里添加测试文件路径
    ]
    
    if test_files:
        print(f"\n开始处理 {len(test_files)} 个测试文件...")
        result = process_multiple_excel_files(test_files)
        
        print(f"\n处理结果:")
        print(f"  总计: {result['total_files']} 个文件")
        print(f"  成功: {result['success_count']} 个文件")
        print(f"  失败: {result['failed_count']} 个文件")
        print(f"  差异文件: {result['diff_count']} 个")
        print(f"  PLM/GBOM文件: {result['plm_gbom_count']} 个")
        print(f"  未知类型: {result['unknown_count']} 个")
        print(f"\n生成的JSON文件:")
        for json_file in result['json_files']:
            print(f"  - {json_file}")
    else:
        print("\n未配置测试文件，请手动指定文件路径")


if __name__ == "__main__":
    main()

