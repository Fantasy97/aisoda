"""
纷享销客API调用工具 - 案例对象列表查询
用于查询CasesObj(案例对象)的列表数据,支持分页、过滤、排序
"""

import requests
import json
import pymysql
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta


class FXiaoKeListQueryClient:
    """纷享销客列表查询API客户端"""
    
    # API配置
    TOKEN_URL = "https://open.fxiaoke.com/cgi/corpAccessToken/get/V2"
    USER_URL = "https://open.fxiaoke.com/cgi/user/getByMobile"
    QUERY_URL = "https://open.fxiaoke.com/cgi/crm/v2/data/query"
    
    # 认证信息
    APP_ID = "FSAID_1321ff2"
    APP_SECRET = "ba97bc1efef445dc8053cadfb2ca967f"
    PERMANENT_CODE = "2C824786794DCB9E6AA7CBD95DC27C5F"
    MOBILE = "15210064866"
    
    def __init__(self):
        """初始化客户端"""
        self.corp_access_token = None
        self.corp_id = None
        self.current_open_user_id = None
        
    def get_token(self) -> bool:
        """
        获取访问令牌
        
        Returns:
            bool: 是否成功获取令牌
        """
        print("正在获取访问令牌...")
        
        payload = {
            "appId": self.APP_ID,
            "appSecret": self.APP_SECRET,
            "permanentCode": self.PERMANENT_CODE
        }
        
        try:
            response = requests.post(self.TOKEN_URL, json=payload)
            result = response.json()
            
            if result.get("errorCode") == 0:
                self.corp_access_token = result.get("corpAccessToken")
                self.corp_id = result.get("corpId")
                print(f"✓ 成功获取令牌")
                print(f"  corpId: {self.corp_id}")
                return True
            else:
                print(f"✗ 获取令牌失败: {result.get('errorMessage')}")
                return False
                
        except Exception as e:
            print(f"✗ 请求失败: {e}")
            return False
    
    def get_user_id(self) -> bool:
        """
        获取用户ID
        
        Returns:
            bool: 是否成功获取用户ID
        """
        print(f"正在获取用户ID (手机号: {self.MOBILE})...")
        
        payload = {
            "corpAccessToken": self.corp_access_token,
            "corpId": self.corp_id,
            "mobile": self.MOBILE
        }
        
        try:
            response = requests.post(self.USER_URL, json=payload)
            result = response.json()
            
            # 检查返回结果
            if result.get("errorCode") == 0 and result.get("empList"):
                emp_list = result.get("empList")
                if len(emp_list) > 0:
                    emp_info = emp_list[0]
                    self.current_open_user_id = emp_info.get("openUserId")
                    print(f"✓ 成功获取用户ID")
                    print(f"  姓名: {emp_info.get('fullName')}")
                    print(f"  openUserId: {self.current_open_user_id}")
                    return True
            
            print(f"✗ 获取用户ID失败: {result.get('errorMessage', '未知错误')}")
            return False
                
        except Exception as e:
            print(f"✗ 请求失败: {e}")
            return False
    
    def query_cases_list(self, 
                         limit: int = 100,
                         offset: int = 0,
                         field_projection: Optional[List[str]] = None,
                         filters: Optional[List[Dict]] = None,
                         orders: Optional[List[Dict]] = None,
                         find_total: bool = True) -> Optional[Dict]:
        """
        查询案例对象列表
        
        Args:
            limit: 分页条数(最大100)
            offset: 偏移量(从0开始,必须为limit的整数倍)
            field_projection: 返回字段列表
            filters: 过滤条件列表
            orders: 排序条件列表
            find_total: 是否返回总数
            
        Returns:
            查询结果字典,失败返回None
        """
        print(f"\n正在查询CasesObj列表...")
        print(f"  分页: limit={limit}, offset={offset}")
        
        # 默认返回字段
        if field_projection is None:
            field_projection = ["name", "create_time"]
        
        # 默认排序(按创建时间倒序)
        if orders is None:
            orders = [{"fieldName": "create_time", "isAsc": False}]
        
        # 默认无过滤
        if filters is None:
            filters = []
        
        # 参数校验
        if limit > 100 or limit <= 0:
            print("✗ limit必须在1-100之间")
            return None
        
        if offset % limit != 0:
            print("✗ offset必须为limit的整数倍")
            return None
        
        payload = {
            "corpAccessToken": self.corp_access_token,
            "currentOpenUserId": self.current_open_user_id,
            "corpId": self.corp_id,
            "data": {
                "dataObjectApiName": "CasesObj",
                "find_explicit_total_num": find_total,
                "search_query_info": {
                    "limit": limit,
                    "offset": offset,
                    "fieldProjection": field_projection,
                    "orders": orders,
                    "filters": filters
                }
            }
        }
        
        try:
            response = requests.post(self.QUERY_URL, json=payload)
            result = response.json()
            
            error_code = result.get("errorCode")
            error_message = result.get("errorMessage", "未知错误")
            
            print(f"\n响应状态码: {response.status_code}")
            print(f"错误码: {error_code}")
            
            if error_code == 0:
                data = result.get("data", {})
                total_size = data.get("totalSize", 0)
                data_list = data.get("dataList", [])
                
                print(f"✓ 查询成功")
                print(f"  总记录数: {total_size}")
                print(f"  返回记录数: {len(data_list)}")
                
                return result
            else:
                print(f"✗ 查询失败 [错误码:{error_code}]")
                print(f"  原因: {error_message}")
                return result
                
        except Exception as e:
            print(f"\n✗ 请求失败: {e}")
            return None
    
    def execute_query(self,
                      limit: int = 100,
                      offset: int = 0,
                      field_projection: Optional[List[str]] = None,
                      filters: Optional[List[Dict]] = None,
                      orders: Optional[List[Dict]] = None,
                      find_total: bool = True) -> Optional[Dict]:
        """
        执行完整查询流程
        
        Args:
            limit: 分页条数
            offset: 偏移量
            field_projection: 返回字段列表
            filters: 过滤条件列表
            orders: 排序条件列表
            find_total: 是否返回总数
            
        Returns:
            查询结果
        """
        print("="*60)
        print("纷享销客API调用 - 案例对象列表查询")
        print("="*60)
        
        # 1. 获取令牌
        if not self.get_token():
            return None
        
        # 2. 获取用户ID
        if not self.get_user_id():
            return None
        
        # 3. 查询列表数据
        result = self.query_cases_list(
            limit=limit,
            offset=offset,
            field_projection=field_projection,
            filters=filters,
            orders=orders,
            find_total=find_total
        )
        
        print("\n" + "="*60)
        return result
    
    def query_all_pages(self,
                        field_projection: Optional[List[str]] = None,
                        filters: Optional[List[Dict]] = None,
                        orders: Optional[List[Dict]] = None,
                        find_total: bool = True,
                        page_size: int = 100) -> Optional[Dict]:
        """
        自动分页查询所有数据
        
        Args:
            field_projection: 返回字段列表
            filters: 过滤条件列表
            orders: 排序条件列表
            find_total: 是否返回总数（只在第一页查询时生效）
            page_size: 每页大小（最大100）
            
        Returns:
            合并后的查询结果字典，包含所有页的数据
        """
        print("="*60)
        print("纷享销客API调用 - 自动分页查询所有数据")
        print("="*60)
        
        # 1. 获取令牌
        if not self.get_token():
            return None
        
        # 2. 获取用户ID
        if not self.get_user_id():
            return None
        
        # 3. 先查询第一页获取总数
        print(f"\n📄 开始自动分页查询（每页 {page_size} 条）...")
        first_result = self.query_cases_list(
            limit=page_size,
            offset=0,
            field_projection=field_projection,
            filters=filters,
            orders=orders,
            find_total=find_total
        )
        
        if not first_result or first_result.get("errorCode") != 0:
            return first_result
        
        first_data = first_result.get("data", {})
        first_data_list = first_data.get("dataList", [])
        # 优先使用 totalSize，其次使用 total，再退回到当前页数量
        total_size = first_data.get("totalSize")
        if not total_size:
            total_size = first_data.get("total")
        if not total_size:
            total_size = len(first_data_list)
        # 避免 total 小于已返回数量的情况
        total_size = max(total_size or 0, len(first_data_list))
        
        print(f"\n📊 总记录数: {total_size}")
        print(f"📄 第 1 页: 获取 {len(first_data_list)} 条记录")
        
        all_data_list = first_data_list.copy()
        
        # 4. 如果总数大于第一页，继续查询后续页
        if total_size > len(first_data_list):
            offset = page_size
            page_num = 2
            
            while len(all_data_list) < total_size:
                page_result = self.query_cases_list(
                    limit=page_size,
                    offset=offset,
                    field_projection=field_projection,
                    filters=filters,
                    orders=orders,
                    find_total=False  # 后续页不需要查询总数
                )
                
                if not page_result or page_result.get("errorCode") != 0:
                    print(f"\n⚠️  第 {page_num} 页查询失败，停止分页")
                    break
                
                page_data = page_result.get("data", {})
                page_data_list = page_data.get("dataList", [])
                
                if not page_data_list:
                    print(f"\n✓ 已获取所有数据（共 {len(all_data_list)} 条）")
                    break
                
                all_data_list.extend(page_data_list)
                print(f"📄 第 {page_num} 页: 获取 {len(page_data_list)} 条记录（累计 {len(all_data_list)}/{total_size}）")
                
                offset += page_size
                page_num += 1
                
                # 防止无限循环
                if len(page_data_list) < page_size:
                    break
        
        # 5. 构建合并后的结果
        merged_result = {
            "traceId": first_result.get("traceId", ""),
            "data": {
                "dataList": all_data_list,
                "offset": 0,
                "limit": len(all_data_list),
                "totalSize": total_size,
                "total": total_size
            },
            "errorDescription": first_result.get("errorDescription", ""),
            "errorMessage": first_result.get("errorMessage", ""),
            "errorCode": first_result.get("errorCode", 0)
        }
        
        print(f"\n✓ 分页查询完成，共获取 {len(all_data_list)} 条记录")
        print("="*60)
        
        return merged_result


