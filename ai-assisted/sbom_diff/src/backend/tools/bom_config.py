#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BOM数据结构配置管理
包含字段映射、验证规则、类别定义等配置信息
"""

import json
import os
from typing import Dict, Any, List


class BOMConfig:
    """BOM配置管理类"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), "bom_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = self._get_default_config()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                # 合并配置，文件配置优先
                default_config.update(file_config)
            except Exception as e:
                print(f"加载配置文件失败，使用默认配置: {e}")
        
        return default_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "field_mappings": {
                "database": {
                    "part_id": "MPART.NO",
                    "part_name": "MPART.NAME", 
                    "quantity": "MBOM.BNUM",
                    "part_type": "MPART.WLSX",
                    "material_class": "item_cls_c"
                },
                "excel": {
                    "part_id": ["零件编号", "物料编号", "Part No", "PART.NO"],
                    "part_name": ["零件名称", "物料名称", "Part Name", "PART.NAME"],
                    "quantity": ["数量", "用量", "Quantity", "QTY"],
                    "part_type": ["类型", "物料类型", "Type", "PART.TYPE"],
                    "category": ["类别", "分类", "Category"],
                    "change_type": ["变更类型", "操作", "Change Type"],
                    "old_quantity": ["原数量", "旧数量", "Old Qty"],
                    "new_quantity": ["新数量", "New Qty"]
                },
                "plm": {
                    "parent_id": "PID",
                    "child_id": "CID", 
                    "quantity": "BNUM",
                    "sequence": "BOMPST",
                    "owner": "OWNER",
                    "creator": "CREATOR",
                    "memo": "ASMEMO"
                }
            },
            "category_mappings": {
                "334": {
                    "name": "主要组件",
                    "type": "component",
                    "description": "产品主要功能组件"
                },
                "510": {
                    "name": "标准件",
                    "type": "standard",
                    "description": "标准紧固件和通用件"
                },
                "520": {
                    "name": "电子元件",
                    "type": "electronic",
                    "description": "电子器件和电路板"
                },
                "530": {
                    "name": "机械件",
                    "type": "mechanical", 
                    "description": "机械加工件和结构件"
                },
                "540": {
                    "name": "包装材料",
                    "type": "packaging",
                    "description": "包装盒、说明书等"
                },
                "550": {
                    "name": "辅助材料",
                    "type": "auxiliary",
                    "description": "胶水、标签等辅助材料"
                }
            },
            "part_type_mappings": {
                "自制": "manufactured",
                "外购": "purchased", 
                "委外": "outsourced",
                "虚拟": "virtual",
                "配置": "configured"
            },
            "validation_rules": {
                "required_fields": ["part_id", "part_name", "quantity"],
                "part_id": {
                    "pattern": r"^[A-Z0-9\-_]+$",
                    "min_length": 3,
                    "max_length": 50
                },
                "part_name": {
                    "min_length": 1,
                    "max_length": 200
                },
                "quantity": {
                    "min_value": 0.001,
                    "max_value": 9999.999,
                    "decimal_places": 3
                },
                "category_id": {
                    "pattern": r"^\d{3}$"
                }
            },
            "excel_templates": {
                "diff_template": {
                    "required_columns": ["零件编号", "零件名称", "数量", "变更类型"],
                    "optional_columns": ["类别", "物料类型", "原数量", "新数量", "备注"],
                    "change_types": ["新增", "修改", "删除", "ADD", "MODIFY", "DELETE"]
                },
                "export_template": {
                    "columns": [
                        {"field": "category_id", "header": "类别", "width": 10},
                        {"field": "part_id", "header": "零件编号", "width": 20},
                        {"field": "part_name", "header": "零件名称", "width": 30},
                        {"field": "quantity", "header": "数量", "width": 10},
                        {"field": "part_type", "header": "物料类型", "width": 15},
                        {"field": "change_type", "header": "变更类型", "width": 15}
                    ]
                }
            },
            "model_patterns": {
                "TA": {
                    "pattern": r"^TA\d{4}-\d{2}-\d{2}-\w+$",
                    "description": "TA系列产品型号"
                },
                "SP": {
                    "pattern": r"^SP\d{4}-\w+-\d{2}-\w+$", 
                    "description": "SP系列产品型号"
                },
                "HSP": {
                    "pattern": r"^HSP\d{4}-\w+-\d{2}-\w+$",
                    "description": "HSP系列产品型号"
                }
            },
            "export_settings": {
                "plm": {
                    "default_owner": "adm",
                    "default_creator": "adm",
                    "memo_template": "外部接口导入{date}",
                    "batch_size": 100
                },
                "json": {
                    "indent": 2,
                    "ensure_ascii": False,
                    "sort_keys": True
                },
                "excel": {
                    "sheet_name": "BOM数据",
                    "freeze_panes": (1, 0),
                    "auto_filter": True
                }
            }
        }
    
    def save_config(self):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_field_mapping(self, source_type: str) -> Dict[str, Any]:
        """获取字段映射配置"""
        return self.config.get("field_mappings", {}).get(source_type, {})
    
    def get_category_info(self, category_id: str) -> Dict[str, str]:
        """获取类别信息"""
        return self.config.get("category_mappings", {}).get(category_id, {
            "name": f"类别{category_id}",
            "type": "unknown",
            "description": ""
        })
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """获取验证规则"""
        return self.config.get("validation_rules", {})
    
    def get_excel_template(self, template_type: str) -> Dict[str, Any]:
        """获取Excel模板配置"""
        return self.config.get("excel_templates", {}).get(template_type, {})
    
    def get_model_pattern(self, model_type: str) -> Dict[str, str]:
        """获取型号模式"""
        return self.config.get("model_patterns", {}).get(model_type, {})
    
    def get_export_settings(self, export_type: str) -> Dict[str, Any]:
        """获取导出设置"""
        return self.config.get("export_settings", {}).get(export_type, {})
    
    def validate_part_id(self, part_id: str) -> bool:
        """验证零件编号格式"""
        import re
        rules = self.get_validation_rules().get("part_id", {})
        
        if "pattern" in rules:
            if not re.match(rules["pattern"], part_id):
                return False
        
        if "min_length" in rules and len(part_id) < rules["min_length"]:
            return False
            
        if "max_length" in rules and len(part_id) > rules["max_length"]:
            return False
        
        return True
    
    def validate_quantity(self, quantity: float) -> bool:
        """验证数量范围"""
        rules = self.get_validation_rules().get("quantity", {})
        
        if "min_value" in rules and quantity < rules["min_value"]:
            return False
            
        if "max_value" in rules and quantity > rules["max_value"]:
            return False
        
        return True
    
    def normalize_part_type(self, part_type: str) -> str:
        """标准化零件类型"""
        mappings = self.config.get("part_type_mappings", {})
        return mappings.get(part_type, part_type)
    
    def find_excel_column(self, df_columns: List[str], field_name: str) -> str:
        """在Excel列中查找对应字段"""
        field_mapping = self.get_field_mapping("excel").get(field_name, [])
        
        if isinstance(field_mapping, str):
            field_mapping = [field_mapping]
        
        for column in df_columns:
            if column in field_mapping:
                return column
        
        # 模糊匹配
        for mapping in field_mapping:
            for column in df_columns:
                if mapping.lower() in column.lower() or column.lower() in mapping.lower():
                    return column
        
        return None
    
    def get_change_type_mapping(self) -> Dict[str, str]:
        """获取变更类型映射"""
        template = self.get_excel_template("diff_template")
        change_types = template.get("change_types", [])
        
        mapping = {}
        for i in range(0, len(change_types), 2):
            if i + 1 < len(change_types):
                mapping[change_types[i]] = change_types[i + 1].lower()
        
        return mapping


