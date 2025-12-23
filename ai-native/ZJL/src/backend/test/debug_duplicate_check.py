#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试重复工单检测逻辑
分析为什么某个工单会被判定为重复
"""

import sys
import os
import pymysql
from datetime import datetime

# 添加tools目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
tools_dir = os.path.join(backend_dir, 'tools')
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from score_cases import DB_CONFIG


def debug_duplicate_check(case_number: str):
    """
    调试重复工单检测
    
    Args:
        case_number: 工单号
    """
    print(f"\n{'='*80}")
    print(f"调试重复工单检测: {case_number}")
    print(f"{'='*80}\n")
    
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 1. 查询当前工单信息
        print("【步骤1】查询当前工单信息")
        print("-" * 80)
        sql_current = "SELECT * FROM `qis_cases_info` WHERE `name` = %s"
        cursor.execute(sql_current, (case_number,))
        current_case = cursor.fetchone()
        
        if not current_case:
            print(f"✗ 未找到工单: {case_number}")
            return
        
        print(f"工单号: {current_case.get('name')}")
        print(f"业务类型: {current_case.get('record_type')}")
        print(f"创建时间: {current_case.get('create_time')}")
        print(f"关联设备: {current_case.get('field_glsb__c')}")
        print(f"公众号用户: {current_case.get('field_o1oCe__c')}")
        print(f"微信昵称: {current_case.get('field_3ff0E__c')}")
        print(f"企微用户/群: {current_case.get('field_812NN__c')}")
        print(f"提报人: {current_case.get('field_iywKQ__c')}")
        print(f"提报人电话: {current_case.get('field_93r62__c')}")
        print(f"负责人ID: {current_case.get('owner')}")
        
        # 2. 判断业务类型
        business_type = str(current_case.get('record_type', '')).strip()
        is_hotline = business_type in ["热线受理", "record_1Z80y__c"]
        print(f"\n业务类型判断: {business_type}")
        print(f"是否为热线受理: {is_hotline}")
        
        # 3. 构建检查字段
        print(f"\n【步骤2】构建检查字段")
        print("-" * 80)
        check_fields = {
            'field_glsb__c': current_case.get('field_glsb__c'),
            'field_o1oCe__c': current_case.get('field_o1oCe__c'),
            'field_3ff0E__c': current_case.get('field_3ff0E__c'),
            'field_812NN__c': current_case.get('field_812NN__c'),
            'field_iywKQ__c': current_case.get('field_iywKQ__c'),
            'field_93r62__c': current_case.get('field_93r62__c')
        }
        
        if is_hotline:
            check_fields['owner'] = current_case.get('owner')
            print("包含负责人ID字段（热线受理类型）")
        
        # 处理空值
        for key, value in check_fields.items():
            if value is None:
                check_fields[key] = None
            else:
                value_str = str(value).strip()
                if value_str in ["", "null", "None"]:
                    check_fields[key] = None
                else:
                    check_fields[key] = value_str
        
        print("\n检查字段值:")
        for key, value in check_fields.items():
            display_value = "NULL" if value is None else value
            print(f"  {key}: {display_value}")
        
        # 4. 构建SQL查询条件
        print(f"\n【步骤3】构建SQL查询条件")
        print("-" * 80)
        conditions = []
        params = []
        
        for db_field, value in check_fields.items():
            if value is None:
                conditions.append(f"`{db_field}` IS NULL")
            else:
                conditions.append(f"`{db_field}` = %s")
                params.append(value)
        
        # 排除当前记录
        conditions.append("`name` != %s")
        params.append(case_number)
        
        # 创建时间条件
        current_create_time = current_case.get('create_time')
        if isinstance(current_create_time, str):
            try:
                current_create_time = datetime.strptime(current_create_time, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        conditions.append("`create_time` < %s")
        params.append(current_create_time)
        
        sql = f"""
            SELECT `name`, `create_time`, `record_type`, 
                   `field_glsb__c`, `field_o1oCe__c`, `field_3ff0E__c`, 
                   `field_812NN__c`, `field_iywKQ__c`, `field_93r62__c`, `owner`
            FROM `qis_cases_info`
            WHERE {' AND '.join(conditions)}
            ORDER BY `create_time` DESC
            LIMIT 10
        """
        
        print("\nSQL查询:")
        print(sql)
        print("\n查询参数:")
        for i, param in enumerate(params):
            print(f"  {i+1}. {param}")
        
        # 5. 执行查询
        print(f"\n【步骤4】执行查询，查找重复记录")
        print("-" * 80)
        cursor.execute(sql, params)
        duplicate_cases = cursor.fetchall()
        
        if duplicate_cases:
            print(f"✓ 找到 {len(duplicate_cases)} 条重复记录（创建时间更早）:\n")
            for idx, dup_case in enumerate(duplicate_cases, 1):
                print(f"重复记录 #{idx}:")
                print(f"  工单号: {dup_case.get('name')}")
                print(f"  业务类型: {dup_case.get('record_type')}")
                print(f"  创建时间: {dup_case.get('create_time')}")
                print(f"  关联设备: {dup_case.get('field_glsb__c')}")
                print(f"  公众号用户: {dup_case.get('field_o1oCe__c')}")
                print(f"  微信昵称: {dup_case.get('field_3ff0E__c')}")
                print(f"  企微用户/群: {dup_case.get('field_812NN__c')}")
                print(f"  提报人: {dup_case.get('field_iywKQ__c')}")
                print(f"  提报人电话: {dup_case.get('field_93r62__c')}")
                print(f"  负责人ID: {dup_case.get('owner')}")
                print()
            
            print(f"\n结论: 当前工单 {case_number} 被判定为重复工单")
            print(f"原因: 存在 {len(duplicate_cases)} 条记录，所有检查字段完全相同，且创建时间更早")
        else:
            print("✓ 未找到重复记录")
            print(f"结论: 当前工单 {case_number} 不是重复工单")
        
        # 6. 详细对比（如果有重复记录）
        if duplicate_cases:
            print(f"\n【步骤5】详细字段对比")
            print("-" * 80)
            first_dup = duplicate_cases[0]
            print(f"当前工单 vs 最早重复工单 ({first_dup.get('name')}):\n")
            
            comparison_fields = list(check_fields.keys())
            if is_hotline and 'owner' not in comparison_fields:
                comparison_fields.append('owner')
            
            for field in comparison_fields:
                current_val = current_case.get(field)
                dup_val = first_dup.get(field)
                
                # 处理None值显示
                current_display = "NULL" if current_val is None else str(current_val)
                dup_display = "NULL" if dup_val is None else str(dup_val)
                
                match = "✓" if current_val == dup_val else "✗"
                print(f"  {field:20s} | 当前: {current_display:30s} | 重复: {dup_display:30s} | {match}")
        
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if connection:
            cursor.close()
            connection.close()


def main():
    """主函数"""
    if len(sys.argv) > 1:
        case_number = sys.argv[1]
    else:
        # 默认测试工单号
        case_number = "CN20251218602014"
    
    debug_duplicate_check(case_number)


if __name__ == "__main__":
    main()
