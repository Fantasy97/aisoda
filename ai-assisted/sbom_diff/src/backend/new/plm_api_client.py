#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PLM接口客户端
支持接口调用和CLI工具两种模式
用于调用PLM系统的BOM信息推送接口
"""

import sys
import os
import requests
import json
import logging
import glob
import re
import copy
from typing import List, Dict, Any
from datetime import datetime, date

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入数据库连接模块
from pathlib import Path as PathLib

tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
try:
    project_root = PathLib(__file__).resolve().parents[3]
    tools_path_abs = os.path.join(str(project_root), 'src', 'backend', 'tools')
except:
    tools_path_abs = tools_path

for path in [tools_path, tools_path_abs]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)

try:
    from db_query import get_connection
    logger.info(f"成功导入 db_query 模块")
except ImportError as e:
    logger.warning(f"无法导入 db_query 模块: {e}")
    def get_connection():
        logger.error("数据库连接模块未找到")
        return None


class PLMApiClient:
    """PLM API客户端类"""
    
    def __init__(self, base_url: str = "http://112.80.38.114:7090"):
        """
        初始化PLM API客户端
        
        Args:
            base_url: PLM API的基础URL
        """
        self.base_url = base_url.rstrip('/')
        self.push_bom_endpoint = f"{self.base_url}/bom/PushBomInfo"
        
        # BOM字段映射表
        self.bom_mapping = {
            "bom_PLM": {
                "CNO": "MPART.NO",      # 子零件号
                "BNUM": "MPART.BNUM",   # 数量
                "PNO": "MPART.PRNT",    # 父零件号
                "BOMPST": "MPART.ID"    # 位置
            }
        }
    
    def extract_all_parts(self, bom_json: Dict[str, Any], validate_only: bool = False) -> List[Dict[str, Any]]:
        """
        从嵌套的BOM JSON中提取所有零件信息
        
        Args:
            bom_json: 完整的BOM JSON数据
            validate_only: 是否递归处理子零件，True时会递归处理
            
        Returns:
            扁平化的零件列表
        """
        all_parts = []
        
        def extract_parts_recursive(parts_list: List[Dict[str, Any]]):
            """递归提取零件信息"""
            for part in parts_list:
                # 添加当前零件
                all_parts.append(part)
                
                # 根据validate_only参数决定是否递归处理子零件
                if validate_only and "children" in part and part["children"]:
                    extract_parts_recursive(part["children"])
        
        # 处理MPART字段下的所有分类
        if "MPART" in bom_json:
            mpart_data = bom_json["MPART"]
            for category_key, parts_list in mpart_data.items():
                if isinstance(parts_list, list):
                    extract_parts_recursive(parts_list)
        
        return all_parts
    
    def transform_diff_data(self, diff_json: Dict[str, Any], 
                           owner: str = "adm", 
                           creator: str = "adm",
                           source: str = "PPPE",
                           operator: str = "sf") -> List[Dict[str, Any]]:
        """
        将差异数据中的sub_bom_items转换为PLM接口所需格式
        
        Args:
            diff_json: 差异数据JSON
            owner: 数据所有者，默认为"adm"
            creator: 数据创建者，默认为"adm"
            source: 数据源，默认为"PPPE"
            operator: 操作员，默认为"sf"
            
        Returns:
            转换后的PLM格式数据列表
        """
        sub_array_data = []
        current_date = datetime.now().strftime("%Y%m%d")
        
        # 处理sub_bom_items
        sub_bom_items = diff_json.get('sub_bom_items', [])
        if sub_bom_items:
            logger.info(f"处理 {len(sub_bom_items)} 个子BOM项目")
            
            for item in sub_bom_items:
                transformed_item = {
                    "PNO": item.get("MPART.PRNT", ""),  # 父零件号
                    "CNO": item.get("MPART.NO", ""),    # 子零件号
                    "BNUM": str(item.get("MPART.BNUM", "1.0")),  # 数量
                    "BOMPST": "1",  # 位置，默认为1
                    "OWNER": owner,
                    "CREATOR": creator,
                    "ASMEMO": f"差异数据子BOM导入{current_date}"
                }
                sub_array_data.append(transformed_item)
                logger.debug(f"转换子BOM项目: {item.get('MPART.NO')} -> {item.get('MPART.PRNT')}")
        
        return sub_array_data

    def transform_bom_data(self, bom_json: Dict[str, Any], 
                          owner: str = "adm", 
                          creator: str = "adm",
                          source: str = "PPPE",
                          operator: str = "sf",
                          validate_only: bool = False) -> Dict[str, Any]:
        """
        将BOM数据转换为PLM接口所需格式
        
        Args:
            bom_json: 完整的BOM JSON数据
            owner: 数据所有者，默认为"adm"
            creator: 数据创建者，默认为"adm"
            source: 数据源，默认为"PPPE"
            operator: 操作员，默认为"sf"
            validate_only: 是否递归处理子零件，默认False
            
        Returns:
            转换后的PLM格式数据字典
        """
        # 提取所有零件（根据validate_only决定是否包括嵌套的）
        all_parts = self.extract_all_parts(bom_json, validate_only)
        
        array_data = []
        current_date = datetime.now().strftime("%Y%m%d")
        
        model_name = bom_json.get('MODEL', 'unknown')

        for item in all_parts:
            transformed_item = {
                "PNO": item.get("MPART.PRNT", ""),
                "CNO": item.get("MPART.NO", ""),
                "BNUM": str(item.get("MPART.BNUM", "1.0")),
                "BOMPST": str(item.get("MPART.ID", "1")),
                "OWNER": owner,
                "CREATOR": creator,
                "ASMEMO": f"外部接口导入{current_date}"
            }
            array_data.append(transformed_item)
        
        # 按照PLM接口要求的格式包装数据
        plm_data = {
            "SOURCE": source,
            "MARK": f"{model_name}",
            "OPERATOR": operator,
            "ARRAY": array_data
        }
        
        return plm_data
    
    def push_bom_info(self, bom_json: Dict[str, Any], 
                     owner: str = "adm", 
                     creator: str = "adm",
                     source: str = "PPPE",
                     operator: str = "sf",
                     validate_only: bool = False,
                     diff_json: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        推送BOM信息到PLM系统
        
        Args:
            bom_json: 完整的BOM JSON数据
            owner: 数据所有者
            creator: 数据创建者
            source: 数据源
            operator: 操作员
            validate_only: 是否仅验证格式（当前接口未启动时使用）
            
        Returns:
            API响应结果
        """
        try:
            # 转换数据格式
            transformed_data = self.transform_bom_data(bom_json, owner, creator, source, operator, validate_only)

            # 处理差异数据中的sub_bom_items
            if diff_json:
                transformed_sub_data = self.transform_diff_data(diff_json, owner, creator, source, operator)
                # 将子BOM数据合并到主数据的ARRAY中
                if transformed_sub_data and isinstance(transformed_data, dict) and 'ARRAY' in transformed_data:
                    transformed_data['ARRAY'].extend(transformed_sub_data)
                    logger.info(f"已合并 {len(transformed_sub_data)} 个子BOM项目到主数据中")
            
            # 准备请求头
            headers = {
                "Content-Type": "application/json"
            }
            
            # 如果仅验证格式，返回格式化后的数据
            # if validate_only:
            #     return {
            #         "status": "validation_success",
            #         "message": "数据格式验证通过",
            #         "data": transformed_data,
            #         "endpoint": self.push_bom_endpoint,
            #         "headers": headers
            #     }
            
            # 保存PLM上传内容
            # output_file = r"D:\code\sbom\release\sbom_diff\data\tmp\DEBUG_plm.json"
            # with open(output_file, 'w', encoding='utf-8') as f:
            #     json.dump(transformed_data, f, ensure_ascii=False, indent=2)
            # logger.info(f"转换结果已保存到: {output_file}")

            # 发送POST请求
            response = requests.post(
                self.push_bom_endpoint,
                headers=headers,
                json=transformed_data,
                timeout=30
            )
            
            # 处理响应
            if response.status_code == 200:
                try:
                    response_data = response.json() if response.content else {}
                    
                    # 检查PLM系统的业务逻辑响应
                    if isinstance(response_data, dict):
                        if response_data.get('success') == False:
                            # PLM系统返回业务错误
                            error_msg = response_data.get('msg', '未知错误')
                            missing_parts = self._parse_missing_parts(error_msg)
                            
                            return {
                                "status": "business_error",
                                "message": "PLM系统业务逻辑错误",
                                "error": error_msg,
                                "missing_parts": missing_parts,
                                "data": response_data
                            }
                        else:
                            # PLM系统返回成功
                            return {
                                "status": "success",
                                "message": "BOM信息推送成功",
                                "data": response_data
                            }
                    else:
                        # 其他格式的响应
                        return {
                            "status": "success",
                            "message": "BOM信息推送成功",
                            "data": response_data
                        }
                        
                except json.JSONDecodeError:
                    # 响应不是JSON格式
                    return {
                        "status": "success",
                        "message": "BOM信息推送成功",
                        "data": response.text
                    }
            else:
                return {
                    "status": "error",
                    "message": f"请求失败，状态码: {response.status_code}",
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"网络请求异常: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": f"处理异常: {str(e)}"
            }
    
    def _parse_missing_parts(self, error_msg: str) -> List[str]:
        """
        从错误消息中解析缺失的物料编号
        
        Args:
            error_msg: PLM系统返回的错误消息
            
        Returns:
            List[str]: 缺失的物料编号列表
        """
        import re
        
        # 使用正则表达式提取物料编号
        # 匹配格式：编号为XXX-XXXXXX-XX的物料在PLM中不存在
        pattern = r'编号为([A-Z0-9\-]+)的物料在PLM中不存在'
        missing_parts = re.findall(pattern, error_msg)
        
        return missing_parts
    
    def analyze_missing_parts(self, bom_json: Dict[str, Any], missing_parts: List[str]) -> Dict[str, Any]:
        """
        分析缺失物料的详细信息
        
        Args:
            bom_json: 完整的BOM JSON数据
            missing_parts: 缺失的物料编号列表
            
        Returns:
            Dict: 缺失物料的分析结果
        """
        all_parts = self.extract_all_parts(bom_json)
        missing_details = []
        
        for part_no in missing_parts:
            # 在BOM数据中查找该物料的详细信息
            for part in all_parts:
                if part.get("MPART.NO") == part_no:
                    missing_details.append({
                        "part_no": part_no,
                        "name": part.get("MPART.NAME", ""),
                        "quantity": part.get("MPART.BNUM", 0),
                        "parent": part.get("MPART.PRNT", ""),
                        "level": part.get("MPART.LVL", 0),
                        "mfg": part.get("MPART.MFG", ""),
                        "category": self._get_part_category(part_no)
                    })
                    break
        
        # 按分类统计
        category_stats = {}
        for detail in missing_details:
            category = detail["category"]
            if category not in category_stats:
                category_stats[category] = []
            category_stats[category].append(detail["part_no"])
        
        return {
            "total_missing": len(missing_parts),
            "missing_details": missing_details,
            "category_stats": category_stats,
            "suggestions": self._generate_missing_parts_suggestions(missing_details)
        }
    
    def _get_part_category(self, part_no: str) -> str:
        """
        根据物料编号获取分类
        
        Args:
            part_no: 物料编号
            
        Returns:
            str: 分类名称
        """
        if not part_no:
            return "UNKNOWN"
        
        # 提取前缀作为分类
        if '-' in part_no:
            return part_no.split('-')[0]
        else:
            # 提取数字前缀
            import re
            match = re.match(r'^([A-Z]*\d+)', part_no)
            if match:
                return match.group(1)
        
        return part_no[:6] if len(part_no) > 6 else part_no
    
    def _generate_missing_parts_suggestions(self, missing_details: List[Dict]) -> List[str]:
        """
        为缺失物料生成建议
        
        Args:
            missing_details: 缺失物料详细信息
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []
        
        if not missing_details:
            return suggestions
        
        # 按分类分组
        categories = {}
        for detail in missing_details:
            category = detail["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(detail)
        
        suggestions.append(f"发现 {len(missing_details)} 个物料在PLM系统中不存在")
        suggestions.append("建议处理方案：")
        
        for category, parts in categories.items():
            suggestions.append(f"• {category}类物料 ({len(parts)}个):")
            for part in parts[:3]:  # 只显示前3个
                suggestions.append(f"  - {part['part_no']}: {part['name']}")
            if len(parts) > 3:
                suggestions.append(f"  - ... 还有 {len(parts) - 3} 个")
        
        suggestions.append("处理建议：")
        suggestions.append("1. 联系PLM管理员添加缺失的物料主数据")
        suggestions.append("2. 检查物料编号是否正确")
        suggestions.append("3. 确认物料是否为新增物料需要先在PLM中创建")
        
        return suggestions


def load_bom_from_file(file_path: str) -> Dict[str, Any]:
    """
    从文件加载BOM数据
    
    Args:
        file_path: BOM JSON文件路径
        
    Returns:
        BOM JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载文件失败: {e}")
        return {}


