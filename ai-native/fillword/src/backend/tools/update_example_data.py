#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据更新工具 - 从empty_cells.json和full_cells.json更新example_data.json
支持API调用和CLI模式
"""

import json
import os
import sys
import argparse
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class DataUpdater:
    """数据更新器 - 负责从源文件提取数据并更新目标文件"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化数据更新器
        
        Args:
            base_dir: 项目根目录，默认为当前文件的上级目录
        """
        if base_dir is None:
            # 获取项目根目录（当前文件的上4级目录）
            current_file = Path(__file__).absolute()
            self.base_dir = current_file.parent.parent.parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        # 设置默认路径
        self.tmp_dir = self.base_dir / "tmp"
        self.data_dir = self.base_dir / "data" / "processed"
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        
    def load_json_file(self, file_path: str) -> Any:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {file_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"解析JSON文件失败: {file_path}, 错误: {e}")
    
    def save_json_file(self, file_path: str, data: Any) -> None:
        """保存JSON文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"成功保存文件: {file_path}")
        except Exception as e:
            raise IOError(f"保存文件失败: {file_path}, 错误: {e}")
    
    def create_relationship_key(self, relationship_list: List[str]) -> str:
        """将relationship列表拼接成关键词"""
        if not relationship_list:
            return ""
        return "".join(relationship_list)
    
    def find_cell_value(self, full_cells_data: Dict, row: int, col: int) -> str:
        """从full_cells.json中根据row和col查找对应的值"""
        try:
            # 在document_structure中查找表格数据
            for item in full_cells_data.get("document_structure", []):
                if item.get("type") == "table":
                    cell_map = item.get("structure", {}).get("cell_map", [])
                    
                    # 遍历所有行
                    for row_data in cell_map:
                        if not row_data:
                            continue
                        
                        # 先尝试精确匹配
                        for cell in row_data:
                            if cell.get("row") == row and cell.get("col") == col:
                                content = cell.get("content", "").strip()
                                if content:
                                    return content
                        
                        # 如果精确匹配失败，尝试在同一行中查找非空的内容单元格
                        # 通常数据在标签单元格的右侧
                        row_cells = [cell for cell in row_data if cell.get("row") == row]
                        row_cells.sort(key=lambda x: x.get("col", 0))
                        
                        for cell in row_cells:
                            content = cell.get("content", "").strip()
                            # 跳过标签单元格（通常包含中文标签）
                            if content and not any(label in content for label in [
                                "企业名称", "企业注册地", "通讯地址", "法定代表人", "控股股东", 
                                "实际控制人", "联系人", "传真", "注册时间", "统一社会信用代码", 
                                "所属行业", "具体细分领域", "企业类型"
                            ]):
                                # 如果目标列在这个范围内，返回这个内容
                                if abs(cell.get("col", 0) - col) <= 2:  # 允许一定的列偏差
                                    return content
            
            return ""
        except Exception as e:
            self.logger.warning(f"查找单元格 ({row}, {col}) 时出错: {e}")
            return ""
    
    def update_example_data(self, 
                          empty_cells_path: str = None, 
                          full_cells_path: str = None, 
                          example_data_path: str = None) -> Dict[str, Any]:
        """
        更新example_data.json的API方法
        
        Args:
            empty_cells_path: 空单元格文件路径
            full_cells_path: 完整单元格文件路径  
            example_data_path: 目标数据文件路径
            
        Returns:
            dict: 更新结果统计信息
        """
        # 设置默认路径
        if empty_cells_path is None:
            empty_cells_path = self.tmp_dir / "empty_cells.json"
        if full_cells_path is None:
            full_cells_path = self.tmp_dir / "full_cells.json"
        if example_data_path is None:
            example_data_path = self.data_dir / "example_data.json"
        
        self.logger.info(f"开始更新数据...")
        self.logger.info(f"空单元格文件: {empty_cells_path}")
        self.logger.info(f"完整数据文件: {full_cells_path}")
        self.logger.info(f"目标文件: {example_data_path}")
        
        try:
            # 加载数据
            empty_cells = self.load_json_file(str(empty_cells_path))
            full_cells = self.load_json_file(str(full_cells_path))
            example_data = self.load_json_file(str(example_data_path))
            
            # 统计更新情况
            updated_count = 0
            not_found_count = 0
            updated_fields = []
            not_found_fields = []
            
            # 处理每个空单元格
            for cell in empty_cells:
                row = cell.get("row")
                col = cell.get("col")
                relationship = cell.get("relationship", [])
                
                if not relationship:
                    continue
                    
                # 创建关键词
                key = self.create_relationship_key(relationship)
                if not key:
                    continue
                    
                # 查找对应的值
                value = self.find_cell_value(full_cells, row, col)
                
                if value:
                    # 更新example_data
                    example_data[key] = value
                    updated_count += 1
                    updated_fields.append(key)
                    self.logger.info(f"更新: {key} = {value}")
                else:
                    not_found_count += 1
                    not_found_fields.append(key)
                    self.logger.warning(f"未找到值: {key} (row: {row}, col: {col})")
            
            # 保存更新后的数据
            self.save_json_file(str(example_data_path), example_data)
            
            # 生成更新摘要
            update_summary = {
                "update_time": datetime.now().isoformat(),
                "total_fields_processed": len(empty_cells),
                "successfully_updated": updated_count,
                "not_found": not_found_count,
                "updated_fields": updated_fields,
                "not_found_fields": not_found_fields,
                "success_rate": f"{(updated_count / len(empty_cells) * 100):.2f}%" if empty_cells else "0%"
            }
            
            # 保存更新摘要
            summary_path = self.tmp_dir / "update_summary.json"
            self.save_json_file(str(summary_path), update_summary)
            
            self.logger.info(f"更新完成!")
            self.logger.info(f"成功更新: {updated_count} 个字段")
            self.logger.info(f"未找到值: {not_found_count} 个字段")
            self.logger.info(f"成功率: {update_summary['success_rate']}")
            
            return update_summary
            
        except Exception as e:
            self.logger.error(f"更新数据失败: {e}")
            raise
    
    def batch_update(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量更新API - 支持多个文件对的更新
        
        Args:
            config: 配置字典，包含文件路径映射
            
        Returns:
            dict: 批量更新结果
        """
        results = []
        
        for item in config.get("update_tasks", []):
            try:
                result = self.update_example_data(
                    empty_cells_path=item.get("empty_cells_path"),
                    full_cells_path=item.get("full_cells_path"),
                    example_data_path=item.get("example_data_path")
                )
                result["task_name"] = item.get("name", "unnamed_task")
                results.append(result)
            except Exception as e:
                self.logger.error(f"任务 {item.get('name', 'unnamed')} 失败: {e}")
                results.append({
                    "task_name": item.get("name", "unnamed_task"),
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "batch_update_time": datetime.now().isoformat(),
            "total_tasks": len(config.get("update_tasks", [])),
            "successful_tasks": len([r for r in results if r.get("successfully_updated", 0) > 0]),
            "results": results
        }


def setup_logging(verbose: bool = False):
    """设置日志配置"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # 确保日志目录存在
    log_dir = Path(__file__).parent.parent.parent.parent / "data" / "processed"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'data_updater.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """CLI模式主函数"""
    parser = argparse.ArgumentParser(
        description='数据更新工具 - 从empty_cells.json和full_cells.json更新example_data.json'
    )
    
    parser.add_argument(
        '--empty-cells', 
        type=str, 
        help='空单元格JSON文件路径'
    )
    
    parser.add_argument(
        '--full-cells', 
        type=str, 
        help='完整单元格JSON文件路径'
    )
    
    parser.add_argument(
        '--example-data', 
        type=str, 
        help='目标数据JSON文件路径'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        help='批量更新配置文件路径'
    )
    
    parser.add_argument(
        '--base-dir', 
        type=str, 
        help='项目根目录路径'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='详细输出模式'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # 初始化更新器
        updater = DataUpdater(args.base_dir)
        
        if args.config:
            # 批量更新模式
            logger.info(f"使用配置文件进行批量更新: {args.config}")
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            result = updater.batch_update(config)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        else:
            # 单次更新模式
            result = updater.update_example_data(
                empty_cells_path=args.empty_cells,
                full_cells_path=args.full_cells,
                example_data_path=args.example_data
            )
            
            print(f"\n=== 更新结果 ===")
            print(f"处理字段总数: {result['total_fields_processed']}")
            print(f"成功更新: {result['successfully_updated']}")
            print(f"未找到数据: {result['not_found']}")
            print(f"成功率: {result['success_rate']}")
            
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()