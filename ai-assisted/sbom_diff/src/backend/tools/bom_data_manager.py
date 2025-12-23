#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BOM数据结构优化 - 统一数据管理器
实现统一的BOM数据处理、转换和验证功能
"""

import json
import copy
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """产品型号信息"""
    product_code: str
    model_type: str
    model_prefix: str
    description: str = ""
    parent_id: str = ""


@dataclass
class ValidationResult:
    """数据验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class PartInfo:
    """零件信息"""
    part_id: str
    part_name: str
    quantity: float
    unit: str = "PCS"
    part_type: str = ""
    material_class: str = ""
    supplier: str = ""
    cost: float = 0.0
    lead_time: int = 0
    status: str = "active"
    attributes: Dict[str, Any] = None
    source_info: Dict[str, Any] = None
    change_info: Dict[str, Any] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.source_info is None:
            self.source_info = {}
        if self.change_info is None:
            self.change_info = {"change_type": "none"}


@dataclass
class CategoryInfo:
    """类别信息"""
    category_id: str
    category_name: str
    category_type: str = "component"
    parts: List[PartInfo] = None

    def __post_init__(self):
        if self.parts is None:
            self.parts = []


@dataclass
class BOMMetadata:
    """BOM元数据"""
    version: str = "1.0"
    created_at: str = ""
    updated_at: str = ""
    source: str = ""
    model_info: ModelInfo = None
    validation: ValidationResult = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


@dataclass
class StandardBOMData:
    """标准BOM数据结构"""
    metadata: BOMMetadata
    bom_data: Dict[str, CategoryInfo]
    statistics: Dict[str, Any] = None

    def __post_init__(self):
        if self.statistics is None:
            self.statistics = self._calculate_statistics()

    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        total_categories = len(self.bom_data)
        total_parts = sum(len(category.parts) for category in self.bom_data.values())
        total_quantity = sum(
            sum(part.quantity for part in category.parts)
            for category in self.bom_data.values()
        )
        
        part_types = {}
        for category in self.bom_data.values():
            for part in category.parts:
                part_type = part.part_type or "未知"
                part_types[part_type] = part_types.get(part_type, 0) + 1

        return {
            "total_categories": total_categories,
            "total_parts": total_parts,
            "total_quantity": total_quantity,
            "part_types": part_types
        }


class BOMDataAdapter(ABC):
    """BOM数据适配器基类"""
    
    def __init__(self, source_type: str):
        self.source_type = source_type
        self.validator = BOMDataValidator()
    
    @abstractmethod
    def load_data(self, source: Any) -> StandardBOMData:
        """加载原始数据并转换为标准格式"""
        pass
    
    @abstractmethod
    def transform_from_standard(self, standard_data: StandardBOMData) -> Any:
        """从标准格式转换为目标格式"""
        pass
    
    def validate_data(self, data: StandardBOMData) -> ValidationResult:
        """验证数据完整性"""
        return self.validator.validate(data)


