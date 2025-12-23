#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用户设计记录查询模块
根据用户ID查询设计记录及关联的飞书审批信息
"""

import logging
from typing import List, Dict, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入数据库连接模块
try:
    import sys
    import os
    # 添加tools目录到路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(os.path.dirname(current_dir), 'tools')
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    
    from db_query import get_connection
    logger.info("成功导入 db_query 模块")
except ImportError as e:
    logger.warning(f"无法导入 db_query 模块: {e}")
    # 备用数据库连接实现
    import pymysql
    
    DB_CONFIG = {
        'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
        'port': 3306,
        'user': 'uat1688',
        'password': 'DFfe2&!Kj890J',
        'database': 'lifetree',
        'charset': 'utf8mb4'
    }
    
    def get_connection():
        """获取数据库连接"""
        try:
            connection = pymysql.connect(**DB_CONFIG)
            return connection
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return None


def query_user_designs(usr_id: int, limit: int = 100) -> Optional[List[Dict]]:
    """
    根据用户ID查询所有相关的设计记录及飞书审批信息
    
    查询逻辑:
    - 从 sbom_design 表获取用户的设计记录
    - 左连接 sbom_feishu_approval 表获取关联的审批信息
    - 返回完整的记录列表
    
    Args:
        usr_id: 用户ID
        limit: 返回记录数限制，默认100条
        
    Returns:
        List[Dict]: 查询结果列表，每条记录包含设计信息和审批信息
                   失败返回None
                   
    示例返回数据:
    [
        {
            # sbom_design 表字段
            'design_pk_id': 1,
            'usr_id': 123,
            'design_id': 'DESIGN001',
            'design_name': 'SP0030-3Q-23-5QP设计',
            'design_type': 'SP',
            'design_status': 'draft',
            'design_info': '{...}',
            'bom_path': '/path/to/bom',
            'design_instance_code': 'INST001',
            'design_create_time': '2025-01-01',
            'design_update_time': '2025-01-01',
            'deleted': '0',
            
            # sbom_feishu_approval 表字段
            'approval_pk_id': 1,
            'approval_instance_code': 'INST001',
            'approval_usr_name': 'user123',
            'feishu_status': 'APPROVED',
            'sbom_status': 'PUSHED',
            'approval_type': 'BOM_CREATE',
            'approval_name': 'BOM审批_DESIGN001',
            'approval_info': '{...}',
            'approval_attachment': '[...]',
            'feishu_response': '{...}',
            'approval_create_time': '2025-01-01',
            'approval_update_time': '2025-01-01'
        }
    ]
    """
    if not usr_id:
        logger.warning("用户ID不能为空")
        return None
    
    connection = get_connection()
    if not connection:
        logger.error("数据库连接失败")
        return None
    
    try:
        import pymysql.cursors
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 构建查询SQL - 左连接设计表和审批表
            sql = """
            SELECT 
                d.id as design_pk_id,
                d.usr_id,
                d.deleted,
                d.create_time as design_create_time,
                d.updater,
                d.update_time as design_update_time,
                d.design_id,
                d.design_name,
                d.design_type,
                d.design_status,
                d.design_info,
                d.bom_path,
                d.instance_code as design_instance_code,
                f.id as approval_pk_id,
                f.instance_code as approval_instance_code,
                f.usr_name as approval_usr_name,
                f.feishu_status,
                f.sbom_status,
                f.approval_type,
                f.approval_name,
                f.approval_info,
                f.approval_attachment,
                f.feishu_response,
                f.create_time as approval_create_time,
                f.update_time as approval_update_time
            FROM sbom_design d
            LEFT JOIN sbom_feishu_approval f ON (d.design_id = f.design_id)
            WHERE d.usr_id = %s
            ORDER BY d.update_time DESC
            LIMIT %s
            """
            
            cursor.execute(sql, (usr_id, limit))
            results = cursor.fetchall()
            
            if not results:
                logger.info(f"未找到用户 {usr_id} 的设计记录")
                return []
            
            logger.info(f"成功查询到用户 {usr_id} 的 {len(results)} 条记录")
            return list(results)
            
    except Exception as e:
        logger.error(f"查询用户设计记录失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        connection.close()


def query_user_designs_by_status(
    usr_id: int, 
    design_status: Optional[str] = None,
    approval_status: Optional[str] = None,
    limit: int = 100
) -> Optional[List[Dict]]:
    """
    根据用户ID和状态查询设计记录
    
    Args:
        usr_id: 用户ID
        design_status: 设计状态筛选 (如: draft, submitted, approved)
        approval_status: 审批状态筛选 (如: PENDING, APPROVED, REJECTED)
        limit: 返回记录数限制
        
    Returns:
        List[Dict]: 查询结果列表
    """
    if not usr_id:
        logger.warning("用户ID不能为空")
        return None
    
    connection = get_connection()
    if not connection:
        logger.error("数据库连接失败")
        return None
    
    try:
        import pymysql.cursors
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 构建动态SQL
            sql = """
            SELECT 
                d.*,
                f.*
            FROM sbom_design d
            LEFT JOIN sbom_feishu_approval f ON (d.design_id = f.design_id)
            WHERE d.usr_id = %s
            """
            
            params: List[Any] = [usr_id]
            
            # 添加设计状态筛选
            if design_status:
                sql += " AND d.design_status = %s"
                params.append(design_status)
            
            # 添加审批状态筛选
            if approval_status:
                sql += " AND f.feishu_status = %s"
                params.append(approval_status)
            
            sql += " ORDER BY d.update_time DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(sql, tuple(params))
            results = cursor.fetchall()
            
            logger.info(f"成功查询到 {len(results)} 条符合条件的记录")
            return list(results) if results else []
            
    except Exception as e:
        logger.error(f"查询用户设计记录失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        connection.close()


def query_designs_summary(usr_id: int) -> Optional[Dict]:
    """
    查询用户设计记录的统计摘要
    
    Args:
        usr_id: 用户ID
        
    Returns:
        Dict: 统计摘要信息
        {
            'total_designs': 100,
            'draft_count': 30,
            'submitted_count': 40,
            'approved_count': 20,
            'rejected_count': 10,
            'pending_approval_count': 15,
            ...
        }
    """
    if not usr_id:
        logger.warning("用户ID不能为空")
        return None
    
    connection = get_connection()
    if not connection:
        logger.error("数据库连接失败")
        return None
    
    try:
        import pymysql.cursors
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询设计记录统计
            sql = """
            SELECT 
                COUNT(*) as total_designs,
                SUM(CASE WHEN d.design_status = 'draft' THEN 1 ELSE 0 END) as draft_count,
                SUM(CASE WHEN d.design_status = 'submitted' THEN 1 ELSE 0 END) as submitted_count,
                SUM(CASE WHEN d.design_status = 'approved' THEN 1 ELSE 0 END) as approved_count,
                SUM(CASE WHEN f.feishu_status = 'PENDING' THEN 1 ELSE 0 END) as pending_approval_count,
                SUM(CASE WHEN f.feishu_status = 'APPROVED' THEN 1 ELSE 0 END) as approved_approval_count,
                SUM(CASE WHEN f.feishu_status = 'REJECTED' THEN 1 ELSE 0 END) as rejected_approval_count,
                SUM(CASE WHEN f.sbom_status = 'PUSHED' THEN 1 ELSE 0 END) as pushed_count
            FROM sbom_design d
            LEFT JOIN sbom_feishu_approval f ON (d.design_id = f.design_id)
            WHERE d.usr_id = %s
            """
            
            cursor.execute(sql, (usr_id,))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"成功查询用户 {usr_id} 的统计摘要")
                return result
            else:
                logger.warning(f"未找到用户 {usr_id} 的统计信息")
                return None
            
    except Exception as e:
        logger.error(f"查询统计摘要失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        connection.close()


def print_designs_table(records: List[Dict]):
    """
    格式化打印设计记录表格
    
    Args:
        records: 查询结果列表
    """
    if not records:
        print("  📭 没有找到任何记录")
        return
    
    print(f"\n{'='*120}")
    print(f"{'序号':<6} {'设计ID':<20} {'设计名称':<25} {'类型':<8} {'设计状态':<12} {'飞书审批状态':<15} {'SBOM状态':<12} {'更新时间':<20}")
    print(f"{'='*120}")
    
    for i, record in enumerate(records, 1):
        design_id = record.get('design_id', 'N/A')
        design_name = record.get('design_name', 'N/A')
        design_type = record.get('design_type', 'N/A')
        design_status = record.get('design_status', 'N/A')
        feishu_status = record.get('feishu_status', 'N/A') or '未提交'
        sbom_status = record.get('sbom_status', 'N/A') or '-'
        update_time = str(record.get('design_update_time', 'N/A'))
        
        # 截断过长的字段
        if len(design_name) > 23:
            design_name = design_name[:20] + '...'
        
        print(f"{i:<6} {design_id:<20} {design_name:<25} {design_type:<8} {design_status:<12} {feishu_status:<15} {sbom_status:<12} {update_time:<20}")
    
    print(f"{'='*120}")
    print(f"共 {len(records)} 条记录\n")


# CLI测试功能
def main():
    """
    命令行测试入口
    """
    import sys
    
    print("\n" + "="*60)
    print("    用户设计记录查询工具")
    print("="*60)
    
    while True:
        print("\n菜单:")
        print("1. 查询用户所有设计记录")
        print("2. 按状态查询设计记录")
        print("3. 查询用户统计摘要")
        print("0. 退出")
        print("="*60)
        
        choice = input("\n请选择功能 (0-3): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        
        elif choice == '1':
            usr_id = input("请输入用户ID: ").strip()
            if not usr_id.isdigit():
                print("❌ 无效的用户ID")
                continue
            
            limit = input("返回记录数限制 (默认100): ").strip() or "100"
            
            results = query_user_designs(int(usr_id), int(limit))
            if results is not None:
                print_designs_table(results)
        
        elif choice == '2':
            usr_id = input("请输入用户ID: ").strip()
            if not usr_id.isdigit():
                print("❌ 无效的用户ID")
                continue
            
            design_status = input("设计状态 (留空查询所有, 如: draft/submitted/approved): ").strip() or None
            approval_status = input("审批状态 (留空查询所有, 如: PENDING/APPROVED/REJECTED): ").strip() or None
            limit = input("返回记录数限制 (默认100): ").strip() or "100"
            
            results = query_user_designs_by_status(
                int(usr_id), 
                design_status, 
                approval_status, 
                int(limit)
            )
            if results is not None:
                print_designs_table(results)
        
        elif choice == '3':
            usr_id = input("请输入用户ID: ").strip()
            if not usr_id.isdigit():
                print("❌ 无效的用户ID")
                continue
            
            summary = query_designs_summary(int(usr_id))
            if summary:
                print("\n" + "="*60)
                print("    统计摘要")
                print("="*60)
                print(f"  总设计数: {summary.get('total_designs', 0)}")
                print(f"  草稿: {summary.get('draft_count', 0)}")
                print(f"  已提交: {summary.get('submitted_count', 0)}")
                print(f"  已批准: {summary.get('approved_count', 0)}")
                print(f"  待审批(飞书): {summary.get('pending_approval_count', 0)}")
                print(f"  审批通过(飞书): {summary.get('approved_approval_count', 0)}")
                print(f"  审批拒绝(飞书): {summary.get('rejected_approval_count', 0)}")
                print(f"  已推送PLM: {summary.get('pushed_count', 0)}")
                print("="*60)
        
        else:
            print("❌ 无效选择")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序异常: {e}")
        import traceback
        traceback.print_exc()