class QueryBuilder:
    """查询条件构建器"""
    
    def __init__(self):
        self.filters = []
        self.orders = []
        self.fields = ["name", "create_time"]
        self.limit_val = 100
        self.offset_val = 0
        self.find_total_val = True
    
    def add_filter_eq(self, field_name: str, value) -> 'QueryBuilder':
        """添加等于过滤条件"""
        self.filters.append({
            "operator": "EQ",
            "field_name": field_name,
            "field_values": [value]
        })
        return self
    
    def add_filter_ne(self, field_name: str, value) -> 'QueryBuilder':
        """添加不等于过滤条件"""
        self.filters.append({
            "operator": "NE",
            "field_name": field_name,
            "field_values": [value]
        })
        return self
    
    def add_filter_in(self, field_name: str, values: List) -> 'QueryBuilder':
        """添加IN过滤条件"""
        self.filters.append({
            "operator": "IN",
            "field_name": field_name,
            "field_values": values
        })
        return self
    
    def add_filter_between(self, field_name: str, start, end) -> 'QueryBuilder':
        """添加范围过滤条件"""
        self.filters.append({
            "operator": "BETWEEN",
            "field_name": field_name,
            "field_values": [start, end]
        })
        return self
    
    def add_filter_like(self, field_name: str, value: str) -> 'QueryBuilder':
        """添加模糊查询条件"""
        self.filters.append({
            "operator": "LIKE",
            "field_name": field_name,
            "field_values": [value]
        })
        return self
    
    def add_order(self, field_name: str, is_asc: bool = True) -> 'QueryBuilder':
        """添加排序条件"""
        self.orders.append({
            "fieldName": field_name,
            "isAsc": is_asc
        })
        return self
    
    def set_fields(self, *fields) -> 'QueryBuilder':
        """设置返回字段"""
        self.fields = list(fields)
        return self
    
    def set_limit(self, limit: int) -> 'QueryBuilder':
        """设置分页大小"""
        self.limit_val = limit
        return self
    
    def set_offset(self, offset: int) -> 'QueryBuilder':
        """设置偏移量"""
        self.offset_val = offset
        return self
    
    def set_find_total(self, find_total: bool) -> 'QueryBuilder':
        """设置是否返回总数"""
        self.find_total_val = find_total
        return self
    
    def build(self) -> Dict:
        """构建查询参数"""
        return {
            "limit": self.limit_val,
            "offset": self.offset_val,
            "field_projection": self.fields,
            "filters": self.filters,
            "orders": self.orders if self.orders else [{"fieldName": "create_time", "isAsc": False}],
            "find_total": self.find_total_val
        }


# ==================== 数据库导入相关配置 ====================

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}

# 中文字段名到数据库字段名的映射
DB_FIELD_MAPPING = {
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
    '备用序号': 'field_TWcZV__c',
    '公司名称': 'account_id',
    '设备类型': 'field_sZHpO__c',
    '关联产品': 'field_glcp__c',
    '设备名称': 'field_FGMjJ__c',
    '解决方案': 'field_h017i__c',
    '现场排查': 'field_1H53l__c',
    '发货原因': 'field_3oyKy__c'
}

# 数据库字段的最大长度限制
DB_FIELD_MAX_LENGTHS = {
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
    'field_TWcZV__c': 100,
    'account_id': 100,
    'field_sZHpO__c': 50,
    'field_glcp__c': 100,
    'field_FGMjJ__c': 500,
    'field_Utj19__c': 2000,  # 问题记录可能较长
    'field_h017i__c': 500,
    'field_1H53l__c': 100,
    'field_3oyKy__c': 100
}


def parse_datetime_for_db(date_str: str) -> Optional[datetime]:
    """解析日期时间字符串为datetime对象（用于数据库）"""
    if not date_str:
        return None
    try:
        # 尝试解析格式: "2025-11-25 17:58:05"
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            # 尝试解析格式: "2025-11-25"
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None


def convert_record_to_db(json_record: Dict[str, Any]) -> Dict[str, Any]:
    """将JSON记录（中文字段名）转换为数据库记录格式（英文字段名）"""
    db_record = {}
    
    for cn_field, db_field in DB_FIELD_MAPPING.items():
        value = json_record.get(cn_field)
        
        # 特殊处理创建时间字段
        if db_field == 'create_time' and value:
            parsed_time = parse_datetime_for_db(value)
            if parsed_time:
                db_record[db_field] = parsed_time
            else:
                db_record[db_field] = None
        else:
            # 对于其他字段，如果值为None或空字符串，设置为None
            if value is None or (isinstance(value, str) and value.strip() == ''):
                db_record[db_field] = None
            else:
                # 确保字符串长度不超过字段限制
                if isinstance(value, str):
                    max_len = DB_FIELD_MAX_LENGTHS.get(db_field)
                    if max_len and len(value) > max_len:
                        value = value[:max_len]
                
                db_record[db_field] = value
    
    return db_record