class BOMDataValidator:
    """BOM数据验证器"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def validate(self, data: StandardBOMData) -> ValidationResult:
        """验证BOM数据"""
        errors = []
        warnings = []
        
        try:
            # 结构验证
            errors.extend(self._validate_structure(data))
            
            # 数据完整性验证
            errors.extend(self._validate_completeness(data))
            
            # 业务规则验证
            warnings.extend(self._validate_business_rules(data))
            
        except Exception as e:
            errors.append(f"验证过程中发生错误: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_structure(self, data: StandardBOMData) -> List[str]:
        """验证数据结构"""
        errors = []
        
        if not isinstance(data, StandardBOMData):
            errors.append("数据不是StandardBOMData类型")
            return errors
        
        if not data.metadata:
            errors.append("缺少metadata信息")
        
        if not data.bom_data:
            errors.append("缺少bom_data信息")
        
        return errors
    
    def _validate_completeness(self, data: StandardBOMData) -> List[str]:
        """验证数据完整性"""
        errors = []
        
        # 检查零件数据完整性
        for category_id, category in data.bom_data.items():
            if not category.parts:
                errors.append(f"类别 {category_id} 没有零件数据")
                continue
                
            for i, part in enumerate(category.parts):
                if not part.part_id:
                    errors.append(f"类别 {category_id} 第 {i+1} 个零件缺少part_id")
                
                if not isinstance(part.quantity, (int, float)) or part.quantity <= 0:
                    errors.append(f"零件 {part.part_id} 数量格式错误或为负数")
        
        return errors
    
    def _validate_business_rules(self, data: StandardBOMData) -> List[str]:
        """验证业务规则"""
        warnings = []
        
        # 检查重复零件
        all_part_ids = []
        for category in data.bom_data.values():
            for part in category.parts:
                if part.part_id in all_part_ids:
                    warnings.append(f"发现重复零件编号: {part.part_id}")
                all_part_ids.append(part.part_id)
        
        # 检查异常数量
        for category in data.bom_data.values():
            for part in category.parts:
                if part.quantity > 100:
                    warnings.append(f"零件 {part.part_id} 数量异常大: {part.quantity}")
        
        return warnings
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            "required_fields": ["part_id", "part_name", "quantity"],
            "quantity_range": [0.001, 9999.999],
            "part_id_pattern": r"^[A-Z0-9\-_]+$"
        }


class MySQLBOMAdapter(BOMDataAdapter):
    """MySQL数据库BOM适配器"""
    
    def __init__(self):
        super().__init__("database")
        # 延迟导入避免循环依赖
        from .db_query import query_bom_from_database, _extract_model_prefix
        self.db_query_func = query_bom_from_database
        self.extract_prefix_func = _extract_model_prefix
    
    def load_data(self, model_name: str) -> StandardBOMData:
        """从数据库加载BOM数据"""
        try:
            raw_data = self.db_query_func(model_name)
            if not raw_data:
                raise ValueError(f"未找到型号 {model_name} 的BOM数据")
            
            return self._transform_to_standard(raw_data, model_name)
        
        except Exception as e:
            logger.error(f"从数据库加载BOM数据失败: {e}")
            raise
    
    def _transform_to_standard(self, raw_data: Dict[str, List[Dict]], model_name: str) -> StandardBOMData:
        """将数据库格式转换为标准格式"""
        
        # 创建模型信息
        model_prefix = self.extract_prefix_func(model_name)
        model_info = ModelInfo(
            product_code=model_name,
            model_type=model_prefix,
            model_prefix=model_prefix,
            description=f"{model_name} BOM数据"
        )
        
        # 创建元数据
        metadata = BOMMetadata(
            source="database",
            model_info=model_info
        )
        
        # 转换BOM数据
        bom_categories = {}
        for category_id, parts_list in raw_data.items():
            parts = []
            for part_data in parts_list:
                part = PartInfo(
                    part_id=part_data.get("MPART.NO", ""),
                    part_name=part_data.get("MPART.NAME", ""),
                    quantity=float(part_data.get("MBOM.BNUM", 0)),
                    part_type=part_data.get("MPART.WLSX", ""),
                    source_info={
                        "database_id": part_data.get("id", ""),
                        "original_data": part_data
                    }
                )
                parts.append(part)
            
            category = CategoryInfo(
                category_id=category_id,
                category_name=self._get_category_name(category_id),
                parts=parts
            )
            bom_categories[category_id] = category
        
        standard_data = StandardBOMData(
            metadata=metadata,
            bom_data=bom_categories
        )
        
        # 验证数据
        validation_result = self.validate_data(standard_data)
        standard_data.metadata.validation = validation_result
        
        return standard_data
    
    def transform_from_standard(self, standard_data: StandardBOMData) -> Dict[str, List[Dict]]:
        """将标准格式转换回数据库格式"""
        result = {}
        
        for category_id, category in standard_data.bom_data.items():
            parts_list = []
            for part in category.parts:
                part_dict = {
                    "MPART.NO": part.part_id,
                    "MPART.NAME": part.part_name,
                    "MBOM.BNUM": part.quantity,
                    "MPART.WLSX": part.part_type
                }
                parts_list.append(part_dict)
            result[category_id] = parts_list
        
        return result
    
    def _get_category_name(self, category_id: str) -> str:
        """获取类别名称"""
        category_mapping = {
            "334": "主要组件",
            "510": "标准件",
            "520": "电子元件",
            "530": "机械件",
            "540": "包装材料"
        }
        return category_mapping.get(category_id, f"类别{category_id}")


class ExcelBOMAdapter(BOMDataAdapter):
    """Excel差异文件BOM适配器"""
    
    def __init__(self):
        super().__init__("excel")
    
    def load_data(self, file_path: str) -> StandardBOMData:
        """从Excel文件加载差异数据"""
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            return self._transform_to_standard(df, file_path)
        
        except Exception as e:
            logger.error(f"从Excel文件加载BOM数据失败: {e}")
            raise
    
    def _transform_to_standard(self, df, file_path: str) -> StandardBOMData:
        """将Excel格式转换为标准格式"""
        # 这里需要根据实际的Excel格式来实现
        # 暂时返回一个示例结构
        
        model_info = ModelInfo(
            product_code="EXCEL_MODEL",
            model_type="EXCEL",
            model_prefix="EXCEL",
            description=f"Excel差异文件: {file_path}"
        )
        
        metadata = BOMMetadata(
            source="excel",
            model_info=model_info
        )
        
        # TODO: 实现具体的Excel解析逻辑
        bom_categories = {}
        
        standard_data = StandardBOMData(
            metadata=metadata,
            bom_data=bom_categories
        )
        
        return standard_data
    
    def transform_from_standard(self, standard_data: StandardBOMData) -> Any:
        """将标准格式转换为Excel格式"""
        # TODO: 实现标准格式到Excel的转换
        pass


class PLMBOMAdapter(BOMDataAdapter):
    """PLM系统BOM适配器"""
    
    def __init__(self):
        super().__init__("plm")
    
    def load_data(self, source: Any) -> StandardBOMData:
        """PLM适配器主要用于输出，不实现加载功能"""
        raise NotImplementedError("PLM适配器主要用于数据输出")
    
    def transform_from_standard(self, standard_data: StandardBOMData) -> List[Dict]:
        """将标准格式转换为PLM格式"""
        plm_data = []
        bom_sequence = 1
        
        parent_id = standard_data.metadata.model_info.parent_id
        if not parent_id:
            parent_id = "WK_100001"  # 默认父件ID
        
        for category in standard_data.bom_data.values():
            for part in category.parts:
                plm_item = {
                    "PID": parent_id,
                    "CID": part.part_id,
                    "BNUM": str(part.quantity),
                    "BOMPST": str(bom_sequence),
                    "OWNER": "adm",
                    "CREATOR": "adm",
                    "ASMEMO": f"外部接口导入{datetime.now().strftime('%Y%m%d')}"
                }
                plm_data.append(plm_item)
                bom_sequence += 1
        
        return plm_data


class BOMDataManager:
    """BOM数据处理管理器"""
    
    def __init__(self):
        self.adapters = {
            "database": MySQLBOMAdapter(),
            "excel": ExcelBOMAdapter(),
            "plm": PLMBOMAdapter()
        }
        self.validator = BOMDataValidator()
    
    def load_from_source(self, source_type: str, source_data: Any) -> StandardBOMData:
        """从指定数据源加载数据"""
        if source_type not in self.adapters:
            raise ValueError(f"不支持的数据源类型: {source_type}")
        
        adapter = self.adapters[source_type]
        standard_data = adapter.load_data(source_data)
        
        logger.info(f"成功从 {source_type} 加载BOM数据，共 {standard_data.statistics['total_parts']} 个零件")
        return standard_data
    
    def merge_bom_data(self, base_data: StandardBOMData, diff_data: StandardBOMData) -> StandardBOMData:
        """合并BOM数据（基础数据 + 差异数据）"""
        merged_data = copy.deepcopy(base_data)
        
        # 合并类别数据
        for category_id, category in diff_data.bom_data.items():
            if category_id not in merged_data.bom_data:
                merged_data.bom_data[category_id] = category
            else:
                # 合并同类别下的零件
                self._merge_category_parts(
                    merged_data.bom_data[category_id],
                    category
                )
        
        # 更新元数据
        merged_data.metadata.updated_at = datetime.now().isoformat()
        merged_data.metadata.source = f"{base_data.metadata.source}+{diff_data.metadata.source}"
        
        # 重新计算统计信息
        merged_data.statistics = merged_data._calculate_statistics()
        
        # 重新验证数据
        validation_result = self.validator.validate(merged_data)
        merged_data.metadata.validation = validation_result
        
        logger.info(f"成功合并BOM数据，合并后共 {merged_data.statistics['total_parts']} 个零件")
        return merged_data
    
    def _merge_category_parts(self, base_category: CategoryInfo, diff_category: CategoryInfo):
        """合并同类别下的零件"""
        # 创建零件ID到零件的映射
        base_parts_map = {part.part_id: part for part in base_category.parts}
        
        for diff_part in diff_category.parts:
            if diff_part.part_id in base_parts_map:
                # 更新现有零件
                base_part = base_parts_map[diff_part.part_id]
                base_part.change_info = {
                    "change_type": "modify",
                    "old_quantity": base_part.quantity,
                    "new_quantity": diff_part.quantity,
                    "change_reason": "差异文件更新"
                }
                base_part.quantity = diff_part.quantity
                base_part.part_name = diff_part.part_name or base_part.part_name
                base_part.part_type = diff_part.part_type or base_part.part_type
            else:
                # 添加新零件
                diff_part.change_info = {
                    "change_type": "add",
                    "old_quantity": 0,
                    "new_quantity": diff_part.quantity,
                    "change_reason": "差异文件新增"
                }
                base_category.parts.append(diff_part)
    
    def export_to_target(self, standard_data: StandardBOMData, target_type: str) -> Any:
        """导出到目标格式"""
        if target_type not in self.adapters:
            raise ValueError(f"不支持的目标类型: {target_type}")
        
        adapter = self.adapters[target_type]
        result = adapter.transform_from_standard(standard_data)
        
        logger.info(f"成功导出BOM数据到 {target_type} 格式")
        return result
    
    def save_to_json(self, standard_data: StandardBOMData, file_path: str):
        """保存标准格式数据到JSON文件"""
        try:
            # 转换为可序列化的字典
            data_dict = self._to_serializable_dict(standard_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"BOM数据已保存到: {file_path}")
        
        except Exception as e:
            logger.error(f"保存JSON文件失败: {e}")
            raise
    
    def load_from_json(self, file_path: str) -> StandardBOMData:
        """从JSON文件加载标准格式数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
            
            return self._from_serializable_dict(data_dict)
        
        except Exception as e:
            logger.error(f"加载JSON文件失败: {e}")
            raise
    
    def _to_serializable_dict(self, standard_data: StandardBOMData) -> Dict:
        """转换为可序列化的字典"""
        result = {
            "metadata": asdict(standard_data.metadata),
            "bom_data": {},
            "statistics": standard_data.statistics
        }
        
        for category_id, category in standard_data.bom_data.items():
            result["bom_data"][category_id] = {
                "category_id": category.category_id,
                "category_name": category.category_name,
                "category_type": category.category_type,
                "parts": [asdict(part) for part in category.parts]
            }
        
        return result
    
    def _from_serializable_dict(self, data_dict: Dict) -> StandardBOMData:
        """从可序列化的字典转换回标准格式"""
        # TODO: 实现从字典到StandardBOMData的转换
        # 这里需要处理嵌套的dataclass转换
        pass


