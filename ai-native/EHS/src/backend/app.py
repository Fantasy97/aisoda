#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web API for Law Date Validator
法律法规日期验证器的Web API接口
"""

from flask import Flask, request, jsonify, Response, send_from_directory, send_file
from flask_cors import CORS
import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback
import json
import time
import shutil
import os

# 添加项目路径到sys.path
current_file = Path(__file__).resolve()
backend_dir = current_file.parent  # src/backend
src_dir = backend_dir.parent       # src
project_root = src_dir.parent      # 项目根目录

# 添加必要的路径到sys.path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from tools.law_date_validator import LawDateValidator
from tools.excel_parser import ExcelParser
from config.paths import PathConfig
from werkzeug.utils import secure_filename

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置文件上传
UPLOAD_FOLDER = project_root / "tmp" / "uploads"
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB最大文件大小

# 确保上传目录存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局验证器实例
validator = None

def initialize_validator():
    """初始化验证器"""
    global validator
    try:
        # 初始化项目目录结构（静默模式）
        PathConfig.initialize_project_structure(verbose=False)
        
        # 获取JSON文件路径
        json_file = str(PathConfig.get_law_json_file())
        
        # 创建验证器实例
        validator = LawDateValidator(
            json_file=json_file,
            enable_searxng=True,
            enable_chat_api=True
        )
        
        logger.info("验证器初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"验证器初始化失败: {e}")
        logger.error(traceback.format_exc())
        return False

def clean_output_directories():
    """清理输出目录"""
    directories_to_clean = [
        project_root / "data" / "processed",
        project_root / "data" / "output"
    ]
    
    for directory in directories_to_clean:
        try:
            if directory.exists():
                # 删除目录中的所有文件和子目录
                for item in directory.iterdir():
                    if item.is_file():
                        item.unlink()
                        logger.info(f"已删除文件: {item}")
                    elif item.is_dir():
                        shutil.rmtree(item)
                        logger.info(f"已删除目录: {item}")
                logger.info(f"✓ 已清理目录: {directory}")
            else:
                logger.info(f"目录不存在，跳过清理: {directory}")
        except Exception as e:
            logger.error(f"清理目录失败 {directory}: {e}")
            # 不抛出异常，继续清理其他目录

@app.route('/', methods=['GET'])
def index():
    """首页接口"""
    return jsonify({
        'message': '法律法规日期验证器 API',
        'version': '1.0.0',
        'endpoints': {
            'validate_single': '/api/validate/single',
            'validate_all': '/api/validate/all (流式)',
            'validate_all_sync': '/api/validate/all/sync (同步)',
            'validate_batch': '/api/validate/batch',
            'health': '/api/health',
            'health_detailed': '/api/health?detailed=true',
            'test_connections': '/api/test-connections'
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    global validator
    
    # 检查是否需要详细检查（通过查询参数控制）
    detailed = request.args.get('detailed', 'false').lower() == 'true'
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'validator_initialized': validator is not None
    }
    
    if validator:
        # 基本检查
        health_status.update({
            'json_file_exists': PathConfig.get_law_json_file().exists(),
            'searxng_enabled': validator.crawler.enable_searxng if hasattr(validator, 'crawler') else False,
            'chat_api_enabled': validator.crawler.enable_chat_api if hasattr(validator, 'crawler') else False
        })
        
        # 只有在请求详细检查时才测试外部服务连接
        if detailed:
            try:
                searxng_status = validator.crawler.test_searxng_connection() if validator.crawler.enable_searxng else 'disabled'
                chat_api_status = validator.crawler.test_chat_api_connection() if validator.crawler.enable_chat_api else 'disabled'
                
                health_status.update({
                    'searxng_connection': searxng_status,
                    'chat_api_connection': chat_api_status
                })
            except Exception as e:
                health_status['status'] = 'degraded'
                health_status['error'] = str(e)
    
    return jsonify(health_status)

@app.route('/api/test-connections', methods=['GET'])
def test_connections():
    """测试外部服务连接"""
    global validator
    
    if not validator:
        return jsonify({
            'success': False,
            'error': '验证器未初始化'
        }), 500
    
    try:
        results = {}
        
        if validator.crawler.enable_searxng:
            results['searxng'] = validator.crawler.test_searxng_connection()
        else:
            results['searxng'] = 'disabled'
            
        if validator.crawler.enable_chat_api:
            results['chat_api'] = validator.crawler.test_chat_api_connection()
        else:
            results['chat_api'] = 'disabled'
        
        return jsonify({
            'success': True,
            'connections': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"连接测试失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload/excel', methods=['POST'])
def upload_excel():
    """上传并解析Excel文件"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有文件被上传'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '文件名为空'
            }), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': '不支持的文件格式，仅支持 .xlsx 和 .xls'
            }), 400
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = app.config['UPLOAD_FOLDER'] / filename
        
        file.save(str(filepath))
        logger.info(f"文件已保存: {filepath}")
        
        # 解析Excel文件
        parser = ExcelParser()
        result = parser.parse_excel_to_law_format(str(filepath))
        
        if result['success']:
            logger.info(f"Excel解析成功: {result['total_count']} 条数据")
            return jsonify({
                'success': True,
                'data': result['data'],
                'sheet_name': result['sheet_name'],
                'total_count': result['total_count'],
                'error_count': result['error_count'],
                'errors': result['errors'],
                'filename': filename
            })
        else:
            logger.error(f"Excel解析失败: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"上传Excel文件失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate/single', methods=['POST'])
def validate_single_law():
    """验证单个法律法规"""
    global validator
    
    if not validator:
        return jsonify({
            'success': False,
            'error': '验证器未初始化'
        }), 500
    
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '请求数据为空'
            }), 400
        
        # 验证必需字段
        required_fields = ['法律、法规、标准及其他要求']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必需字段: {field}'
                }), 400
        
        # 设置默认值
        law_item = {
            '法律、法规、标准及其他要求': data.get('法律、法规、标准及其他要求', ''),
            '施行（修改）日期': data.get('施行（修改）日期', ''),
            '获取途径': data.get('获取途径', ''),
            '序号': data.get('序号', ''),
            '网址': data.get('网址', '')
        }
        
        category = data.get('category', '未知分类')
        subcategory = data.get('subcategory', '未知子分类')
        
        # 执行验证
        result = validator.validate_single_law(law_item, category, subcategory)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"单个法律验证失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate/all', methods=['POST'])