def check_duplicate_in_db(connection, name: str) -> bool:
    """检查案例名称是否已存在于数据库中"""
    cursor = connection.cursor()
    try:
        sql = "SELECT COUNT(*) FROM `qis_cases_info` WHERE `name` = %s"
        cursor.execute(sql, (name,))
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        cursor.close()


def insert_records_to_db(connection, records: List[Dict[str, Any]]) -> int:
    """批量插入记录到数据库
    
    Args:
        connection: 数据库连接
        records: 记录列表（使用数据库字段名）
    
    Returns:
        成功插入的记录数
    """
    if not records:
        return 0
    
    # 构建插入SQL
    fields = list(DB_FIELD_MAPPING.values())
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


def import_result_to_db(result: Dict[str, Any], 
                       skip_duplicates: bool = True,
                       batch_size: int = 1000) -> Tuple[int, int, int]:
    """
    将查询结果导入到数据库
    
    Args:
        result: API查询结果（包含中文字段名的dataList）
        skip_duplicates: 是否跳过重复记录（基于案例名称）
        batch_size: 批量插入的大小（默认1000条）
    
    Returns:
        (成功插入数, 跳过数, 错误数)
    """
    if not result or result.get("errorCode") != 0:
        print("⚠️  查询结果无效，无法导入数据库")
        return (0, 0, 0)
    
    # 提取数据列表
    data = result.get("data", {})
    data_list = data.get("dataList", [])
    
    if not data_list:
        print("⚠️  没有数据需要导入")
        return (0, 0, 0)
    
    print(f"\n📊 开始导入数据库，共 {len(data_list)} 条记录")
    
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return (0, 0, 0)
    
    try:
        # 转换和过滤记录
        valid_records = []
        skipped_count = 0
        error_count = 0
        
        for idx, json_record in enumerate(data_list, 1):
            try:
                # 检查必填字段
                case_name = json_record.get('案例名称')
                if not case_name:
                    print(f"⚠️  第 {idx} 条记录缺少案例名称，跳过")
                    skipped_count += 1
                    continue
                
                # 检查重复
                if skip_duplicates:
                    if check_duplicate_in_db(connection, case_name):
                        if (idx - 1) % 100 == 0:  # 每100条打印一次，避免刷屏
                            print(f"跳过重复记录: {case_name} (已处理 {idx}/{len(data_list)})")
                        skipped_count += 1
                        continue
                
                # 转换记录
                db_record = convert_record_to_db(json_record)
                valid_records.append(db_record)
                
            except Exception as e:
                print(f"✗ 处理第 {idx} 条记录时出错: {e}")
                error_count += 1
                continue
        
        print(f"\n📋 数据统计:")
        print(f"   有效记录: {len(valid_records)} 条")
        print(f"   跳过记录: {skipped_count} 条")
        print(f"   错误记录: {error_count} 条")
        
        # 批量插入
        total_inserted = 0
        if valid_records:
            for i in range(0, len(valid_records), batch_size):
                batch = valid_records[i:i + batch_size]
                try:
                    inserted = insert_records_to_db(connection, batch)
                    total_inserted += inserted
                    print(f"   ✓ 已插入 {total_inserted}/{len(valid_records)} 条记录")
                except Exception as e:
                    print(f"   ✗ 插入第 {i+1}-{min(i+batch_size, len(valid_records))} 条记录时出错: {e}")
                    error_count += len(batch)
            
            print(f"\n✓ 导入完成! 成功插入 {total_inserted} 条记录")
        else:
            print("⚠️  没有有效记录需要插入")
        
        return (total_inserted, skipped_count, error_count)
    
    finally:
        connection.close()
        print("✓ 数据库连接已关闭")


# ==================== 数据库删除相关函数 ====================

def delete_by_names(case_names: List[str], batch_size: int = 1000) -> Tuple[int, int]:
    """
    根据案例名称列表批量删除记录
    
    Args:
        case_names: 案例名称列表
        batch_size: 批量删除的大小（默认1000条）
    
    Returns:
        (成功删除数, 错误数)
    """
    if not case_names:
        print("⚠️  案例名称列表为空")
        return (0, 0)
    
    print(f"\n🗑️  开始删除记录，共 {len(case_names)} 个案例名称")
    
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return (0, 0)
    
    try:
        cursor = connection.cursor()
        total_deleted = 0
        error_count = 0
        
        # 批量删除
        for i in range(0, len(case_names), batch_size):
            batch = case_names[i:i + batch_size]
            try:
                # 构建 IN 子句
                placeholders = ', '.join(['%s'] * len(batch))
                sql = f"DELETE FROM `qis_cases_info` WHERE `name` IN ({placeholders})"
                
                affected_rows = cursor.execute(sql, batch)
                connection.commit()
                total_deleted += affected_rows
                print(f"   ✓ 已删除 {total_deleted}/{len(case_names)} 条记录")
            except Exception as e:
                connection.rollback()
                print(f"   ✗ 删除第 {i+1}-{min(i+batch_size, len(case_names))} 条记录时出错: {e}")
                error_count += len(batch)
        
        cursor.close()
        print(f"\n✓ 删除完成! 成功删除 {total_deleted} 条记录")
        if error_count > 0:
            print(f"⚠️  删除失败 {error_count} 条记录")
        
        return (total_deleted, error_count)
    
    finally:
        connection.close()
        print("✓ 数据库连接已关闭")


