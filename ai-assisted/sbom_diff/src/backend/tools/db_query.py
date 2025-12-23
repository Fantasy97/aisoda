#!/usr/bin/env python
# -*- coding: utf-8 -*-

# amazonq-ignore-next-line
import pymysql
import json
import logging
import os
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    # amazonq-ignore-next-line
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}

def get_connection():
    """获取数据库连接"""
    try:
        # amazonq-ignore-next-line
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    # amazonq-ignore-next-line
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

# 查询bom
def query_bom_from_database(model_name):
    """
    从数据库查询BOM数据
    
    Args:
        model_name: 型号名称
        
    Returns:
        dict: BOM数据，按类别分组，失败返回None
    """
    if not model_name or not model_name.strip():
        logger.warning("型号名称不能为空")
        return None
        
    connection = get_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
            SELECT item_no_c, item_name_c, qty, item_cls_c, 
                   unit_c, loc, op, effective_date, expire_date,
                   item_id_c, entry_id, bom_version_c
            FROM dwd_mfg_bom_df 
            WHERE product_item_no = %s AND level = '0'
            """
            cursor.execute(sql, (model_name.strip(),))
            results = cursor.fetchall()
            
            if not results:
                logger.info(f"未找到型号 {model_name} 的BOM数据")
                return None
            
            # 按类别分组
            grouped_data = defaultdict(list)
            for row in results:
                part_no = row['item_no_c']
                if not part_no:
                    logger.warning(f"发现空的零件编号，跳过该记录")
                    continue
                    
                # 改进的分类逻辑
                category = _extract_category(part_no)
                
                part_data = {
                    'MPART.NO': row['item_no_c'],
                    'MPART.NAME': row['item_name_c'] or '',
                    'MBOM.BNUM': float(row['qty']) if row['qty'] else 0.0,
                    'MPART.WLSX': row['item_cls_c'] or '',
                    'MPART.UNIT': row['unit_c'] or 'PCS',
                    'MBOM.LOC': row['loc'] or '',
                    'MBOM.OP': row['op'] or '',
                    'MPART.EFFECTIVE_DATE': row['effective_date'] or '',
                    'MPART.EXPIRE_DATE': row['expire_date'] or '',
                    'MPART.ID': row['item_id_c'] or '',
                    'MBOM.ENTRY_ID': row['entry_id'] or '',
                    'MPART.BOM_VERSION': row['bom_version_c'] or ''
                }
                grouped_data[category].append(part_data)
            
            logger.info(f"成功查询到型号 {model_name} 的BOM数据，共 {len(results)} 条记录")
            return dict(grouped_data)
            
    except pymysql.Error as e:
        logger.error(f"数据库查询BOM数据失败: {e}")
        return None
    except Exception as e:
        logger.error(f"查询BOM数据时发生未知错误: {e}")
        return None
    finally:
        connection.close()

def _extract_model_prefix(model_name):
    """
    从型号名称中提取前缀
    
    Args:
        model_name: 型号名称，如 SP0030-0W-23-5EP
        
    Returns:
        str: 型号前缀，如 SP、HSP、TA等
    """
    if not model_name:
        return 'UNKNOWN'
    
    import re
    # 匹配字母开头的前缀
    match = re.match(r'^([A-Z]+)', model_name)
    if match:
        return match.group(1)
    
    return 'UNKNOWN'

def _extract_category(part_no):
    """
    从零件编号中提取分类
    
    Args:
        part_no: 零件编号
        
    Returns:
        str: 分类名称
    """
    if not part_no:
        return 'UNKNOWN'
    
    # 处理常见的零件编号格式
    if '-' in part_no:
        parts = part_no.split('-')
        if parts[0].isdigit() and len(parts[0]) == 3:
            return parts[0]
    
    # 如果没有标准格式，尝试提取前缀数字
    import re
    match = re.match(r'^(\d+)', part_no)
    if match:
        return match.group(1)
    
    # 默认返回完整编号作为分类
    return part_no

# 查询型号
def get_model_list(model_type=None):
    """
    获取型号列表
    
    Args:
        model_type: 型号类型 (TA/SP)
        
    Returns:
        list: 型号列表
    """
    connection = get_connection()
    if not connection:
        return []
    
    try:
        with connection.cursor() as cursor:
            if model_type:
                sql = "SELECT DISTINCT product_item_no FROM mfg_bom WHERE product_item_no LIKE %s"
                cursor.execute(sql, (f"{model_type}%",))
            else:
                sql = "SELECT DISTINCT product_item_no FROM mfg_bom"
                cursor.execute(sql)
            
            results = cursor.fetchall()
            return [row[0] for row in results if row[0]]
            
    except Exception as e:
        print(f"获取型号列表失败: {e}")
        return []
    finally:
        connection.close()
    
# 查询零件
def query_part_info(part_no):
    """
    查询单个零件信息
    
    Args:
        part_no: 零件编号
        
    Returns:
        dict: 零件信息或多条记录供选择
    """
    connection = get_connection()
    if not connection:
        return None
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
            SELECT product_item_no, item_no_c, item_name_c, qty, item_cls_c 
            FROM mfg_bom 
            WHERE item_no_c = %s
            """
            cursor.execute(sql, (part_no,))
            results = cursor.fetchall()
            
            if not results:
                return None
            elif len(results) == 1:
                row = results[0]
                return {
                    'MPART.NO': row['item_no_c'],
                    'MPART.NAME': row['item_name_c'] or '',
                    'MBOM.BNUM': row['qty'] or 0,
                    'MPART.WLSX': row['item_cls_c'] or '',
                    'PRODUCT_ITEM_NO': row['product_item_no']
                }
            else:
                # 多条记录，返回供用户选择
                return {'multiple': results}
            
    except Exception as e:
        print(f"查询零件信息失败: {e}")
        return None
    finally:
        connection.close()


