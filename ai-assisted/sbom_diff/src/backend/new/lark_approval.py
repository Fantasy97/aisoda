import json
import os
import sys
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from requests_toolbelt import MultipartEncoder
import requests

import lark_oapi as lark

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入数据库连接模块（参考 multi_excel_processor.py）
tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools'))
project_root = Path(__file__).resolve().parents[3]  # src/backend/new -> 项目根目录
tools_path_abs = os.path.join(str(project_root), 'src', 'backend', 'tools')

for path in [tools_path, tools_path_abs]:
    if path not in sys.path and os.path.exists(path):
        sys.path.insert(0, path)
        logger.debug(f"已添加路径到 sys.path: {path}")

try:
    from db_query import get_connection
    logger.info(f"成功导入 db_query 模块")
except ImportError as e:
    logger.error(f"无法导入 db_query 模块: {e}")
    def get_connection():
        logger.warning("数据库连接模块未找到，将跳过数据库保存")
        return None
from lark_oapi.api.approval.v4 import (
    GetInstanceRequest,
    GetInstanceResponse,
    QueryInstanceRequest,
    QueryInstanceResponse,
    InstanceSearch,
    CreateInstanceRequest,
    CreateInstanceResponse,
    InstanceCreate,
    CreateInstanceCommentRequest,
    CreateInstanceCommentResponse,
    CommentRequest,
)

# 飞书登录配置
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', 'cli_a867431a582b500c')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', 'Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj')
FEISHU_API_BASE = 'https://open.feishu.cn/open-apis'

