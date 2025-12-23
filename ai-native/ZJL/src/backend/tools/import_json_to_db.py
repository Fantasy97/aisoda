#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将替换发货.json文件中的数据导入到MySQL数据库
"""

import json
import pymysql
from datetime import datetime
from typing import Dict, Any, Optional

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}

# JSON字段名到数据库字段名的映射
FIELD_MAPPING = {
    '案例名称': 'name',
    '创建时间': 'create_time',
    '负责人ID': 'owner',
    '业务类型': 'record_type',
    '工单状态': 'field_v24BD__c',
    '问题记录': 'field_Utj19__c',
    '问题类型': 'field_0uAwt__c',
    '问题归类': 'field_toFhx__c',
    '提报人': 'field_iywKQ__c',
    '提报人电话': 'field_93r62__c',
    '公众号用户': 'field_o1oCe__c',
    '微信昵称': 'field_3ff0E__c',
    '企微用户/群': 'field_812NN__c',
    '需求来源': 'field_Mc0p7__c',
    '关联设备': 'field_glsb__c',
    '公司名称': 'account_id',
    '设备类型': 'field_sZHpO__c',
    '关联产品': 'field_glcp__c',
    '设备名称': 'field_FGMjJ__c',
    '解决方案': 'field_h017i__c',
    '现场排查': 'field_1H53l__c',
    '发货原因': 'field_3oyKy__c'
}


def parse_datetime(date_str: str) -> Optional[datetime]:
    """解析日期时间字符串"""
    if not date_str:
        return None
    try:
        # 尝试解析格式: "2025-11-25 17:58:05"
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


def convert_record(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """将JSON记录转换为数据库记录格式"""
    db_record = {}
    
    for json_key, db_key in FIELD_MAPPING.items():
        value = json_record.get(json_key)
        
        # 特殊处理创建时间字段
        if db_key == 'create_time' and value:
            parsed_time = parse_datetime(value)
            if parsed_time:
                db_record[db_key] = parsed_time
            else:
                db_record[db_key] = None
        else:
            # 对于其他字段，如果值为None或空字符串，设置为None
            if value is None or (isinstance(value, str) and value.strip() == ''):
                db_record[db_key] = None
            else:
                # 确保字符串长度不超过字段限制
                if isinstance(value, str):
                    # 根据数据库字段类型限制长度
                    max_lengths = {
                        'name': 50,
                        'owner': 100,
                        'record_type': 50,
                        'field_v24BD__c': 50,
                        'field_0uAwt__c': 100,
                        'field_toFhx__c': 100,
                        'field_iywKQ__c': 100,
                        'field_93r62__c': 100,
                        'field_o1oCe__c': 100,
                        'field_3ff0E__c': 200,
                        'field_812NN__c': 200,
                        'field_Mc0p7__c': 100,
                        'field_glsb__c': 100,
                        'account_id': 100,
                        'field_sZHpO__c': 50,
                        'field_glcp__c': 100,
                        'field_FGMjJ__c': 500,
                        'field_h017i__c': 500,
                        'field_1H53l__c': 100,
                        'field_3oyKy__c': 100
                    }
                    max_len = max_lengths.get(db_key)
                    if max_len and len(value) > max_len:
                        value = value[:max_len]
                
                db_record[db_key] = value
    
    return db_record


def insert_records(connection, records: list):
    """批量插入记录到数据库"""
    if not records:
        return 0
    
    # 构建插入SQL
    fields = list(FIELD_MAPPING.values())
    placeholders = ', '.join(['%s'] * len(fields))
    field_names = ', '.join([f'`{field}`' for field in fields])
    
    sql = f"""
        INSERT INTO `qis_cases_info` ({field_names})
        VALUES ({placeholders})
    """
    
    # 准备数据
    values_list = []
    for record in records:
        values = [record.get(field) for field in fields]
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


def check_duplicate(connection, name: str) -> bool:
    """检查案例名称是否已存在"""
    cursor = connection.cursor()
    try:
        sql = "SELECT COUNT(*) FROM `qis_cases_info` WHERE `name` = %s"
        cursor.execute(sql, (name,))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        cursor.close()


def import_json_to_db(json_file_path: str, skip_duplicates: bool = True):
    """
    导入JSON文件到数据库
    
    Args:
        json_file_path: JSON文件路径
        skip_duplicates: 是否跳过重复的记录（基于案例名称）
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
    
    # 提取数据列表
    data_list = data.get('data', {}).get('dataList', [])
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
                # 检查必填字段
                if not json_record.get('案例名称'):
                    print(f"警告: 第 {idx} 条记录缺少案例名称，跳过")
                    skipped_count += 1
                    continue
                
                # 检查重复
                if skip_duplicates:
                    if check_duplicate(connection, json_record['案例名称']):
                        print(f"跳过重复记录: {json_record['案例名称']}")
                        skipped_count += 1
                        continue
                
                # 转换记录
                db_record = convert_record(json_record)
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


if __name__ == '__main__':
    # JSON文件路径
    json_file_path = r'D:\code\ZJL\替换发货.json'
    
    # 执行导入
    import_json_to_db(json_file_path, skip_duplicates=True)