def validate_all_laws():
    """验证所有法律法规（流式响应）"""
    global validator
    
    if not validator:
        return jsonify({
            'success': False,
            'error': '验证器未初始化'
        }), 500
    
    def generate_validation_stream():
        """生成验证流"""
        try:
            # 发送开始信号和功能说明
            yield f"data: {json.dumps({'type': 'start', 'message': '法律法规日期验证器', 'timestamp': datetime.now().isoformat()})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '=' * 50, 'log_type': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '功能说明:', 'log_type': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '- 官方数据库来源: 仅使用 flk.npc.gov.cn 查询', 'log_type': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '- 其他来源: 优先官方数据库，失败时依次使用 SearXNG 和 ChatAPI 备用搜索', 'log_type': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '- 对比原始日期与查询结果的一致性', 'log_type': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '', 'log_type': 'info'})}\n\n"
            
            # 测试SearXNG连接
            if validator.crawler.enable_searxng:
                yield f"data: {json.dumps({'type': 'log', 'message': '测试SearXNG连接...', 'log_type': 'info'})}\n\n"
                try:
                    if validator.crawler.test_searxng_connection():
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ SearXNG连接正常', 'log_type': 'success'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': '✗ SearXNG连接失败，将仅使用官方数据库', 'log_type': 'warning'})}\n\n"
                        validator.crawler.enable_searxng = False
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✗ SearXNG连接测试异常: {str(e)}，将仅使用官方数据库', 'log_type': 'warning'})}\n\n"
                    validator.crawler.enable_searxng = False
            
            # 测试ChatAPI连接
            if validator.crawler.enable_chat_api:
                yield f"data: {json.dumps({'type': 'log', 'message': '测试ChatAPI连接...', 'log_type': 'info'})}\n\n"
                try:
                    if validator.crawler.test_chat_api_connection():
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ ChatAPI连接正常', 'log_type': 'success'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': '✗ ChatAPI连接失败，将不使用ChatAPI', 'log_type': 'warning'})}\n\n"
                        validator.crawler.enable_chat_api = False
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✗ ChatAPI连接测试异常: {str(e)}，将不使用ChatAPI', 'log_type': 'warning'})}\n\n"
                    validator.crawler.enable_chat_api = False
            
            yield f"data: {json.dumps({'type': 'log', 'message': '', 'log_type': 'info'})}\n\n"
            
            # 获取所有法律数据
            data = validator.load_data()
            if not data:
                yield f"data: {json.dumps({'type': 'error', 'message': '无法加载法律数据'})}\n\n"
                return
            
            # 重置统计信息
            validator.reset_stats()
            
            yield f"data: {json.dumps({'type': 'log', 'message': '开始验证法律法规日期...', 'log_type': 'info'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '=' * 80, 'log_type': 'info'})}\n\n"
            
            all_laws = []
            # 正确访问分类数据结构
            classification_data = data.get('分类数据', {})
            yield f"data: {json.dumps({'type': 'log', 'message': f'找到分类数据，包含 {len(classification_data)} 个分类', 'log_type': 'info'})}\n\n"
            
            for category, subcategories in classification_data.items():
                if isinstance(subcategories, dict):
                    yield f"data: {json.dumps({'type': 'log', 'message': f'处理分类: {category}，包含 {len(subcategories)} 个子分类', 'log_type': 'info'})}\n\n"
                    for subcategory, laws in subcategories.items():
                        if isinstance(laws, list):
                            yield f"data: {json.dumps({'type': 'log', 'message': f'  子分类: {subcategory}，包含 {len(laws)} 条法律', 'log_type': 'info'})}\n\n"
                            for law in laws:
                                all_laws.append((law, category, subcategory))
            
            total_laws = len(all_laws)
            yield f"data: {json.dumps({'type': 'progress', 'current': 0, 'total': total_laws, 'message': f'准备验证 {total_laws} 个法律法规'})}\n\n"
            
            if total_laws == 0:
                yield f"data: {json.dumps({'type': 'error', 'message': '没有找到任何法律数据进行验证'})}\n\n"
                return
            
            results = []
            
            # 逐个验证
            for i, (law_item, category, subcategory) in enumerate(all_laws, 1):
                try:
                    # 更新统计信息
                    validator.stats['total_laws'] += 1
                    
                    # 显示开始验证的法律信息
                    law_name = law_item.get('法律、法规、标准及其他要求', '未知法律')
                    original_date = law_item.get('施行日期', '')
                    source = law_item.get('获取途径', '')
                    
                    # 发送验证开始信息
                    info_message = f"验证法律: {law_name}"
                    if original_date:
                        info_message += f" | 原始日期: {original_date}"
                    if source:
                        info_message += f" | 来源: {source}"
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': info_message, 'log_type': 'info'})}\n\n"
                    
                    # 验证单个法律
                    result = validator.validate_single_law(law_item, category, subcategory)
                    results.append(result)
                    
                    # 发送进度更新
                    law_name = law_item.get('法律、法规、标准及其他要求', '未知法律')
                    status = result.get('状态', '未知')
                    date_matched = result.get('日期匹配', False)
                    original_date = result.get('原始日期', '')
                    found_date = result.get('查询日期', '')
                    source = result.get('获取途径', '')
                    
                    # 根据实际的状态值和日期匹配情况确定显示格式
                    if status == '找到':
                        if date_matched:
                            if found_date and original_date:
                                if found_date == original_date:
                                    date_info = f"日期精确匹配: {original_date}"
                                else:
                                    date_info = f"日期匹配(搜索日期更旧): {found_date} <= {original_date}"
                            else:
                                date_info = "日期匹配"
                            message = f"[{i:3d}] ✓ {law_name[:35]:<35} - {date_info}"
                            log_type = 'success'
                        else:
                            date_info = f"日期不匹配: 原始({original_date}) vs 查询({found_date})" if found_date else f"日期不匹配: {original_date}"
                            message = f"[{i:3d}] ⚠ {law_name[:35]:<35} - {date_info}"
                            log_type = 'warning'
                    elif status == '跳过':
                        message = f"[{i:3d}] - {law_name[:35]:<35} - 跳过验证"
                        log_type = 'info'
                    else:  # '未找到' 或 '错误'
                        error_reason = result.get('错误信息', '未找到相关信息')
                        message = f"[{i:3d}] ✗ {law_name[:35]:<35} - {error_reason}"
                        log_type = 'error'
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': message, 'log_type': log_type, 'timestamp': datetime.now().isoformat()})}\n\n"
                    yield f"data: {json.dumps({'type': 'progress', 'current': i, 'total': total_laws, 'message': f'已验证 {i}/{total_laws}'})}\n\n"
                    
                    # 添加空行分隔每个验证结果
                    if i % 5 == 0:  # 每5个法律后添加一个分隔线
                        yield f"data: {json.dumps({'type': 'log', 'message': '─' * 80, 'log_type': 'info'})}\n\n"
                    
                    # 请求间隔 - 跟随main函数的逻辑
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"[{i:3d}] ✗ {law_item.get('法律、法规、标准及其他要求', '未知法律')[:40]:<40} - 验证异常: {str(e)}"
                    yield f"data: {json.dumps({'type': 'log', 'message': error_msg, 'log_type': 'error', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
                    results.append({
                        '序号': str(i),
                        '法律名称': law_item.get('法律、法规、标准及其他要求', '未知法律'),
                        '状态': '验证异常',
                        'error': str(e)
                    })
            
            # 生成报告
            report = validator.generate_report(results)
            
            # 清理输出目录
            clean_output_directories()
            
            # 保存结果
            html_file = validator.save_results(results, report)
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'message': '全量验证完成！', 'results': {'total': len(results), 'statistics': validator.stats, 'files': {'html_file': str(html_file)}}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"全量验证流失败: {e}")
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'message': f'验证过程中发生错误: {str(e)}'})}\n\n"
    
    return Response(
        generate_validation_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.route('/api/validate/all/sync', methods=['POST'])
def validate_all_laws_sync():
    """验证所有法律法规（同步版本）"""
    global validator
    
    if not validator:
        return jsonify({
            'success': False,
            'error': '验证器未初始化'
        }), 500
    
    try:
        # 测试SearXNG连接
        if validator.crawler.enable_searxng:
            if not validator.crawler.test_searxng_connection():
                validator.crawler.enable_searxng = False
        
        # 测试ChatAPI连接
        if validator.crawler.enable_chat_api:
            if not validator.crawler.test_chat_api_connection():
                validator.crawler.enable_chat_api = False
        
        # 执行全量验证
        results = validator.validate_all_laws()
        
        # 生成报告
        report = validator.generate_report(results)
        
        # 清理输出目录
        clean_output_directories()
        
        # 保存结果
        results_file, report_file, html_file = validator.save_results(results, report)
        
        # 返回结果
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'statistics': validator.stats,
                'report': report,
                'files': {
                    'results_file': str(results_file),
                    'report_file': str(report_file),
                    'html_file': str(html_file)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"全量验证失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate/batch', methods=['POST'])
def validate_batch_laws():
    """批量验证法律法规"""
    global validator
    
    if not validator:
        return jsonify({
            'success': False,
            'error': '验证器未初始化'
        }), 500
    
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data or 'laws' not in data:
            return jsonify({
                'success': False,
                'error': '请求数据格式错误，需要laws数组'
            }), 400
        
        laws = data['laws']
        if not isinstance(laws, list):
            return jsonify({
                'success': False,
                'error': 'laws必须是数组格式'
            }), 400
        
        # 重置统计信息
        validator.reset_stats()
        
        results = []
        
        # 逐个验证
        for i, law_data in enumerate(laws):
            try:
                # 更新统计信息
                validator.stats['total_laws'] += 1
                
                law_item = {
                    '法律、法规、标准及其他要求': law_data.get('法律、法规、标准及其他要求', ''),
                    '施行（修改）日期': law_data.get('施行（修改）日期', ''),
                    '获取途径': law_data.get('获取途径', ''),
                    '序号': law_data.get('序号', str(i + 1)),
                    '网址': law_data.get('网址', '')
                }
                
                category = law_data.get('category', '批量验证')
                subcategory = law_data.get('subcategory', f'批次{i + 1}')
                
                result = validator.validate_single_law(law_item, category, subcategory)
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量验证第{i + 1}项失败: {e}")
                results.append({
                    '序号': str(i + 1),
                    '法律名称': law_data.get('法律、法规、标准及其他要求', '未知'),
                    '状态': '错误',
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'total': len(results),
                'processed': len([r for r in results if r.get('状态') != '错误'])
            }
        })
        
    except Exception as e:
        logger.error(f"批量验证失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/validate/parsed', methods=['POST'])
def validate_parsed_data():
    """验证解析后的数据（流式响应）"""
    global validator
    
    if not validator:
        return jsonify({
            'success': False,
            'error': '验证器未初始化'
        }), 500
    
    # 获取请求数据
    try:
        request_data = request.get_json()
        if not request_data or 'data' not in request_data:
            return jsonify({
                'success': False,
                'error': '请求数据格式错误，需要包含data字段'
            }), 400
        
        parsed_laws = request_data['data']
        if not isinstance(parsed_laws, list) or len(parsed_laws) == 0:
            return jsonify({
                'success': False,
                'error': '数据格式错误，data字段应为非空数组'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'解析请求数据失败: {str(e)}'
        }), 400
    
    def generate_validation_stream():
        """生成验证流"""
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'type': 'start', 'message': '开始验证解析数据', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            # 测试连接
            yield f"data: {json.dumps({'type': 'log', 'message': '测试外部服务连接...', 'log_type': 'info'})}\n\n"
            
            # 测试SearXNG连接
            if validator.crawler.enable_searxng:
                try:
                    if validator.crawler.test_searxng_connection():
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ SearXNG连接正常', 'log_type': 'success'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': '✗ SearXNG连接失败', 'log_type': 'warning'})}\n\n"
                        validator.crawler.enable_searxng = False
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✗ SearXNG连接异常: {str(e)}', 'log_type': 'warning'})}\n\n"
                    validator.crawler.enable_searxng = False
            
            # 测试ChatAPI连接
            if validator.crawler.enable_chat_api:
                try:
                    if validator.crawler.test_chat_api_connection():
                        yield f"data: {json.dumps({'type': 'log', 'message': '✓ ChatAPI连接正常', 'log_type': 'success'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'log', 'message': '✗ ChatAPI连接失败', 'log_type': 'warning'})}\n\n"
                        validator.crawler.enable_chat_api = False
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'log', 'message': f'✗ ChatAPI连接异常: {str(e)}', 'log_type': 'warning'})}\n\n"
                    validator.crawler.enable_chat_api = False
            
            # 重置统计信息
            validator.reset_stats()
            
            total_laws = len(parsed_laws)
            yield f"data: {json.dumps({'type': 'progress', 'current': 0, 'total': total_laws, 'message': f'准备验证 {total_laws} 条解析数据'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '开始验证解析数据...', 'log_type': 'info'})}\n\n"
            
            results = []
            
            # 逐个验证解析的法律数据
            for i, law_item in enumerate(parsed_laws, 1):
                try:
                    # 更新统计信息
                    validator.stats['total_laws'] += 1
                    
                    # 获取法律信息
                    law_name = law_item.get('法律、法规、标准及其他要求', '未知法律')
                    original_date = law_item.get('施行（修改）日期', '')
                    source = law_item.get('获取途径', '')
                    
                    # 发送验证开始信息
                    info_message = f"验证法律: {law_name}"
                    if original_date:
                        info_message += f" | 原始日期: {original_date}"
                    if source:
                        info_message += f" | 来源: {source}"
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': info_message, 'log_type': 'info'})}\n\n"
                    
                    # 验证单个法律 - 使用默认分类
                    result = validator.validate_single_law(law_item, '解析数据', '导入数据')
                    results.append(result)
                    
                    # 发送进度更新
                    status = result.get('状态', '未知')
                    date_matched = result.get('日期匹配', False)
                    original_date = result.get('原始日期', '')
                    found_date = result.get('查询日期', '')
                    
                    # 根据验证结果显示不同格式的消息
                    if status == '找到':
                        if date_matched:
                            if found_date and original_date:
                                if found_date == original_date:
                                    date_info = f"日期精确匹配: {original_date}"
                                else:
                                    date_info = f"日期匹配: {found_date} <= {original_date}"
                            else:
                                date_info = "日期匹配"
                            message = f"[{i:3d}] ✓ {law_name[:40]:<40} - {date_info}"
                            log_type = 'success'
                        else:
                            date_info = f"日期不匹配: 原始({original_date}) vs 查询({found_date})" if found_date else f"日期不匹配: {original_date}"
                            message = f"[{i:3d}] ⚠ {law_name[:40]:<40} - {date_info}"
                            log_type = 'warning'
                    elif status == '跳过':
                        message = f"[{i:3d}] - {law_name[:40]:<40} - 跳过验证"
                        log_type = 'info'
                    else:  # '未找到' 或 '错误'
                        error_reason = result.get('错误信息', '未找到相关信息')
                        message = f"[{i:3d}] ✗ {law_name[:40]:<40} - {error_reason}"
                        log_type = 'error'
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': message, 'log_type': log_type, 'timestamp': datetime.now().isoformat()})}\n\n"
                    yield f"data: {json.dumps({'type': 'progress', 'current': i, 'total': total_laws, 'message': f'已验证 {i}/{total_laws}'})}\n\n"
                    
                    # 添加分隔线
                    if i % 5 == 0:
                        yield f"data: {json.dumps({'type': 'log', 'message': '─' * 80, 'log_type': 'info'})}\n\n"
                    
                    # 请求间隔
                    time.sleep(1)
                    
                except Exception as e:
                    error_msg = f"[{i:3d}] ✗ {law_item.get('法律、法规、标准及其他要求', '未知法律')[:40]:<40} - 验证异常: {str(e)}"
                    yield f"data: {json.dumps({'type': 'log', 'message': error_msg, 'log_type': 'error', 'timestamp': datetime.now().isoformat()})}\n\n"
                    
                    results.append({
                        '序号': str(i),
                        '法律名称': law_item.get('法律、法规、标准及其他要求', '未知法律'),
                        '状态': '验证异常',
                        'error': str(e)
                    })
            
            # 生成报告
            report = validator.generate_report(results)
            
            # 清理输出目录
            clean_output_directories()
            
            # 保存结果
            html_file = validator.save_results(results, report)
            
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'message': '解析数据验证完成！', 'results': {'total': len(results), 'statistics': validator.stats, 'files': {'html_file': str(html_file)}}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
        except Exception as e:
            logger.error(f"解析数据验证失败: {e}")
            logger.error(traceback.format_exc())
            yield f"data: {json.dumps({'type': 'error', 'message': f'验证过程中发生错误: {str(e)}'})}\n\n"
    
    return Response(
        generate_validation_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

def startup_check():
    """启动时检查整个项目"""
    logger.info("开始启动检查...")
    
    # 检查项目结构
    logger.info("检查项目目录结构...")
    try:
        PathConfig.initialize_project_structure(verbose=True)
        logger.info("✓ 项目目录结构正常")
    except Exception as e:
        logger.error(f"✗ 项目目录结构检查失败: {e}")
        return False
    
    # 检查输入文件
    json_file = PathConfig.get_law_json_file()
    if json_file.exists():
        logger.info(f"✓ 输入文件存在: {json_file}")
    else:
        logger.warning(f"⚠ 输入文件不存在: {json_file}")
    
    # 初始化验证器
    logger.info("初始化验证器...")
    if initialize_validator():
        logger.info("✓ 验证器初始化成功")
    else:
        logger.error("✗ 验证器初始化失败")
        return False
    
    # 检查外部服务配置（不进行实际连接测试）
    if validator:
        logger.info("检查外部服务配置...")
        
        if validator.crawler.enable_searxng:
            logger.info("✓ SearXNG已启用")
        else:
            logger.info("- SearXNG已禁用")
        
        if validator.crawler.enable_chat_api:
            logger.info("✓ ChatAPI已启用")
        else:
            logger.info("- ChatAPI已禁用")
        
        logger.info("提示: 使用 /api/test-connections 接口测试外部服务连接")
    
    logger.info("启动检查完成")
    return True

@app.route('/api/download/html', methods=['GET'])
def download_html_report():
    """下载HTML报告"""
    try:
        # 获取最新的HTML报告文件
        output_dir = PathConfig.get_output_dir()
        logger.info(f"查找HTML文件，输出目录: {output_dir}")
        logger.info(f"输出目录是否存在: {output_dir.exists()}")
        logger.info(f"当前工作目录: {Path.cwd()}")
        
        # 先查找所有HTML文件
        all_html = list(output_dir.glob('*.html'))
        logger.info(f"输出目录中所有HTML文件: {all_html}")
        
        # 查找法律验证报告HTML文件
        html_files = list(output_dir.glob('law_validation_report_*.html'))
        logger.info(f"找到法律验证HTML文件: {html_files}")
        
        if not html_files:
            return jsonify({
                'success': False,
                'error': f'未找到HTML报告文件，输出目录: {output_dir}，所有HTML文件: {[str(f) for f in all_html]}'
            }), 404
        
        # 获取最新的文件
        latest_html = max(html_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"选择最新HTML文件: {latest_html}")
        logger.info(f"文件是否存在: {latest_html.exists()}")
        
        from flask import send_file
        return send_file(
            str(latest_html),  # 转换为字符串路径
            as_attachment=True,
            download_name=f'法律法规验证报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html',
            mimetype='text/html'
        )
        
    except Exception as e:
        logger.error(f"下载HTML报告失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

@app.route('/api/download/results', methods=['GET'])
def download_results():
    """下载JSON结果文件"""
    try:
        # 获取最新的结果文件
        output_dir = PathConfig.get_output_dir()
        logger.info(f"查找JSON文件，输出目录: {output_dir}")
        
        # 查找法律验证结果JSON文件
        json_files = list(output_dir.glob('law_validation_results_*.json'))
        logger.info(f"找到法律验证JSON文件: {json_files}")
        
        if not json_files:
            # 尝试查找所有JSON文件进行调试
            all_json = list(output_dir.glob('*.json'))
            logger.info(f"输出目录中所有JSON文件: {all_json}")
            return jsonify({
                'success': False,
                'error': f'未找到结果文件，输出目录: {output_dir}，所有JSON文件: {[str(f) for f in all_json]}'
            }), 404
        
        # 获取最新的文件
        latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"选择最新JSON文件: {latest_json}")
        
        from flask import send_file
        return send_file(
            str(latest_json),  # 转换为字符串路径
            as_attachment=True,
            download_name=f'法律法规验证结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f"下载结果文件失败: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

@app.route('/api/debug/files', methods=['GET'])
def debug_files():
    """调试文件路径"""
    try:
        output_dir = PathConfig.get_output_dir()
        data_dir = PathConfig.get_data_dir()
        
        # 列出所有文件
        output_files = list(output_dir.glob('*')) if output_dir.exists() else []
        data_files = list(data_dir.glob('*')) if data_dir.exists() else []
        
        return jsonify({
            'success': True,
            'paths': {
                'output_dir': str(output_dir),
                'data_dir': str(data_dir),
                'output_exists': output_dir.exists(),
                'data_exists': data_dir.exists()
            },
            'files': {
                'output_files': [str(f) for f in output_files],
                'data_files': [str(f) for f in data_files]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/report', methods=['GET'])
def download_text_report():
    """下载文本报告"""
    try:
        # 获取最新的文本报告文件
        output_dir = PathConfig.get_output_dir()
        txt_files = list(output_dir.glob('law_validation_report_*.txt'))
        
        if not txt_files:
            return jsonify({
                'success': False,
                'error': '未找到文本报告文件'
            }), 404
        
        # 获取最新的文件
        latest_txt = max(txt_files, key=lambda x: x.stat().st_mtime)
        
        from flask import send_file
        return send_file(
            latest_txt,
            as_attachment=True,
            download_name=f'法律法规验证报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt',
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.error(f"下载文本报告失败: {e}")
        return jsonify({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }), 500

# 静态文件服务路由
@app.route('/excel_parser')
def serve_excel_parser():
    """提供excel_parser.html页面"""
    try:
        frontend_dir = src_dir / "frontend"
        file_path = frontend_dir / "excel_parser.html"
        logger.info(f"尝试提供文件: {file_path}")
        return send_file(file_path)
    except Exception as e:
        logger.error(f"提供excel_parser.html失败: {str(e)}")
        return jsonify({'error': '页面加载失败'}), 500

@app.route('/static/<path:filename>')
def serve_static_files(filename):
    """提供静态文件服务"""
    try:
        frontend_dir = src_dir / "frontend"
        return send_from_directory(frontend_dir, filename)
    except Exception as e:
        logger.error(f"提供静态文件失败: {str(e)}")
        return jsonify({'error': '文件未找到'}), 404

if __name__ == '__main__':
    # 启动时检查
    if not startup_check():
        logger.error("启动检查失败，退出程序")
        sys.exit(1)
    
    # 启动Flask应用
    logger.info("启动Flask应用...")
    app.run(
        host='0.0.0.0',
        port=5005,
        debug=False,  # 关闭debug模式避免重复启动
        use_reloader=False  # 关闭自动重载
    )