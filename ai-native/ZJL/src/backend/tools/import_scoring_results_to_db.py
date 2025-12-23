#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将质检评分结果数据导入到MySQL数据库的qis_scoring_results表
"""

import json
import pymysql
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}

# JSON字段名到数据库字段名的映射（可根据实际JSON结构调整）
FIELD_MAPPING = {
    # 基础业务字段
    '关联单号': 'related_order_no',
    '质检类型': 'quality_check_type',
    '业务类型': 'business_type',
    '质检记录': 'quality_check_record',
    
    # 400电话评分项
    '400-标准话术': 'call_standard_script_score',
    '400-语言技巧': 'call_language_skill_score',
    '400-沟通技巧': 'call_communication_skill_score',
    '400-服务态度': 'call_service_attitude_score',
    '400-业务解答': 'call_business_answer_score',
    '400问题记录': 'call_issue_notes',
    
    # 公众号评分项
    '公众号-标准话术': 'wechat_standard_script_score',
    '公众号-语言技巧': 'wechat_language_skill_score',
    '公众号-服务态度': 'wechat_service_attitude_score',
    '公众号-业务解答': 'wechat_business_answer_score',
    '公众号问题记录': 'wechat_issue_notes',
    
    # 工单评分项
    '工单-流程': 'ticket_process_score',
    '工单-基本信息': 'ticket_basic_info_score',
    '工单-问题记录': 'ticket_issue_record_score',
    '工单-发货明细': 'ticket_shipping_detail_score',
    '工单问题记录': 'ticket_issue_notes',
    
    # 责任人
    '负责人': 'responsible_person',
    '新建时间': 'created_time',
    
    # 组织权限字段
    '人员-普通成员-只读': 'readonly_member_user',
    '人员-普通成员-读写': 'readwrite_member_user',
    '部门-普通成员-只读': 'readonly_member_dept',
    '部门-普通成员-读写': 'readwrite_member_dept',
    '用户组-普通成员-只读': 'readonly_member_group',
    '用户组-普通成员-读写': 'readwrite_member_group',
    '角色-普通成员-只读': 'readonly_member_role',
    '角色-普通成员-读写': 'readwrite_member_role',
}

# 所有数据库字段列表（不包括自增和时间戳字段）
DB_FIELDS = [
    'related_order_no', 'quality_check_type', 'business_type', 'quality_check_record',
    'call_standard_script_score', 'call_language_skill_score', 'call_communication_skill_score',
    'call_service_attitude_score', 'call_business_answer_score', 'call_issue_notes',
    'wechat_standard_script_score', 'wechat_language_skill_score', 'wechat_service_attitude_score',
    'wechat_business_answer_score', 'wechat_issue_notes',
    'ticket_process_score', 'ticket_basic_info_score', 'ticket_issue_record_score',
    'ticket_shipping_detail_score', 'ticket_issue_notes',
    'responsible_person', 'created_time',
    'readonly_member_user', 'readwrite_member_user', 'readonly_member_dept', 'readwrite_member_dept',
    'readonly_member_group', 'readwrite_member_group', 'readonly_member_role', 'readwrite_member_role'
]

# 必填字段
REQUIRED_FIELDS = ['related_order_no', 'quality_check_type', 'business_type', 'responsible_person']

# 评分字段（需要验证范围0-255）
SCORE_FIELDS = [
    'call_standard_script_score', 'call_language_skill_score', 'call_communication_skill_score',
    'call_service_attitude_score', 'call_business_answer_score',
    'wechat_standard_script_score', 'wechat_language_skill_score', 'wechat_service_attitude_score',
    'wechat_business_answer_score',
    'ticket_process_score', 'ticket_basic_info_score', 'ticket_issue_record_score',
    'ticket_shipping_detail_score'
]


def parse_datetime(date_str: str) -> Optional[datetime]:
    """解析日期时间字符串"""
    if not date_str:
        return None
    try:
        # 尝试解析格式: "2025-11-25 17:58:05"
        if isinstance(date_str, datetime):
            return date_str
        return datetime.strptime(str(date_str), '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        try:
            # 尝试其他常见格式
            return datetime.strptime(str(date_str), '%Y-%m-%d')
        except (ValueError, TypeError):
            return None


def validate_score(score: Any, field_name: str) -> Optional[int]:
    """验证并转换评分值（0-255）"""
    if score is None:
        return 0
    
    try:
        score_int = int(score)
        if score_int < 0:
            return 0
        if score_int > 255:
            print(f"警告: {field_name} 评分值 {score_int} 超过255，将被截断为255")
            return 255
        return score_int
    except (ValueError, TypeError):
        print(f"警告: {field_name} 评分值 '{score}' 无法转换为整数，使用默认值0")
        return 0


def convert_record(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """将JSON记录转换为数据库记录格式"""
    db_record = {}
    
    # 如果JSON记录已经使用数据库字段名，直接使用
    # 否则使用字段映射转换
    for db_field in DB_FIELDS:
        # 先尝试直接使用数据库字段名
        value = json_record.get(db_field)
        
        # 如果直接获取失败，尝试通过映射获取
        if value is None:
            for json_key, mapped_db_key in FIELD_MAPPING.items():
                if mapped_db_key == db_field:
                    value = json_record.get(json_key)
                    break
        
        # 处理特殊字段
        if db_field == 'created_time' and value:
            parsed_time = parse_datetime(value)
            db_record[db_field] = parsed_time
        elif db_field in SCORE_FIELDS:
            # 评分字段需要验证范围
            db_record[db_field] = validate_score(value, db_field)
        else:
            # 其他字段处理
            if value is None or (isinstance(value, str) and value.strip() == ''):
                # 对于必填字段，不能为None（但会在插入时检查）
                if db_field in REQUIRED_FIELDS:
                    db_record[db_field] = None
                else:
                    # 可选字段，根据类型设置默认值
                    if db_field.endswith('_notes') or db_field.startswith('readonly_') or db_field.startswith('readwrite_'):
                        db_record[db_field] = ''
                    else:
                        db_record[db_field] = None
            else:
                # 确保字符串长度不超过字段限制
                if isinstance(value, str):
                    max_lengths = {
                        'related_order_no': 50,
                        'quality_check_type': 50,
                        'business_type': 50,
                        'responsible_person': 50,
                        'call_issue_notes': 255,
                        'wechat_issue_notes': 255,
                        'ticket_issue_notes': 255,
                        'readonly_member_user': 255,
                        'readwrite_member_user': 255,
                        'readonly_member_dept': 255,
                        'readwrite_member_dept': 255,
                        'readonly_member_group': 255,
                        'readwrite_member_group': 255,
                        'readonly_member_role': 255,
                        'readwrite_member_role': 255,
                    }
                    max_len = max_lengths.get(db_field)
                    if max_len and len(value) > max_len:
                        print(f"警告: {db_field} 值长度超过限制({max_len})，将被截断")
                        value = value[:max_len]
                
                db_record[db_field] = value
    
    return db_record


def validate_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """验证记录是否有效"""
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return False, f"必填字段 '{field}' 不能为空"
    return True, None


def insert_records(connection, records: List[Dict[str, Any]]):
    """批量插入记录到数据库"""
    if not records:
        return 0
    
    # 构建插入SQL（不包括自增和时间戳字段）
    placeholders = ', '.join(['%s'] * len(DB_FIELDS))
    field_names = ', '.join([f'`{field}`' for field in DB_FIELDS])
    
    sql = f"""
        INSERT INTO `qis_scoring_results` ({field_names})
        VALUES ({placeholders})
    """
    
    # 准备数据
    values_list = []
    for record in records:
        values = [record.get(field) for field in DB_FIELDS]
        values_list.append(values)
    
    cursor = connection.cursor()
    try:
        # 批量插入
        affected_rows = cursor.executemany(sql, values_list)
        connection.commit()
        return affected_rows
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()


def check_duplicate(connection, related_order_no: str, quality_check_type: str) -> bool:
    """检查记录是否已存在（基于关联单号和质检类型）"""
    cursor = connection.cursor()
    try:
        sql = """
            SELECT COUNT(*) FROM `qis_scoring_results` 
            WHERE `related_order_no` = %s AND `quality_check_type` = %s
        """
        cursor.execute(sql, (related_order_no, quality_check_type))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        cursor.close()


def import_json_to_db(json_file_path: str, skip_duplicates: bool = True):
    """
    导入JSON文件到数据库
    
    Args:
        json_file_path: JSON文件路径
        skip_duplicates: 是否跳过重复的记录（基于关联单号和质检类型）
    """
    print(f"开始读取JSON文件: {json_file_path}")
    
    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件 {json_file_path} 不存在")
        return
    except json.JSONDecodeError as e:
        print(f"错误: JSON文件解析失败: {e}")
        return
    
    # 提取数据列表（支持多种JSON格式）
    data_list = []
    if isinstance(data, list):
        data_list = data
    elif isinstance(data, dict):
        data_list = data.get('data', {}).get('dataList', [])
        if not data_list:
            data_list = data.get('dataList', [])
        if not data_list:
            data_list = data.get('data', [])
    
    if not data_list:
        print("警告: JSON文件中没有找到数据列表")
        return
    
    print(f"找到 {len(data_list)} 条记录")
    
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("数据库连接成功")
    except Exception as e:
        print(f"错误: 数据库连接失败: {e}")
        return
    
    try:
        # 转换和过滤记录
        valid_records = []
        skipped_count = 0
        error_count = 0
        
        for idx, json_record in enumerate(data_list, 1):
            try:
                # 转换记录
                db_record = convert_record(json_record)
                
                # 验证必填字段
                is_valid, error_msg = validate_record(db_record)
                if not is_valid:
                    print(f"警告: 第 {idx} 条记录验证失败: {error_msg}，跳过")
                    skipped_count += 1
                    continue
                
                # 检查重复
                if skip_duplicates:
                    if check_duplicate(connection, 
                                     db_record['related_order_no'], 
                                     db_record['quality_check_type']):
                        print(f"跳过重复记录: 关联单号={db_record['related_order_no']}, "
                              f"质检类型={db_record['quality_check_type']}")
                        skipped_count += 1
                        continue
                
                valid_records.append(db_record)
                
            except Exception as e:
                print(f"错误: 处理第 {idx} 条记录时出错: {e}")
                error_count += 1
                continue
        
        print(f"\n有效记录: {len(valid_records)} 条")
        print(f"跳过记录: {skipped_count} 条")
        print(f"错误记录: {error_count} 条")
        
        # 批量插入（每批1000条）
        if valid_records:
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(valid_records), batch_size):
                batch = valid_records[i:i + batch_size]
                try:
                    inserted = insert_records(connection, batch)
                    total_inserted += inserted
                    print(f"已插入 {total_inserted}/{len(valid_records)} 条记录")
                except Exception as e:
                    print(f"错误: 插入第 {i+1}-{min(i+batch_size, len(valid_records))} 条记录时出错: {e}")
            
            print(f"\n导入完成! 成功插入 {total_inserted} 条记录")
        else:
            print("没有有效记录需要插入")
    
    finally:
        connection.close()
        print("数据库连接已关闭")


def insert_single_record(record: Dict[str, Any], skip_duplicates: bool = True):
    """
    插入单条记录到数据库
    
    Args:
        record: 记录字典（可以使用JSON字段名或数据库字段名）
        skip_duplicates: 是否跳过重复的记录
    """
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"错误: 数据库连接失败: {e}")
        return False
    
    try:
        # 转换记录
        db_record = convert_record(record)
        
        # 验证必填字段
        is_valid, error_msg = validate_record(db_record)
        if not is_valid:
            print(f"错误: 记录验证失败: {error_msg}")
            return False
        
        # 检查重复
        if skip_duplicates:
            if check_duplicate(connection, 
                             db_record['related_order_no'], 
                             db_record['quality_check_type']):
                print(f"记录已存在: 关联单号={db_record['related_order_no']}, "
                      f"质检类型={db_record['quality_check_type']}")
                return False
        
        # 插入记录
        inserted = insert_records(connection, [db_record])
        if inserted > 0:
            print(f"成功插入 1 条记录")
            return True
        else:
            print("插入失败")
            return False
    
    finally:
        connection.close()


if __name__ == '__main__':
    # 示例1: 从JSON文件导入
    json_file_path = r'D:\code\ZJL\data\qis_scoring_results.json'
    import_json_to_db(json_file_path, skip_duplicates=True)
    
    # 示例2: 插入单条记录
    # record = {
    #     'related_order_no': 'ORD001',
    #     'quality_check_type': '工单',
    #     'business_type': '替换发货',
    #     'quality_check_record': '这是一条质检记录',
    #     'responsible_person': '张三',
    #     'ticket_process_score': 25,
    #     'ticket_basic_info_score': 18,
    #     'ticket_issue_record_score': 30,
    #     'ticket_shipping_detail_score': 12,
    # }
    # insert_single_record(record, skip_duplicates=True)
    
    print("请修改脚本中的示例代码来执行导入操作")