def delete_by_date_range(start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        record_type: Optional[str] = None) -> Tuple[int, int]:
    """
    根据日期范围删除记录
    
    Args:
        start_date: 开始日期（包含），None表示不限制
        end_date: 结束日期（包含），None表示不限制
        record_type: 业务类型过滤（'record_1Z80y__c' 表示热线受理，'default__c' 表示替换发货），None表示不限制
    
    Returns:
        (成功删除数, 错误数)
    """
    print(f"\n🗑️  开始根据日期范围删除记录")
    
    if start_date:
        print(f"   开始日期: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
    if end_date:
        print(f"   结束日期: {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    if record_type:
        type_name = "热线受理" if record_type == "record_1Z80y__c" else "替换发货"
        print(f"   业务类型: {type_name}")
    
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return (0, 0)
    
    try:
        cursor = connection.cursor()
        
        # 构建SQL条件
        conditions = []
        params = []
        
        if start_date:
            conditions.append("`create_time` >= %s")
            params.append(start_date)
        
        if end_date:
            # 结束日期包含当天的23:59:59
            end_datetime = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            conditions.append("`create_time` <= %s")
            params.append(end_datetime)
        
        if record_type:
            conditions.append("`record_type` = %s")
            params.append(record_type)
        
        if not conditions:
            print("⚠️  警告: 没有指定任何删除条件，将删除所有记录！")
            response = input("确认要删除所有记录吗？(yes/no): ")
            if response.lower() != 'yes':
                print("❌ 操作已取消")
                return (0, 0)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"DELETE FROM `qis_cases_info` WHERE {where_clause}"
        
        # 先查询要删除的记录数
        count_sql = f"SELECT COUNT(*) FROM `qis_cases_info` WHERE {where_clause}"
        cursor.execute(count_sql, params)
        count = cursor.fetchone()[0]
        print(f"   找到 {count} 条记录将被删除")
        
        if count == 0:
            print("⚠️  没有找到符合条件的记录")
            return (0, 0)
        
        # 执行删除
        try:
            affected_rows = cursor.execute(sql, params)
            connection.commit()
            print(f"\n✓ 删除完成! 成功删除 {affected_rows} 条记录")
            return (affected_rows, 0)
        except Exception as e:
            connection.rollback()
            print(f"\n✗ 删除失败: {e}")
            return (0, 1)
    
    finally:
        cursor.close()
        connection.close()
        print("✓ 数据库连接已关闭")


def delete_by_single_name(case_name: str) -> bool:
    """
    根据单个案例名称删除记录
    
    Args:
        case_name: 案例名称
    
    Returns:
        是否删除成功
    """
    if not case_name:
        print("⚠️  案例名称为空")
        return False
    
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print(f"🗑️  删除案例: {case_name}")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False
    
    try:
        cursor = connection.cursor()
        sql = "DELETE FROM `qis_cases_info` WHERE `name` = %s"
        affected_rows = cursor.execute(sql, (case_name,))
        connection.commit()
        
        if affected_rows > 0:
            print(f"✓ 成功删除 {affected_rows} 条记录")
            return True
        else:
            print(f"⚠️  未找到案例名称: {case_name}")
            return False
    
    except Exception as e:
        connection.rollback()
        print(f"✗ 删除失败: {e}")
        return False
    
    finally:
        cursor.close()
        connection.close()


def delete_all_records(confirm: bool = False) -> Tuple[int, int]:
    """
    删除所有记录（危险操作，需谨慎使用）
    
    Args:
        confirm: 是否已确认（默认False，需要显式传入True才能执行）
    
    Returns:
        (成功删除数, 错误数)
    """
    if not confirm:
        print("⚠️  警告: 此操作将删除所有记录！")
        print("   如需执行，请调用 delete_all_records(confirm=True)")
        return (0, 0)
    
    print(f"\n🗑️  开始删除所有记录")
    
    # 连接数据库
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功")
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return (0, 0)
    
    try:
        cursor = connection.cursor()
        
        # 先查询总记录数
        cursor.execute("SELECT COUNT(*) FROM `qis_cases_info`")
        count = cursor.fetchone()[0]
        print(f"   找到 {count} 条记录将被删除")
        
        if count == 0:
            print("⚠️  数据库中没有记录")
            return (0, 0)
        
        # 执行删除
        try:
            affected_rows = cursor.execute("DELETE FROM `qis_cases_info`")
            connection.commit()
            print(f"\n✓ 删除完成! 成功删除 {affected_rows} 条记录")
            return (affected_rows, 0)
        except Exception as e:
            connection.rollback()
            print(f"\n✗ 删除失败: {e}")
            return (0, 1)
    
    finally:
        cursor.close()
        connection.close()
        print("✓ 数据库连接已关闭")


def delete_by_date(target_date: Optional[datetime] = None,
                   delete_hotline: bool = True,
                   delete_replacement: bool = True) -> Dict[str, Any]:
    """
    按指定日期删除工单数据
    
    Args:
        target_date: 目标日期，可以是datetime对象或None（None表示昨天）
                    也可以传入字符串格式 "YYYY-MM-DD"
        delete_hotline: 是否删除热线受理数据（默认True）
        delete_replacement: 是否删除替换发货数据（默认True）
    
    Returns:
        包含删除结果的字典:
        {
            "date": 删除的日期字符串,
            "hotline_deleted": 热线受理删除数,
            "replacement_deleted": 替换发货删除数,
            "total_deleted": 总删除数
        }
    
    Example:
        # 删除昨天的数据
        results = delete_by_date()
        
        # 删除指定日期的数据
        from datetime import datetime
        date = datetime(2024, 1, 15)
        results = delete_by_date(date)
        
        # 只删除热线受理数据
        results = delete_by_date(date, delete_replacement=False)
    """
    # 处理日期参数
    if target_date is None:
        # 默认删除昨天
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query_date = today_start - timedelta(days=1)
    elif isinstance(target_date, str):
        # 字符串格式 "YYYY-MM-DD"
        try:
            query_date = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"日期格式错误，应为 'YYYY-MM-DD'，实际为: {target_date}")
    elif isinstance(target_date, datetime):
        # datetime对象，只取日期部分
        query_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise TypeError(f"不支持的日期类型: {type(target_date)}")
    
    # 计算时间范围（该日期的 00:00:00 到 23:59:59）
    start_time = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = query_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    date_str = query_date.strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"🗑️  删除日期: {date_str}")
    print(f"   时间范围: {start_time:%Y-%m-%d %H:%M:%S} ~ {end_time:%Y-%m-%d %H:%M:%S}")
    print(f"{'='*60}\n")
    
    results = {
        "date": date_str,
        "hotline_deleted": 0,
        "replacement_deleted": 0,
        "total_deleted": 0
    }
    
    # 删除热线受理数据
    if delete_hotline:
        print("\n" + "="*60)
        print("🗑️  删除热线受理数据")
        print("="*60)
        deleted, errors = delete_by_date_range(
            start_date=start_time,
            end_date=end_time,
            record_type="record_1Z80y__c"
        )
        results["hotline_deleted"] = deleted
    
    # 删除替换发货数据
    if delete_replacement:
        print("\n" + "="*60)
        print("🗑️  删除替换发货数据")
        print("="*60)
        deleted, errors = delete_by_date_range(
            start_date=start_time,
            end_date=end_time,
            record_type="default__c"
        )
        results["replacement_deleted"] = deleted
    
    results["total_deleted"] = results["hotline_deleted"] + results["replacement_deleted"]
    
    # 显示删除结果摘要
    print("\n" + "="*60)
    print("📊 删除结果摘要")
    print("="*60)
    print(f"📞 热线受理: 删除 {results['hotline_deleted']} 条")
    print(f"📦 替换发货: 删除 {results['replacement_deleted']} 条")
    print(f"📋 总计: 删除 {results['total_deleted']} 条")
    print("="*60)
    
    return results


