"""
数据库操作工具类
用于连接和操作 MySQL 数据库
"""

import pymysql
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager


# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}


class Database:
    """数据库操作类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化数据库连接配置
        
        Args:
            config: 数据库配置字典，如果为 None 则使用默认配置
        """
        self.config = config or DB_CONFIG
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            conn = pymysql.connect(**self.config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, sql: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        执行查询语句，返回结果列表
        
        Args:
            sql: SQL 查询语句
            params: 查询参数元组
            
        Returns:
            查询结果列表，每个元素是一个字典，键为字段名，值为字段值
            
        Example:
            results = db.execute_query("SELECT * FROM users WHERE age > %s", (18,))
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def execute_one(self, sql: str, params: Tuple = None) -> Optional[Dict[str, Any]]:
        """
        执行查询语句，返回单条结果
        
        Args:
            sql: SQL 查询语句
            params: 查询参数元组
            
        Returns:
            查询结果字典，如果没有结果则返回 None
            
        Example:
            user = db.execute_one("SELECT * FROM users WHERE id = %s", (1,))
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute(sql, params)
            return cursor.fetchone()
    
    def execute_update(self, sql: str, params: Tuple = None) -> int:
        """
        执行更新/插入/删除语句
        
        Args:
            sql: SQL 语句
            params: 参数元组
            
        Returns:
            受影响的行数
            
        Example:
            rows = db.execute_update("UPDATE users SET name = %s WHERE id = %s", ("John", 1))
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            affected_rows = cursor.execute(sql, params)
            return affected_rows
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> int:
        """
        批量执行 SQL 语句
        
        Args:
            sql: SQL 语句
            params_list: 参数列表，每个元素是一个参数元组
            
        Returns:
            受影响的行数
            
        Example:
            params = [("John", 20), ("Jane", 25)]
            rows = db.execute_many("INSERT INTO users (name, age) VALUES (%s, %s)", params)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            affected_rows = cursor.executemany(sql, params_list)
            return affected_rows
    
    def get_tables(self) -> List[str]:
        """
        获取数据库中的所有表名
        
        Returns:
            表名列表
        """
        sql = "SHOW TABLES"
        results = self.execute_query(sql)
        # 提取表名（MySQL 返回的字段名可能是 'Tables_in_database_name'）
        table_key = list(results[0].keys())[0] if results else None
        return [row[table_key] for row in results] if table_key else []
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取指定表的所有列信息
        
        Args:
            table_name: 表名
            
        Returns:
            列信息列表，每个元素包含字段名、类型等信息
        """
        sql = f"DESCRIBE {table_name}"
        return self.execute_query(sql)
    
    def test_connection(self) -> bool:
        """
        测试数据库连接是否正常
        
        Returns:
            连接成功返回 True，否则返回 False
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False


# 创建全局数据库实例
db = Database()


# 便捷函数
def query(sql: str, params: Tuple = None) -> List[Dict[str, Any]]:
    """便捷查询函数"""
    return db.execute_query(sql, params)


def query_one(sql: str, params: Tuple = None) -> Optional[Dict[str, Any]]:
    """便捷单条查询函数"""
    return db.execute_one(sql, params)


def update(sql: str, params: Tuple = None) -> int:
    """便捷更新函数"""
    return db.execute_update(sql, params)


if __name__ == "__main__":
    # 测试代码
    print("测试数据库连接...")
    
    # 测试连接
    if db.test_connection():
        print("✓ 数据库连接成功！")
        
        # 获取所有表
        print("\n数据库中的表:")
        tables = db.get_tables()
        for table in tables:
            print(f"  - {table}")
        
        # 如果有表，显示第一个表的结构
        if tables:
            print(f"\n表 '{tables[0]}' 的列信息:")
            columns = db.get_table_columns(tables[0])
            for col in columns:
                print(f"  - {col}")
    else:
        print("✗ 数据库连接失败！")