# 飞书登录辅助函数
def get_app_access_token():
    """获取应用访问令牌"""
    url = f'{FEISHU_API_BASE}/auth/v3/app_access_token/internal'
    data = {'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET}
    result = requests.post(url, json=data).json()
    if result.get('code') == 0:
        return result.get('app_access_token')
    raise Exception(f"获取令牌失败: {result}")

def get_user_access_token(code):
    """使用授权码获取用户访问令牌"""
    app_token = get_app_access_token()
    url = f'{FEISHU_API_BASE}/authen/v1/oidc/access_token'
    headers = {'Authorization': f'Bearer {app_token}'}
    data = {'grant_type': 'authorization_code', 'code': code}
    result = requests.post(url, json=data, headers=headers).json()
    if result.get('code') == 0:
        return result.get('data')
    raise Exception(f"获取用户令牌失败: {result}")

def get_user_info(user_token):
    """获取用户信息"""
    url = f'{FEISHU_API_BASE}/authen/v1/user_info'
    headers = {'Authorization': f'Bearer {user_token}'}
    result = requests.get(url, headers=headers).json()
    if result.get('code') == 0:
        return result.get('data')
    raise Exception(f"获取用户信息失败: {result}")


def upload_approval_file(file_path: str, file_type: str = "attachment") -> Dict[str, Any]:
    """上传文件到飞书审批系统
    
    Args:
        file_path: 文件的绝对路径
        file_type: 文件类型，"image"（图片）或 "attachment"（附件）
        
    Returns:
        返回字典包含:
        - success: bool - 上传是否成功
        - file_code: str | None - 文件标识码（用于表单赋值）
        - file_url: str | None - 文件URL
        - error: dict | None - 错误信息（仅在失败时）
    """
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a867431a582b500c") \
        .app_secret("Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj") \
        .log_level(lark.LogLevel.INFO) \
        .build()

    # 构造请求对象
    file = open(file_path, "rb")
    file_name = os.path.basename(file_path)
    data = {
        "name": file_name,
        "type": file_type,
        "content": (file_name, file, "")
    }
    body = MultipartEncoder(lark.Files.parse_form_data(data))

    request: lark.BaseRequest = (
        lark.BaseRequest.builder()
        .http_method(lark.HttpMethod.POST)
        .uri("/approval/openapi/v2/file/upload")
        .headers({"Content-Type": body.content_type})
        .token_types({lark.AccessTokenType.TENANT})
        .body(body)
        .build()
    )

    # 发起请求
    response: lark.BaseResponse = client.request(request)

    # 处理失败返回
    if not response.success():
        return {
            "success": False,
            "file_code": None,
            "file_url": None,
            "error": {
                "code": response.code,
                "msg": response.msg,
                "log_id": response.get_log_id()
            }
        }

    # 处理业务结果
    response_data = json.loads(str(response.raw.content, lark.UTF_8))
    
    # 检查响应状态
    if response_data.get("code") != 0:
        return {
            "success": False,
            "file_code": None,
            "file_url": None,
            "error": {
                "code": response_data.get("code"),
                "msg": response_data.get("msg", "上传失败"),
                "log_id": None
            }
        }
    
    # 提取文件code和url
    data = response_data.get("data", {})
    file_code = data.get("code")
    file_url = data.get("url")
    
    # 关闭文件
    file.close()
    
    return {
        "success": True,
        "file_code": file_code,
        "file_url": file_url,
        "error": None
    }


def get_instance_status_and_form(instance_id: str) -> Dict[str, Any]:
    """根据instance_id查询审批实例的status和form字段,usr_id
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        返回字典包含:
        - success: bool - 请求是否成功
        - status: str | None - 审批状态 (如 "APPROVED", "PENDING" 等)
        - form: str | None - 表单内容 (JSON字符串格式)
        - user_id: str | None - 用户ID
        - error: dict | None - 错误信息 (仅在失败时)
    """
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a867431a582b500c") \
        .app_secret("Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj") \
        .log_level(lark.LogLevel.INFO) \
        .build()

    # 构造请求对象
    request: GetInstanceRequest = GetInstanceRequest.builder() \
        .instance_id(instance_id) \
        .build()

    # 发起请求
    response: GetInstanceResponse = client.approval.v4.instance.get(request)

    # 处理失败返回
    if not response.success():
        error_detail = {
            "code": response.code,
            "msg": response.msg,
            "log_id": response.get_log_id(),
        }
        try:
            error_detail["resp"] = json.loads(response.raw.content)
        except Exception:
            error_detail["resp"] = None
            
        return {
            "success": False,
            "status": None,
            "form": None,
            "error": error_detail
        }

    # 处理业务结果 - 解析response.data获取status和form,usr_id
    try:
        data_dict = json.loads(lark.JSON.marshal(response.data))
        status = data_dict.get("status")
        form = data_dict.get("form")
        user_id = data_dict.get("user_id")
        task_list = data_dict.get("task_list")
        timeline = data_dict.get("timeline")
        
        return {
            "success": True,
            "status": status,
            "form": form,
            "user_id": user_id,
            "task_list": task_list,
            "timeline": timeline,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "status": None,
            "form": None,
            "error": {
                "code": "PARSE_ERROR",
                "msg": f"解析响应数据失败: {str(e)}",
                "log_id": None
            }
        }


def check_and_update_pending_approvals() -> Dict[str, Any]:
    """查询并更新PENDING状态的审批实例,返回所有APPROVED的design_id
    
    功能说明:
    1. 查询sbom_feishu_approval表中所有feishu_status为PENDING的记录（不限制用户ID）
    2. 调用飞书API查询每个实例的最新状态
    3. 更新数据库中的feishu_status
    4. 返回所有状态为APPROVED的design_id
    
    Returns:
        返回字典包含:
        - success: bool - 整体操作是否成功
        - total_pending: int - 待处理的审批数量
        - checked_count: int - 成功检查的审批数量
        - updated_count: int - 成功更新的审批数量
        - approved_design_ids: List[int] - 所有APPROVED状态的design_id列表
        - details: List[dict] - 每个审批实例的处理详情
        - error: str | None - 错误信息(仅在失败时)
    """
    connection = None
    
    try:
        # 获取数据库连接
        connection = get_connection()
        if not connection:
            logger.error("数据库连接失败")
            return {
                "success": False,
                "total_pending": 0,
                "checked_count": 0,
                "updated_count": 0,
                "approved_design_ids": [],
                "details": [],
                "error": "数据库连接失败"
            }
        
        # 查询所有PENDING状态的审批实例（不限制用户ID）
        with connection.cursor() as cursor:
            query_sql = """
            SELECT id, instance_code, design_id, feishu_status
            FROM sbom_feishu_approval
            WHERE feishu_status = 'PENDING' AND deleted = '0'
            ORDER BY create_time DESC
            """
            cursor.execute(query_sql)
            pending_records = cursor.fetchall()
            
            total_pending = len(pending_records)
            logger.info(f"找到 {total_pending} 条PENDING状态的审批记录（所有用户）")
            
            if total_pending == 0:
                return {
                    "success": True,
                    "total_pending": 0,
                    "checked_count": 0,
                    "updated_count": 0,
                    "approved_design_ids": [],
                    "details": [],
                    "error": None
                }
        
        # 检查和更新每个实例的状态
        checked_count = 0
        updated_count = 0
        approved_design_ids = []
        details = []
        
        for record in pending_records:
            record_id = record[0]
            instance_code = record[1]
            design_id = record[2]
            old_status = record[3]
            
            logger.info(f"正在检查审批实例: instance_code={instance_code}, design_id={design_id}")
            
            # 调用飞书API查询实例状态
            result = get_instance_status_and_form(instance_code)
            
            detail = {
                "id": record_id,
                "instance_code": instance_code,
                "design_id": design_id,
                "old_status": old_status,
                "new_status": None,
                "updated": False,
                "error": None
            }
            
            if not result["success"]:
                # API调用失败
                error_msg = result.get("error", {}).get("msg", "未知错误")
                logger.warning(f"查询审批状态失败: instance_code={instance_code}, error={error_msg}")
                detail["error"] = error_msg
                details.append(detail)
                continue
            
            checked_count += 1
            new_status = result["status"]
            detail["new_status"] = new_status
            
            # 如果新状态是APPROVED,直接添加到返回列表,不更新数据库
            if new_status == "APPROVED":
                if design_id:
                    approved_design_ids.append(design_id)
                    logger.info(f"发现已批准的审批: design_id={design_id}")
                logger.info(f"状态为APPROVED,跳过数据库更新: instance_code={instance_code}")
            # 如果状态发生变化且不是APPROVED,更新数据库
            elif new_status and new_status != old_status:
                try:
                    with connection.cursor() as cursor:
                        update_sql = """
                        UPDATE sbom_feishu_approval
                        SET feishu_status = %s, sbom_status = %s, update_time = %s
                        WHERE id = %s
                        """
                        now = datetime.now()  # 使用 datetime 对象而不是字符串
                        sbom_status = "DISCARDED"  # 审批状态变化（非APPROVED）时，设置sbom_status为DISCARDED
                        cursor.execute(update_sql, (new_status, sbom_status, now, record_id))
                        
                        # 如果存在design_id，同时更新sbom_design表的design_status
                        if design_id:
                            try:
                                update_design_sql = """
                                    UPDATE sbom_design 
                                    SET design_status = %s, 
                                        update_time = %s
                                    WHERE design_id = %s
                                """
                                cursor.execute(update_design_sql, (sbom_status, now, design_id))
                                design_update_rows = cursor.rowcount
                                if design_update_rows > 0:
                                    logger.info(f"已更新 sbom_design 表: design_id={design_id}, design_status={sbom_status}")
                                else:
                                    logger.warning(f"未找到匹配的 sbom_design 记录: design_id={design_id}")
                            except Exception as design_update_error:
                                logger.error(f"更新 sbom_design 表失败: design_id={design_id}, error={str(design_update_error)}")
                                # 即使更新sbom_design失败，也不影响主更新操作
                        
                        connection.commit()
                        
                        updated_count += 1
                        detail["updated"] = True
                        logger.info(f"已更新审批状态: id={record_id}, {old_status} -> {new_status}, sbom_status={sbom_status}")
                            
                except Exception as e:
                    logger.error(f"更新数据库失败: id={record_id}, error={str(e)}")
                    detail["error"] = f"数据库更新失败: {str(e)}"
            else:
                # 状态未变化或新状态为空
                logger.info(f"状态未变化: instance_code={instance_code}, status={new_status}")
            
            details.append(detail)
        
        logger.info(f"审批状态检查完成: 总计={total_pending}, 检查={checked_count}, 更新={updated_count}, 已批准={len(approved_design_ids)}")
        
        return {
            "success": True,
            "total_pending": total_pending,
            "checked_count": checked_count,
            "updated_count": updated_count,
            "approved_design_ids": approved_design_ids,
            "details": details,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"检查和更新审批状态时发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return {
            "success": False,
            "total_pending": 0,
            "checked_count": 0,
            "updated_count": 0,
            "approved_design_ids": [],
            "details": [],
            "error": str(e)
        }
    finally:
        if connection:
            try:
                connection.close()
                logger.debug("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {str(e)}")


def _convert_timestamp_to_datetime(timestamp_ms: str) -> Optional[str]:
    """将毫秒时间戳转换为标准时间格式
    
    Args:
        timestamp_ms: 毫秒时间戳字符串
        
    Returns:
        格式化的时间字符串 (YYYY-MM-DD HH:MM:SS) 或 None
    """
    try:
        if not timestamp_ms or timestamp_ms == "0":
            return None
        ts = int(timestamp_ms) / 1000  # 转换为秒
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def get_user_instances(
    user_id: str,
    approval_code: str = "F8804181-ED37-43B3-90CB-6287BC89DA77",
    page_size: int = 10
) -> Dict[str, Any]:
    """根据user_id查询用户的审批实例列表
    
    Args:
        user_id: 用户ID
        approval_code: 审批定义Code (默认为BOM创建审批)
        page_size: 每页返回数量
        
    Returns:
        返回字典包含:
        - success: bool - 请求是否成功
        - count: int - 实例总数
        - instance_list: List[Dict] - 实例列表,每个实例包含:
            - code: str - 实例code
            - title: str - 标题
            - start_time: str - 开始时间 (标准格式)
            - end_time: str | None - 结束时间 (标准格式,未结束则为None)
        - error: dict | None - 错误信息 (仅在失败时)
    """
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a867431a582b500c") \
        .app_secret("Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj") \
        .log_level(lark.LogLevel.INFO) \
        .build()

    # 构造请求对象
    request: QueryInstanceRequest = QueryInstanceRequest.builder() \
        .page_size(page_size) \
        .user_id_type("user_id") \
        .request_body(InstanceSearch.builder()
            .user_id(user_id)
            .approval_code(approval_code)
            .locale("zh-CN")
            .build()) \
        .build()

    # 发起请求
    response: QueryInstanceResponse = client.approval.v4.instance.query(request)

    # 处理失败返回
    if not response.success():
        error_detail = {
            "code": response.code,
            "msg": response.msg,
            "log_id": response.get_log_id(),
        }
        try:
            error_detail["resp"] = json.loads(response.raw.content)
        except Exception:
            error_detail["resp"] = None
            
        return {
            "success": False,
            "count": 0,
            "instance_list": [],
            "error": error_detail
        }

    # 处理业务结果 - 解析response.data
    try:
        data_dict = json.loads(lark.JSON.marshal(response.data))
        count = data_dict.get("count", 0)
        raw_instance_list = data_dict.get("instance_list", [])
        
        # 提取并格式化instance信息
        formatted_instances = []
        for item in raw_instance_list:
            instance = item.get("instance", {})
            if not instance:
                continue
                
            code = instance.get("code", "")
            title = instance.get("title", "")
            start_time_ms = instance.get("start_time", "0")
            end_time_ms = instance.get("end_time", "0")
            
            # 转换时间戳
            start_time = _convert_timestamp_to_datetime(start_time_ms)
            end_time = _convert_timestamp_to_datetime(end_time_ms)
            
            formatted_instances.append({
                "code": code,
                "title": title,
                "start_time": start_time,
                "end_time": end_time
            })
        
        return {
            "success": True,
            "count": count,
            "instance_list": formatted_instances,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "count": 0,
            "instance_list": [],
            "error": {
                "code": "PARSE_ERROR",
                "msg": f"解析响应数据失败: {str(e)}",
                "log_id": None
            }
        }


def create_approval_instance(
    user_id: str,
    value: str,
    value2: str = "test",
    file_path: Optional[str] = None,
    approval_code: str = "F8804181-ED37-43B3-90CB-6287BC89DA77"
) -> Dict[str, Any]:
    """创建审批实例（支持文件上传）
    
    Args:
        user_id: 用户ID
        value: 第一个表单字段的值 (widget17605183653670001)
        value2: 第二个表单字段的值 (widget17610278501620001, 默认为"test")
        file_path: 可选的文件路径，如果提供则先上传文件
        approval_code: 审批定义Code (默认为BOM创建审批)
        
    Returns:
        返回字典包含:
        - success: bool - 请求是否成功
        - instance_code: str | None - 创建的实例code
        - file_code: str | None - 上传的文件code（如果有文件）
        - error: dict | None - 错误信息 (仅在失败时)
    """
    file_code = None
    
    # 如果提供了文件路径，先上传文件
    if file_path:
        upload_result = upload_approval_file(file_path, file_type="attachment")
        
        if not upload_result["success"]:
            return {
                "success": False,
                "instance_code": None,
                "file_code": None,
                "error": upload_result["error"]
            }
        
        file_code = upload_result["file_code"]
    
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a867431a582b500c") \
        .app_secret("Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj") \
        .log_level(lark.LogLevel.INFO) \
        .build()

    # 构造表单数据 - 包含两个字段
    form_fields = [
        {
            "id": "widget17605183653670001",
            "type": "input",
            "value": value
        },
        {
            "id": "widget17610278501620001",
            "type": "input",
            "value": value2
        }
    ]
    
    # 如果有文件，添加附件字段
    if file_code:
        form_fields.append({
            "id": "widget17611037016100001",  # BOM审批附件控件ID
            "type": "attachmentV2",
            "value": [file_code]
        })
    
    form_data = json.dumps(form_fields, ensure_ascii=False)

    # 构造请求对象
    request: CreateInstanceRequest = CreateInstanceRequest.builder() \
        .request_body(InstanceCreate.builder()
            .approval_code(approval_code)
            .user_id(user_id)
            .form(form_data)
            .build()) \
        .build()

    # 发起请求
    response: CreateInstanceResponse = client.approval.v4.instance.create(request)

    # 处理失败返回
    if not response.success():
        error_detail = {
            "code": response.code,
            "msg": response.msg,
            "log_id": response.get_log_id(),
        }
        try:
            error_detail["resp"] = json.loads(response.raw.content)
        except Exception:
            error_detail["resp"] = None
            
        return {
            "success": False,
            "instance_code": None,
            "file_code": file_code,
            "error": error_detail
        }

    # 处理业务结果 - 解析response.data获取instance_code
    try:
        data_dict = json.loads(lark.JSON.marshal(response.data))
        instance_code = data_dict.get("instance_code")
        
        return {
            "success": True,
            "instance_code": instance_code,
            "file_code": file_code,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "instance_code": None,
            "file_code": file_code,
            "error": {
                "code": "PARSE_ERROR",
                "msg": f"解析响应数据失败: {str(e)}",
                "log_id": None
            }
        }


def _get_design_id_from_result(design_id_str: str) -> Optional[int]:
    """
    根据 design_id 字符串查询 sbom_design 表获取对应的 id
    
    Args:
        design_id_str: design_id 字符串（如 "SBOM_20241103_A1B2C3D4"）
        
    Returns:
        int: sbom_design 表的 id，查询失败返回 None
    """
    if not design_id_str:
        return None
    
    try:
        connection = get_connection()
        if not connection:
            logger.warning("数据库连接失败，无法查询 design_id")
            return None
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM sbom_design WHERE design_id = %s LIMIT 1",
                (design_id_str,)
            )
            result = cursor.fetchone()
            if result:
                design_id_value = result[0]
                logger.info(f"找到关联的 design_id: {design_id_str} -> {design_id_value}")
                return design_id_value
            else:
                logger.warning(f"未找到 design_id 对应的记录: {design_id_str}")
                return None
    except Exception as e:
        logger.error(f"查询 design_id 失败: {e}")
        return None
    finally:
        if 'connection' in locals() and connection:
            try:
                connection.close()
            except:
                pass