def query_by_date(target_date: Optional[datetime] = None, 
                  save_files: bool = True,
                  query_hotline: bool = True,
                  query_replacement: bool = True,
                  import_to_db: bool = False,
                  skip_duplicates: bool = True) -> Dict[str, Any]:
    """
    按指定日期查询工单数据（自动分页获取所有数据）
    
    Args:
        target_date: 目标日期，可以是datetime对象或None（None表示昨天）
                    也可以传入字符串格式 "YYYY-MM-DD"
        save_files: 是否保存为JSON文件（默认True）
        query_hotline: 是否查询热线受理数据（默认True）
        query_replacement: 是否查询替换发货数据（默认True）
        import_to_db: 是否导入到数据库（默认False）
        skip_duplicates: 导入数据库时是否跳过重复记录（默认True）
    
    Returns:
        包含查询结果的字典:
        {
            "hotline": 热线受理查询结果,
            "replacement": 替换发货查询结果,
            "date": 查询的日期字符串,
            "hotline_import": 热线受理导入统计 (inserted, skipped, errors),
            "replacement_import": 替换发货导入统计 (inserted, skipped, errors)
        }
    
    Example:
        # 查询昨天的数据
        results = query_by_date()
        
        # 查询指定日期的数据并导入数据库
        from datetime import datetime
        date = datetime(2024, 1, 15)
        results = query_by_date(date, import_to_db=True)
        
        # 查询指定日期但不保存文件，只导入数据库
        results = query_by_date(date, save_files=False, import_to_db=True)
        
        # 只查询热线受理数据并导入数据库
        results = query_by_date(date, query_replacement=False, import_to_db=True)
    """
    client = FXiaoKeListQueryClient()
    
    # 处理日期参数
    if target_date is None:
        # 默认查询昨天
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query_date = today_start - timedelta(days=1)
    elif isinstance(target_date, str):
        # 字符串格式 "YYYY-MM-DD"
        try:
            query_date = datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"日期格式错误，应为 'YYYY-MM-DD'，实际为: {target_date}")
    elif isinstance(target_date, datetime):
        # datetime对象，只取日期部分
        query_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise TypeError(f"不支持的日期类型: {type(target_date)}")
    
    # 计算时间范围（该日期的 00:00:00 到 23:59:59）
    start_time = query_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = query_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)
    
    date_str = query_date.strftime("%Y-%m-%d")
    print(f"\n{'='*60}")
    print(f"📅 查询日期: {date_str}")
    print(f"   时间范围: {start_time:%Y-%m-%d %H:%M:%S} ~ {end_time:%Y-%m-%d %H:%M:%S}")
    print(f"   时间戳范围: {start_timestamp} ~ {end_timestamp}")
    print(f"{'='*60}\n")
    
    results = {
        "date": date_str,
        "hotline": None,
        "replacement": None
    }
    
    # 热线受理字段列表
    hotline_fields = [
        "name", "create_time", "owner", "record_type", "field_v24BD__c",
        "field_Utj19__c",  # 问题记录
        "field_0uAwt__c",  # 问题类型
        "field_toFhx__c",  # 问题归类
        "field_iywKQ__c",  # 提报人
        "field_93r62__c",  # 提报人电话
        "field_o1oCe__c",  # 公众号用户
        "field_3ff0E__c",  # 微信昵称
        "field_812NN__c",  # 企微用户/群
        "field_Mc0p7__c",  # 需求来源
        "field_glsb__c",   # 关联设备
        "field_TWcZV__c",  # 备用序号
        "account_id",      # 公司名称
        "field_sZHpO__c",  # 设备类型
        "field_glcp__c",   # 关联产品
        "field_FGMjJ__c",  # 设备名称
    ]
    
    # 替换发货字段列表
    replacement_fields = [
        "name", "create_time", "owner", "record_type", "field_v24BD__c",
        "field_Utj19__c",  # 问题记录
        "field_h017i__c",  # 解决方案
        "field_1H53l__c",  # 现场排查
        "field_3oyKy__c",  # 发货原因
        "field_iywKQ__c",  # 提报人
        "field_93r62__c",  # 提报人电话
        "field_o1oCe__c",  # 公众号用户
        "field_3ff0E__c",  # 微信昵称
        "field_812NN__c",  # 企微用户/群
        "field_Mc0p7__c",  # 需求来源
        "field_glsb__c",   # 关联设备
        "field_TWcZV__c",  # 备用序号
        "account_id",      # 公司名称
        "field_sZHpO__c",  # 设备类型
        "field_glcp__c",   # 关联产品
        "field_FGMjJ__c",  # 设备名称
    ]
    
    # 查询热线受理数据
    if query_hotline:
        print("\n" + "="*60)
        print("📞 查询热线受理数据")
        print("="*60)
        
        hotline_result = client.query_all_pages(
            field_projection=hotline_fields,
            filters=[
                {
                    "operator": "IN",
                    "field_name": "record_type",
                    "field_values": ["record_1Z80y__c"]
                },
                {
                    "operator": "BETWEEN",
                    "field_name": "create_time",
                    "field_values": [start_timestamp, end_timestamp]
                }
            ],
            orders=[{"fieldName": "create_time", "isAsc": False}]
        )
        
        results["hotline"] = hotline_result
        
        if save_files and hotline_result and hotline_result.get("errorCode") == 0:
            filename = f"热线受理_{date_str}.json"
            save_result(hotline_result, filename)
        
        # 导入数据库
        if import_to_db and hotline_result and hotline_result.get("errorCode") == 0:
            print("\n" + "="*60)
            print("💾 导入热线受理数据到数据库")
            print("="*60)
            # 需要先转换为中文字段格式
            hotline_result_cn = hotline_result.copy()
            if hotline_result_cn.get("data", {}).get("dataList"):
                data_list = hotline_result_cn["data"]["dataList"]
                # 如果数据是英文字段（检查第一个记录是否有英文字段），需要转换
                if data_list and len(data_list) > 0:
                    first_item = data_list[0]
                    # 检查是否包含英文字段（如 "name"）而不是中文字段（如 "案例名称"）
                    if "name" in first_item and "案例名称" not in first_item:
                        # 转换为中文字段
                        converted_list = [convert_to_chinese_fields(item, translate_values=True) for item in data_list]
                        hotline_result_cn["data"]["dataList"] = converted_list
            inserted, skipped, errors = import_result_to_db(hotline_result_cn, skip_duplicates=skip_duplicates)
            results["hotline_import"] = (inserted, skipped, errors)
    
    # 查询替换发货数据
    if query_replacement:
        print("\n" + "="*60)
        print("📦 查询替换发货数据")
        print("="*60)
        
        replacement_result = client.query_all_pages(
            field_projection=replacement_fields,
            filters=[
                {
                    "operator": "IN",
                    "field_name": "record_type",
                    "field_values": ["default__c"]
                },
                {
                    "operator": "BETWEEN",
                    "field_name": "create_time",
                    "field_values": [start_timestamp, end_timestamp]
                },
                {
                    "operator": "N",
                    "field_name": "field_v24BD__c",
                    "field_values": ["5S0abGR2n"]
                },
                {
                    "operator": "N",
                    "field_name": "field_v24BD__c",
                    "field_values": ["3pmDO0ar2"]
                }
            ],
            orders=[{"fieldName": "create_time", "isAsc": False}]
        )
        
        results["replacement"] = replacement_result
        
        if save_files and replacement_result and replacement_result.get("errorCode") == 0:
            filename = f"替换发货_{date_str}.json"
            save_result(replacement_result, filename)
        
        # 导入数据库
        if import_to_db and replacement_result and replacement_result.get("errorCode") == 0:
            print("\n" + "="*60)
            print("💾 导入替换发货数据到数据库")
            print("="*60)
            # 需要先转换为中文字段格式
            replacement_result_cn = replacement_result.copy()
            if replacement_result_cn.get("data", {}).get("dataList"):
                data_list = replacement_result_cn["data"]["dataList"]
                # 如果数据是英文字段（检查第一个记录是否有英文字段），需要转换
                if data_list and len(data_list) > 0:
                    first_item = data_list[0]
                    # 检查是否包含英文字段（如 "name"）而不是中文字段（如 "案例名称"）
                    if "name" in first_item and "案例名称" not in first_item:
                        # 转换为中文字段
                        converted_list = [convert_to_chinese_fields(item, translate_values=True) for item in data_list]
                        replacement_result_cn["data"]["dataList"] = converted_list
            inserted, skipped, errors = import_result_to_db(replacement_result_cn, skip_duplicates=skip_duplicates)
            results["replacement_import"] = (inserted, skipped, errors)
    
    return results