def test_bom_table():
    """
    测试数据库中的BOM相关表
    """
    connection = get_connection()
    if not connection:
        print("数据库连接失败")
        return
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查看所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            # amazonq-ignore-next-line
            print("数据库中的所有表:")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"  - {table_name}")
            
            # 查看mfg_bom表结构
            print("\n=== mfg_bom 表结构 ===")
            cursor.execute("DESCRIBE mfg_bom")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col['Field']}: {col['Type']} - {col.get('Comment', '')}")
            
            # 查询记录数
            cursor.execute("SELECT COUNT(*) as total FROM mfg_bom")
            total = cursor.fetchone()['total']
            print(f"\n表 mfg_bom 总记录数: {total}")
            
    except Exception as e:
        print(f"查询失败: {e}")
    finally:
        connection.close()

# amazonq-ignore-next-line
def test_query_bom_from_database(model_code):
    """
    从数据库查询BOM数据（示例实现）
    
    Args:
        model_code: 型号编码，如 TA0033-00-20-5WP
        
    Returns:
        dict: BOM数据字典，失败返回None
    """
    try:
        # 示例实现：这里可以接入真实的数据库查询
        # import sqlite3
        # import mysql.connector
        # 或者调用API接口
        
        print(f"正在查询数据库中的型号: {model_code}")
        
        # 示例1：模拟数据库查询结果
        # 实际使用时需要替换为真实的数据库查询逻辑
        mock_bom_data = {
            "334": [
                {
                    "MPART.NO": "334-100001-00",
                    "MPART.NAME": f"{model_code} 示例组件",
                    "MBOM.BNUM": 1,
                    "MPART.WLSX": "自制"
                }
            ],
            "510": [
                {
                    "MPART.NO": "510-100001-00",
                    "MPART.NAME": f"{model_code} 示例零件",
                    "MBOM.BNUM": 2,
                    "MPART.WLSX": "外购"
                }
            ]
        }
        
        # 示例2：真实数据库查询示例（注释掉）
        # conn = sqlite3.connect('bom_database.db')
        # cursor = conn.cursor()
        # cursor.execute("""
        #     SELECT category, part_no, part_name, quantity, part_type 
        #     FROM bom_parts 
        #     WHERE model_code = ?
        # """, (model_code,))
        # 
        # results = cursor.fetchall()
        # conn.close()
        # 
        # if not results:
        #     return None
        # 
        # # 转换为标准格式
        # bom_data = defaultdict(list)
        # for category, part_no, part_name, quantity, part_type in results:
        #     bom_data[category].append({
        #         "MPART.NO": part_no,
        #         "MPART.NAME": part_name,
        #         "MBOM.BNUM": quantity,
        #         "MPART.WLSX": part_type
        #     })
        # 
        # return dict(bom_data)
        
        # 仅作为示例，返回模拟数据
        print(f"数据库查询成功，返回模拟数据")
        return mock_bom_data
        
    except Exception as e:
        print(f"数据库查询失败: {str(e)}")
        return None
    
