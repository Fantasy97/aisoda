import logging
from typing import List, Optional, Dict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import os
    import sys

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    TOOLS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), 'tools')
    if TOOLS_DIR not in sys.path:
        sys.path.insert(0, TOOLS_DIR)

    from db_query import get_connection
    logger.info("成功导入 db_query 模块")
except ImportError as exc:
    logger.warning(f"无法导入 db_query 模块: {exc}")

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
        except Exception as error:
            logger.error(f"数据库连接失败: {error}")
            return None


def get_login_name_by_login_id(login_id: str) -> Optional[str]:
    """
    根据 login_id 查询 login_name。

    Args:
        login_id: 用户登录 ID。

    Returns:
        login_name 字符串或 None（未找到或查询失败）。
    """
    if not login_id:
        logger.warning("login_id 不能为空")
        return None

    connection = get_connection()
    if not connection:
        logger.error("数据库连接不可用")
        return None

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT login_name
                FROM sbom_usr_info
                WHERE login_id = %s AND deleted = '0'
                LIMIT 1
            """
            cursor.execute(sql, (login_id,))
            result = cursor.fetchone()
            if not result:
                logger.info(f"未找到 login_id 为 {login_id} 的用户")
                return None

            # cursor.fetchone() 返回 tuple，当使用默认 cursor 时。
            login_name = result[0] if isinstance(result, (list, tuple)) else result.get('login_name')
            logger.info(f"成功根据 login_id {login_id} 查询到 login_name: {login_name}")
            return login_name
    except Exception as error:
        logger.error(f"查询 login_name 失败: {error}")
        return None
    finally:
        connection.close()


def get_login_id_by_login_name(login_name: str) -> Optional[str]:
    """
    根据 login_name 查询 login_id。

    Args:
        login_name: 用户登录名称。

    Returns:
        login_id 字符串或 None（未找到或查询失败）。
    """
    if not login_name:
        logger.warning("login_name 不能为空")
        return None

    connection = get_connection()
    if not connection:
        logger.error("数据库连接不可用")
        return None

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT login_id
                FROM sbom_usr_info
                WHERE login_name = %s AND deleted = '0'
                LIMIT 1
            """
            cursor.execute(sql, (login_name,))
            result = cursor.fetchone()
            if not result:
                logger.info(f"未找到 login_name 为 {login_name} 的用户")
                return None

            # cursor.fetchone() 返回 tuple，当使用默认 cursor 时。
            login_id = result[0] if isinstance(result, (list, tuple)) else result.get('login_id')
            logger.info(f"成功根据 login_name {login_name} 查询到 login_id: {login_id}")
            return login_id
    except Exception as error:
        logger.error(f"查询 login_id 失败: {error}")
        return None
    finally:
        connection.close()


def search_user_login_info(keyword: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    根据用户输入的关键字联想查询登录信息。

    支持 login_id 前缀匹配以及 login_name 模糊匹配，默认仅返回 limit 条记录。

    Args:
        keyword: 用户输入的关键字，可为 login_id 或 login_name 的一部分。
        limit: 返回的记录上限，默认 5。

    Returns:
        包含 login_id 与 login_name 的字典列表，查询失败或未命中时返回空列表。
    """
    if not keyword:
        logger.warning("keyword 不能为空")
        return []

    connection = get_connection()
    if not connection:
        logger.error("数据库连接不可用")
        return []

    keyword = keyword.strip()
    id_pattern = f"{keyword}%"
    name_pattern = f"%{keyword}%"

    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT login_id, login_name
                FROM sbom_usr_info
                WHERE deleted = '0'
                  AND (login_id LIKE %s OR login_name LIKE %s)
                ORDER BY login_id
                LIMIT %s
            """
            cursor.execute(sql, (id_pattern, name_pattern, limit))
            records = cursor.fetchall() or []

        suggestions: List[Dict[str, str]] = []
        for record in records:
            if isinstance(record, (list, tuple)):
                login_id, login_name = record[0], record[1] if len(record) > 1 else None
            else:
                login_id = record.get("login_id")
                login_name = record.get("login_name")

            if not login_id and not login_name:
                continue

            suggestions.append(
                {
                    "login_id": str(login_id) if login_id is not None else "",
                    "login_name": login_name or "",
                }
            )

        logger.info(
            "联想查询关键字 %s 返回 %d 条记录",
            keyword,
            len(suggestions),
        )
        return suggestions[:limit]
    except Exception as error:
        logger.error(f"联想查询失败: {error}")
        return []
    finally:
        connection.close()