def main():
    """主函数 - 核心数据导出流程（查询昨天的数据）"""
    print("=== 纷享销客工单导出 ===")
    
    # 使用新的按日期查询接口，查询昨天的数据
    # 可以通过修改 import_to_db=True 来启用数据库导入
    results = query_by_date(import_to_db=True, skip_duplicates=True)
    
    # 显示查询结果摘要
    print("\n" + "="*60)
    print("📊 查询结果摘要")
    print("="*60)
    
    if results["hotline"]:
        hotline_data = results["hotline"].get("data", {})
        hotline_count = len(hotline_data.get("dataList", []))
        print(f"📞 热线受理: {hotline_count} 条")
        if "hotline_import" in results:
            inserted, skipped, errors = results["hotline_import"]
            print(f"   💾 数据库导入: 成功 {inserted} 条, 跳过 {skipped} 条, 错误 {errors} 条")
    
    if results["replacement"]:
        replacement_data = results["replacement"].get("data", {})
        replacement_count = len(replacement_data.get("dataList", []))
        print(f"📦 替换发货: {replacement_count} 条")
        if "replacement_import" in results:
            inserted, skipped, errors = results["replacement_import"]
            print(f"   💾 数据库导入: 成功 {inserted} 条, 跳过 {skipped} 条, 错误 {errors} 条")
    
    print("="*60)