def create_sample_bom_data() -> Dict[str, Any]:
    """
    创建示例BOM数据用于测试
    
    Returns:
        示例BOM JSON数据
    """
    return {
        "MODEL": "TEST_MODEL",
        "MPART": {
            "test_category": [
                {
                    "MPART.PRNT": "WK_100001",
                    "MPART.NO": "WK_200001", 
                    "MPART.BNUM": 2.0,
                    "MPART.ID": 1,
                    "children": []
                },
                {
                    "MPART.PRNT": "WK_100001",
                    "MPART.NO": "WK_200002",
                    "MPART.BNUM": 1.0, 
                    "MPART.ID": 2,
                    "children": []
                }
            ]
        }
    }

# ==================== 接口函数 ====================

def push_bom_to_plm(bom_file_path: str, owner: str = "adm", creator: str = "adm", 
                   source: str = "PPPE", operator: str = "sf",
                   validate_only: bool = False,
                   diff_file_path: str = None,
                   output_dir: str = None) -> Dict[str, Any]:
    """
    推送BOM数据到PLM系统 (供app.py调用的接口)
    
    Args:
        bom_file_path: BOM JSON文件路径
        owner: 数据所有者，默认为"adm"
        creator: 数据创建者，默认为"adm"
        source: 数据源，默认为"PPPE"
        operator: 操作员，默认为"sf"
        validate_only: 是否仅验证格式，默认False
        diff_file_path: 差异数据文件路径，可选
        output_dir: 输出目录，用于保存转换结果
        
    Returns:
        dict: 包含推送结果的字典
        {
            'success': bool,
            'status': str,
            'message': str,
            'data': dict,  # 转换后的PLM格式数据(包含SOURCE,MARK,OPERATOR,ARRAY)
            'stats': dict,  # 统计信息
            'file_path': str  # 保存的文件路径(如果有)
        }
    """
    try:
        logger.info(f"开始处理BOM文件: {bom_file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(bom_file_path):
            logger.error(f"BOM文件不存在: {bom_file_path}")
            return {
                'success': False,
                'status': 'error',
                'message': f'BOM文件不存在: {bom_file_path}',
                'data': None,
                'stats': None,
                'file_path': None
            }
        
        # 加载BOM数据
        bom_data = load_bom_from_file(bom_file_path)
        if not bom_data:
            return {
                'success': False,
                'status': 'error',
                'message': f'无法加载BOM文件: {bom_file_path}',
                'data': None,
                'stats': None,
                'file_path': None
            }
        
        # 加载差异数据（可选）
        diff_data = None
        if diff_file_path:
            if os.path.exists(diff_file_path):
                diff_data = load_bom_from_file(diff_file_path)
                if diff_data:
                    logger.info(f"已加载差异数据文件: {diff_file_path}")
                else:
                    logger.warning(f"无法解析差异数据文件: {diff_file_path}")
            else:
                logger.warning(f"差异数据文件不存在: {diff_file_path}")
        
        # 创建PLM客户端并推送数据
        plm_client = PLMApiClient()
        result = plm_client.push_bom_info(bom_data, owner, creator, source, operator, validate_only, diff_data)
        logger.info(f"PLM系统返回信息: {result['data']}")
        
        # 统计信息
        transformed_data = result.get('data', {})
        all_parts = plm_client.extract_all_parts(bom_data, validate_only)
        
        # 层级统计
        level_stats = {}
        for part in all_parts:
            level = part.get("MPART.LVL", 0)
            level_stats[level] = level_stats.get(level, 0) + 1
        
        # 从转换后的数据中获取ARRAY部分的长度
        array_data = transformed_data.get('ARRAY', []) if isinstance(transformed_data, dict) else []
        
        # 统计子BOM项目
        sub_bom_count = 0
        if diff_data and 'sub_bom_items' in diff_data:
            sub_bom_count = len(diff_data['sub_bom_items'])
        
        stats = {
            'model': bom_data.get('MODEL', 'Unknown'),
            'total_parts': len(array_data),
            'sub_bom_parts': sub_bom_count,
            'level_distribution': level_stats,
            'categories': len(bom_data.get('MPART', {})),
            'endpoint': result.get('endpoint', ''),
            'headers': result.get('headers', {}),
            'source': transformed_data.get('SOURCE', '') if isinstance(transformed_data, dict) else '',
            'mark': transformed_data.get('MARK', '') if isinstance(transformed_data, dict) else '',
            'operator': transformed_data.get('OPERATOR', '') if isinstance(transformed_data, dict) else '',
            'diff_file': diff_file_path if diff_file_path else None
        }
        
        # 保存转换结果到文件（可选）
        output_file = None
        if output_dir and transformed_data:
            try:
                os.makedirs(output_dir, exist_ok=True)
                model_name = bom_data.get('MODEL', 'unknown')
                output_file = os.path.join(output_dir, f"{model_name}_plm_data.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(transformed_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"转换结果已保存到: {output_file}")
            except Exception as e:
                logger.warning(f"保存转换结果失败: {e}")
        
        success = result.get('status') in ['validation_success', 'success']
        
        # 处理业务错误
        if result.get('status') == 'business_error':
            missing_parts = result.get('missing_parts', [])
            if missing_parts:
                # 分析缺失物料
                missing_analysis = plm_client.analyze_missing_parts(bom_data, missing_parts)
                stats['missing_analysis'] = missing_analysis
                logger.warning(f"PLM业务错误: {len(missing_parts)}个物料不存在")
            else:
                logger.warning(f"PLM业务错误: {result.get('message')}")
        
        logger.info(f"BOM处理完成: {stats['total_parts']}个零件, 状态: {result.get('status')}")
        
        return {
            'success': success,
            'status': result.get('status', 'unknown'),
            'message': result.get('message', ''),
            'data': transformed_data,
            'stats': stats,
            'file_path': output_file,
            'plm_error': result.get('error') if result.get('status') == 'business_error' else None,
            'missing_parts': result.get('missing_parts', []) if result.get('status') == 'business_error' else None
        }
        
    except Exception as e:
        logger.error(f"推送BOM数据失败: {e}")
        return {
            'success': False,
            'status': 'error',
            'message': str(e),
            'data': None,
            'stats': None,
            'file_path': None
        }

def validate_bom_format(bom_file_path: str):
    """
    验证BOM文件格式 (不推送，仅验证)
    
    Args:
        bom_file_path: BOM JSON文件路径
        
    Returns:
        dict: 验证结果
    """
    try:
        return push_bom_to_plm(bom_file_path, validate_only=True)
    except Exception as e:
        logger.error(f"验证BOM格式失败: {e}")
        return {
            'success': False,
            'status': 'error',
            'message': str(e),
            'data': None,
            'stats': None,
            'file_path': None
        }

def batch_push_bom_to_plm(bom_file_list: List[str], owner: str = "adm", 
                         creator: str = "adm", source: str = "PPPE", 
                         operator: str = "sf", validate_only: bool = False, 
                         output_dir: str = None):
    """
    批量推送BOM数据到PLM系统
    
    Args:
        bom_file_list: BOM文件路径列表
        owner: 数据所有者
        creator: 数据创建者
        validate_only: 是否仅验证格式
        output_dir: 输出目录
        
    Returns:
        dict: 批量推送结果
    """
    results = []
    success_count = 0
    
    for bom_file in bom_file_list:
        result = push_bom_to_plm(bom_file, owner, creator, source, operator, validate_only, output_dir)
        results.append({
            'file': bom_file,
            **result
        })
        
        if result['success']:
            success_count += 1
    
    return {
        'total': len(bom_file_list),
        'success': success_count,
        'failed': len(bom_file_list) - success_count,
        'results': results
    }

def batch_upload_bom_files(file_paths: List[str], owner: str = "adm", creator: str = "adm", 
                          source: str = "PPPE", operator: str = "sf",
                          validate_only: bool = False, output_dir: str = None,
                          continue_on_error: bool = True, max_retries: int = 0) -> Dict[str, Any]:
    """
    批量上传BOM文件到PLM系统 (增强版批量处理接口)
    
    Args:
        file_paths: BOM文件路径数组，支持相对路径和绝对路径
        owner: 数据所有者，默认为"adm"
        creator: 数据创建者，默认为"adm"
        source: 数据源，默认为"PPPE"
        operator: 操作员，默认为"sf"
        validate_only: 是否仅验证格式，默认False（实际上传）
        output_dir: 输出目录，用于保存转换结果，默认为"tmp"
        continue_on_error: 遇到错误时是否继续处理其他文件，默认True
        max_retries: 失败时的最大重试次数，默认0（不重试）
        
    Returns:
        dict: 批量上传结果
        {
            'success': bool,              # 整体是否成功（所有文件都成功）
            'total': int,                 # 总文件数
            'processed': int,             # 已处理文件数
            'success_count': int,         # 成功文件数
            'failed_count': int,          # 失败文件数
            'skipped_count': int,         # 跳过文件数
            'total_parts': int,           # 总零件数
            'processing_time': float,     # 处理耗时（秒）
            'results': List[dict],        # 每个文件的详细结果
            'summary': dict,              # 汇总统计
            'failed_files': List[str],    # 失败的文件列表
            'missing_files': List[str],   # 不存在的文件列表
            'business_errors': List[dict] # 业务错误汇总
        }
    """
    import time
    from datetime import datetime
    
    start_time = time.time()
    current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 初始化结果统计
    results = []
    success_count = 0
    failed_count = 0
    skipped_count = 0
    total_parts = 0
    failed_files = []
    missing_files = []
    business_errors = []
    
    # 设置默认输出目录
    if output_dir is None:
        output_dir = "tmp"
    
    logger.info(f"开始批量上传 {len(file_paths)} 个BOM文件到PLM系统")
    logger.info(f"参数: validate_only={validate_only}, continue_on_error={continue_on_error}, max_retries={max_retries}")
    
    # 预检查文件存在性
    valid_files = []
    for file_path in file_paths:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.warning(f"文件不存在，跳过: {file_path}")
            skipped_count += 1
        else:
            valid_files.append(file_path)
    
    # 处理每个有效文件
    for i, file_path in enumerate(valid_files, 1):
        logger.info(f"处理文件 {i}/{len(valid_files)}: {file_path}")
        
        retry_count = 0
        file_success = False
        file_result = None
        
        # 重试机制
        while retry_count <= max_retries and not file_success:
            try:
                if retry_count > 0:
                    logger.info(f"重试第 {retry_count} 次: {file_path}")
                
                # 调用单文件上传接口
                file_result = push_bom_to_plm(
                    bom_file_path=file_path,
                    owner=owner,
                    creator=creator,
                    source=source,
                    operator=operator,
                    validate_only=validate_only,
                    output_dir=output_dir
                )
                
                # 检查结果
                if file_result['success']:
                    file_success = True
                    success_count += 1
                    
                    # 累计零件数
                    if file_result.get('stats') and file_result['stats'].get('total_parts'):
                        total_parts += file_result['stats']['total_parts']
                    
                    logger.info(f"✓ 文件处理成功: {file_path}")
                else:
                    # 处理业务错误
                    if file_result.get('status') == 'business_error':
                        missing_parts = file_result.get('missing_parts', [])
                        if missing_parts:
                            business_errors.append({
                                'file': file_path,
                                'error': file_result.get('plm_error', ''),
                                'missing_parts': missing_parts,
                                'missing_count': len(missing_parts)
                            })
                    
                    if retry_count < max_retries:
                        logger.warning(f"文件处理失败，准备重试: {file_path} - {file_result['message']}")
                        retry_count += 1
                        time.sleep(1)  # 重试前等待1秒
                    else:
                        failed_count += 1
                        failed_files.append(file_path)
                        logger.error(f"✗ 文件处理失败: {file_path} - {file_result['message']}")
                        
                        # 是否继续处理其他文件
                        if not continue_on_error:
                            logger.error("遇到错误，停止批量处理")
                            break
                        
                        break  # 退出重试循环
                        
            except Exception as e:
                logger.error(f"处理文件时发生异常: {file_path} - {str(e)}")
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(1)
                else:
                    failed_count += 1
                    failed_files.append(file_path)
                    
                    # 创建错误结果
                    file_result = {
                        'success': False,
                        'status': 'error',
                        'message': f'处理异常: {str(e)}',
                        'data': None,
                        'stats': None,
                        'file_path': None
                    }
                    
                    if not continue_on_error:
                        break
                    break
        
        # 记录文件处理结果
        if file_result:
            results.append({
                'file': file_path,
                'index': i,
                'retry_count': retry_count,
                **file_result
            })
        
        # 如果不继续处理且失败，退出循环
        if not continue_on_error and not file_success:
            break
    
    # 计算处理时间
    processing_time = time.time() - start_time
    processed_count = success_count + failed_count
    
    # 生成汇总统计
    summary = {
        'models': [],
        'total_categories': 0,
        'level_distribution': {},
        'business_error_summary': {},
        'processing_rate': processed_count / len(file_paths) if file_paths else 0,
        'success_rate': success_count / processed_count if processed_count > 0 else 0,
        'avg_processing_time': processing_time / processed_count if processed_count > 0 else 0
    }
    
    # 统计模型和分类信息
    for result in results:
        if result['success'] and result.get('stats'):
            stats = result['stats']
            if stats.get('model'):
                summary['models'].append(stats['model'])
            if stats.get('categories'):
                summary['total_categories'] += stats['categories']
            
            # 合并层级分布
            level_dist = stats.get('level_distribution', {})
            for level, count in level_dist.items():
                summary['level_distribution'][level] = summary['level_distribution'].get(level, 0) + count
    
    # 统计业务错误
    if business_errors:
        error_stats = {}
        total_missing = 0
        for error in business_errors:
            total_missing += error['missing_count']
            error_stats[error['file']] = error['missing_count']
        
        summary['business_error_summary'] = {
            'files_with_errors': len(business_errors),
            'total_missing_parts': total_missing,
            'error_details': error_stats
        }
    
    # 整体成功标志
    overall_success = (failed_count == 0 and len(missing_files) == 0)
    
    # 记录最终结果
    logger.info(f"批量上传完成: 总计{len(file_paths)}个文件, 成功{success_count}个, 失败{failed_count}个, 跳过{skipped_count}个")
    logger.info(f"处理耗时: {processing_time:.2f}秒, 总零件数: {total_parts}")
    
    return {
        'success': overall_success,
        'total': len(file_paths),
        'processed': processed_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'total_parts': total_parts,
        'processing_time': processing_time,
        'results': results,
        'summary': summary,
        'failed_files': failed_files,
        'missing_files': missing_files,
        'business_errors': business_errors,
        'timestamp': current_date
    }

def push_multi_files_from_directory(directory_path: str, owner: str = "adm", creator: str = "adm", 
                                    source: str = "PPPE", operator: str = "sf",
                                    output_dir: str = None, continue_on_error: bool = True, 
                                    max_retries: int = 0) -> Dict[str, Any]:
    """
    从目录中处理多文件推送场景
    根据文件后缀应用不同规则：
    - GBOM后缀：正常推送（validate_only=False）
    - PLM后缀：推送时validate_only=True
    - DIFF后缀：仅推送其中一个，规则是找到包含"_to_"的DIFF文件，提取"to_"后面的信息，推送对应的DIFF文件
    
    Args:
        directory_path: 包含BOM文件的目录路径
        owner: 数据所有者，默认为"adm"
        creator: 数据创建者，默认为"adm"
        source: 数据源，默认为"PPPE"
        operator: 操作员，默认为"sf"
        output_dir: 输出目录，用于保存转换结果，默认为None（使用目录路径下的tmp子目录）
        continue_on_error: 遇到错误时是否继续处理其他文件，默认True
        max_retries: 失败时的最大重试次数，默认0（不重试）
        
    Returns:
        dict: 批量上传结果（与batch_upload_bom_files返回格式相同）
    """
    import time
    
    start_time = time.time()
    
    # 检查目录是否存在
    if not os.path.isdir(directory_path):
        logger.error(f"目录不存在: {directory_path}")
        return {
            'success': False,
            'total': 0,
            'processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'total_parts': 0,
            'processing_time': 0,
            'results': [],
            'summary': {},
            'failed_files': [],
            'missing_files': [directory_path],
            'business_errors': [],
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    logger.info(f"开始处理目录中的文件: {directory_path}")
    
    # 设置默认输出目录
    if output_dir is None:
        output_dir = os.path.join(directory_path, "tmp")
    
    # 获取目录中所有JSON文件
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    
    if not json_files:
        logger.warning(f"目录中没有找到JSON文件: {directory_path}")
        return {
            'success': True,
            'total': 0,
            'processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'total_parts': 0,
            'processing_time': 0,
            'results': [],
            'summary': {},
            'failed_files': [],
            'missing_files': [],
            'business_errors': [],
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    logger.info(f"找到 {len(json_files)} 个JSON文件")
    
    # 分类文件
    gbom_files = []  # GBOM后缀文件：正常推送
    plm_files = []   # PLM后缀文件：validate_only=True推送
    diff_files = []  # DIFF后缀文件：需要特殊处理
    diff_to_files = {}  # 存储包含_to_的DIFF文件映射
    
    for file_path in json_files:
        file_name = os.path.basename(file_path)
        
        if file_name.endswith('_GBOM.json'):
            gbom_files.append(file_path)
        elif file_name.endswith('_PLM.json'):
            plm_files.append(file_path)
        elif file_name.endswith('_DIFF.json'):
            diff_files.append(file_path)
            
            # 检查是否包含_to_模式
            # 格式：XXX_to_YYY_DIFF.json，提取YYY_DIFF.json
            match = re.search(r'(.+?)_to_(.+?_DIFF\.json)$', file_name)
            if match:
                target_file_name = match.group(2)  # 提取to_后面的部分
                target_file_path = os.path.join(directory_path, target_file_name)
                diff_to_files[file_path] = target_file_path
                logger.info(f"发现_to_模式文件: {file_name} -> 目标文件: {target_file_name}")
    
    # 确定需要推送的DIFF文件
    diff_files_to_push = []
    diff_files_to_skip = set()
    
    # 收集所有被_to_指向的目标文件
    target_files_set = set(diff_to_files.values())
    
    for diff_file in diff_files:
        # 如果这个文件是被_to_指向的目标文件，则推送
        if diff_file in target_files_set:
            diff_files_to_push.append(diff_file)
            logger.info(f"DIFF文件将被推送（作为_to_目标）: {os.path.basename(diff_file)}")
        # 如果这个文件是包含_to_的源文件，则跳过
        elif diff_file in diff_to_files:
            diff_files_to_skip.add(diff_file)
            logger.info(f"DIFF文件将被跳过（_to_源文件）: {os.path.basename(diff_file)}")
        # 其他独立的DIFF文件也跳过（根据规则只推送被_to_指向的文件）
        else:
            diff_files_to_skip.add(diff_file)
            logger.info(f"DIFF文件将被跳过（独立的DIFF文件）: {os.path.basename(diff_file)}")
    
    # 构建最终的文件列表和对应的validate_only标志
    files_to_process = []
    
    # GBOM文件：validate_only=False
    for file_path in gbom_files:
        files_to_process.append({
            'file_path': file_path,
            'validate_only': False,
            'type': 'GBOM'
        })
    
    # PLM文件：validate_only=True
    for file_path in plm_files:
        files_to_process.append({
            'file_path': file_path,
            'validate_only': True,
            'type': 'PLM'
        })
    
    # DIFF文件：validate_only=False（正常推送）
    for file_path in diff_files_to_push:
        files_to_process.append({
            'file_path': file_path,
            'validate_only': False,
            'type': 'DIFF'
        })
    
    logger.info(f"文件分类统计: GBOM={len(gbom_files)}, PLM={len(plm_files)}, DIFF推送={len(diff_files_to_push)}, DIFF跳过={len(diff_files_to_skip)}")
    logger.info(f"总计需要处理: {len(files_to_process)} 个文件")
    
    # 使用batch_upload_bom_files的逻辑处理文件，但需要为每个文件设置不同的validate_only
    # 由于batch_upload_bom_files不支持每个文件不同的validate_only，我们需要自己实现处理逻辑
    results = []
    success_count = 0
    failed_count = 0
    skipped_count = len(diff_files_to_skip)
    total_parts = 0
    failed_files = []
    business_errors = []
    
    # 处理每个文件
    for i, file_info in enumerate(files_to_process, 1):
        file_path = file_info['file_path']
        validate_only = file_info['validate_only']
        file_type = file_info['type']
        
        logger.info(f"处理文件 {i}/{len(files_to_process)} [{file_type}]: {os.path.basename(file_path)} (validate_only={validate_only})")
        
        retry_count = 0
        file_success = False
        file_result = None
        
        # 重试机制
        while retry_count <= max_retries and not file_success:
            try:
                if retry_count > 0:
                    logger.info(f"重试第 {retry_count} 次: {file_path}")
                
                # 调用单文件上传接口
                file_result = push_bom_to_plm(
                    bom_file_path=file_path,
                    owner=owner,
                    creator=creator,
                    source=source,
                    operator=operator,
                    validate_only=validate_only,
                    output_dir=output_dir
                )
                
                # 检查结果
                if file_result['success']:
                    file_success = True
                    success_count += 1
                    
                    # 累计零件数
                    if file_result.get('stats') and file_result['stats'].get('total_parts'):
                        total_parts += file_result['stats']['total_parts']
                    
                    logger.info(f"✓ 文件处理成功 [{file_type}]: {os.path.basename(file_path)}")
                else:
                    # 处理业务错误
                    if file_result.get('status') == 'business_error':
                        missing_parts = file_result.get('missing_parts', [])
                        if missing_parts:
                            business_errors.append({
                                'file': file_path,
                                'error': file_result.get('plm_error', ''),
                                'missing_parts': missing_parts,
                                'missing_count': len(missing_parts)
                            })
                    
                    if retry_count < max_retries:
                        logger.warning(f"文件处理失败，准备重试 [{file_type}]: {os.path.basename(file_path)} - {file_result['message']}")
                        retry_count += 1
                        time.sleep(1)  # 重试前等待1秒
                    else:
                        failed_count += 1
                        failed_files.append(file_path)
                        logger.error(f"✗ 文件处理失败 [{file_type}]: {os.path.basename(file_path)} - {file_result['message']}")
                        
                        # 是否继续处理其他文件
                        if not continue_on_error:
                            logger.error("遇到错误，停止批量处理")
                            break
                        
                        break  # 退出重试循环
                        
            except Exception as e:
                logger.error(f"处理文件时发生异常 [{file_type}]: {os.path.basename(file_path)} - {str(e)}")
                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(1)
                else:
                    failed_count += 1
                    failed_files.append(file_path)
                    
                    # 创建错误结果
                    file_result = {
                        'success': False,
                        'status': 'error',
                        'message': f'处理异常: {str(e)}',
                        'data': None,
                        'stats': None,
                        'file_path': None
                    }
                    
                    if not continue_on_error:
                        break
                    break
        
        # 记录文件处理结果
        if file_result:
            results.append({
                'file': file_path,
                'file_type': file_type,
                'index': i,
                'retry_count': retry_count,
                'validate_only': validate_only,
                **file_result
            })
        
        # 如果不继续处理且失败，退出循环
        if not continue_on_error and not file_success:
            break
    
    # 计算处理时间
    processing_time = time.time() - start_time
    processed_count = success_count + failed_count
    
    # 生成汇总统计
    summary = {
        'models': [],
        'total_categories': 0,
        'level_distribution': {},
        'business_error_summary': {},
        'processing_rate': processed_count / len(files_to_process) if files_to_process else 0,
        'success_rate': success_count / processed_count if processed_count > 0 else 0,
        'avg_processing_time': processing_time / processed_count if processed_count > 0 else 0,
        'file_type_summary': {
            'gbom_count': len(gbom_files),
            'plm_count': len(plm_files),
            'diff_push_count': len(diff_files_to_push),
            'diff_skip_count': len(diff_files_to_skip)
        }
    }
    
    # 统计模型和分类信息
    for result in results:
        if result['success'] and result.get('stats'):
            stats = result['stats']
            if stats.get('model'):
                summary['models'].append(stats['model'])
            if stats.get('categories'):
                summary['total_categories'] += stats['categories']
            
            # 合并层级分布
            level_dist = stats.get('level_distribution', {})
            for level, count in level_dist.items():
                summary['level_distribution'][level] = summary['level_distribution'].get(level, 0) + count
    
    # 统计业务错误
    if business_errors:
        error_stats = {}
        total_missing = 0
        for error in business_errors:
            total_missing += error['missing_count']
            error_stats[os.path.basename(error['file'])] = error['missing_count']
        
        summary['business_error_summary'] = {
            'files_with_errors': len(business_errors),
            'total_missing_parts': total_missing,
            'error_details': error_stats
        }
    
    # 整体成功标志
    overall_success = (failed_count == 0)
    
    # 记录最终结果
    logger.info(f"目录文件处理完成: 总计{len(json_files)}个文件, 成功{success_count}个, 失败{failed_count}个, 跳过{skipped_count}个")
    logger.info(f"处理耗时: {processing_time:.2f}秒, 总零件数: {total_parts}")
    
    return {
        'success': overall_success,
        'total': len(json_files),
        'processed': processed_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'total_parts': total_parts,
        'processing_time': processing_time,
        'results': results,
        'summary': summary,
        'failed_files': failed_files,
        'missing_files': [],
        'business_errors': business_errors,
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'directory_path': directory_path,
        'file_type_breakdown': {
            'gbom': gbom_files,
            'plm': plm_files,
            'diff_pushed': diff_files_to_push,
            'diff_skipped': list(diff_files_to_skip)
        }
    }

def push_merged_bom_from_directory(directory_path: str, owner: str = "adm", creator: str = "adm",
                                   source: str = "PPPE", operator: str = "sf",
                                   output_dir: str = None, continue_on_error: bool = True,
                                   max_retries: int = 0) -> Dict[str, Any]:
    """
    将目录中的所有需推送文件合并成一个BOM JSON，使用PLMApiClient.push_bom_info直接推送
    
    规则与 push_multi_files_from_directory 一致：
    - GBOM后缀：正常推送（validate_only=False）
    - PLM后缀：推送时validate_only=True
    - DIFF后缀：仅推送被 "_to_" 指向的目标 DIFF 文件，提取sub_bom_items合并
    
    合并方法参考 transform_bom_data：
    - 合并所有GBOM和PLM文件的MPART数据到一个BOM JSON
    - 合并选中的DIFF文件的sub_bom_items到一个DIFF JSON
    - 使用PLMApiClient.push_bom_info直接推送合并后的数据
    
    Args:
        directory_path: 包含BOM文件的目录路径
        owner: 数据所有者，默认为"adm"
        creator: 数据创建者，默认为"adm"
        source: 数据源，默认为"PPPE"
        operator: 操作员，默认为"sf"
        output_dir: 输出目录，用于保存转换结果，默认为None（使用目录路径下的tmp子目录）
        continue_on_error: 遇到错误时是否继续处理其他文件，默认True（合并推送模式下此参数无效）
        max_retries: 失败时的最大重试次数，默认0（不重试）
        
    Returns:
        dict: 批量上传结果（与push_multi_files_from_directory返回格式相同）
    """
    import time
    
    start_time = time.time()
    
    # 检查目录是否存在
    if not os.path.isdir(directory_path):
        logger.error(f"目录不存在: {directory_path}")
        return {
            'success': False,
            'total': 0,
            'processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'total_parts': 0,
            'processing_time': 0,
            'results': [],
            'summary': {},
            'failed_files': [],
            'missing_files': [directory_path],
            'business_errors': [],
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    logger.info(f"开始合并处理目录中的文件: {directory_path}")
    
    # 设置默认输出目录
    if output_dir is None:
        output_dir = os.path.join(directory_path, "tmp")
    
    # 获取目录中所有JSON文件
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    
    if not json_files:
        logger.warning(f"目录中没有找到JSON文件: {directory_path}")
        return {
            'success': True,
            'total': 0,
            'processed': 0,
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'total_parts': 0,
            'processing_time': 0,
            'results': [],
            'summary': {},
            'failed_files': [],
            'missing_files': [],
            'business_errors': [],
            'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S")
        }
    
    logger.info(f"找到 {len(json_files)} 个JSON文件")
    
    # 分类文件
    gbom_files = []  # GBOM后缀文件：正常推送
    plm_files = []   # PLM后缀文件：validate_only=True推送
    diff_files = []  # DIFF后缀文件：需要特殊处理
    diff_to_files = {}  # 存储包含_to_的DIFF文件映射
    
    for file_path in json_files:
        file_name = os.path.basename(file_path)
        
        if file_name.endswith('_GBOM.json'):
            gbom_files.append(file_path)
        elif file_name.endswith('_PLM.json'):
            plm_files.append(file_path)
        elif file_name.endswith('_DIFF.json'):
            diff_files.append(file_path)
            
            # 检查是否包含_to_模式
            # 格式：XXX_to_YYY_DIFF.json，提取YYY_DIFF.json
            match = re.search(r'(.+?)_to_(.+?_DIFF\.json)$', file_name)
            if match:
                target_file_name = match.group(2)  # 提取to_后面的部分
                target_file_path = os.path.join(directory_path, target_file_name)
                diff_to_files[file_path] = target_file_path
                logger.info(f"发现_to_模式文件: {file_name} -> 目标文件: {target_file_name}")
    
    # 确定需要推送的DIFF文件
    diff_files_to_push = []
    diff_files_to_skip = set()
    
    # 收集所有被_to_指向的目标文件
    target_files_set = set(diff_to_files.values())
    
    for diff_file in diff_files:
        # 如果这个文件是被_to_指向的目标文件，则推送
        if diff_file in target_files_set:
            diff_files_to_push.append(diff_file)
            logger.info(f"DIFF文件将被推送（作为_to_目标）: {os.path.basename(diff_file)}")
        # 如果这个文件是包含_to_的源文件，则跳过
        elif diff_file in diff_to_files:
            diff_files_to_skip.add(diff_file)
            logger.info(f"DIFF文件将被跳过（_to_源文件）: {os.path.basename(diff_file)}")
        # 其他独立的DIFF文件也跳过（根据规则只推送被_to_指向的文件）
        else:
            diff_files_to_skip.add(diff_file)
            logger.info(f"DIFF文件将被跳过（独立的DIFF文件）: {os.path.basename(diff_file)}")
    
    logger.info(f"文件分类统计: GBOM={len(gbom_files)}, PLM={len(plm_files)}, DIFF推送={len(diff_files_to_push)}, DIFF跳过={len(diff_files_to_skip)}")
    
    # 合并GBOM和PLM文件的MPART数据
    merged_bom = {
        "MODEL": "BATCH_MERGED",
        "DESC": ["BATCH MERGED BOM"],
        "MPART": {}
    }
    
    def _remove_children_recursive(part: Dict[str, Any]):
        """递归清除children字段，将第一层的children设置为空数组"""
        if isinstance(part, dict):
            # 如果存在children字段，先递归处理children中的子项
            if 'children' in part:
                for child in part['children']:
                    _remove_children_recursive(child)
                # 将第一层的children设置为空数组
                part['children'] = []
    
    def _merge_mpart_from_file(file_path: str, remove_children: bool = False):
        """从文件中提取并合并MPART数据
        
        Args:
            file_path: 文件路径
            remove_children: 是否清除children字段
        """
        try:
            bom_data = load_bom_from_file(file_path)
            if not bom_data:
                return
            
            mpart_data = bom_data.get('MPART', {})
            if isinstance(mpart_data, dict):
                for category, parts_list in mpart_data.items():
                    if isinstance(parts_list, list):
                        if category not in merged_bom['MPART']:
                            merged_bom['MPART'][category] = []
                        
                        # 复制零件列表，避免修改原数据
                        parts_to_add = []
                        for part in parts_list:
                            # 深拷贝零件数据（包括嵌套结构）
                            if isinstance(part, dict):
                                part_copy = copy.deepcopy(part)
                            else:
                                part_copy = part
                            
                            # 如果需要清除children字段
                            if remove_children and isinstance(part_copy, dict):
                                _remove_children_recursive(part_copy)
                            
                            parts_to_add.append(part_copy)
                        
                        merged_bom['MPART'][category].extend(parts_to_add)
        except Exception as e:
            logger.warning(f"合并MPART失败: {file_path} - {e}")
    
    # 合并GBOM文件（清除children字段）
    for file_path in gbom_files:
        _merge_mpart_from_file(file_path, remove_children=True)
    
    # 合并PLM文件（不清除children，保持原样）
    for file_path in plm_files:
        _merge_mpart_from_file(file_path, remove_children=False)
    
    # 合并DIFF文件的MPART数据（被_to_指向的目标文件，清除children字段）
    for file_path in diff_files_to_push:
        _merge_mpart_from_file(file_path, remove_children=True)
        logger.info(f"合并DIFF文件MPART: {os.path.basename(file_path)}")
    
    # 合并DIFF文件的sub_bom_items
    # 仅从被跳过的包含_to_的源文件中提取sub_bom_items
    merged_diff = {"sub_bom_items": []}
    diff_to_source_files = [f for f in diff_files_to_skip if f in diff_to_files]
    
    for diff_file in diff_to_source_files:
        try:
            diff_data = load_bom_from_file(diff_file)
            if diff_data and isinstance(diff_data, dict):
                sub_bom_items = diff_data.get('sub_bom_items', [])
                if isinstance(sub_bom_items, list):
                    merged_diff['sub_bom_items'].extend(sub_bom_items)
                    logger.info(f"从_to_源文件提取sub_bom_items: {os.path.basename(diff_file)}, 数量: {len(sub_bom_items)}")
        except Exception as e:
            logger.warning(f"合并DIFF失败: {diff_file} - {e}")
    
    if merged_diff['sub_bom_items']:
        logger.info(f"共合并 {len(merged_diff['sub_bom_items'])} 个sub_bom_items")
    
    # 保存合并后的BOM JSON到目录
    merged_bom_path = os.path.join(directory_path, 'merged_bom.json')
    with open(merged_bom_path, 'w', encoding='utf-8') as f:
        json.dump(merged_bom, f, ensure_ascii=False, indent=2)
    logger.info(f"合并BOM文件已保存: {merged_bom_path}")
    
    # 确定validate_only：如果有PLM文件，使用validate_only=True；否则使用False（GBOM正常推送）
    has_plm_files = len(plm_files) > 0
    validate_only = has_plm_files
    
    if has_plm_files:
        logger.info(f"检测到PLM文件，合并推送将使用validate_only=True")
    else:
        logger.info(f"仅有GBOM文件，合并推送将使用validate_only=False")
    
    # 使用PLMApiClient.push_bom_info直接推送
    plm_client = PLMApiClient()
    
    # 重试机制
    retry_count = 0
    push_result = None
    file_success = False
    
    while retry_count <= max_retries and not file_success:
        try:
            if retry_count > 0:
                logger.info(f"重试第 {retry_count} 次推送合并BOM")
            
            # 调用push_bom_info推送合并后的数据
            diff_data_for_push = merged_diff if merged_diff.get('sub_bom_items') else None
            push_result = plm_client.push_bom_info(
                bom_json=merged_bom,
                owner=owner,
                creator=creator,
                source=source,
                operator=operator,
                validate_only=validate_only,
                diff_json=diff_data_for_push
            )
            
            if push_result.get('status') in ['success', 'validation_success']:
                file_success = True
            else:
                if retry_count < max_retries:
                    logger.warning(f"合并推送失败，准备重试: {push_result.get('message', '')}")
                    retry_count += 1
                    time.sleep(1)
                else:
                    break
                    
        except Exception as e:
            logger.error(f"合并推送时发生异常: {str(e)}")
            if retry_count < max_retries:
                retry_count += 1
                time.sleep(1)
            else:
                push_result = {
                    'status': 'error',
                    'message': f'处理异常: {str(e)}',
                    'data': None
                }
                break
    
    processing_time = time.time() - start_time
    
    # 构建与push_multi_files_from_directory兼容的返回格式
    success = push_result and push_result.get('status') in ['success', 'validation_success']
    success_count = 1 if success else 0
    failed_count = 1 if not success else 0
    skipped_count = len(diff_files_to_skip)
    processed_count = success_count + failed_count
    
    # 构建results列表
    results = []
    if push_result:
        result_item = {
            'file': merged_bom_path,
            'file_type': 'MERGED',
            'index': 1,
            'retry_count': retry_count,
            'validate_only': validate_only,
            'success': success,
            'status': push_result.get('status', 'unknown'),
            'message': push_result.get('message', ''),
            'data': push_result.get('data'),
            'stats': None,
            'file_path': None
        }
        
        # 尝试从push_result中提取统计信息
        if push_result.get('data'):
            transformed_data = push_result['data']
            if isinstance(transformed_data, dict) and 'ARRAY' in transformed_data:
                total_parts = len(transformed_data['ARRAY'])
                result_item['stats'] = {
                    'model': merged_bom.get('MODEL', 'BATCH_MERGED'),
                    'total_parts': total_parts,
                    'level_distribution': {},
                    'categories': len(merged_bom.get('MPART', {}))
                }
        
        results.append(result_item)
    
    # 统计业务错误
    business_errors = []
    failed_files = []
    if push_result and push_result.get('status') == 'business_error':
        missing_parts = push_result.get('missing_parts', [])
        if missing_parts:
            business_errors.append({
                'file': merged_bom_path,
                'error': push_result.get('error', ''),
                'missing_parts': missing_parts,
                'missing_count': len(missing_parts)
            })
    
    if not success:
        failed_files.append(merged_bom_path)
    
    # 生成汇总统计
    total_parts = 0
    if results and results[0].get('stats'):
        total_parts = results[0]['stats'].get('total_parts', 0)
    
    summary = {
        'models': [merged_bom.get('MODEL', 'BATCH_MERGED')],
        'total_categories': len(merged_bom.get('MPART', {})),
        'level_distribution': {},
        'business_error_summary': {},
        'processing_rate': processed_count / len(json_files) if json_files else 0,
        'success_rate': success_count / processed_count if processed_count > 0 else 0,
        'avg_processing_time': processing_time / processed_count if processed_count > 0 else 0,
        'file_type_summary': {
            'gbom_count': len(gbom_files),
            'plm_count': len(plm_files),
            'diff_push_count': len(diff_files_to_push),
            'diff_skip_count': len(diff_files_to_skip)
        }
    }
    
    # 统计业务错误
    if business_errors:
        error_stats = {}
        total_missing = 0
        for error in business_errors:
            total_missing += error['missing_count']
            error_stats[os.path.basename(error['file'])] = error['missing_count']
        
        summary['business_error_summary'] = {
            'files_with_errors': len(business_errors),
            'total_missing_parts': total_missing,
            'error_details': error_stats
        }
    
    overall_success = (failed_count == 0)
    
    logger.info(f"合并推送完成: 总计{len(json_files)}个文件, 成功{success_count}个, 失败{failed_count}个, 跳过{skipped_count}个")
    logger.info(f"处理耗时: {processing_time:.2f}秒, 总零件数: {total_parts}")
    
    return {
        'success': overall_success,
        'total': len(json_files),
        'processed': processed_count,
        'success_count': success_count,
        'failed_count': failed_count,
        'skipped_count': skipped_count,
        'total_parts': total_parts,
        'processing_time': processing_time,
        'results': results,
        'summary': summary,
        'failed_files': failed_files,
        'missing_files': [],
        'business_errors': business_errors,
        'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
        'directory_path': directory_path,
        'file_type_breakdown': {
            'gbom': gbom_files,
            'plm': plm_files,
            'diff_pushed': diff_files_to_push,
            'diff_skipped': list(diff_files_to_skip)
        },
        'merged_bom_path': merged_bom_path
    }

def push_bom_files_by_design_id(design_id: str, owner: str = "adm", creator: str = "adm",
                                 source: str = "PPPE", operator: str = "sf",
                                 output_dir: str = None, continue_on_error: bool = True,
                                 max_retries: int = 0) -> Dict[str, Any]:
    """
    根据design_id查询数据库，获取bom_path和design_info，然后调用push_multi_files_from_directory推送文件
    
    处理逻辑：
    - 如果全部成功：修改design_status字段为'PUSHED'，清空bom_info中的"json_files"字段
    - 如果部分成功：更新design_status字段为'FAILED'，去除bom_info中"json_files"中已推送的文件
    
    Args:
        design_id: 设计ID，格式如 "SBOM_20251103_F573B7D3"
        owner: 数据所有者，默认为"adm"
        creator: 数据创建者，默认为"adm"
        source: 数据源，默认为"PPPE"
        operator: 操作员，默认为"sf"
        output_dir: 输出目录，用于保存转换结果，默认为None（使用bom_path下的tmp子目录）
        continue_on_error: 遇到错误时是否继续处理其他文件，默认True
        max_retries: 失败时的最大重试次数，默认0（不重试）
        
    Returns:
        dict: 推送和处理结果
        {
            'success': bool,              # 整体是否成功
            'design_id': str,             # design_id
            'push_result': dict,          # push_multi_files_from_directory的返回结果
            'db_update_success': bool,     # 数据库更新是否成功
            'message': str                # 处理消息
        }
    """
    import pymysql
    
    logger.info(f"开始处理design_id: {design_id}")
    
    # 查询数据库获取bom_path和design_info
    connection = get_connection()
    if not connection:
        return {
            'success': False,
            'design_id': design_id,
            'push_result': None,
            'db_update_success': False,
            'message': '数据库连接失败'
        }
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询设计记录
            sql = "SELECT bom_path, design_info, design_status FROM sbom_design WHERE design_id = %s"
            cursor.execute(sql, (design_id,))
            record = cursor.fetchone()
            
            if not record:
                logger.error(f"未找到design_id={design_id}的记录")
                return {
                    'success': False,
                    'design_id': design_id,
                    'push_result': None,
                    'db_update_success': False,
                    'message': f'未找到design_id={design_id}的记录'
                }
            
            bom_path = record['bom_path']
            design_info_str = record.get('design_info', '{}')
            current_status = record.get('design_status', '')
            
            # 解析design_info JSON
            try:
                if isinstance(design_info_str, str):
                    design_info = json.loads(design_info_str) if design_info_str else {}
                else:
                    design_info = design_info_str
            except json.JSONDecodeError:
                logger.warning(f"design_info JSON解析失败，使用空字典")
                design_info = {}
            
            if not bom_path:
                logger.error(f"bom_path为空")
                return {
                    'success': False,
                    'design_id': design_id,
                    'push_result': None,
                    'db_update_success': False,
                    'message': 'bom_path为空'
                }
            
            logger.info(f"查询到记录: bom_path={bom_path}, design_status={current_status}")
            logger.info(f"design_info中的json_files数量: {len(design_info.get('json_files', []))}")
            
            # 将相对路径转换为绝对路径
            # bom_path格式可能是: data/tmp/250048_20251103_150933
            if not os.path.isabs(bom_path):
                # 尝试从项目根目录构建绝对路径
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
                absolute_bom_path = os.path.join(project_root, bom_path.replace('/', os.sep))
            else:
                absolute_bom_path = bom_path.replace('/', os.sep)
            
            logger.info(f"转换后的绝对路径: {absolute_bom_path}")
            
            # 检查目录是否存在
            if not os.path.isdir(absolute_bom_path):
                logger.error(f"目录不存在: {absolute_bom_path}")
                return {
                    'success': False,
                    'design_id': design_id,
                    'push_result': None,
                    'db_update_success': False,
                    'message': f'目录不存在: {absolute_bom_path}'
                }
            
            # 调用push_multi_files_from_directory
            # push_merged_bom_from_directory
            logger.info(f"开始调用push_multi_files_from_directory处理目录: {absolute_bom_path}")
            push_result = push_merged_bom_from_directory(
                directory_path=absolute_bom_path,
                owner=owner,
                creator=creator,
                source=source,
                operator=operator,
                output_dir=output_dir,
                continue_on_error=continue_on_error,
                max_retries=max_retries
            )
            
            logger.info(f"推送结果: 成功={push_result['success_count']}, 失败={push_result['failed_count']}, 跳过={push_result['skipped_count']}")
            
            # 获取已推送成功的文件列表（从results中提取）
            pushed_files = []
            for result in push_result.get('results', []):
                if result.get('success'):
                    file_path = result.get('file', '')
                    if file_path:
                        # 转换为相对路径（相对于bom_path）
                        if os.path.isabs(file_path):
                            rel_path = os.path.relpath(file_path, absolute_bom_path)
                            # 转换为正斜杠格式
                            rel_path = rel_path.replace('\\', '/')
                            pushed_files.append(rel_path)
                        else:
                            pushed_files.append(file_path)
            
            logger.info(f"已推送成功的文件数: {len(pushed_files)}")
            
            # 更新数据库
            try:
                # 获取原始json_files列表
                json_files = design_info.get('json_files', [])
                
                # 判断是否全部成功
                # 全部成功：至少推送了一些文件，且没有失败的文件（跳过的不算失败）
                all_success = (push_result['success_count'] > 0 and 
                             push_result['failed_count'] == 0)
                
                # 从push_result的results中提取第一个结果的status、message和data
                push_status = None
                push_message = None
                push_data = None
                if push_result.get('results') and len(push_result['results']) > 0:
                    first_result = push_result['results'][0]
                    push_status = first_result.get('status')
                    push_message = first_result.get('message')
                    push_data = first_result.get('data')
                
                # 更新design_status
                new_design_info = design_info.copy()
                if all_success:
                    # 全部成功：更新status为'PUSHED'
                    new_status = 'PUSHED'
                    logger.info(f"全部推送成功，更新status为PUSHED")
                else:
                    # 部分成功：更新status为'FAILED'
                    new_status = 'FAILED'
                    logger.info(f"部分推送成功，更新status为FAILED")
                
                # 使用push_result中的status、message和data更新design_info
                if push_status is not None:
                    new_design_info['push_status'] = push_status
                if push_message is not None:
                    new_design_info['push_message'] = push_message
                if push_data is not None:
                    new_design_info['push_data'] = push_data
                
                # 添加推送时间戳
                new_design_info['push_time'] = datetime.now().isoformat()
                
                # 更新数据库
                update_sql = """
                    UPDATE sbom_design 
                    SET design_status = %s, 
                        design_info = %s,
                        update_time = %s
                    WHERE design_id = %s
                """
                update_time = datetime.now()
                cursor.execute(update_sql, (
                    new_status,
                    json.dumps(new_design_info, ensure_ascii=False),
                    update_time,
                    design_id
                ))
                
                # 同步更新 sbom_feishu_approval 表中 design_id 相同的记录
                try:
                    # 如果 new_status 是 PUSHED，需要更新 feishu_status 为 APPROVED
                    if new_status == 'PUSHED':
                        update_approval_sql = """
                            UPDATE sbom_feishu_approval 
                            SET sbom_status = %s, 
                                feishu_status = %s,
                                update_time = %s
                            WHERE design_id = %s AND deleted = '0'
                        """
                        cursor.execute(update_approval_sql, (
                            new_status,      # sbom_status = 'PUSHED'
                            'APPROVED',      # feishu_status = 'APPROVED'
                            update_time,
                            design_id
                        ))
                    else:
                        # 其他状态只更新 sbom_status
                        update_approval_sql = """
                            UPDATE sbom_feishu_approval 
                            SET sbom_status = %s, 
                                update_time = %s
                            WHERE design_id = %s AND deleted = '0'
                        """
                        cursor.execute(update_approval_sql, (
                            new_status,      # sbom_status = 'FAILED' 或其他
                            update_time,
                            design_id
                        ))
                    
                    approval_update_rows = cursor.rowcount
                    if approval_update_rows > 0:
                        logger.info(f"已同步更新 sbom_feishu_approval 表: design_id={design_id}, sbom_status={new_status}, 影响行数: {approval_update_rows}")
                        if new_status == 'PUSHED':
                            logger.info(f"已将 feishu_status 更新为 APPROVED")
                    else:
                        logger.warning(f"未找到匹配的 sbom_feishu_approval 记录: design_id={design_id}")
                except Exception as approval_update_error:
                    logger.error(f"更新 sbom_feishu_approval 表失败: design_id={design_id}, error={str(approval_update_error)}")
                    # 即使更新失败，也不影响主更新操作，继续执行
                
                connection.commit()
                
                logger.info(f"数据库更新成功: design_status={new_status}")
                
                return {
                    'success': True,
                    'design_id': design_id,
                    'push_result': push_result,
                    'db_update_success': True,
                    'message': f'处理完成: 成功{push_result["success_count"]}个, 失败{push_result["failed_count"]}个, 状态更新为{new_status}'
                }
                
            except Exception as e:
                logger.error(f"更新数据库失败: {e}")
                connection.rollback()
                return {
                    'success': push_result.get('success', False),
                    'design_id': design_id,
                    'push_result': push_result,
                    'db_update_success': False,
                    'message': f'推送完成但数据库更新失败: {str(e)}'
                }
                
    except Exception as e:
        logger.error(f"处理design_id时发生异常: {e}")
        if connection:
            connection.rollback()
        return {
            'success': False,
            'design_id': design_id,
            'push_result': None,
            'db_update_success': False,
            'message': f'处理异常: {str(e)}'
        }
    finally:
        if connection:
            connection.close()

def get_plm_client_info():
    """
    获取PLM客户端信息
    
    Returns:
        dict: 客户端信息
    """
    plm_client = PLMApiClient()
    return {
        'endpoint': plm_client.push_bom_endpoint,
        'mapping': plm_client.bom_mapping,
        'base_url': plm_client.base_url
    }

# ==================== CLI工具函数 ====================

def push_bom_file_cli(bom_file_path: str, validate_only: bool = False, diff_file_path: str = None):
    """
    推送BOM文件 (CLI工具用)
    
    Args:
        bom_file_path: BOM文件路径
        validate_only: 是否仅验证格式
        diff_file_path: 差异数据文件路径，可选
        
    Returns:
        bool: 是否成功
    """
    result = push_bom_to_plm(bom_file_path, validate_only=validate_only, 
                            output_dir="plm_output", diff_file_path=diff_file_path)
    
    if result['success']:
        status_text = "格式验证通过" if validate_only else "推送成功"
        print(f"✓ {status_text}: {bom_file_path}")
        
        stats = result['stats']
        print(f"统计信息:")
        print(f"  型号: {stats['model']}")
        print(f"  零件数: {stats['total_parts']}")
        if stats.get('sub_bom_parts', 0) > 0:
            print(f"  子BOM项目: {stats['sub_bom_parts']}")
        print(f"  分类数: {stats['categories']}")
        print(f"  接口地址: {stats['endpoint']}")
        if stats.get('diff_file'):
            print(f"  差异文件: {stats['diff_file']}")
        
        if stats['level_distribution']:
            print(f"  层级分布:")
            for level in sorted(stats['level_distribution'].keys()):
                print(f"    层级 {level}: {stats['level_distribution'][level]} 个零件")
        
        if result['file_path']:
            print(f"  转换结果已保存到: {result['file_path']}")
        
        return True
    else:
        print(f"✗ 处理失败: {result['message']}")
        
        # 处理业务错误（如缺失物料）
        if result.get('status') == 'business_error':
            missing_parts = result.get('missing_parts', [])
            if missing_parts:
                print(f"⚠️  发现 {len(missing_parts)} 个物料在PLM中不存在:")
                for i, part in enumerate(missing_parts[:10], 1):  # 只显示前10个
                    print(f"    {i}. {part}")
                if len(missing_parts) > 10:
                    print(f"    ... 还有 {len(missing_parts) - 10} 个物料")
                
                # 显示处理建议
                stats = result.get('stats', {})
                missing_analysis = stats.get('missing_analysis', {})
                if missing_analysis:
                    suggestions = missing_analysis.get('suggestions', [])
                    if suggestions:
                        print(f"\n💡 处理建议:")
                        for suggestion in suggestions[:5]:  # 只显示前5条建议
                            print(f"    {suggestion}")
        
        return False

def show_bom_info_cli(bom_file_path: str):
    """
    显示BOM文件信息 (CLI工具用)
    
    Args:
        bom_file_path: BOM文件路径
    """
    try:
        bom_data = load_bom_from_file(bom_file_path)
        if not bom_data:
            print(f"无法加载文件: {bom_file_path}")
            return
        
        plm_client = PLMApiClient()
        all_parts = plm_client.extract_all_parts(bom_data, validate_only=False)
        
        print(f"\nBOM文件信息: {bom_file_path}")
        print(f"  型号: {bom_data.get('MODEL', 'Unknown')}")
        print(f"  描述: {', '.join(bom_data.get('DESC', []))}")
        print(f"  总零件数: {len(all_parts)}")
        print(f"  分类数: {len(bom_data.get('MPART', {}))}")
        
        # 层级统计
        level_stats = {}
        for part in all_parts:
            level = part.get("MPART.LVL", 0)
            level_stats[level] = level_stats.get(level, 0) + 1
        
        if level_stats:
            print(f"  层级分布:")
            for level in sorted(level_stats.keys()):
                print(f"    层级 {level}: {level_stats[level]} 个零件")
        
        # 分类统计
        mpart_data = bom_data.get('MPART', {})
        if mpart_data:
            print(f"  分类详情:")
            for category, parts in mpart_data.items():
                parts_with_children = sum(1 for part in parts if part.get('children'))
                print(f"    {category}: {len(parts)} 个零件，{parts_with_children} 个有子件")
        
    except Exception as e:
        print(f"显示BOM信息失败: {e}")

def show_plm_client_info_cli():
    """
    显示PLM客户端信息 (CLI工具用)
    """
    try:
        info = get_plm_client_info()
        print(f"\nPLM客户端信息:")
        print(f"  基础URL: {info['base_url']}")
        print(f"  推送接口: {info['endpoint']}")
        print(f"  字段映射:")
        for plm_field, bom_field in info['mapping']['bom_PLM'].items():
            print(f"    {plm_field} <- {bom_field}")
        print(f"  接口格式:")
        print(f"    SOURCE: 数据源 (默认: PPPE)")
        print(f"    MARK: 标记 (格式: 型号_日期)")
        print(f"    OPERATOR: 操作员 (默认: sf)")
        print(f"    ARRAY: BOM数据数组")
    except Exception as e:
        print(f"获取PLM客户端信息失败: {e}")


def main():
    """
    CLI工具主函数
    """
    while True:
        print("\n=== PLM BOM数据推送工具 ===")
        print("1. 推送单个BOM文件到PLM (验证格式)")
        print("2. 推送单个BOM文件到PLM (实际推送)")
        print("3. 批量推送BOM文件")
        print("4. 查看BOM文件信息")
        print("5. 查看PLM客户端信息")
        print("6. 推送默认文件 (SP0030-00-23-5QP.json)")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-6): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
            
        elif choice == '1':
            file_path = input("请输入BOM文件路径: ").strip()
            if file_path:
                push_bom_file_cli(file_path, validate_only=True)
            else:
                print("文件路径不能为空")
                
        elif choice == '2':
            file_path = input("请输入BOM文件路径: ").strip()
            if file_path:
                confirm = input("确认要实际推送到PLM系统吗? (y/N): ").strip().lower()
                if confirm == 'y':
                    push_bom_file_cli(file_path, validate_only=False)
                else:
                    print("已取消推送")
            else:
                print("文件路径不能为空")
                
        elif choice == '3':
            files_input = input("请输入BOM文件路径列表 (用逗号分隔): ").strip()
            if files_input:
                file_list = [f.strip() for f in files_input.split(',') if f.strip()]
                validate_only = input("是否仅验证格式? (Y/n): ").strip().lower() != 'n'
                
                print(f"\n开始批量处理 {len(file_list)} 个文件...")
                batch_result = batch_push_bom_to_plm(file_list, validate_only=validate_only, 
                                                   output_dir="plm_output")
                
                print(f"\n批量处理完成:")
                print(f"  总计: {batch_result['total']} 个文件")
                print(f"  成功: {batch_result['success']} 个文件")
                print(f"  失败: {batch_result['failed']} 个文件")
                
                if batch_result['failed'] > 0:
                    print(f"\n失败的文件:")
                    for result in batch_result['results']:
                        if not result['success']:
                            print(f"  {result['file']}: {result['message']}")
            else:
                print("文件路径列表不能为空")
                
        elif choice == '4':
            file_path = input("请输入BOM文件路径: ").strip()
            if file_path:
                show_bom_info_cli(file_path)
            else:
                print("文件路径不能为空")
                
        elif choice == '5':
            show_plm_client_info_cli()
            
        elif choice == '6':
            default_file = "data/processed/SP0030-00-23-5QP.json"
            print(f"推送默认文件: {default_file}")
            push_bom_file_cli(default_file, validate_only=True)
            
        else:
            print("无效选择，请重新输入")


def test_with_specific_file(file_path: str):
    """
    使用指定文件进行测试 (兼容旧版本)
    
    Args:
        file_path: BOM文件路径
    """
    print(f"测试文件: {file_path}")
    push_bom_file_cli(file_path, validate_only=True)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 如果提供了文件路径参数，使用指定文件进行测试
        file_path = sys.argv[1]
        test_with_specific_file(file_path)
    else:
        # 否则运行CLI工具
        main()