# 便捷函数
def create_bom_manager() -> BOMDataManager:
    """创建BOM数据管理器实例"""
    return BOMDataManager()


def load_bom_from_database(model_name: str) -> StandardBOMData:
    """从数据库加载BOM数据的便捷函数"""
    manager = create_bom_manager()
    return manager.load_from_source("database", model_name)


def export_bom_to_plm(standard_data: StandardBOMData) -> List[Dict]:
    """导出BOM数据到PLM格式的便捷函数"""
    manager = create_bom_manager()
    return manager.export_to_target(standard_data, "plm")


if __name__ == "__main__":
    # 测试代码
    try:
        # 测试从数据库加载数据
        manager = create_bom_manager()
        
        # 这里需要一个真实的型号进行测试
        test_model = "TA0030-00-24-52P"
        
        print(f"正在测试加载型号: {test_model}")
        bom_data = manager.load_from_source("database", test_model)
        
        print(f"加载成功！")
        print(f"总类别数: {bom_data.statistics['total_categories']}")
        print(f"总零件数: {bom_data.statistics['total_parts']}")
        print(f"验证结果: {'通过' if bom_data.metadata.validation.is_valid else '失败'}")
        
        if bom_data.metadata.validation.errors:
            print("验证错误:")
            for error in bom_data.metadata.validation.errors:
                print(f"  - {error}")
        
        # 测试导出到PLM格式
        plm_data = manager.export_to_target(bom_data, "plm")
        print(f"PLM格式数据条数: {len(plm_data)}")
        
        # 测试保存到JSON
        json_file = "tmp/test_bom_data.json"
        manager.save_to_json(bom_data, json_file)
        print(f"数据已保存到: {json_file}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()