def translate_field_values(field_name: str, field_value: Any) -> Any:
    """将字段的编码值转换为可读的中文描述
    
    Args:
        field_name: 字段名称（英文或中文）
        field_value: 字段值
    
    Returns:
        转换后的值，如果没有匹配的转换规则则返回原值
    """
    # 字段值转换映射表
    value_mapping = {
        # 问题类型 (field_0uAwt__c / 问题类型)
        "问题类型": {
            "option1": "设备问题",
            "u4A1sg3pL": "远程调参",
            "2of5lS6RA": "备件请求",
            "l18y3b5Z2": "其他",
        },
        # 需求来源 (field_Mc0p7__c / 需求来源)
        "需求来源": {
            "67NYnAQ8s": "400电话",
            "8I80aKGOd": "微信公众号",
            "Awar33KQB": "企业微信",
        },
        "业务类型" : {
            "default__c": "替换发货",
            "record_1Z80y__c": "热线受理",
        },
        "问题归类" : {
            "gwAKRjO83": "IN00-设备不发电",
            "R65m0a5pd": "IN01-面板问题",
            "9Qj608BYn": "IN02-交流端子问题",
            "2webwy3Q4": "IN03-直流端子问题",
            "JNP2Ev52U": "IN04-直流开关问题",
            "g3uuoX4D8": "IN05-通讯端子问题",
            "8fte1zMKe": "IN06-风扇问题",
            "jXrljT11T": "IN07-影响其它设备运行",
            "152lEbubo": "IN08-发电效率低问题",
            "JKb9jxtvi": "IN09-噪音",
            "bpzlos1sR": "IN10-一路MPPT不工作",
            "4bs2s4Tu8": "IN11-设备数据不正常",
            "5p3YU3Uj0": "IN12-设备无法被监控",
            "x5iNH2r5s": "IN13-设备信息不正确（DSP内部信息）",
            "tItxpm1jd": "IN14-设备无法调整参数",
            "DPsrdh3gm": "IN15-设备进水",
            "l55Btf6d3": "IN16-设备烧毁",
            "8t2J3GQmc": "IN17-生产端问题",
            "ud21m12kO": "MO01-采集器宕机（指示灯全不亮）",
            "uiv1etgAN": "MO02-采集不到设备数据",
            "DHZexs6qv": "MO03-数据传输不到服务器（连接基站、路由失败等）",
            "maNE92ofp": "MO04-现场信号值弱",
            "E218v5Fsm": "MO05-内网配置失败或无法调整参数",
            "gu8ub74kD": "MO06-采集器影响其它设备正常工作",
            "Hj1tq43K3": "MO07-设备进水",
            "s1p2ObsiF": "MO08-升级引起的问题（软件问题等）",
            "DGrlqDsRU": "MO09-设备信息不正确（内部读取信息）",
            "a2DTJhhM2": "MO10-生产端问题",
            "DFca56n49": "MO11-流量（销号）问题",
            "2wTm17gNM": "MO12-硬件问题（版本退回）",
            "xzY1cIpgc": "ME01-烧毁",
            "2o1yv5FKx": "ME02-无法与设备通讯",
            "2lqeBKfeg": "ME03-显示数据异常",
            "9jJxSiyhT": "EV01-设备不工作",
            "e87AoItG4": "EV-02噪音",
            "FV4wjQAsN": "EV03-无法被监控",
            "0u6xHY643": "N/A",
            "wjhBN23lM": "E00：通讯故障",
            "WKjJx9od9": "E01：主副CPU通讯失败",
            "08PUs51i2": "E02：EEPROM读写失败",
            "TU29701qy": "E03：继电器检测失败",
            "4I3u6qamf": "E04：直流电流分量注入过高",
            "2l0aoG661": "E05：自检失败",
            "Seqo7CQ1J": "E06：直流母线电压过高",
            "kdsEqTPr2": "E07：内部参考电压异常",
            "3d1krGMk6": "E08：AC侧电流传感器失效",
            "k53y7NAGo": "E09：残余电流检测设备失效",
            "h7lsy704Z": "E10：设备故障",
            "k3l5xJ2Tj": "E11：主副CPU软件版本号不匹配",
            "z9dG2t5cd": "E32：频率变化率异常",
            "Is7ognj8R": "E33：AC侧频率超范围",
            "p1D42UEmW": "E34：AC侧电压超范围",
            "Of2VGu9il": "E35：电网丢失",
            "zDj7RlQa4": "E36：残余电流检测失败",
            "DUn2O0lfU": "E37：PV侧过压",
            "2Fhgrm7j8": "E38：绝缘阻抗检测失败",
            "Ttm9Od6Gi": "E40：逆变器过温",
            "ps52m95VU": "E41：主副CPU AC侧电压采样不一致",
            "Lsty55kcQ": "E42：主副CPU AC侧频率采样不一致",
            "71nV8OjdK": "E43：主副CPU 接地电流采样不一致",
            "PuL5b7fO3": "E44：主副CPU直流电流注入值采样不一致",
            "6JKdtnqpr": "E45：主副CPU AC侧频率、电压值采样不一致",
            "Oi2JiVH43": "E46：直流母线电压高",
            "N3G13qunm": "E47：主副一致性故障",
            "524a6sJvH": "E48：十分钟电压平均值过压",
            "1mfnDr8Ba": "E49：PV1防雷器故障",
            "2Jep97rQ0": "E50：PV2防雷器故障",
            "lDWc067pC": "E51：保险丝故障",
            "R0vl2ncFp": "E52：N线丢失故障",
            "b614TfX00": "E53：绝缘阻抗检测：在使能恒流源之前，绝缘阻抗测量电压采样值大于300mv",
            "sIKy57z26": "E54：绝缘阻抗检测：在使能恒流源之后，绝缘阻抗检测测量电压采样值超出范围(1.37v+/-20%)",
            "v110spApp": "E55：绝缘阻抗检测：N-PE继电器切换，绝缘阻抗检测检测测量电压瞬时值小于40mv",
            "rkft1ig4q": "E56：GFCI保护错误：30毫安等级",
            "InBy18p2q": "E57：GFCI保护错误：60毫安等级",
            "XhklBNwq1": "E58：GFCI保护错误：150毫安等级",
            "g3IlmxEP1": "E59：PV1组串电流异常",
            "51141ws5S": "E60：PV2组串电流异常",
            "2JC2s041U": "E61：DRMS 通讯失败(S9 Open)",
            "pllji6fLz": "E62：DRMS 设备断开(S0 Close)",
            "M9z86Dd4y": "E63：L-PE短路保护错误",
            "sXM5cR1Rl": "E64：PV输入模式错误",
            "g66JQG9BL": "E65：地线连接错误",
            "Mf1Ea1hQe": "E66：PV1反接故障",
            "M470AcY50": "E67：PV2反接故障",
            "ocbOeoHa0": "E68：PV3反接故障",
            "m2Hl8MJVa": "E69：外部输入故障",
            "YA96fh6Bx": "E70：AFCI自检失败",
            "zvqjkQ6jj": "E71：AFCI故障",
            "wqtl7IhGh": "W0：无警告",
            "FdgKV952c": "W30：从警告中恢复",
            "bmk1wmBYV": "W31：PV1输入电压过压",
            "j2n4Wm4Wl": "W32：PV2输入电压过压",
            "kBkC2U1oh": "W33：PV3输入电压过压",
            "sW76XdwfK": "W34：PV1输入电流软件测量过流",
            "II1u5hW35": "W35：PV1输入电流硬件测量过流",
            "iqj6qTDUj": "W36：PV2输入电流软件测量过流",
            "V2SGmAiF6": "W37：PV2输入电流硬件测量过流",
            "8U551IwJ9": "W38：PV3输入电流软件测量过流",
            "0232V150Z": "W39：PV3输入电流硬件测量过流",
            "31hQftas9": "W40：直流母线软件测量过压",
            "mC22fky63": "W41：直流母线硬件测量过压",
            "TqS74ziFL": "W42：直流母线电压不平衡",
            "thzlfX4SX": "W43：电压电压持续十分钟过压（超过额定电压的110%）",
            "U7N5Vu8hI": "W44：电网电压瞬时值过压",
            "34S026Nrx": "W45：输出电流软件测量过流",
            "2j821dLUc": "W46：输出电流硬件测量过流",
            "FdgKV952c": "W47：发生反孤岛",
            "WiwV0cc14": "W48：发生低电压穿越",
            "47D20s6mn": "W49：电网频率过高导致输出功率降低",
            "Gm0Y1w7aN": "W50：温度过高导致输出功率降低",
            "kLCt6Y1yc": "W51：输入限流导致输出输出功率降低",
            "4B51rV1l1": "W52：输出限流导致输出功率降低",
            "cEGc62o1c": "W53：温度过低",
            "g1Ao883h6": "W54：数据存储Flash异常",
            "c5A1Esxxc": "W55：R相异常",
            "YSj7M2avg": "W56：S相异常",
            "zp7eccwmS": "W57：相异常",
            "HRs2ibvjS": "W58：风扇异常",
            "LE9toK2Px": "W59：控制板温度过高",
            "idLnke951": "W60：外部风扇1异常",
            "00elk8ik8": "W61：外部风扇2异常",
            "0Iq8o7Tcm": "W70：电池电流高（软件保护）",
            "9ogzk1N11": "W71：DAB高压侧电流高（软件保护）",
            "K19p062bd": "W72：电池电流高（硬件保护）",
            "92C9u5wd9": "W73：DAB高压侧电流高（硬件保护）",
            "dOwq2eXeU": "W74：EPS电流高（硬件保护）",
            "yNV24eByf": "W75：电池电压高（软件保护）",
            "7yh777t7x": "W76：EPS电流超出范围（软件保护）",
            "7C4YAsozy": "W77：电池处于警告状态",
            "gOsF16PgU": "W78：PV电压与电池电压均低",
            "3vn6hp5Sr": "W79：PV启动过压",
            "Iv37ly1kw": "W80：电网电压过高导致输出功率降低",
            "OiC3eO1D3": "W141：PV4输入电压过压",
            "1Qnzhg10l": "W142：PV5输入电压过压",
            "Qz857zc91": "W143：PV6输入电压过压",
            "s6DSBk9xK": "W144：PV4输入电流软件测量过流",
            "7fvofl816": "W145：PV4输入电流硬件测量过流",
            "otkE2rU4o": "W146：PV5输入电流软件测量过流",
            "621c6PegH": "W147：PV5输入电流硬件测量过流",
            "f8O2wL6Ka": "W148：PV6输入电流软件测量过流",
            "m082iuEyR": "W149：PV6输入电流硬件测量过流",
            "mJf2J21C0": "W150：SPD损坏",
            "t2G1ra2y9": "W156：内部风扇异常",
            "VD7Wqaft1": "W157：外部风扇1异常",
            "Oj6E12i2W": "W158：外部风扇2异常",
            "1jssn24kc": "W161：保险丝异常",
            "982h3iGcN": "W163：PV组串异常",
            "tcWr9A1GN": "W165：接地连接异常警告",
            "6467EoPz4": "W166：CPU自检-寄存器异常",
            "8c72uN4z6": "W167：CPU自检-RAM异常",
            "NECD5Tyo3": "W168：CPU自检-ROM异常",
            "wh35hMwfC": "W169：电网电压变量值冗余校验异常",
            "r0FiVfHu1": "W170：电网频率变量值冗余校验异常",
            "Bw2y16gpm": "W171：DCI变量值冗余校验异常",
            "olh876u8d": "W172：GFCl 变量值冗余校验异常",
            "ry624LT5d": "W173：AID变量值冗余校验异常",
            "LtEV9WrqW": "W174：温度过低",
            "gvVOR1M2n": "W175：电池SOC低",
            "VN23xVtxz": "W176：电池发生故障",
            "177dY0Ff7": "W177：电池通讯断开",
            "iMV0r2B28": "W178：EPS输出过载",
            "Mp2Sfa7hz": "W179：Combox与Cloud连接断开",
            "x4ziZ2a31": "W180：PV组串反接",
            "KP4e95Eb5": "Error GND — Bad Grounding",
            "O7kyw792g": "Error ES — Emergency Stop",
            "LofG5Ph6S": "Error CP — Charging CP signal error",
            "sOBAchi1s": "Error OC — Over Current",
            "Ufu19kLi6": "Error OV — Over Voltage",
            "zl59HMdc5": "Error UV —  Under Voltage",
            "uj9gn3v3O": "Error OT — Over Temperature",
            "71s3RR6Pd": "Error LC — Leakage Current",
            "o0t9jf65i": "Error 02 — Electric lock failure.",
            "p03424RTW": "Error 04 —WIFI module failure",
            "5174zEaMk": "Error 06 — RFID module failure",
            "W2cjiCQmc": "Error 08 — Control board failure",
            "q1wSGotz5": "Error 11 — Control board failure",
            "3nrPDieg9": "Error 12 — Control board failure",
            "L4iObl281": "Error 13 — Control board failure",
            "64vh1mduz": "Error 14 — Charging CP signal error",
            "l6ur3vE5a": "Error 15 — Relay Failure",
            "d3yn2RA": "Error 16 — Leakage current",
        },
        "发货原因" : {  
            "option1": "故障更换",
            "faJp9612f": "配件更换",
            "24cj08J1c": "操作不当",
            "U6YSjleKD": "换机测试",
            "vf5rqTm82": "重新换货",
            "v4zl29995": "货损缺失",
            "k2SP2op5C": "生产制程",
            "r9ocd8oKb": "初装故障",
            "R3c2C2G60": "维修制程",
            "zMGy0lj6I": "备件申请",
            "Ut29Wb1vP": "返厂维修",
            "I1gKZyoY5": "其它",
            "19ZTV20Wc": "服务销售",
            "2E01gMkf3": "确认抵扣",
            "e7G1Zr6hs": "陕西电科院",
            "e0eb8h7E1": "无效工单",
            "SqexnfUsC": "主动运维",
        },
        # 可以继续添加其他字段的映射规则
        # 例如：
        # "field_xxx__c": {
        #     "code1": "中文描述1",
        #     "code2": "中文描述2",
        # },
    }
    
    # 如果字段有转换规则
    if field_name in value_mapping:
        field_map = value_mapping[field_name]
        # 如果值在映射表中，返回转换后的值
        if field_value in field_map:
            return field_map[field_value]
    
    # 如果没有匹配的转换规则，返回原值
    return field_value


