#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SBOM差异处理应用 - app.py
封装以下函数为API接口:
- process_multiple_excel_files: 批量处理多个Excel文件
- create_approval_instance_with_multiple_files: 创建审批实例（支持多文件上传）
- push_bom_files_by_design_id: 根据design_id推送BOM文件到PLM系统
- check_and_update_pending_approvals: 检查并更新待审批状态

定时任务:
- scheduled_check_and_push: 每5分钟自动执行一次
  - 检查待审批状态并更新数据库
  - 自动推送所有已批准的design_id到PLM系统
"""

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# 导入处理模块 - 使用相对路径
from new.multi_excel_processor import process_multiple_excel_files
from new.lark_approval import (
    create_approval_instance_with_multiple_files, 
    check_and_update_pending_approvals,
    get_user_access_token,
    get_user_info,
    get_instance_status_and_form
)
from new.plm_api_client import push_bom_files_by_design_id
from new.query_user_designs import query_user_designs
from new.query_user_login_info import search_user_login_info

#旧模块
import re
from new.enhanced_diff_parser import parse_diff_excel
from new.simple_ai_generator import generate_ai_analysis_json
from new.bom_transformer import transform_bom_json
from new.plm_api_client import push_bom_to_plm

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 飞书登录配置
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', 'cli_a867431a582b500c')
REDIRECT_URI = 'https://ai-uat.aiswei-tech.com/sbom/callback'
FEISHU_API_BASE = 'https://open.feishu.cn/open-apis'

# 定时任务调度器
scheduler = None


@app.route('/process_multiple_excel_files', methods=['POST'])
def api_process_multiple_excel_files():
    """
    批量处理多个Excel文件接口
    
    POST /process_multiple_excel_files
    
    请求方式1: 文件上传 (multipart/form-data)
        - files: 多个Excel文件 (支持 .xls, .xlsx)
        - worker_id: 工号 (可选，默认 "250000")
        - output_dir: 输出目录 (可选，默认 "data/tmp")
        - create_subdir: 是否创建子目录 (可选，默认 true)
    
    请求方式2: JSON (application/json)
        {
            "excel_file_paths": ["path/to/file1.xlsx", "path/to/file2.xls"],
            "worker_id": "250048",
            "output_dir": "data/tmp",
            "create_subdir": true
        }
    
    Returns:
        JSON响应包含处理结果
    """
    try:
        # 检查请求内容类型
        content_type = request.content_type or ''
        
        excel_file_paths = []
        worker_id = "250000"
        output_dir = "data/tmp"
        create_subdir = True
        
        if 'multipart/form-data' in content_type:
            # 方式1: 文件上传
            if 'files' not in request.files:
                return jsonify({
                    'success': False,
                    'error': '请至少上传一个Excel文件',
                    'message': '请求中缺少 files 参数'
                }), 400
            
            # 获取上传的文件列表
            files = request.files.getlist('files')
            if not files or all(f.filename == '' for f in files):
                return jsonify({
                    'success': False,
                    'error': '请至少上传一个有效的Excel文件',
                    'message': '上传的文件列表为空'
                }), 400
            
            # 保存上传的文件到临时目录
            tmp_dir = Path("data/tmp")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = []
            for file in files:
                if file.filename and file.filename.endswith(('.xls', '.xlsx')):
                    # 保存文件
                    tmp_path = tmp_dir / file.filename
                    file.save(str(tmp_path))
                    saved_files.append(str(tmp_path))
                    logger.info(f"保存上传文件: {file.filename} -> {tmp_path}")
            
            if not saved_files:
                return jsonify({
                    'success': False,
                    'error': '没有有效的Excel文件',
                    'message': '上传的文件必须是 .xls 或 .xlsx 格式'
                }), 400
            
            excel_file_paths = saved_files
            
            # 获取其他参数
            worker_id = request.form.get('worker_id', '250000')
            output_dir = request.form.get('output_dir', 'data/tmp')
            create_subdir_str = request.form.get('create_subdir', 'true')
            create_subdir = create_subdir_str.lower() in ('true', '1', 'yes')
            
        else:
            # 方式2: JSON请求
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': '请求体不能为空',
                    'message': '请提供JSON格式的请求体'
                }), 400
            
            excel_file_paths = data.get('excel_file_paths', [])
            if not excel_file_paths:
                return jsonify({
                    'success': False,
                    'error': '缺少excel_file_paths参数',
                    'message': '请提供要处理的Excel文件路径列表'
                }), 400
            
            # 验证文件路径是否存在
            missing_files = []
            for file_path in excel_file_paths:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            if missing_files:
                return jsonify({
                    'success': False,
                    'error': f'以下文件不存在: {", ".join(missing_files)}',
                    'message': '请检查文件路径是否正确',
                    'missing_files': missing_files
                }), 400
            
            worker_id = data.get('worker_id', '250000')
            output_dir = data.get('output_dir', 'data/tmp')
            create_subdir = data.get('create_subdir', True)
        
        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始批量处理Excel文件: {len(excel_file_paths)} 个文件")
        logger.info(f"参数: worker_id={worker_id}, output_dir={output_dir}, create_subdir={create_subdir}")
        
        # 调用处理函数
        result = process_multiple_excel_files(
            excel_file_paths=excel_file_paths,
            output_dir=output_dir,
            worker_id=worker_id,
            create_subdir=create_subdir
        )
        
        # 转换绝对路径为相对路径（如果可能）
        def get_relative_path(abs_path):
            try:
                if abs_path and os.path.isabs(abs_path):
                    return str(Path(abs_path).relative_to(Path.cwd()))
                return abs_path
            except:
                return abs_path
        
        # 处理返回结果中的路径
        if 'output_dir' in result:
            result['output_dir_relative'] = get_relative_path(result['output_dir'])
        
        if 'json_files' in result:
            result['json_files'] = [get_relative_path(f) for f in result['json_files']]
        
        if 'results' in result:
            for file_result in result['results']:
                if 'file_path' in file_result:
                    file_result['file_path'] = get_relative_path(file_result['file_path'])
                if 'files' in file_result:
                    file_result['files'] = [get_relative_path(f) for f in file_result['files']]
        
        logger.info(f"批量处理完成: 成功 {result.get('success_count', 0)}/{result.get('total_files', 0)} 个文件")
        
        return jsonify({
            'success': result.get('success', False),
            'message': f"批量处理完成，成功 {result.get('success_count', 0)}/{result.get('total_files', 0)} 个文件",
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"批量处理Excel文件失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'批量处理Excel文件失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/create_approval_instance_with_multiple_files', methods=['POST'])
def api_create_approval_instance_with_multiple_files():
    """
    创建审批实例（支持多文件上传）接口
    
    POST /create_approval_instance_with_multiple_files
    
    Request Body (JSON):
        {
            "user_id": "250048",                    // 必填：用户ID
            "title": "设计ID",                      // 必填：审批标题的值
            "description": "统计信息",                   // 可选：表单字段2的值
            "approver1_contact_ids": ["250048"],    // 可选：研发代表联系人列表
            "approver2_contact_ids": ["250048"],    // 可选：部门经理联系人列表
            "file_path": "/path/to/file.xlsx",      // 可选：单个文件路径或目录路径
            "file_paths": ["path1", "path2"],      // 可选：文件路径列表
            "process_result": {...},               // 可选：process_multiple_excel_files的返回结果（优先使用）
            "approval_code": "F8804181-..."        // 可选：审批定义Code
        }
    
    Returns:
        JSON响应包含审批创建结果
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'message': '请提供JSON格式的请求体'
            }), 400
        
        # 必填参数检查
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id不能为空',
                'message': '请提供用户ID'
            }), 400
        
        # 可选参数
        value = data.get('title')
        value2 = data.get('description')
        approver1_contact_ids = data.get('approver1_contact_ids')
        approver2_contact_ids = data.get('approver2_contact_ids')
        file_path = data.get('file_path')
        file_paths = data.get('file_paths')
        process_result = data.get('process_result')
        approval_code = data.get('approval_code', 'F8804181-ED37-43B3-90CB-6287BC89DA77')
        
        logger.info(f"创建审批实例: user_id={user_id}, approval_code={approval_code}")
        if process_result:
            logger.info(f"使用 process_result 自动提取信息")
        if file_path:
            logger.info(f"文件路径: {file_path}")
        if file_paths:
            logger.info(f"文件路径列表: {len(file_paths)} 个文件")
        
        # 调用创建审批函数
        result = create_approval_instance_with_multiple_files(
            user_id=user_id,
            value=value,
            value2=value2,
            file_path=file_path,
            file_paths=file_paths,
            process_result=process_result,
            approver1_contact_ids=approver1_contact_ids,
            approver2_contact_ids=approver2_contact_ids,
            approval_code=approval_code
        )
        
        logger.info(f"审批创建结果: 成功={result.get('success')}, instance_code={result.get('instance_code')}")
        
        return jsonify({
            'success': result.get('success', False),
            'message': '审批实例创建成功' if result.get('success') else '审批实例创建失败',
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"创建审批实例失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'创建审批实例失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/push_bom_files_by_design_id', methods=['POST'])
def api_push_bom_files_by_design_id():
    """
    根据design_id推送BOM文件到PLM系统接口
    
    POST /push_bom_files_by_design_id
    
    Request Body (JSON):
        {
            "design_id": "SBOM_20251103_F573B7D3",  // 必填：设计ID
            "owner": "adm",                          // 可选：数据所有者，默认 "adm"
            "creator": "adm",                        // 可选：数据创建者，默认 "adm"
            "source": "PPPE",                        // 可选：数据源，默认 "PPPE"
            "operator": "sf",                        // 可选：操作员，默认 "sf"
            "output_dir": null,                      // 可选：输出目录，默认 None（使用bom_path下的tmp子目录）
            "continue_on_error": true,               // 可选：遇到错误时是否继续处理，默认 true
            "max_retries": 0                         // 可选：失败时的最大重试次数，默认 0
        }
    
    Returns:
        JSON响应包含推送结果
        {
            "success": bool,              // 整体是否成功
            "design_id": str,             // design_id
            "push_result": dict,          // push_multi_files_from_directory的返回结果
            "db_update_success": bool,     // 数据库更新是否成功
            "message": str                 // 处理消息
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '请求体不能为空',
                'message': '请提供JSON格式的请求体'
            }), 400
        
        # 必填参数检查
        design_id = data.get('design_id')
        if not design_id:
            return jsonify({
                'success': False,
                'error': 'design_id不能为空',
                'message': '请提供设计ID'
            }), 400
        
        # 可选参数
        owner = data.get('owner', 'adm')
        creator = data.get('creator', 'adm')
        source = data.get('source', 'PPPE')
        operator = data.get('operator', 'sf')
        output_dir = data.get('output_dir', None)
        continue_on_error = data.get('continue_on_error', True)
        max_retries = data.get('max_retries', 0)
        
        logger.info(f"根据design_id推送BOM文件: design_id={design_id}")
        logger.info(f"参数: owner={owner}, creator={creator}, source={source}, operator={operator}")
        logger.info(f"continue_on_error={continue_on_error}, max_retries={max_retries}")
        
        # 调用推送函数
        result = push_bom_files_by_design_id(
            design_id=design_id,
            owner=owner,
            creator=creator,
            source=source,
            operator=operator,
            output_dir=output_dir,
            continue_on_error=continue_on_error,
            max_retries=max_retries
        )
        
        logger.info(f"推送结果: 成功={result.get('success')}, 数据库更新={result.get('db_update_success')}")
        
        # 转换绝对路径为相对路径（如果可能）
        def get_relative_path(abs_path):
            try:
                if abs_path and os.path.isabs(abs_path):
                    return str(Path(abs_path).relative_to(Path.cwd()))
                return abs_path
            except:
                return abs_path
        
        # 处理返回结果中的路径
        push_result = result.get('push_result')
        if push_result:
            # 处理推送结果中的文件路径
            if 'failed_files' in push_result:
                push_result['failed_files'] = [get_relative_path(f) for f in push_result['failed_files']]
            if 'results' in push_result:
                for file_result in push_result['results']:
                    if 'file_path' in file_result:
                        file_result['file_path'] = get_relative_path(file_result['file_path'])
                    if 'output_file' in file_result:
                        file_result['output_file'] = get_relative_path(file_result['output_file'])
        
        return jsonify({
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"根据design_id推送BOM文件失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'根据design_id推送BOM文件失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/check_and_update_pending_approvals', methods=['POST'])
def api_check_and_update_pending_approvals():
    """
    检查并更新待审批状态接口
    
    POST /check_and_update_pending_approvals
    
    功能说明:
    1. 查询sbom_feishu_approval表中所有feishu_status为PENDING的记录（不限制用户ID）
    2. 调用飞书API查询每个实例的最新状态
    3. 更新数据库中的feishu_status
    4. 返回所有状态为APPROVED的design_id
    
    Request Body (JSON):
        {}  // 无需参数，查询所有用户的待审批记录
    
    Returns:
        JSON响应包含检查结果
        {
            "success": bool,                  // 整体操作是否成功
            "total_pending": int,             // 待处理的审批数量
            "checked_count": int,             // 成功检查的审批数量
            "updated_count": int,             // 成功更新的审批数量
            "approved_design_ids": List[str], // 所有APPROVED状态的design_id列表
            "details": List[dict],            // 每个审批实例的处理详情
            "error": str | None               // 错误信息(仅在失败时)
        }
    """
    try:
        logger.info("检查并更新待审批状态（所有用户）")
        
        # 调用检查函数
        result = check_and_update_pending_approvals()
        
        logger.info(f"检查结果: 成功={result.get('success')}, "
                   f"待处理={result.get('total_pending')}, "
                   f"已检查={result.get('checked_count')}, "
                   f"已更新={result.get('updated_count')}, "
                   f"已批准={len(result.get('approved_design_ids', []))}")
        
        return jsonify({
            'success': result.get('success', False),
            'message': f"检查完成: 待处理{result.get('total_pending', 0)}个, "
                      f"已检查{result.get('checked_count', 0)}个, "
                      f"已更新{result.get('updated_count', 0)}个, "
                      f"已批准{len(result.get('approved_design_ids', []))}个",
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"检查并更新待审批状态失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'检查并更新待审批状态失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/upload_files', methods=['POST'])
def api_upload_files():
    """
    上传文件到 data/input 目录接口
    每次上传会创建一个新的时间戳子目录
    
    POST /api/upload_files
    请求方式: multipart/form-data
        - files: 多个Excel文件 (支持 .xls, .xlsx)
        - user_id: 用户ID (可选，用于记录上传者)
    
    Returns:
        JSON响应包含:
        - success: 是否成功
        - upload_dir: 上传目录的相对路径 (如 "data/input/20241103_143025")
        - files: 上传成功的文件列表
        - message: 消息
    """
    try:
        # 检查是否有文件
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': '请至少上传一个文件',
                'message': '请求中缺少 files 参数'
            }), 400
        
        # 获取上传的文件列表
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': '请至少上传一个有效的文件',
                'message': '上传的文件列表为空'
            }), 400
        
        # 获取用户ID（可选）
        user_id = request.form.get('user_id', '')
        
        # 创建上传目录 - 使用时间戳创建唯一子目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_dir = Path("data/input") / timestamp
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件
        saved_files = []
        for file in files:
            if file.filename:
                # 只保存Excel文件
                if file.filename.endswith(('.xls', '.xlsx')):
                    # 保存文件
                    file_path = upload_dir / file.filename
                    file.save(str(file_path))
                    saved_files.append({
                        'filename': file.filename,
                        'path': str(file_path),
                        'relative_path': f"data/input/{timestamp}/{file.filename}",
                        'size': file_path.stat().st_size
                    })
                    logger.info(f"保存上传文件: {file.filename} -> {file_path}")
        
        if not saved_files:
            return jsonify({
                'success': False,
                'error': '没有有效的Excel文件',
                'message': '上传的文件必须是 .xls 或 .xlsx 格式'
            }), 400
        
        # 返回上传结果
        relative_upload_dir = f"data/input/{timestamp}"
        return jsonify({
            'success': True,
            'upload_dir': relative_upload_dir,
            'absolute_upload_dir': str(upload_dir),
            'files': saved_files,
            'file_count': len(saved_files),
            'user_id': user_id,
            'timestamp': timestamp,
            'message': f'成功上传 {len(saved_files)} 个文件到 {relative_upload_dir}'
        }), 200
        
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'文件上传失败: {str(e)}',
            'message': '服务器内部错误'
        }), 500

@app.route('/api/get_json_file', methods=['GET'])
def api_get_json_file():
    """
    获取JSON文件内容接口
    
    GET /api/get_json_file?file_path=relative/path/to/file.json
    
    Returns:
        JSON响应包含文件内容
    """
    try:
        file_path = request.args.get('file_path')
        if not file_path:
            return jsonify({
                'success': False,
                'error': '缺少file_path参数'
            }), 400
        
        # 转换为绝对路径
        if not os.path.isabs(file_path):
            abs_path = os.path.join(os.getcwd(), file_path)
        else:
            abs_path = file_path
        
        # 检查文件是否存在
        if not os.path.exists(abs_path):
            return jsonify({
                'success': False,
                'error': f'文件不存在: {file_path}'
            }), 404
        
        # 读取JSON文件
        with open(abs_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': json_data,
            'file_path': file_path
        }), 200
        
    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': f'JSON解析失败: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"获取JSON文件失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'获取文件失败: {str(e)}'
        }), 500

@app.route('/login', methods=['GET'])
def login():
    """跳转到飞书授权"""
    params = {
        'app_id': FEISHU_APP_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'contact:user.base:readonly'
    }
    auth_url = f'{FEISHU_API_BASE}/authen/v1/authorize?' + urlencode(params)
    return redirect(auth_url)

@app.route('/callback', methods=['GET'])
def callback():
    """授权回调"""
    code = request.args.get('code')
    if not code:
        return '''<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>登录失败</title>
            <style>
                body { font-family: Arial, sans-serif; background: #f5f5f5; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
                .container { background: white; border-radius: 15px; padding: 40px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
                .error { font-size: 48px; margin-bottom: 20px; }
                h1 { color: #e74c3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">❌</div>
                <h1>登录失败</h1>
                <p>未获取到授权码</p>
            </div>
        </body>
        </html>''', 400
    
    try:
        # 获取用户信息
        token_data = get_user_access_token(code)
        user_info = get_user_info(token_data.get('access_token'))
        
        user_id = user_info.get('user_id')
        name = user_info.get('name', '')
        
        logger.info(f"✅ 飞书登录成功！user_id: {user_id}, name: {name}")
        
        # 返回页面，将user_id传递给前端，立即关闭窗口不显示内容
        return f'''<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>登录成功</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background: transparent;
                }}
            </style>
            <script>
                // 将user_id传递给父窗口并立即关闭
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'feishu_login_success',
                        userId: '{user_id}',
                        name: '{name}'
                    }}, '*');
                    // 立即关闭窗口，不显示任何内容
                    window.close();
                }}
            </script>
        </head>
        <body></body>
        </html>'''
    except Exception as e:
        logger.error(f"❌ 飞书登录失败: {e}")
        return f'''<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>登录失败</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f5f5f5; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
                .container {{ background: white; border-radius: 15px; padding: 40px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
                .error {{ font-size: 48px; margin-bottom: 20px; }}
                h1 {{ color: #e74c3c; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">❌</div>
                <h1>登录失败</h1>
                <p>{str(e)}</p>
            </div>
        </body>
        </html>''', 500


@app.route('/health', methods=['GET'])
def api_health():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'healthy',
        'version': 'app_v1.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/process_multiple_excel_files',
            '/create_approval_instance_with_multiple_files',
            '/push_bom_files_by_design_id',
            '/check_and_update_pending_approvals',
            '/health',
            '/api/user_designs'
        ]
    })


@app.route('/api/user_designs', methods=['GET'])
def api_user_designs():
    """
    获取用户设计记录列表接口
    
    GET /api/user_designs?usr_id=250048&limit=50
    
    查询参数:
        usr_id: 用户ID (必填)
        limit: 返回记录数限制，默认50
    
    Returns:
        JSON响应包含设计记录列表，格式化为前端所需格式
        {
            "success": true,
            "data": [
                {
                    "design_id": "DESIGN001",
                    "title": "SP0012-3Q-23-5QP 产品设计",
                    "desc": "基于SP0012-00-23-5QP新建生成，包含完整的BOM结构和设计文档",
                    "status": "审核中",
                    "status_class": "status-review",
                    "author_name": "吉飞洲",
                    "author_avatar": "吉",
                    "date": "2024-10-30"
                }
            ],
            "count": 10
        }
    """
    try:
        # 获取查询参数
        usr_id = request.args.get('usr_id')
        limit = request.args.get('limit', 50, type=int)
        
        if not usr_id:
            return jsonify({
                'success': False,
                'error': 'usr_id参数不能为空',
                'message': '请提供用户ID查询参数'
            }), 400
        
        try:
            usr_id = int(usr_id)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'usr_id参数格式错误',
                'message': '用户ID必须是数字'
            }), 400
        
        logger.info(f"查询用户设计记录: usr_id={usr_id}, limit={limit}")
        
        # 查询设计记录
        results = query_user_designs(usr_id, limit=limit)
        
        if results is None:
            return jsonify({
                'success': False,
                'error': '查询失败',
                'message': '数据库查询出错'
            }), 500
        
        # 转换数据格式为前端所需格式
        formatted_data = []
        for record in results:
            # 确定状态 - 优先使用design_status，如果为空则使用sbom_status
            design_status = record.get('design_status', '').upper() if record.get('design_status') else ''
            sbom_status = record.get('sbom_status', '').upper() if record.get('sbom_status') else ''
            feishu_status = record.get('feishu_status', '').upper() if record.get('feishu_status') else ''
            
            # 状态映射逻辑 - 支持5种状态：DRAFT, PENDING, PUSHED, FAILED, DISCARDED
            status_code = ''  # 原始状态码，用于前端筛选
            if design_status == 'DRAFT' or (not design_status and not sbom_status):
                status = '草稿'
                status_class = 'status-draft'
                status_code = 'DRAFT'
            elif design_status == 'PENDING' or feishu_status == 'PENDING':
                status = '审核中'
                status_class = 'status-review'
                status_code = 'PENDING'
            elif design_status == 'PUSHED' or sbom_status == 'PUSHED':
                status = '已推送'
                status_class = 'status-pushed'
                status_code = 'PUSHED'
            elif design_status == 'FAILED' or sbom_status == 'FAILED':
                status = '失败'
                status_class = 'status-failed'
                status_code = 'FAILED'
            elif design_status == 'DISCARDED':
                status = '已废弃'
                status_class = 'status-discarded'
                status_code = 'DISCARDED'
            else:
                # 兼容旧的状态值
                if design_status == 'DRFAT':  # 修复拼写错误
                    status = '草稿'
                    status_class = 'status-draft'
                    status_code = 'DRAFT'
                elif feishu_status == 'APPROVED':
                    status = '已推送'
                    status_class = 'status-pushed'
                    status_code = 'PUSHED'
                elif feishu_status == 'REJECTED':
                    status = '失败'
                    status_class = 'status-failed'
                    status_code = 'FAILED'
                else:
                    # 默认状态
                    status = '草稿'
                    status_class = 'status-draft'
                    status_code = 'DRAFT'
            
            # 获取标题（使用approval_name，如果没有则使用design_name）
            title = record.get('approval_name') or record.get('design_name') or record.get('design_id', '未知设计')
            
            # 获取详情（从approval_info中提取form_value2和create_time）
            approval_info = record.get('approval_info', '')
            form_value2 = ''
            approval_create_time = ''
            desc = ''
            
            if approval_info:
                try:
                    import json
                    info_dict = json.loads(approval_info) if isinstance(approval_info, str) else approval_info
                    form_value2 = info_dict.get('form_value2', '') or ''
                    approval_create_time = info_dict.get('create_time', '') or ''
                except Exception as e:
                    logger.warning(f"解析approval_info失败: {e}")
                    pass
            
            # 构建详情描述：form_value2 + create_time
            if form_value2 or approval_create_time:
                parts = []
                if form_value2:
                    parts.append(str(form_value2))
                if approval_create_time:
                    # 格式化时间显示（包含时分秒）
                    try:
                        if isinstance(approval_create_time, str):
                            # 尝试解析为datetime并格式化
                            formats = [
                                '%Y-%m-%d %H:%M:%S',
                                '%Y-%m-%d %H:%M:%S.%f',
                                '%Y-%m-%dT%H:%M:%S',
                                '%Y-%m-%dT%H:%M:%S.%f',
                                '%Y-%m-%d'
                            ]
                            time_str = None
                            for fmt in formats:
                                try:
                                    dt = datetime.strptime(approval_create_time.split('.')[0].replace('T', ' ').replace('Z', '').strip(), fmt.split('.')[0].replace('T', ' ').replace('Z', '').strip())
                                    time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                                    break
                                except:
                                    continue
                            if not time_str:
                                # 如果解析失败，尝试直接提取
                                if 'T' in approval_create_time:
                                    # ISO格式：2024-10-30T14:30:00 或 2024-10-30T14:30:00.123456
                                    parts_temp = approval_create_time.split('T')
                                    if len(parts_temp) == 2:
                                        date_part = parts_temp[0]
                                        time_part = parts_temp[1].split('.')[0].split('Z')[0]
                                        time_str = f"{date_part} {time_part}" if len(time_part) >= 8 else approval_create_time[:19]
                                    else:
                                        time_str = approval_create_time[:19]
                                else:
                                    time_str = approval_create_time[:19] if len(approval_create_time) >= 19 else approval_create_time
                            parts.append(f"创建时间: {time_str}")
                        else:
                            time_str = approval_create_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(approval_create_time, 'strftime') else str(approval_create_time)[:19]
                            parts.append(f"创建时间: {time_str}")
                    except Exception as e:
                        parts.append(f"创建时间: {str(approval_create_time)[:19]}")
                desc = ' | '.join(parts)
            else:
                # 如果没有approval_info，使用design_info作为备用
                design_info = record.get('design_info', '')
                if design_info:
                    try:
                        import json
                        info_dict = json.loads(design_info) if isinstance(design_info, str) else design_info
                        desc = info_dict.get('description', '') or info_dict.get('desc', '') or '暂无描述'
                    except:
                        desc = '暂无描述'
                else:
                    desc = '暂无描述'
            
            # 格式化最后更新时间（使用approval_update_time，如果没有则使用design_update_time）
            # 格式：YYYY-MM-DD HH:MM:SS
            update_time = record.get('approval_update_time') or record.get('design_update_time')
            if update_time:
                if isinstance(update_time, str):
                    # 如果是字符串，尝试解析为datetime然后格式化
                    try:
                        # 尝试多种日期时间格式
                        formats = [
                            '%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%d %H:%M:%S.%f',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S.%f',
                            '%Y-%m-%d %H:%M:%S.%fZ',
                            '%Y-%m-%d %H:%M:%SZ',
                            '%Y-%m-%d'
                        ]
                        date_str = None
                        for fmt in formats:
                            try:
                                dt = datetime.strptime(update_time.split('.')[0].replace('T', ' ').replace('Z', '').strip(), fmt.split('.')[0].replace('T', ' ').replace('Z', '').strip())
                                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                                break
                            except:
                                continue
                        if not date_str:
                            # 如果所有格式都失败，尝试简单提取
                            if ' ' in update_time:
                                date_str = update_time.split('.')[0].replace('T', ' ')[:19]
                            else:
                                date_str = update_time[:19] if len(update_time) >= 19 else update_time
                    except:
                        # 如果解析失败，尝试直接提取
                        date_str = update_time.split('.')[0].replace('T', ' ')[:19] if 'T' in update_time or ' ' in update_time else update_time
                else:
                    # 如果是datetime对象
                    date_str = update_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(update_time, 'strftime') else str(update_time)[:19]
            else:
                # 使用创建时间
                create_time = record.get('approval_create_time') or record.get('design_create_time')
                if create_time:
                    if isinstance(create_time, str):
                        try:
                            # 尝试解析为datetime
                            formats = [
                                '%Y-%m-%d %H:%M:%S',
                                '%Y-%m-%d %H:%M:%S.%f',
                                '%Y-%m-%dT%H:%M:%S',
                                '%Y-%m-%dT%H:%M:%S.%f',
                                '%Y-%m-%d'
                            ]
                            date_str = None
                            for fmt in formats:
                                try:
                                    dt = datetime.strptime(create_time.split('.')[0].replace('T', ' ').strip(), fmt.split('.')[0].replace('T', ' ').strip())
                                    date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                                    break
                                except:
                                    continue
                            if not date_str:
                                date_str = create_time.split('.')[0].replace('T', ' ')[:19] if 'T' in create_time or ' ' in create_time else create_time
                        except:
                            date_str = create_time.split('.')[0].replace('T', ' ')[:19] if 'T' in create_time or ' ' in create_time else create_time
                    else:
                        date_str = create_time.strftime('%Y-%m-%d %H:%M:%S') if hasattr(create_time, 'strftime') else str(create_time)[:19]
                else:
                    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            formatted_data.append({
                'design_id': record.get('design_id', ''),
                'title': title,
                'desc': desc,
                'status': status,
                'status_code': status_code,  # 添加状态码用于前端筛选
                'status_class': status_class,
                'date': date_str,
                'design_info': record.get('design_info', ''),  # 添加原始设计信息
                'approval_info': record.get('approval_info', ''),  # 添加原始审批信息
                'bom_path': record.get('bom_path', ''),  # 添加BOM路径，用于加载详情数据
                'approval_instance_code': record.get('approval_instance_code', '')  # 添加审批实例代码，用于查询飞书审批状态
            })
        
        logger.info(f"成功查询并格式化 {len(formatted_data)} 条设计记录")
        
        return jsonify({
            'success': True,
            'data': formatted_data,
            'count': len(formatted_data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取用户设计记录失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'获取用户设计记录失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/user_login_search', methods=['GET'])
def api_user_login_search():
    """
    根据关键字联想查询用户登录信息。

    GET /api/user_login_search?keyword=2500&limit=5

    查询参数:
        keyword: 查询关键字，支持 login_id 前缀与 login_name 模糊匹配 (必填)
        limit: 返回记录数限制，默认 5，最大 20

    Returns:
        JSON 响应包含匹配到的登录信息列表
        {
            "success": true,
            "data": [
                {"login_id": "250048", "login_name": "房天顺"},
                ...
            ],
            "count": 3,
            "timestamp": "2025-11-10T12:34:56.789123"
        }
    """
    keyword = (request.args.get('keyword') or '').strip()
    if not keyword:
        return jsonify({
            'success': False,
            'error': 'keyword参数不能为空',
            'message': '请提供联想查询关键字'
        }), 400

    try:
        limit = request.args.get('limit', default=5, type=int)
    except (TypeError, ValueError):
        limit = 5

    if limit is None:
        limit = 5

    if limit <= 0:
        limit = 5
    limit = min(limit, 20)

    try:
        logger.info(f"联想查询用户登录信息: keyword={keyword}, limit={limit}")
        suggestions = search_user_login_info(keyword, limit=limit)

        return jsonify({
            'success': True,
            'data': suggestions,
            'count': len(suggestions),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as exc:
        logger.error(f"联想查询用户登录信息失败: {exc}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': '查询失败',
            'message': str(exc)
        }), 500


@app.route('/api/lark/instance/<instance_id>', methods=['GET'])
def api_get_lark_instance(instance_id):
    """根据instance_id查询飞书审批实例的status和form
    
    GET /api/lark/instance/<instance_id>
    
    Returns:
        JSON响应包含status和form字段
    """
    try:
        logger.info(f"查询飞书审批实例: {instance_id}")
        result = get_instance_status_and_form(instance_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"查询飞书审批实例失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "status": None,
            "form": None,
            "error": {
                "code": "SERVER_ERROR",
                "msg": str(e),
                "log_id": None
            }
        }), 500

# 旧接口
@app.route('/process_diff_and_generate_new', methods=['POST'])
def api_process_diff_and_generate_new():
    """
    新版一键处理差异文件并生成BOM对比API
    参考原api_process_diff_and_generate函数，依次调用新模块
    """
    tmp_path = None
    try:
        # 1. 获取上传的文件
        file = request.files['file']
        
        # 设置基础目录和临时目录 - 使用D:\code\sbom\release\sbom_diff\tmp
        base_dir = Path(__file__).resolve().parents[2]  # 回到sbom_diff目录
        tmp_dir = Path("data/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件到临时目录
        tmp_path = tmp_dir / file.filename
        file.save(str(tmp_path))
        
        logger.info(f"开始处理文件: {file.filename}")
        
        # 2. 步骤1：解析差异文件 (enhanced_diff_parser)
        logger.info("步骤1: 调用enhanced_diff_parser解析差异文件...")
        diff_result = parse_diff_excel(
            excel_file_path=str(tmp_path),
            output_dir=str(tmp_dir)
        )
        
        if not diff_result['success']:
            return jsonify({
                'success': False,
                'error': f'差异文件解析失败: {diff_result["error"]}',
                'step': 'enhanced_diff_parser'
            })
        
        diff_file_path = diff_result['file_path']
        base_model = diff_result['stats']['base_model']
        target_model = diff_result['stats']['target_model']
        
        logger.info(f"差异文件解析成功: {base_model} -> {target_model}")
        logger.info(f"差异文件保存到: {diff_file_path}")
        
        # 3. 步骤2：生成基础模型的AI分析数据 (simple_ai_generator)
        logger.info("步骤2: 调用simple_ai_generator生成基础模型AI分析数据...")
        base_ai_result = generate_ai_analysis_json(
            model_name=base_model,
            output_dir=str(tmp_dir)
        )
        
        if not base_ai_result['success']:
            return jsonify({
                'success': False,
                'error': f'基础模型AI分析生成失败: {base_ai_result["error"]}',
                'step': 'simple_ai_generator',
                'model': base_model
            })
        
        base_bom_file = base_ai_result['file_path']
        logger.info(f"基础模型AI分析生成成功: {base_bom_file}")
        
        # 4. 步骤3：BOM转换 (bom_transformer)
        logger.info("步骤3: 调用bom_transformer执行BOM转换...")
        transform_result = transform_bom_json(
            base_file=base_bom_file,
            diff_file=diff_file_path,
            output_file=str(tmp_dir / f"{target_model}.json"),
            tmp_dir=str(tmp_dir)
        )
        
        if not transform_result['success']:
            return jsonify({
                'success': False,
                'error': f'BOM转换失败: {transform_result["error"]}',
                'step': 'bom_transformer'
            })
        
        target_bom_file = transform_result['file_path']
        logger.info(f"BOM转换成功: {target_bom_file}")
        
        # 5. 步骤4：推送到PLM系统 (plm_api_client) - 暂时跳过，由前端单独调用
        # 这里不执行PLM推送，留给前端的"上传系统"按钮来处理
        logger.info("步骤4: PLM推送将由前端单独调用")
        
        # 6. 生成BOM对比数据（参考原函数逻辑）
        logger.info("步骤5: 生成BOM对比数据...")
        
        # 读取基础BOM和目标BOM文件进行对比
        try:
            with open(base_bom_file, 'r', encoding='utf-8') as f:
                base_bom_data = json.load(f)
            with open(target_bom_file, 'r', encoding='utf-8') as f:
                target_bom_data = json.load(f)
            
            # 处理对比数据 - 提取所有零件信息
            base_map, target_map = {}, {}
            
            # 处理基础BOM数据
            for category, items in base_bom_data.get('MPART', {}).items():
                if isinstance(items, list):
                    for item in items:
                        code = item.get('MPART.NO')
                        if code:
                            base_map[code] = {
                                'name': item.get('MPART.NAME', ''),
                                'quantity': item.get('MPART.BNUM', 0)
                            }
            
            # 处理目标BOM数据
            for category, items in target_bom_data.get('MPART', {}).items():
                if isinstance(items, list):
                    for item in items:
                        code = item.get('MPART.NO')
                        if code:
                            target_map[code] = {
                                'name': item.get('MPART.NAME', ''),
                                'quantity': item.get('MPART.BNUM', 0)
                            }
            
            # 生成对比结果
            all_codes = sorted(set(list(base_map.keys()) + list(target_map.keys())))
            comparison_results = []
            
            for index, code in enumerate(all_codes):
                base_item = base_map.get(code, {'name': '', 'quantity': 0})
                target_item = target_map.get(code, {'name': '', 'quantity': 0})
                
                comparison_results.append({
                    'seq': index + 1,
                    'code': code,
                    'name': base_item['name'] or target_item['name'],
                    'baseQuantity': base_item['quantity'],
                    'targetQuantity': target_item['quantity'],
                    'status': 'changed' if base_item['quantity'] != target_item['quantity'] else 'unchanged'
                })
            
            logger.info(f"BOM对比完成，共对比 {len(comparison_results)} 个零件")
            
        except Exception as e:
            logger.error(f"BOM对比失败: {e}")
            comparison_results = []
        
        # 7. 汇总最终结果 - 使用相对路径
        # 将绝对路径转换为相对于项目根目录的路径
        def get_relative_path(abs_path):
            try:
                return str(Path(abs_path).relative_to(Path.cwd()))
            except:
                return abs_path

        # 处理型号
        match = re.match(r'^[A-Za-z]+', target_model) if target_model else None
        model_type = match.group(0) if match else 'UNKNOWN'

        result_summary = {
            'success': True,
            'message': '新版差异处理流程完成',
            'data': {
                'baseModel': base_model,
                'targetModel': target_model,
                'modelType': model_type,
                'comparison': comparison_results
            },
            'processing_steps': {
                'enhanced_diff_parser': {
                    'status': 'success',
                    'file_path': get_relative_path(diff_file_path),
                    'stats': diff_result['stats']
                },
                'simple_ai_generator': {
                    'status': 'success',
                    'file_path': get_relative_path(base_bom_file),
                    'stats': base_ai_result['stats']
                },
                'bom_transformer': {
                    'status': 'success',
                    'file_path': get_relative_path(target_bom_file),
                    'tmp_file_path': get_relative_path(transform_result['tmp_file_path']),
                    'stats': transform_result['stats']
                }
                # 'plm_api_client': {
                #     'status': 'success' if plm_result['success'] else 'warning',
                #     'file_path': plm_result.get('file_path'),
                #     'stats': plm_result.get('stats'),
                #     'message': plm_result.get('message')
                # }
            },
            'files': {
                'original_file': get_relative_path(str(tmp_path)),
                'diff_file': get_relative_path(diff_file_path),
                'base_bom_file': get_relative_path(base_bom_file),
                'target_bom_file': get_relative_path(target_bom_file),
                # 'plm_data_file': plm_result.get('file_path')
            },
            'statistics': {
                'diff_items': diff_result['stats']['diff_count'],
                'sub_bom_items': diff_result['stats']['sub_bom_count'],
                'base_bom_parts': base_ai_result['stats']['total_parts'],
                'target_bom_parts': transform_result['stats']['total_parts'],
                'comparison_items': len(comparison_results)
            }
        }
        
        logger.info("新版差异处理流程全部完成")
        return jsonify(result_summary)
        
    except Exception as e:
        logger.error(f"处理过程中发生异常: {e}")
        return jsonify({
            'success': False,
            'error': f'处理过程中发生异常: {str(e)}',
            'step': 'unknown'
        })
    finally:
        # 清理上传的临时文件
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
                logger.info(f"已清理临时文件: {tmp_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")

@app.route('/process_single_step', methods=['POST'])
def api_process_single_step():
    """
    单步处理API - 允许用户单独调用某个处理步骤
    """
    try:
        data = request.get_json()
        step = data.get('step')
        tmp_dir = Path("data/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        if step == 'parse_diff':
            # 步骤1: 解析差异文件
            file_path = data.get('file_path')
            if not file_path:
                return jsonify({'success': False, 'error': '缺少file_path参数'})
            
            result = parse_diff_excel(file_path, str(tmp_dir))
            return jsonify(result)
            
        elif step == 'generate_ai':
            # 步骤2: 生成AI分析数据
            model_name = data.get('model_name')
            if not model_name:
                return jsonify({'success': False, 'error': '缺少model_name参数'})
            
            result = generate_ai_analysis_json(model_name, str(tmp_dir))
            return jsonify(result)
            
        elif step == 'transform_bom':
            # 步骤3: BOM转换
            base_file = data.get('base_file')
            diff_file = data.get('diff_file')
            if not base_file or not diff_file:
                return jsonify({'success': False, 'error': '缺少base_file或diff_file参数'})
            
            output_file = data.get('output_file')
            result = transform_bom_json(base_file, diff_file, output_file, str(tmp_dir))
            return jsonify(result)
            
        elif step == 'push_plm':
            # 步骤4: 推送到PLM
            bom_file_path = data.get('bom_file_path')
            if not bom_file_path:
                return jsonify({'success': False, 'error': '缺少bom_file_path参数'})
            
            # 处理相对路径，转换为绝对路径
            if not os.path.isabs(bom_file_path):
                bom_file_path = os.path.join(os.getcwd(), bom_file_path)
            
            diff_file_path = data.get('diff_file_path')
            if diff_file_path and not os.path.isabs(diff_file_path):
                diff_file_path = os.path.join(os.getcwd(), diff_file_path)
            
            owner = data.get('owner', 'adm')
            creator = data.get('creator', 'adm')
            source = data.get('source', 'PPPE')
            operator = data.get('operator', 'sf')
            validate_only = data.get('validate_only', False)
            
            logger.info(f"PLM推送 - BOM文件: {bom_file_path}")
            logger.info(f"PLM推送 - BOM文件存在: {os.path.exists(bom_file_path)}")
            if diff_file_path:
                logger.info(f"PLM推送 - 差异文件: {diff_file_path}")
                logger.info(f"PLM推送 - 差异文件存在: {os.path.exists(diff_file_path)}")
            
            result = push_bom_to_plm(
                bom_file_path=bom_file_path,
                owner=owner,
                creator=creator,
                source=source,
                operator=operator,
                validate_only=validate_only,
                output_dir=str(tmp_dir),
                diff_file_path=diff_file_path
            )
            
            logger.info(f"PLM推送结果: {result.get('success')}, 状态: {result.get('status')}")
            return jsonify(result)
            
        else:
            return jsonify({
                'success': False,
                'error': f'未知的处理步骤: {step}',
                'available_steps': ['parse_diff', 'generate_ai', 'transform_bom', 'push_plm']
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'单步处理失败: {str(e)}'
        })

@app.route('/process_excel_auto_detect', methods=['POST'])
def api_process_excel_auto_detect():
    """
    Excel文件自动检测处理API
    自动检测Excel中所有sheet的格式并调用相应的处理函数
    """
    tmp_path = None
    try:
        # 1. 获取上传的文件
        file = request.files['file']
        
        # 设置临时目录
        tmp_dir = Path("data/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件到临时目录
        tmp_path = tmp_dir / file.filename
        file.save(str(tmp_path))
        
        logger.info(f"开始自动检测处理Excel文件: {file.filename}")
        
        # 2. 导入并调用process_excel_auto_detect函数
        from new.plm_excel_processor import process_excel_auto_detect
        
        # 3. 执行自动检测处理
        result = process_excel_auto_detect(
            excel_file_path=str(tmp_path),
            output_dir=str(tmp_dir)
        )
        
        logger.info(f"Excel自动检测处理完成: {result.get('success', False)}")
        
        # 4. 处理返回结果，转换绝对路径为相对路径
        def get_relative_path(abs_path):
            try:
                return str(Path(abs_path).relative_to(Path.cwd()))
            except:
                return abs_path
        
        # 如果结果中包含文件路径，转换为相对路径
        if result.get('success') and 'files' in result:
            for file_info in result['files']:
                if 'file_path' in file_info:
                    file_info['file_path'] = get_relative_path(file_info['file_path'])
        
        # 5. 返回处理结果
        response_data = {
            'success': result.get('success', False),
            'message': result.get('message', ''),
            'data': result,
            'original_filename': file.filename,
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加原始文件的绝对路径到data中，用于审批附件上传
        if tmp_path:
            response_data['data']['original_file'] = str(tmp_path.absolute())
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Excel自动检测处理失败: {e}")
        return jsonify({
            'success': False,
            'error': f'Excel自动检测处理失败: {str(e)}',
            'original_filename': file.filename if 'file' in locals() else 'unknown'
        })
    finally:
        # 清理上传的临时文件
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
                logger.info(f"已清理临时文件: {tmp_path}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


@app.route('/batch_upload_bom_files', methods=['POST'])
def api_batch_upload_bom_files():
    """
    批量上传BOM文件到PLM系统API
    支持批量处理多个BOM文件并上传到PLM系统
    """
    try:
        # 1. 获取请求参数
        data = request.get_json()
        
        # 必需参数
        file_paths = data.get('file_paths', [])
        if not file_paths:
            return jsonify({
                'success': False,
                'error': '缺少file_paths参数，请提供要上传的BOM文件路径列表'
            })
        
        # 可选参数
        owner = data.get('owner', 'adm')
        creator = data.get('creator', 'adm')
        source = data.get('source', 'PPPE')
        operator = data.get('operator', 'sf')
        validate_only = data.get('validate_only', False)
        continue_on_error = data.get('continue_on_error', True)
        max_retries = data.get('max_retries', 0)
        
        # 设置输出目录
        tmp_dir = Path("data/tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        output_dir = data.get('output_dir', str(tmp_dir))
        
        logger.info(f"开始批量上传BOM文件，共 {len(file_paths)} 个文件")
        logger.info(f"参数: owner={owner}, creator={creator}, source={source}, operator={operator}")
        logger.info(f"验证模式: {validate_only}, 继续处理: {continue_on_error}, 重试次数: {max_retries}")
        
        # 2. 处理文件路径 - 转换相对路径为绝对路径
        processed_file_paths = []
        for file_path in file_paths:
            if not os.path.isabs(file_path):
                # 相对路径转换为绝对路径
                abs_path = os.path.join(os.getcwd(), file_path)
                processed_file_paths.append(abs_path)
            else:
                processed_file_paths.append(file_path)
        
        # 3. 导入并调用batch_upload_bom_files函数
        from new.plm_api_client import batch_upload_bom_files
        
        # 4. 执行批量上传
        result = batch_upload_bom_files(
            file_paths=processed_file_paths,
            owner=owner,
            creator=creator,
            source=source,
            operator=operator,
            validate_only=validate_only,
            output_dir=output_dir,
            continue_on_error=continue_on_error,
            max_retries=max_retries
        )
        
        logger.info(f"批量上传完成: 成功 {result.get('success_count', 0)}/{result.get('total', 0)} 个文件")
        
        # 5. 处理返回结果，转换绝对路径为相对路径
        def get_relative_path(abs_path):
            try:
                return str(Path(abs_path).relative_to(Path.cwd()))
            except:
                return abs_path
        
        # 转换结果中的文件路径
        if 'results' in result:
            for file_result in result['results']:
                if 'file_path' in file_result:
                    file_result['file_path'] = get_relative_path(file_result['file_path'])
                if 'output_file' in file_result:
                    file_result['output_file'] = get_relative_path(file_result['output_file'])
        
        # 转换失败和缺失文件列表中的路径
        if 'failed_files' in result:
            result['failed_files'] = [get_relative_path(fp) for fp in result['failed_files']]
        if 'missing_files' in result:
            result['missing_files'] = [get_relative_path(fp) for fp in result['missing_files']]
        
        # 6. 返回处理结果
        return jsonify({
            'success': result.get('success', False),
            'message': f"批量上传完成，成功 {result.get('success_count', 0)}/{result.get('total', 0)} 个文件",
            'data': result,
            'timestamp': datetime.now().isoformat(),
            'request_params': {
                'file_count': len(file_paths),
                'owner': owner,
                'creator': creator,
                'source': source,
                'operator': operator,
                'validate_only': validate_only,
                'continue_on_error': continue_on_error,
                'max_retries': max_retries
            }
        })
        
    except Exception as e:
        logger.error(f"批量上传BOM文件失败: {e}")
        return jsonify({
            'success': False,
            'error': f'批量上传BOM文件失败: {str(e)}',
            'timestamp': datetime.now().isoformat()
        })


def scheduled_check_and_push():
    """
    定时任务：检查待审批状态并自动推送已批准的design_id
    
    功能说明:
    1. 调用 check_and_update_pending_approvals 检查所有用户的待审批状态（不限制用户ID）
    2. 收集所有已批准的 design_id
    3. 对合并后的所有已批准的 design_id 调用 push_bom_files_by_design_id 推送到PLM系统
    """
    try:
        logger.info("=" * 80)
        logger.info("定时任务开始执行: 检查并推送已批准的审批")
        logger.info("=" * 80)
        
        logger.info("步骤1: 开始检查所有用户的待审批状态...")
        
        # 调用检查函数（不再限制用户ID）
        check_result = check_and_update_pending_approvals()
        
        if not check_result.get('success'):
            logger.error(f"检查审批状态失败: {check_result.get('error')}")
            return
        
        # 获取所有已批准的design_id
        all_approved_design_ids = check_result.get('approved_design_ids', [])
        total_pending_all = check_result.get('total_pending', 0)
        total_updated_all = check_result.get('updated_count', 0)
        
        # 去重处理（确保design_id不重复）
        all_approved_design_ids = list(set(all_approved_design_ids))
        
        logger.info("-" * 80)
        logger.info(f"步骤1完成: 检查所有用户的待审批状态")
        logger.info(f"  总待处理: {total_pending_all}, 总已更新: {total_updated_all}")
        logger.info(f"  已批准design_id数量: {len(all_approved_design_ids)}")
        
        if not all_approved_design_ids:
            logger.info("没有已批准的审批，无需推送")
            return
        
        # 步骤2: 对合并后的所有已批准的 design_id 执行推送
        logger.info(f"步骤2: 开始推送 {len(all_approved_design_ids)} 个已批准的 design_id...")
        
        push_results = []
        success_count = 0
        failed_count = 0
        
        for design_id in all_approved_design_ids:
            try:
                logger.info(f"正在推送 design_id: {design_id}")
                
                # 调用推送函数（使用默认参数）
                push_result = push_bom_files_by_design_id(
                    design_id=design_id,
                    owner="adm",
                    creator="adm",
                    source="PPPE",
                    operator="sf",
                    output_dir=None,
                    continue_on_error=True,
                    max_retries=0
                )
                
                push_results.append({
                    'design_id': design_id,
                    'success': push_result.get('success', False),
                    'db_update_success': push_result.get('db_update_success', False),
                    'message': push_result.get('message', '')
                })
                
                if push_result.get('success') and push_result.get('db_update_success'):
                    success_count += 1
                    logger.info(f"✅ design_id {design_id} 推送成功")
                else:
                    failed_count += 1
                    logger.warning(f"⚠️  design_id {design_id} 推送失败或数据库更新失败: {push_result.get('message')}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ design_id {design_id} 推送异常: {str(e)}")
                push_results.append({
                    'design_id': design_id,
                    'success': False,
                    'db_update_success': False,
                    'message': f'推送异常: {str(e)}'
                })
        
        # 汇总结果
        logger.info("=" * 80)
        logger.info(f"定时任务执行完成:")
        logger.info(f"  已批准的审批数: {len(all_approved_design_ids)}")
        logger.info(f"  推送成功: {success_count} 个")
        logger.info(f"  推送失败: {failed_count} 个")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"定时任务执行异常: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


def init_scheduler():
    """
    初始化定时任务调度器
    防止在Flask debug模式重启时重复创建调度器
    """
    global scheduler
    
    # 检查是否已经存在运行的调度器
    if scheduler is not None and scheduler.running:
        logger.info("定时任务调度器已在运行，跳过重复初始化")
        return
    
    try:
        # 如果存在旧的调度器但未运行，先关闭它
        if scheduler is not None:
            try:
                scheduler.shutdown(wait=False)
            except:
                pass
        
        scheduler = BackgroundScheduler()
        
        # 添加定时任务：每30分钟执行一次
        scheduler.add_job(
            func=scheduled_check_and_push,
            trigger=IntervalTrigger(minutes=30),
            id='check_and_push_approvals',
            name='检查并推送已批准的审批',
            replace_existing=True,
            max_instances=1  # 确保同一时间只有一个实例在运行
        )
        
        scheduler.start()
        logger.info("✅ 定时任务调度器已启动: 每30分钟检查一次已批准的审批")
        
    except Exception as e:
        logger.error(f"❌ 定时任务调度器启动失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    # Flask debug模式下的reloader会启动子进程，需要避免重复启动调度器
    # WERKZEUG_RUN_MAIN='true' 表示这是reloader启动的实际工作进程
    # 在debug模式下，第一次启动时这个变量不存在（父进程），重启后才会存在（子进程）
    # 在生产模式下，这个变量也不存在，但应该启动调度器
    
    # 启动时创建临时目录（无论是否启动调度器都需要）
    tmp_dir = Path("data/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"临时目录已创建: {tmp_dir}")
    
    # 判断是否应该启动调度器
    # Flask reloader机制说明：
    # - 第一次启动：父进程，WERKZEUG_RUN_MAIN 不存在，不应该启动调度器（会启动子进程）
    # - 重启后：子进程，WERKZEUG_RUN_MAIN='true'，应该启动调度器（实际运行应用）
    # - 生产模式：直接运行，WERKZEUG_RUN_MAIN 不存在，应该启动调度器
    
    werkzeug_run_main = os.environ.get('WERKZEUG_RUN_MAIN')
    
    should_start_scheduler = False
    
    if werkzeug_run_main == 'true':
        # Reloader的子进程（实际运行应用的进程）- 应该启动调度器
        should_start_scheduler = True
        logger.info("Flask reloader子进程，启动定时任务调度器")
    elif werkzeug_run_main is None:
        # 没有reloader，可能是生产模式或debug模式的父进程
        # 检查代码中是否有debug=True（简单判断）
        # 由于我们在app.run()中明确设置了debug=True，这里假设是debug模式
        # 如果将来需要生产模式，可以设置环境变量或修改代码
        logger.info("Flask reloader父进程或生产模式")
        # 为了安全，假设是debug模式的父进程，不启动调度器
        # 如果确实需要生产模式，可以通过环境变量控制
        if os.environ.get('FORCE_START_SCHEDULER') == 'true':
            should_start_scheduler = True
            logger.info("强制启动调度器（生产模式）")
        else:
            logger.info("跳过定时任务初始化（将在reloader子进程中启动）")
            should_start_scheduler = False
    
    # 启动定时任务调度器
    if should_start_scheduler:
        try:
            init_scheduler()
        except Exception as e:
            logger.error(f"定时任务启动失败，但继续启动应用: {str(e)}")
    
    # 启动Flask应用
    try:
        app.run(debug=True, host='0.0.0.0', port=5004, use_reloader=True)
    finally:
        # 应用关闭时停止定时任务
        if scheduler:
            try:
                scheduler.shutdown()
                logger.info("定时任务调度器已关闭")
            except Exception as e:
                logger.error(f"关闭定时任务调度器失败: {str(e)}")