def test_query_and_save_bom(model_name, base_path=r"D:\code\sbom\release\sbom_web\data\output"):
    """
    测试查询BOM数据并保存为JSON文件
    
    Args:
        model_name: 型号名称，如 'TA0030-00-24-52P'
        base_path: 基础保存路径
    """
    logger.info(f"开始查询型号: {model_name}")
    
    # 查询BOM数据
    bom_data = query_bom_from_database(model_name)
    
    if not bom_data:
        logger.warning(f"未查询到型号 {model_name} 的BOM数据")
        return False
    
    # 确定保存路径
    model_prefix = model_name.split('-')[0] if '-' in model_name else model_name[:2]
    save_dir = os.path.join(base_path, model_prefix)
    save_path = os.path.join(save_dir, f"{model_name}.json")
    
    # 创建目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 保存JSON文件
    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(bom_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"BOM数据已保存到: {save_path}")
        logger.info(f"共包含 {sum(len(parts) for parts in bom_data.values())} 个零件，{len(bom_data)} 个分类")
        return True
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return False

def main():
    """
    CLI工具主函数
    """
    while True:
        print("\n=== BOM数据库查询工具 ===")
        print("1. 查询BOM数据")
        print("2. 查询并保存BOM数据")
        print("3. 获取型号列表")
        print("4. 查询零件信息")
        print("5. 测试数据库表")
        print("0. 退出")
        
        choice = input("\n请选择功能 (0-5): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            model_name = input("请输入型号名称: ").strip()
            if model_name:
                bom_data = query_bom_from_database(model_name)
                if bom_data:
                    print(f"\n查询成功，共 {len(bom_data)} 个分类:")
                    for category, parts in bom_data.items():
                        print(f"  分类 {category}: {len(parts)} 个零件")
                else:
                    print("未找到数据")
        elif choice == '2':
            model_name = input("请输入型号名称: ").strip()
            if model_name:
                base_path = input(f"请输入保存路径 (默认: D:\\code\\sbom\\release\\sbom_web\\data\\output): ").strip()
                if not base_path:
                    base_path = r"D:\code\sbom\release\sbom_web\data\output"
                success = test_query_and_save_bom(model_name, base_path)
                print("保存成功" if success else "保存失败")
        elif choice == '3':
            model_type = input("请输入型号类型 (如TA/SP/HSP，留空查询所有): ").strip() or None
            models = get_model_list(model_type)
            if models:
                # 按型号前缀分组
                prefix_groups = defaultdict(list)
                for model in models:
                    prefix = _extract_model_prefix(model)
                    prefix_groups[prefix].append(model)
                
                print(f"\n找到 {len(models)} 个型号，按类型分组:")
                for prefix, model_list in sorted(prefix_groups.items()):
                    print(f"\n型号类型 {prefix} ({len(model_list)} 个):")
                    for model in model_list[:5]:  # 每类型显示前5个
                        print(f"  {model}")
                    if len(model_list) > 5:
                        print(f"  ... 还有 {len(model_list) - 5} 个 {prefix} 型号")
            else:
                print("未找到型号")
        elif choice == '4':
            part_no = input("请输入零件编号: ").strip()
            if part_no:
                part_info = query_part_info(part_no)
                if part_info:
                    if 'multiple' in part_info:
                        print(f"\n找到 {len(part_info['multiple'])} 条记录，请选择 (可输入编号或型号名称):")
                        for i, record in enumerate(part_info['multiple'], 1):
                            print(f"  {i}. 型号: {record['product_item_no']} - {record['item_name_c'] or '无名称'}")
                        
                        user_input = input("请选择记录编号或型号名称: ").strip()
                        selected = None
                        
                        # 尝试解析为数字
                        try:
                            idx = int(user_input) - 1
                            if 0 <= idx < len(part_info['multiple']):
                                selected = part_info['multiple'][idx]
                        except ValueError:
                            # 不是数字，尝试匹配型号名称
                            for record in part_info['multiple']:
                                if record['product_item_no'] == user_input:
                                    selected = record
                                    break
                        
                        if selected:
                            print("\n零件信息:")
                            print(f"  零件编号: {selected['item_no_c']}")
                            print(f"  零件名称: {selected['item_name_c'] or ''}")
                            print(f"  数量: {selected['qty'] or 0}")
                            print(f"  物料属性: {selected['item_cls_c'] or ''}")
                            print(f"  所属型号: {selected['product_item_no']}")
                        else:
                            print("无效选择，请输入正确的编号或型号名称")
                    else:
                        print("\n零件信息:")
                        for key, value in part_info.items():
                            print(f"  {key}: {value}")
                else:
                    print("未找到零件信息")
        elif choice == '5':
            test_bom_table()
        else:
            print("无效选择，请重新输入")
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")