# 全局配置实例
_config_instance = None


def get_bom_config() -> BOMConfig:
    """获取全局BOM配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = BOMConfig()
    return _config_instance


def reload_bom_config():
    """重新加载配置"""
    global _config_instance
    _config_instance = None
    return get_bom_config()


# 便捷函数
def get_category_name(category_id: str) -> str:
    """获取类别名称"""
    config = get_bom_config()
    return config.get_category_info(category_id).get("name", f"类别{category_id}")


def validate_part_id(part_id: str) -> bool:
    """验证零件编号"""
    config = get_bom_config()
    return config.validate_part_id(part_id)


def validate_quantity(quantity: float) -> bool:
    """验证数量"""
    config = get_bom_config()
    return config.validate_quantity(quantity)


def normalize_part_type(part_type: str) -> str:
    """标准化零件类型"""
    config = get_bom_config()
    return config.normalize_part_type(part_type)


if __name__ == "__main__":
    # 测试配置功能
    config = get_bom_config()
    
    print("=== BOM配置测试 ===")
    
    # 测试类别信息
    print(f"类别334信息: {config.get_category_info('334')}")
    
    # 测试字段映射
    print(f"数据库字段映射: {config.get_field_mapping('database')}")
    
    # 测试验证
    print(f"零件编号 '334-100001-00' 验证: {config.validate_part_id('334-100001-00')}")
    print(f"数量 1.5 验证: {config.validate_quantity(1.5)}")
    
    # 测试零件类型标准化
    print(f"'自制' 标准化为: {config.normalize_part_type('自制')}")
    
    # 保存配置文件示例
    config.save_config()
    print(f"配置已保存到: {config.config_file}")