def _save_approval_to_database(
    instance_code: str,
    user_id: str,
    approval_code: str,
    form_value1: str,
    form_value2: str,
    file_codes: List[str],
    uploaded_files: List[Dict],
    response_data: Dict,
    design_id: Optional[int] = None,
    design_id_str: Optional[str] = None
) -> Optional[int]:
    """
    保存审批记录到数据库 sbom_feishu_approval 表
    
    Args:
        instance_code: 审批实例code
        user_id: 用户ID
        approval_code: 审批定义code
        form_value1: 表单字段1的值
        form_value2: 表单字段2的值
        file_codes: 上传的文件code列表
        uploaded_files: 上传的文件信息列表
        response_data: 飞书返回的完整响应数据
        design_id: sbom_design 表的 id（可选，用于关联设计记录）
        design_id_str: design_id 字符串（可选，用于生成审批名称）
        
    Returns:
        int: 插入记录的 id，失败返回 None
    """
    logger.info(f"开始保存审批记录到数据库: instance_code={instance_code}, user_id={user_id}")
    
    try:
        connection = get_connection()
        if not connection:
            logger.error("数据库连接失败：get_connection() 返回 None")
            return None
        
        logger.info("数据库连接成功")
        
        import pymysql
        
        # 尝试将 user_id 转换为整数
        try:
            usr_id = int(user_id) if user_id.isdigit() else 1
        except:
            usr_id = 1
        
        # design_id 已经通过参数传入，直接使用
        design_id_value = design_id_str
        
        now = datetime.now()
        
        # 构建审批信息 JSON
        approval_info = {
            "approval_code": approval_code,
            "form_value1": form_value1,
            "form_value2": form_value2,
            "file_count": len(file_codes),
            "uploaded_files": uploaded_files[:10],  # 只保存前10个文件信息，避免JSON过大
            "create_time": datetime.now().isoformat()
        }
        
        # 构建附件信息（文件路径或文件名列表）
        attachment_info = []
        for file_info in uploaded_files[:10]:  # 限制数量
            attachment_info.append({
                "file": file_info.get('file'),
                "file_code": file_info.get('file_code')
            })
        approval_attachment = json.dumps(attachment_info, ensure_ascii=False) if attachment_info else None
        
        # 构建飞书响应信息（JSON格式）
        feishu_response = json.dumps(response_data, ensure_ascii=False) if response_data else None
        
        # 生成审批名称
        if form_value1:
            approval_name = f"{form_value1}"
        else:
            approval_name = f"BOM审批_{instance_code[:8]}"
        
        # 确定审批类型（根据 approval_code 或默认）
        approval_type = "BOM_CREATE"  # 默认类型，可以根据 approval_code 判断
        
        # 确定状态
        feishu_status = "PENDING"  # 飞书状态：待审批
        sbom_status = "PENDING"    # SBOM状态：待审批
        
        logger.info(f"准备插入数据库记录: instance_code={instance_code}")
        
        with connection.cursor() as cursor:
            # 插入记录到 sbom_feishu_approval 表
            sql = """
            INSERT INTO sbom_feishu_approval (
                usr_id, deleted, create_time, updater, update_time,
                instance_code, usr_name, feishu_status, sbom_status,
                approval_type, approval_name, approval_info,
                approval_attachment, feishu_response, design_id
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            )
            """
            
            values = (
                usr_id,                # usr_id
                '0',                   # deleted (默认未删除)
                now,                   # create_time
                usr_id,                # updater (同 usr_id)
                now,                   # update_time
                instance_code,         # instance_code (唯一)
                user_id,               # usr_name (暂时使用user_id，后续可以查询用户名)
                feishu_status,        # feishu_status
                sbom_status,          # sbom_status
                approval_type,        # approval_type
                approval_name,        # approval_name
                json.dumps(approval_info, ensure_ascii=False),  # approval_info (JSON格式)
                approval_attachment,   # approval_attachment
                feishu_response,      # feishu_response (JSON格式)
                design_id_value        # design_id (关联 sbom_design.id)
            )
            
            logger.debug(f"SQL参数: usr_id={usr_id}, instance_code={instance_code}, design_id={design_id_value}")
            
            cursor.execute(sql, values)
            inserted_id = cursor.lastrowid
            affected_rows = cursor.rowcount
            logger.info(f"SQL执行成功，影响行数: {affected_rows}, 插入ID: {inserted_id}")
            
            # 更新 sbom_design 表中对应记录的 design_status
            if design_id_value:
                try:
                    update_sql = """
                        UPDATE sbom_design 
                        SET design_status = %s, 
                            updater = %s,
                            update_time = %s
                        WHERE design_id = %s
                    """
                    update_values = (
                        sbom_status,      # design_status（使用sbom_status的值更新design_status字段）
                        usr_id,           # updater
                        now,              # update_time
                        design_id_value   # design_id
                    )
                    cursor.execute(update_sql, update_values)
                    update_affected_rows = cursor.rowcount
                    if update_affected_rows > 0:
                        logger.info(f"成功更新 sbom_design 表: design_id={design_id_value}, design_status={sbom_status}, 影响行数: {update_affected_rows}")
                    else:
                        logger.warning(f"未找到匹配的 sbom_design 记录: design_id={design_id_value}")
                except Exception as update_error:
                    logger.error(f"更新 sbom_design 表失败: {update_error}")
                    # 即使更新失败，也不影响插入操作，继续执行
            
            connection.commit()
            logger.info(f"事务提交成功")
            
            logger.info(f"成功保存审批记录到数据库: id={inserted_id}, instance_code={instance_code}")
            return inserted_id
            
    except Exception as e:
        logger.error(f"保存审批记录失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        if 'connection' in locals() and connection:
            try:
                connection.rollback()
                logger.info("已回滚事务")
            except Exception as rollback_error:
                logger.error(f"回滚失败: {rollback_error}")
        return None
    finally:
        if 'connection' in locals() and connection:
            try:
                connection.close()
                logger.info("数据库连接已关闭")
            except Exception as close_error:
                logger.error(f"关闭连接失败: {close_error}")


def create_approval_instance_with_multiple_files(
    user_id: str,
    value: Optional[str] = None,
    value2: Optional[str] = None,
    file_path: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    process_result: Optional[Dict[str, Any]] = None,
    approver1_contact_ids: Optional[List[str]] = None,
    approver2_contact_ids: Optional[List[str]] = None,
    approval_code: str = "F8804181-ED37-43B3-90CB-6287BC89DA77"
) -> Dict[str, Any]:
    """创建审批实例（支持多文件上传）
    
    支持以下方式指定文件：
    1. process_result: process_multiple_excel_files 的返回结果（优先）
       - 自动提取 design_id 作为 value1
       - 自动格式化统计信息作为 value2（成功数、DIFF数、PLM数等）
       - 使用 json_files 作为要上传的文件列表
    2. file_path: 单个文件路径或目录路径
       - 如果是文件：上传该文件
       - 如果是目录：上传目录中的所有文件（递归遍历）
    3. file_paths: 文件路径列表，上传列表中的所有文件
    
    如果提供了 process_result，会优先使用其中的信息，其他参数会被忽略。
    
    Args:
        user_id: 用户ID
        value: 第一个表单字段的值 (widget17605183653670001)
              如果提供了 process_result，此参数会被忽略，使用 process_result['design_id']
        value2: 第二个表单字段的值 (widget17610278501620001)
               如果提供了 process_result，此参数会被忽略，自动格式化统计信息
        file_path: 可选的文件路径或目录路径
        file_paths: 可选的文件路径列表
        process_result: process_multiple_excel_files 的返回结果（优先使用）
        approver1_contact_ids: 研发代表字段联系人列表 (widget17627452200550001)
                             默认使用当前用户ID
        approver2_contact_ids: 部门经理字段联系人列表 (widget17627452594610001)
                             默认使用 ["250048"]
        approval_code: 审批定义Code (默认为BOM创建审批)
        
    Returns:
        返回字典包含:
        - success: bool - 请求是否成功
        - instance_code: str | None - 创建的实例code
        - file_codes: List[str] - 上传的所有文件code列表
        - uploaded_files: List[dict] - 成功上传的文件信息列表
        - failed_files: List[dict] - 上传失败的文件信息列表
        - error: dict | None - 错误信息 (仅在失败时)
    """
    file_codes = []
    uploaded_files = []
    failed_files = []
    
    # 如果提供了 process_result，优先使用其中的信息
    if process_result:
        # 从 process_result 中提取 value1 (design_id)
        if value is None:
            value = process_result.get('design_id', '')
        
        # 从 process_result 中提取并格式化 value2 (统计信息)
        if value2 is None:
            success_count = process_result.get('success_count', 0)
            total_files = process_result.get('total_files', 0)
            diff_count = process_result.get('diff_count', 0)
            plm_gbom_count = process_result.get('plm_gbom_count', 0)
            failed_count = process_result.get('failed_count', 0)
            
            # 格式化统计信息
            stats_parts = []
            if diff_count > 0:
                stats_parts.append(f"由差异表生成:{diff_count}个")
            if plm_gbom_count > 0:
                stats_parts.append(f"新建BOM生成:{plm_gbom_count}个")
            if failed_count > 0:
                stats_parts.append(f"格式解析失败:{failed_count}个,请联系开发人员处理")
            
            value2 = f"本次审批共包含:{total_files}个设计BOM申请, " + ", ".join(stats_parts) if stats_parts else f"总数:{total_files}"
        
        # 从 process_result 中提取原始Excel文件路径（优先于JSON文件）
        # 如果用户明确指定了 file_path 或 file_paths，则不自动提取
        if file_path is None and file_paths is None:
            # 优先使用顶层的 excel_file_paths（原始输入文件路径列表）
            excel_file_paths = process_result.get('excel_file_paths', [])
            
            # 过滤出存在的文件
            excel_files = []
            for excel_file in excel_file_paths:
                if excel_file and os.path.exists(excel_file):
                    excel_files.append(excel_file)
            
            # 如果有原始Excel文件，使用它们；否则使用JSON文件
            if excel_files:
                file_paths = excel_files
            else:
                # 如果没有原始文件，回退到JSON文件
                json_files = process_result.get('json_files', [])
                if json_files:
                    file_paths = json_files
            file_path = None  # 清空 file_path，避免重复处理
    
    # 收集所有需要上传的文件路径
    files_to_upload = []
    
    # 处理 file_path
    if file_path:
        if not os.path.exists(file_path):
            return {
                "success": False,
                "instance_code": None,
                "file_codes": [],
                "uploaded_files": [],
                "failed_files": [],
                "error": {
                    "code": "PATH_NOT_FOUND",
                    "msg": f"路径不存在: {file_path}",
                    "log_id": None
                }
            }
        
        if os.path.isfile(file_path):
            files_to_upload.append(file_path)
        elif os.path.isdir(file_path):
            # 遍历目录中的所有文件
            for root, dirs, files in os.walk(file_path):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    files_to_upload.append(full_path)
        else:
            return {
                "success": False,
                "instance_code": None,
                "file_codes": [],
                "uploaded_files": [],
                "failed_files": [],
                "error": {
                    "code": "INVALID_PATH_TYPE",
                    "msg": f"路径既不是文件也不是目录: {file_path}",
                    "log_id": None
                }
            }
    
    # 处理 file_paths
    if file_paths:
        for path in file_paths:
            if os.path.isfile(path):
                if path not in files_to_upload:  # 避免重复
                    files_to_upload.append(path)
            elif os.path.isdir(path):
                # 遍历目录中的所有文件
                for root, dirs, files in os.walk(path):
                    for filename in files:
                        full_path = os.path.join(root, filename)
                        if full_path not in files_to_upload:  # 避免重复
                            files_to_upload.append(full_path)
            else:
                failed_files.append({
                    "file": path,
                    "path": path,
                    "error": {
                        "code": "PATH_NOT_FOUND",
                        "msg": f"路径不存在或无效: {path}"
                    }
                })
    
    # 如果没有文件需要上传，直接创建审批实例（不带附件）
    if not files_to_upload:
        # 如果没有指定文件，回退到原始函数的行为
        # 确保 value 和 value2 有默认值
        if value is None:
            value = "test"
        if value2 is None:
            value2 = ""
        return create_approval_instance(
            user_id=user_id,
            value=value,
            value2=value2,
            file_path=None,
            approval_code=approval_code
        )
    
    # 上传所有文件
    for file_path_item in files_to_upload:
        upload_result = upload_approval_file(file_path_item, file_type="attachment")
        
        if upload_result["success"]:
            uploaded_files.append({
                "file": os.path.basename(file_path_item),
                "path": file_path_item,
                "file_code": upload_result["file_code"],
                "file_url": upload_result.get("file_url")
            })
            file_codes.append(upload_result["file_code"])
        else:
            failed_files.append({
                "file": os.path.basename(file_path_item),
                "path": file_path_item,
                "error": upload_result.get("error", {})
            })
    
    # 如果没有成功上传任何文件，返回错误
    if not file_codes:
        return {
            "success": False,
            "instance_code": None,
            "file_codes": [],
            "uploaded_files": [],
            "failed_files": failed_files,
            "error": {
                "code": "UPLOAD_ALL_FAILED",
                "msg": f"所有文件上传失败，共 {len(failed_files)} 个文件",
                "log_id": None,
                "failed_files": failed_files
            }
        }
    
    # 确保 value 和 value2 有值
    if value is None:
        value = "test"
    if value2 is None:
        value2 = ""
    if approver1_contact_ids is None:
        approver1_contact_ids = [user_id]
    if approver2_contact_ids is None:
        approver2_contact_ids = ["250048"]
    
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a867431a582b500c") \
        .app_secret("Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj") \
        .log_level(lark.LogLevel.INFO) \
        .build()

    # 构造表单数据 - 包含两个字段
    form_fields = [
        {
            "id": "widget17605183653670001",
            "type": "input",
            "value": value
        },
        {
            "id": "widget17610278501620001",
            "type": "input",
            "value": value2
        },
        {
            "id": "widget17627452200550001",
            "type": "contact",
            "value": approver1_contact_ids
        },
        {
            "id": "widget17627452594610001",
            "type": "contact",
            "value": approver2_contact_ids
        }
    ]
    
    # 添加多个文件到附件字段
    if file_codes:
        form_fields.append({
            "id": "widget17611037016100001",  # BOM审批附件控件ID
            "type": "attachmentV2",
            "value": file_codes  # 多个文件code
        })
    
    form_data = json.dumps(form_fields, ensure_ascii=False)

    # 构造请求对象
    request: CreateInstanceRequest = CreateInstanceRequest.builder() \
        .request_body(InstanceCreate.builder()
            .approval_code(approval_code)
            .user_id(user_id)
            .form(form_data)
            .build()) \
        .build()

    # 发起请求
    response: CreateInstanceResponse = client.approval.v4.instance.create(request)

    # 处理失败返回
    if not response.success():
        error_detail = {
            "code": response.code,
            "msg": response.msg,
            "log_id": response.get_log_id(),
        }
        try:
            error_detail["resp"] = json.loads(response.raw.content)
        except Exception:
            error_detail["resp"] = None
            
        return {
            "success": False,
            "instance_code": None,
            "file_codes": file_codes,
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "error": error_detail
        }

    # 处理业务结果 - 解析response.data获取instance_code
    try:
        data_dict = json.loads(lark.JSON.marshal(response.data))
        instance_code = data_dict.get("instance_code")
        
        # 保存到数据库
        db_id = None
        if instance_code:
            try:
                # 获取完整的响应数据
                full_response = {
                    "code": 0,
                    "msg": "success",
                    "data": data_dict
                }
                
                # 从 process_result 中获取 design_id（如果有）
                design_id_value = None
                design_id_str = None
                if process_result:
                    design_id_str = process_result.get('design_id', '')
                    if design_id_str:
                        design_id_value = _get_design_id_from_result(design_id_str)
                        if design_id_value:
                            logger.info(f"成功获取关联的 design_id: {design_id_str} -> {design_id_value}")
                        else:
                            logger.warning(f"未能找到 design_id 对应的记录: {design_id_str}")
                
                db_id = _save_approval_to_database(
                    instance_code=instance_code,
                    user_id=user_id,
                    approval_code=approval_code,
                    form_value1=value,
                    form_value2=value2,
                    file_codes=file_codes,
                    uploaded_files=uploaded_files,
                    response_data=full_response,
                    design_id=design_id_value,
                    design_id_str=design_id_str
                )
                if db_id:
                    logger.info(f"审批记录已保存到数据库，记录ID: {db_id}")
                else:
                    logger.warning("审批记录保存失败，但审批创建成功")
            except Exception as db_error:
                logger.error(f"保存审批记录到数据库时发生错误: {db_error}")
                # 不阻止返回成功结果，只记录错误
        
        return {
            "success": True,
            "instance_code": instance_code,
            "file_codes": file_codes,
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,  # 即使部分文件失败，如果审批创建成功也返回
            "db_id": db_id,  # 数据库记录ID
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "instance_code": None,
            "file_codes": file_codes,
            "uploaded_files": uploaded_files,
            "failed_files": failed_files,
            "error": {
                "code": "PARSE_ERROR",
                "msg": f"解析响应数据失败: {str(e)}",
                "log_id": None
            }
        }


def create_instance_comment(
    instance_code: str,
    user_id: str = "250048"
) -> Dict[str, Any]:
    """为审批实例创建评论
    
    Args:
        instance_code: 审批实例代码，将同时用作instance_id和评论内容
        user_id: 用户ID (默认为"250048")
        
    Returns:
        返回字典包含:
        - success: bool - 请求是否成功
        - comment_id: str | None - 评论ID
        - error: dict | None - 错误信息 (仅在失败时)
    """
    # 创建client
    client = lark.Client.builder() \
        .app_id("cli_a867431a582b500c") \
        .app_secret("Bf3dIF9D8vM78IPDv5wzUcKI3Gy8MxTj") \
        .log_level(lark.LogLevel.INFO) \
        .build()

    # 构造评论内容 - 使用instance_code作为内容
    comment_content = json.dumps({
        "text": instance_code
    }, ensure_ascii=False)

    # 构造请求对象
    request: CreateInstanceCommentRequest = CreateInstanceCommentRequest.builder() \
        .instance_id(instance_code) \
        .user_id_type("user_id") \
        .user_id(user_id) \
        .request_body(CommentRequest.builder()
            .content(comment_content)
            .build()) \
        .build()

    # 发起请求
    response: CreateInstanceCommentResponse = client.approval.v4.instance_comment.create(request)

    # 处理失败返回
    if not response.success():
        error_detail = {
            "code": response.code,
            "msg": response.msg,
            "log_id": response.get_log_id(),
        }
        try:
            error_detail["resp"] = json.loads(response.raw.content)
        except Exception:
            error_detail["resp"] = None
            
        return {
            "success": False,
            "comment_id": None,
            "error": error_detail
        }

    # 处理业务结果 - 解析response.data获取comment_id
    try:
        data_dict = json.loads(lark.JSON.marshal(response.data))
        comment_id = data_dict.get("comment_id")
        
        return {
            "success": True,
            "comment_id": comment_id,
            "instance_code": instance_code,
            "user_id": user_id,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "comment_id": None,
            "error": {
                "code": "PARSE_ERROR",
                "msg": f"解析响应数据失败: {str(e)}",
                "log_id": None
            }
        }


if __name__ == "__main__":
    # # 测试示例1: 查询单个实例的status和form
    # print("=" * 60)
    # print("测试1: 查询实例status和form")
    # print("=" * 60)
    # result1 = get_instance_status_and_form("2A396282-E240-4F55-BCEA-A1C39DDCA4FC")
    # print(json.dumps(result1, indent=2, ensure_ascii=False))
    
    # # 测试示例2: 查询用户的实例列表
    # print("\n" + "=" * 60)
    # print("测试2: 查询用户实例列表")
    # print("=" * 60)
    # result2 = get_user_instances("250048")
    # print(json.dumps(result2, indent=2, ensure_ascii=False))
    
    # 测试示例3: 创建审批实例
    print("\n" + "=" * 60)
    print("测试3: 创建审批实例 (两个字段)")
    print("=" * 60)
    result3 = create_approval_instance(
        user_id="250048", 
        value="https://ai-uat.aiswei-tech.com/factory/sbom_diff.html",
        value2="test_value2"
    )
    print(json.dumps(result3, indent=2, ensure_ascii=False))
    
    # # 测试示例4: 创建审批实例评论
    # if result3.get('success') and result3.get('instance_code'):
    #     print("\n" + "=" * 60)
    #     print("测试4: 创建审批实例评论")
    #     print("=" * 60)
    #     result4 = create_instance_comment(
    #         instance_code=result3['instance_code'],
    #         user_id="250048"
    #     )
    #     print(json.dumps(result4, indent=2, ensure_ascii=False))