FIELD_DISPLAY_RULES = [
    ("name", "案例名称"),
    ("create_time", "创建时间"),
    ("owner", "负责人ID"),
    ("record_type", "业务类型"),
    ("field_v24BD__c", "工单状态"),
    ("field_Utj19__c", "问题记录"),
    ("field_0uAwt__c", "问题类型"),
    ("field_toFhx__c", "问题归类"),
    ("field_iywKQ__c", "提报人"),
    ("field_93r62__c", "提报人电话"),
    ("field_o1oCe__c", "公众号用户"),
    ("field_3ff0E__c", "微信昵称"),
    ("field_812NN__c", "企微用户/群"),
    ("field_Mc0p7__c", "需求来源"),
    ("field_glsb__c", "关联设备"),
    ("field_TWcZV__c", "备用序号"),
    ("account_id", "公司名称"),
    ("field_sZHpO__c", "设备类型"),
    ("field_glcp__c", "关联产品"),
    ("field_FGMjJ__c", "设备名称"),
    ("field_wJsp4__c", "机型分类"),
    ("field_qT1uy__c", "质保期至"),
    ("field_7jD1u__c", "辅助属性"),
    ("field_h017i__c", "解决方案"),
    ("field_1H53l__c", "现场排查"),
    ("field_3oyKy__c", "发货原因"),
]

FIELD_DISPLAY_DICT = dict(FIELD_DISPLAY_RULES)


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple, set)):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def _format_field_value(field_name: str,
                        value: Any,
                        cn_field: Optional[str] = None,
                        translate_values: bool = True) -> Any:
    """格式化字段值：时间转换、列表拼接、描述映射"""
    if value is None:
        return None
    
    formatted_value = value
    
    # 时间戳 -> 人类可读
    if field_name == "create_time" and isinstance(formatted_value, (int, float)):
        try:
            formatted_value = datetime.fromtimestamp(formatted_value / 1000).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
    
    # 处理列表，过滤空值并拼接
    if isinstance(formatted_value, list):
        processed_items = []
        for item in formatted_value:
            if _is_empty_value(item):
                continue
            processed_item = item
            if translate_values:
                processed_item = translate_field_values(cn_field or field_name, processed_item)
                if processed_item == item and cn_field:
                    processed_item = translate_field_values(field_name, processed_item)
            if not _is_empty_value(processed_item):
                processed_items.append(str(processed_item))
        if not processed_items:
            return None
        formatted_value = ", ".join(processed_items)
    else:
        # 普通值的描述映射
        if translate_values and not _is_empty_value(formatted_value):
            translated_value = translate_field_values(cn_field or field_name, formatted_value)
            if translated_value == formatted_value and cn_field:
                translated_value = translate_field_values(field_name, formatted_value)
            formatted_value = translated_value
    
    if isinstance(formatted_value, str):
        formatted_value = formatted_value.strip()
    
    return formatted_value


def convert_to_chinese_fields(data_item: Dict, use_grouping: bool = False, translate_values: bool = True) -> Dict:
    """将API字段转换为中文字段名，并按指定顺序排列
    
    Args:
        data_item: 原始数据项（包含英文字段名）
        use_grouping: 是否按业务逻辑分组（默认False）
        translate_values: 是否转换字段值为中文（默认True）
    
    Returns:
        转换后的数据项（中文字段名，按顺序排列或分组）
    """
    converted_item = {}
    
    for en_field, cn_field in FIELD_DISPLAY_RULES:
        if en_field not in data_item:
            continue
        
        value = _format_field_value(
            en_field,
            data_item[en_field],
            cn_field if translate_values else None,
            translate_values=translate_values
        )
        
        if _is_empty_value(value):
            continue
        
        converted_item[cn_field] = value
    
    return converted_item


def save_result(result: Dict, filename: str, use_chinese_fields: bool = True, use_grouping: bool = False, translate_values: bool = True):
    """保存查询结果到JSON文件
    
    Args:
        result: API返回的结果
        filename: 保存的文件名
        use_chinese_fields: 是否使用中文字段名（默认True）
        use_grouping: 是否按业务逻辑分组（默认False）
        translate_values: 是否转换字段值为中文（默认True）
    """
    save_data = result.copy()
    if use_chinese_fields and result.get("errorCode") == 0:
        data = result.get("data", {})
        data_list = data.get("dataList", [])
        
        if data_list:
            # 转换dataList中的每个数据项
            converted_list = [convert_to_chinese_fields(item, use_grouping=use_grouping, translate_values=translate_values) for item in data_list]
            
            # 保持原始结构，只替换dataList
            save_data = {
                "traceId": result.get("traceId", ""),
                "data": {
                    "dataList": converted_list,
                    "offset": data.get("offset", 0),
                    "limit": data.get("limit", 0),
                    "total": data.get("total", 0)
                },
                "errorDescription": result.get("errorDescription", ""),
                "errorMessage": result.get("errorMessage", ""),
                "errorCode": result.get("errorCode", 0)
            }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    print(f"  💾 结果已保存: {filename}")
    
    # 显示数据摘要
    if result.get("errorCode") == 0:
        data = result.get("data", {})
        data_list = data.get("dataList", [])
        
        if data_list:
            print(f"  📊 数据预览 (共{len(data_list)}条):")
            preview_count = min(3, len(data_list))
            
            for idx in range(preview_count):
                item = data_list[idx]
                # 处理两种数据结构：原始格式和中文字段格式
                name = item.get("案例名称") or item.get("name", "N/A")
                print(f"\n     [{idx + 1}] {name}")
                
                # 显示前5个字段
                shown = 0
                for field_key, field_value in item.items():
                    if field_key in ["name", "案例名称"]:
                        continue
                    if field_value in [None, "", [], {}]:
                        continue
                    display_name = FIELD_DISPLAY_DICT.get(field_key, field_key)
                    print(f"         {display_name}: {field_value}")
                    shown += 1
                    if shown >= 5:
                        break
            
            if len(data_list) > 3:
                print(f"\n     ... 还有 {len(data_list) - 3} 条记录")


if __name__ == "__main__":
    main()
