#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BOM数据处理器 - 基于重新设计的AI分析JSON结构
处理用户上传差异表 → 数据库补全 → PLM系统上传的完整流程
"""

import json
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import re
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BOMInfo:
    """BOM基本信息"""
    product_code: str
    base_product_code: str = ""
    model_type: str = ""
    created_at: str = ""
    updated_at: str = ""
    data_sources: List[str] = None
    plm_parent_id: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if self.data_sources is None:
            self.data_sources = []
        if not self.model_type and self.product_code:
            self.model_type = self._extract_model_type(self.product_code)

    def _extract_model_type(self, product_code: str) -> str:
        """从产品编码提取型号类型"""
        match = re.match(r'^([A-Z]+)', product_code)
        return match.group(1) if match else "UNKNOWN"


@dataclass
class BOMPart:
    """BOM零件信息"""
    MPART_NO: str  # 零件编号
    MPART_NAME: str = ""  # 零件名称
    MBOM_BNUM: float = 0.0  # 数量
    MPART_WLSX: str = ""  # 物料属性
    MPART_UNIT: str = "PCS"  # 单位
    MBOM_LOC: str = ""  # 位置号
    MBOM_OP: str = ""  # 工位
    MBOM_CHANGE_TYPE: str = "none"  # 变更类型
    MBOM_OLD_PART: str = ""  # 原零件编号
    MBOM_OLD_BNUM: float = 0.0  # 原数量
    MBOM_CHANGE_REASON: str = ""  # 变更原因
    MPART_SOURCE: str = ""  # 数据来源
    MPART_EFFECTIVE_DATE: str = ""  # 生效日期
    MPART_EXPIRE_DATE: str = ""  # 失效日期
    SUB_BOM: List['BOMPart'] = None  # 子阶BOM

    def __post_init__(self):
        if self.SUB_BOM is None:
            self.SUB_BOM = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "MPART.NO": self.MPART_NO,
            "MPART.NAME": self.MPART_NAME,
            "MBOM.BNUM": self.MBOM_BNUM,
            "MPART.WLSX": self.MPART_WLSX,
            "MPART.UNIT": self.MPART_UNIT,
            "MBOM.LOC": self.MBOM_LOC,
            "MBOM.OP": self.MBOM_OP,
            "MBOM.CHANGE_TYPE": self.MBOM_CHANGE_TYPE,
            "MPART.SOURCE": self.MPART_SOURCE
        }
        
        # 只在有值时添加可选字段
        if self.MBOM_OLD_PART:
            result["MBOM.OLD_PART"] = self.MBOM_OLD_PART
        if self.MBOM_OLD_BNUM > 0:
            result["MBOM.OLD_BNUM"] = self.MBOM_OLD_BNUM
        if self.MBOM_CHANGE_REASON:
            result["MBOM.CHANGE_REASON"] = self.MBOM_CHANGE_REASON
        if self.MPART_EFFECTIVE_DATE:
            result["MPART.EFFECTIVE_DATE"] = self.MPART_EFFECTIVE_DATE
        if self.MPART_EXPIRE_DATE:
            result["MPART.EXPIRE_DATE"] = self.MPART_EXPIRE_DATE
        if self.SUB_BOM:
            result["SUB_BOM"] = [part.to_dict() for part in self.SUB_BOM]
            
        return result


@dataclass
class ChangeSummary:
    """变更汇总"""
    total_changes: int = 0
    add_count: int = 0
    modify_count: int = 0
    delete_count: int = 0
    unchanged_count: int = 0
    sub_bom_count: int = 0


class BOMDataProcessor:
    """BOM数据处理器"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.db_query = None
        self._init_db_connection()
    
    def _load_config(self, config_file: str = None) -> Dict[str, Any]:
        """加载配置文件"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 返回默认配置
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "database_mapping": {
                "table_name": "dwd_mfg_bom_df",
                "query_condition": "product_item_no = ? AND level = '0'",
                "field_mapping": {
                    "MPART.NO": "item_no_c",
                    "MPART.NAME": "item_name_c",
                    "MBOM.BNUM": "qty",
                    "MPART.WLSX": "item_cls_c",
                    "MPART.UNIT": "unit_c",
                    "MBOM.LOC": "loc",
                    "MBOM.OP": "op",
                    "MPART.EFFECTIVE_DATE": "effective_date",
                    "MPART.EXPIRE_DATE": "expire_date"
                },
                "category_extraction": {
                    "method": "part_number_prefix",
                    "pattern": "^(\\d{3})",
                    "fallback": "999"
                }
            },
            "excel_diff_mapping": {
                "sheet_name": "BOM差异表",
                "header_detection": {
                    "base_bom_indicators": ["Base BOM", "基础BOM", "原BOM"],
                    "new_bom_indicators": ["新建 BOM", "新BOM", "目标BOM"]
                },
                "column_mapping": {
                    "base_section": {
                        "MPART.NO": ["差异料号", "料号"],
                        "MPART.PARENT": ["其上阶料号", "上阶料号"],
                        "MBOM.LOC": ["位置号"],
                        "MBOM.BNUM": ["数量"],
                        "MBOM.OP": ["工位"],
                        "MBOM.REMARK": ["备注"]
                    },
                    "new_section": {
                        "MPART.NO": ["差异料号", "料号"],
                        "MPART.PARENT": ["其上阶料号", "上阶料号"],
                        "MBOM.LOC": ["位置号"],
                        "MBOM.BNUM": ["数量"],
                        "MBOM.OP": ["工位"],
                        "MBOM.CHANGE_REASON": ["备注"]
                    },
                    "common": {
                        "MPART.NAME": ["差异物料名称", "物料名称"]
                    }
                },
                "change_type_detection": {
                    "delete_indicators": ["delete", "删除", "0"],
                    "add_indicators": ["add", "新增", "新建"],
                    "modify_indicators": ["change", "修改", "变更"]
                }
            },
            "excel_sub_bom_mapping": {
                "sheet_name": "子阶BOM建立",
                "column_mapping": {
                    "MPART.NAME": ["物料名称"],
                    "MPART.NO": ["子阶料号", "料号"],
                    "MPART.PARENT": ["上阶料号"],
                    "MBOM.LOC": ["位置号"],
                    "MBOM.BNUM": ["数量"],
                    "MBOM.OP": ["工位"],
                    "MBOM.REMARK": ["备注"]
                },
                "default_values": {
                    "MBOM.CHANGE_TYPE": "add",
                    "MPART.SOURCE": "excel_sub_bom",
                    "MPART.WLSX": "外购"
                }
            },
            "plm_mapping": {
                "api_endpoint": "/sipmweb/api/PushBomInfo",
                "field_mapping": {
                    "PID": "bom_info.plm_parent_id",
                    "CID": "MPART.NO",
                    "BNUM": "MBOM.BNUM",
                    "BOMPST": "auto_sequence",
                    "OWNER": "adm",
                    "CREATOR": "adm",
                    "ASMEMO": "外部接口导入{date}"
                },
                "export_rules": {
                    "exclude_zero_quantity": True,
                    "exclude_deleted_items": True,
                    "include_sub_bom": True,
                    "sequence_start": 1
                }
            }
        }
    
    def _init_db_connection(self):
        """初始化数据库连接"""
        try:
            from .db_query import query_bom_from_database
            self.db_query = query_bom_from_database
        except ImportError:
            logger.warning("无法导入数据库查询模块")
            self.db_query = None
    
    def process_excel_diff(self, excel_file: str) -> Dict[str, Any]:
        """处理Excel差异文件，生成AI分析JSON"""
        try:
            logger.info(f"开始处理Excel差异文件: {excel_file}")
            
            # 1. 解析Excel文件
            diff_data, sub_bom_data, bom_info = self._parse_excel_file(excel_file)
            
            # 2. 从数据库获取Base BOM
            base_bom_data = self._get_base_bom_from_db(bom_info.base_product_code)
            
            # 3. 合并生成新BOM
            final_bom_data = self._merge_bom_data(base_bom_data, diff_data, sub_bom_data)
            
            # 4. 生成AI分析JSON
            ai_json = self._generate_ai_json(bom_info, final_bom_data)
            
            logger.info("Excel差异文件处理完成")
            return ai_json
            
        except Exception as e:
            logger.error(f"处理Excel差异文件失败: {e}")
            raise
    
    def _parse_excel_file(self, excel_file: str) -> Tuple[Dict[str, List[BOMPart]], Dict[str, List[BOMPart]], BOMInfo]:
        """解析Excel文件"""
        logger.info("解析Excel文件结构")
        
        # 读取Excel文件
        excel_data = pd.ExcelFile(excel_file)
        
        # 解析BOM差异表
        diff_data = {}
        bom_info = None
        
        diff_config = self.config["excel_diff_mapping"]
        if diff_config["sheet_name"] in excel_data.sheet_names:
            diff_df = pd.read_excel(excel_file, sheet_name=diff_config["sheet_name"])
            diff_data, bom_info = self._parse_diff_sheet(diff_df)
        
        # 解析子阶BOM建立
        sub_bom_data = {}
        sub_config = self.config["excel_sub_bom_mapping"]
        if sub_config["sheet_name"] in excel_data.sheet_names:
            sub_df = pd.read_excel(excel_file, sheet_name=sub_config["sheet_name"])
            sub_bom_data = self._parse_sub_bom_sheet(sub_df)
        
        return diff_data, sub_bom_data, bom_info
    
    def _parse_diff_sheet(self, df: pd.DataFrame) -> Tuple[Dict[str, List[BOMPart]], BOMInfo]:
        """解析差异表sheet"""
        logger.info("解析BOM差异表")
        
        # 提取产品编码信息
        bom_info = self._extract_bom_info_from_header(df)
        
        # 查找列映射
        column_mapping = self._detect_column_mapping(df.columns.tolist())
        
        diff_data = {}
        
        # 遍历数据行
        for index, row in df.iterrows():
            if pd.isna(row.get(column_mapping.get("MPART.NAME", ""), "")):
                continue  # 跳过空行
            
            # 解析Base BOM和New BOM数据
            base_part = self._parse_diff_row(row, column_mapping, "base")
            new_part = self._parse_diff_row(row, column_mapping, "new")
            
            if base_part and new_part:
                # 确定变更类型
                change_type = self._determine_change_type(base_part, new_part)
                
                # 创建最终零件数据
                final_part = self._create_final_part(base_part, new_part, change_type)
                
                # 按类别分组
                category = self._extract_category(final_part.MPART_NO)
                if category not in diff_data:
                    diff_data[category] = []
                diff_data[category].append(final_part)
        
        return diff_data, bom_info
    
    def _parse_sub_bom_sheet(self, df: pd.DataFrame) -> Dict[str, List[BOMPart]]:
        """解析子阶BOM建立sheet"""
        logger.info("解析子阶BOM建立")
        
        sub_bom_data = {}
        column_mapping = self._detect_sub_bom_column_mapping(df.columns.tolist())
        
        for index, row in df.iterrows():
            if pd.isna(row.get(column_mapping.get("MPART.NO", ""), "")):
                continue
            
            part = BOMPart(
                MPART_NO=str(row.get(column_mapping.get("MPART.NO", ""), "")),
                MPART_NAME=str(row.get(column_mapping.get("MPART.NAME", ""), "")),
                MBOM_BNUM=float(row.get(column_mapping.get("MBOM.BNUM", ""), 0)),
                MBOM_OP=str(row.get(column_mapping.get("MBOM.OP", ""), "")),
                MBOM_CHANGE_TYPE="add",
                MPART_SOURCE="excel_sub_bom",
                MPART_WLSX="外购"
            )
            
            # 获取上阶料号，用于分组
            parent_part = str(row.get(column_mapping.get("MPART.PARENT", ""), ""))
            if parent_part:
                if parent_part not in sub_bom_data:
                    sub_bom_data[parent_part] = []
                sub_bom_data[parent_part].append(part)
        
        return sub_bom_data
    
    def _get_base_bom_from_db(self, base_product_code: str) -> Dict[str, List[BOMPart]]:
        """从数据库获取Base BOM数据"""
        logger.info(f"从数据库查询Base BOM: {base_product_code}")
        
        if not self.db_query or not base_product_code:
            logger.warning("数据库查询不可用或Base产品编码为空")
            return {}
        
        try:
            raw_data = self.db_query(base_product_code)
            if not raw_data:
                logger.warning(f"未找到Base产品 {base_product_code} 的BOM数据")
                return {}
            
            # 转换为BOMPart格式
            base_bom_data = {}
            for category, parts_list in raw_data.items():
                base_bom_data[category] = []
                for part_data in parts_list:
                    part = BOMPart(
                        MPART_NO=part_data.get("MPART.NO", ""),
                        MPART_NAME=part_data.get("MPART.NAME", ""),
                        MBOM_BNUM=float(part_data.get("MBOM.BNUM", 0)),
                        MPART_WLSX=part_data.get("MPART.WLSX", ""),
                        MPART_UNIT=part_data.get("MPART.UNIT", "PCS"),
                        MBOM_LOC=part_data.get("MBOM.LOC", ""),
                        MBOM_OP=part_data.get("MBOM.OP", ""),
                        MPART_SOURCE="database",
                        MPART_EFFECTIVE_DATE=part_data.get("MPART.EFFECTIVE_DATE", ""),
                        MPART_EXPIRE_DATE=part_data.get("MPART.EXPIRE_DATE", "")
                    )
                    base_bom_data[category].append(part)
            
            logger.info(f"成功获取Base BOM数据，共 {sum(len(parts) for parts in base_bom_data.values())} 个零件")
            return base_bom_data
            
        except Exception as e:
            logger.error(f"从数据库获取Base BOM失败: {e}")
            return {}
    
    def _merge_bom_data(self, base_bom: Dict[str, List[BOMPart]], 
                       diff_data: Dict[str, List[BOMPart]], 
                       sub_bom_data: Dict[str, List[BOMPart]]) -> Dict[str, List[BOMPart]]:
        """合并BOM数据"""
        logger.info("合并BOM数据")
        
        final_bom = {}
        
        # 1. 添加Base BOM中的所有零件
        for category, parts in base_bom.items():
            final_bom[category] = []
            for part in parts:
                final_bom[category].append(part)
        
        # 2. 应用差异数据
        for category, diff_parts in diff_data.items():
            if category not in final_bom:
                final_bom[category] = []
            
            for diff_part in diff_parts:
                # 查找是否存在相同零件编号
                existing_part_index = -1
                for i, existing_part in enumerate(final_bom[category]):
                    if existing_part.MPART_NO == diff_part.MPART_NO:
                        existing_part_index = i
                        break
                
                if existing_part_index >= 0:
                    # 更新现有零件
                    final_bom[category][existing_part_index] = diff_part
                else:
                    # 添加新零件
                    final_bom[category].append(diff_part)
        
        # 3. 添加子阶BOM
        for parent_part_no, sub_parts in sub_bom_data.items():
            # 查找父件并添加子阶BOM
            for category, parts in final_bom.items():
                for part in parts:
                    if part.MPART_NO == parent_part_no:
                        part.SUB_BOM.extend(sub_parts)
                        break
        
        # 4. 过滤删除的零件
        for category in final_bom:
            final_bom[category] = [
                part for part in final_bom[category] 
                if part.MBOM_CHANGE_TYPE != "delete" and part.MBOM_BNUM > 0
            ]
        
        return final_bom
    
    def _generate_ai_json(self, bom_info: BOMInfo, bom_data: Dict[str, List[BOMPart]]) -> Dict[str, Any]:
        """生成AI分析JSON"""
        logger.info("生成AI分析JSON")
        
        # 计算变更汇总
        change_summary = self._calculate_change_summary(bom_data)
        
        # 构建最终JSON
        ai_json = {
            "bom_info": asdict(bom_info),
            "bom_data": {},
            "change_summary": asdict(change_summary),
            "plm_export_ready": True
        }
        
        # 转换BOM数据
        for category, parts in bom_data.items():
            if parts:  # 只包含非空类别
                ai_json["bom_data"][category] = [part.to_dict() for part in parts]
        
        return ai_json
    
    def export_to_plm_format(self, ai_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """转换为PLM格式"""
        logger.info("转换为PLM格式")
        
        plm_data = []
        sequence = self.config["plm_mapping"]["export_rules"]["sequence_start"]
        
        parent_id = ai_json["bom_info"]["plm_parent_id"]
        if not parent_id:
            parent_id = "WK_100001"  # 默认父件ID
        
        for category, parts in ai_json["bom_data"].items():
            for part in parts:
                # 跳过删除的零件和数量为0的零件
                if (part.get("MBOM.CHANGE_TYPE") == "delete" or 
                    part.get("MBOM.BNUM", 0) <= 0):
                    continue
                
                plm_item = {
                    "PID": parent_id,
                    "CID": part["MPART.NO"],
                    "BNUM": str(part["MBOM.BNUM"]),
                    "BOMPST": str(sequence),
                    "OWNER": "adm",
                    "CREATOR": "adm",
                    "ASMEMO": f"外部接口导入{datetime.now().strftime('%Y%m%d')}"
                }
                plm_data.append(plm_item)
                sequence += 1
                
                # 处理子阶BOM
                if "SUB_BOM" in part and part["SUB_BOM"]:
                    for sub_part in part["SUB_BOM"]:
                        sub_plm_item = {
                            "PID": part["MPART.NO"],  # 父件为当前零件
                            "CID": sub_part["MPART.NO"],
                            "BNUM": str(sub_part["MBOM.BNUM"]),
                            "BOMPST": str(sequence),
                            "OWNER": "adm",
                            "CREATOR": "adm",
                            "ASMEMO": f"外部接口导入{datetime.now().strftime('%Y%m%d')}"
                        }
                        plm_data.append(sub_plm_item)
                        sequence += 1
        
        logger.info(f"PLM格式转换完成，共 {len(plm_data)} 条记录")
        return plm_data
    
    # 辅助方法
    def _extract_bom_info_from_header(self, df: pd.DataFrame) -> BOMInfo:
        """从表头提取BOM信息"""
        # 简化实现，实际需要根据Excel格式解析
        product_code = "SP0030-3Q-23-5QP"  # 示例
        base_product_code = "SP0030-00-23-5QP"  # 示例
        
        return BOMInfo(
            product_code=product_code,
            base_product_code=base_product_code,
            data_sources=["database", "excel_diff"]
        )
    
    def _detect_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """检测列映射"""
        # 简化实现
        return {
            "MPART.NAME": "差异物料名称",
            "base_MPART.NO": "差异料号",
            "new_MPART.NO": "差异料号.1",
            "base_MBOM.BNUM": "数量",
            "new_MBOM.BNUM": "数量.1"
        }
    
    def _detect_sub_bom_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """检测子阶BOM列映射"""
        return {
            "MPART.NAME": "物料名称",
            "MPART.NO": "子阶料号",
            "MPART.PARENT": "上阶料号",
            "MBOM.BNUM": "数量",
            "MBOM.OP": "工位"
        }
    
    def _parse_diff_row(self, row: pd.Series, column_mapping: Dict[str, str], section: str) -> Optional[BOMPart]:
        """解析差异行数据"""
        # 简化实现
        return None
    
    def _determine_change_type(self, base_part: BOMPart, new_part: BOMPart) -> str:
        """确定变更类型"""
        if new_part.MBOM_BNUM == 0:
            return "delete"
        elif base_part.MPART_NO != new_part.MPART_NO:
            return "modify"
        elif base_part.MBOM_BNUM != new_part.MBOM_BNUM:
            return "modify"
        else:
            return "none"
    
    def _create_final_part(self, base_part: BOMPart, new_part: BOMPart, change_type: str) -> BOMPart:
        """创建最终零件数据"""
        # 简化实现
        return new_part
    
    def _extract_category(self, part_no: str) -> str:
        """提取类别"""
        match = re.match(r'^(\d{3})', part_no)
        return match.group(1) if match else "999"
    
    def _calculate_change_summary(self, bom_data: Dict[str, List[BOMPart]]) -> ChangeSummary:
        """计算变更汇总"""
        summary = ChangeSummary()
        
        for parts in bom_data.values():
            for part in parts:
                if part.MBOM_CHANGE_TYPE == "add":
                    summary.add_count += 1
                elif part.MBOM_CHANGE_TYPE == "modify":
                    summary.modify_count += 1
                elif part.MBOM_CHANGE_TYPE == "delete":
                    summary.delete_count += 1
                else:
                    summary.unchanged_count += 1
                
                if part.SUB_BOM:
                    summary.sub_bom_count += len(part.SUB_BOM)
        
        summary.total_changes = summary.add_count + summary.modify_count + summary.delete_count
        
        return summary


# 便捷函数
def process_bom_diff_file(excel_file: str, config_file: str = None) -> Dict[str, Any]:
    """处理BOM差异文件的便捷函数"""
    processor = BOMDataProcessor(config_file)
    return processor.process_excel_diff(excel_file)


def convert_to_plm_format(ai_json: Dict[str, Any], config_file: str = None) -> List[Dict[str, Any]]:
    """转换为PLM格式的便捷函数"""
    processor = BOMDataProcessor(config_file)
    return processor.export_to_plm_format(ai_json)


if __name__ == "__main__":
    # 测试代码
    try:
        processor = BOMDataProcessor()
        
        # 测试配置加载
        print("配置加载测试:")
        print(f"数据库表名: {processor.config['database_mapping']['table_name']}")
        print(f"Excel差异表sheet名: {processor.config['excel_diff_mapping']['sheet_name']}")
        
        # 测试BOM信息创建
        bom_info = BOMInfo(
            product_code="SP0030-3Q-23-5QP",
            base_product_code="SP0030-00-23-5QP"
        )
        print(f"\nBOM信息测试:")
        print(f"产品编码: {bom_info.product_code}")
        print(f"型号类型: {bom_info.model_type}")
        
        # 测试零件创建
        part = BOMPart(
            MPART_NO="334-000338-00",
            MPART_NAME="文档包组件",
            MBOM_BNUM=1.0,
            MPART_WLSX="自制",
            MBOM_CHANGE_TYPE="modify"
        )
        print(f"\n零件信息测试:")
        print(json.dumps(part.to_dict(), ensure_ascii=False, indent=2))
        
        print("\n测试完成！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()