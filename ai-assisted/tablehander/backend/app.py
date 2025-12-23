from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys

# 添加tools目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.join(current_dir, 'tools')
sys.path.insert(0, tools_dir)

from data_query import DataQueryHandler
from word_parser import WordParser

# 配置静态文件路径
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(current_dir), 'frontend')

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})  # 允许跨域请求

# 配置文件上传
UPLOAD_FOLDER = os.path.join(current_dir, 'uploads')
ALLOWED_EXTENSIONS = {'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化数据查询处理器和Word解析器
query_handler = DataQueryHandler()
word_parser = WordParser()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def safe_filename_for_output(filename):
    """
    为输出文件生成安全的文件名，保留原始文件名的可读性
    但移除潜在的安全风险字符
    """
    import re
    # 移除路径分隔符和其他危险字符
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除连续的点（防止路径遍历）
    safe_name = re.sub(r'\.{2,}', '.', safe_name)
    # 确保不以点开头或结尾
    safe_name = safe_name.strip('.')
    # 限制长度
    if len(safe_name) > 200:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:200-len(ext)] + ext
    return safe_name

@app.route('/api/query', methods=['POST'])
def query_data():
    """
    数据查询接口
    POST /api/query
    Body: {
        "keyword": "营业收入",
        "include_context": true,
        "case_sensitive": false
    }
    """
    try:
        data = request.get_json()
        if not data or 'keyword' not in data:
            return jsonify({
                'success': False,
                'message': '请提供查询关键词'
            }), 400
        
        keyword = data['keyword']
        include_context = data.get('include_context', True)
        case_sensitive = data.get('case_sensitive', False)
        
        # 调用查询功能
        results = query_handler.query_by_partial_key(
            keyword, 
            case_sensitive=case_sensitive, 
            include_context=include_context
        )
        
        return jsonify({
            'success': True,
            'message': f'找到 {len(results)} 条结果',
            'data': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'查询失败: {str(e)}'
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history_files():
    """
    获取历史文件列表接口
    GET /api/history
    """
    try:
        files_info = query_handler.get_history_files_info()
        
        return jsonify({
            'success': True,
            'message': f'找到 {len(files_info)} 个文件',
            'data': files_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取历史文件失败: {str(e)}'
        }), 500

@app.route('/api/file/<filename>', methods=['GET'])
def get_file_content(filename):
    """
    根据文件名获取文件内容接口
    GET /api/file/<filename>
    """
    try:
        result = query_handler.get_file_by_name(filename)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取文件失败: {str(e)}'
        }), 500

@app.route('/api/update-data', methods=['POST'])
def update_example_data():
    """
    更新example_data.json文件接口
    POST /api/update-data
    Body: {
        "data": {
            "key1": "value1",
            "key2": "value2",
            ...
        }
    }
    """
    print("收到更新数据请求")
    try:
        request_data = request.get_json()
        print(f"请求数据: {request_data}")
        if not request_data or 'data' not in request_data:
            return jsonify({
                'success': False,
                'message': '请提供要更新的数据'
            }), 400
        
        update_data = request_data['data']
        
        # 验证数据格式
        if not isinstance(update_data, dict):
            return jsonify({
                'success': False,
                'message': '数据必须是键值对格式的对象'
            }), 400
        
        if not update_data:
            return jsonify({
                'success': False,
                'message': '更新数据不能为空'
            }), 400
        
        # 调用更新功能
        result = query_handler.update_example_data(update_data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'数据更新失败: {str(e)}'
        }), 500

@app.route('/api/parse-word', methods=['POST'])
def parse_word_document():
    """
    Word文档解析接口
    POST /api/parse-word
    Body: {
        "input_file": "path/to/document.docx",
        "output_path": "path/to/output.json" (可选)
    }
    """
    try:
        data = request.get_json()
        if not data or 'input_file' not in data:
            return jsonify({
                'success': False,
                'message': '请提供输入文件路径'
            }), 400
        
        input_file = data['input_file']
        output_path = data.get('output_path', None)
        
        # 检查输入文件是否存在
        if not os.path.exists(input_file):
            return jsonify({
                'success': False,
                'message': f'输入文件不存在: {input_file}'
            }), 400
        
        # 调用Word解析功能
        result = word_parser.extract_full_document(input_file, output_path)
        
        # 统计信息
        paragraphs = [item for item in result['document_structure'] if item['type'] == 'paragraph']
        tables = [item for item in result['document_structure'] if item['type'] == 'table']
        
        return jsonify({
            'success': True,
            'message': '文档解析成功',
            'data': {
                'document_structure': result['document_structure'],
                'statistics': {
                    'total_items': len(result['document_structure']),
                    'paragraphs': len(paragraphs),
                    'tables': len(tables)
                },
                'output_file': output_path if output_path else '默认输出路径'
            }
        })
        
    except FileNotFoundError as e:
        return jsonify({
            'success': False,
            'message': f'文件不存在: {str(e)}'
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文档解析失败: {str(e)}'
        }), 500

@app.route('/api/history/<filename>', methods=['DELETE'])
def delete_history_file(filename):
    """
    删除历史文件接口
    DELETE /api/history/<filename>
    """
    try:
        # 构建历史文件的完整路径
        history_dir = os.path.join('..', 'data', 'history')
        file_path = os.path.join(history_dir, filename)
        
        # 安全检查：确保文件在history目录内
        abs_history_dir = os.path.abspath(history_dir)
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(abs_history_dir):
            return jsonify({
                'success': False,
                'message': '非法的文件路径'
            }), 400
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': f'文件不存在: {filename}'
            }), 404
        
        # 检查是否为JSON文件
        if not filename.lower().endswith('.json'):
            return jsonify({
                'success': False,
                'message': '只能删除JSON文件'
            }), 400
        
        # 删除文件
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': f'文件 {filename} 已成功删除'
        })
        
    except PermissionError:
        return jsonify({
            'success': False,
            'message': '没有权限删除该文件'
        }), 403
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除文件失败: {str(e)}'
        }), 500

@app.route('/api/upload-and-parse', methods=['POST'])
def upload_and_parse_word():
    """
    上传并解析Word文档接口
    POST /api/upload-and-parse
    Form-data: file (Word文档文件)
    """
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': '只支持.doc和.docx文件'
            }), 400
        
        # 保存上传的文件
        original_filename = file.filename
        secure_filename_for_upload = secure_filename(original_filename)
        import time
        timestamp = str(int(time.time()))
        
        # 为临时文件使用安全文件名
        temp_name, temp_ext = os.path.splitext(secure_filename_for_upload)
        unique_filename = f"{temp_name}_{timestamp}{temp_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        try:
            # 使用原始文件名生成输出文件名（保持用户期望的文件名，但确保安全）
            original_name, original_ext = os.path.splitext(original_filename)
            safe_output_name = safe_filename_for_output(original_name)
            
            # 检查文件是否已存在，如果存在则添加序号
            base_output_name = safe_output_name
            counter = 1
            output_filename = f"{safe_output_name}.json"
            output_path = os.path.join('..', 'data', 'history', output_filename)
            
            while os.path.exists(output_path):
                safe_output_name = f"{base_output_name}({counter})"
                output_filename = f"{safe_output_name}.json"
                output_path = os.path.join('..', 'data', 'history', output_filename)
                counter += 1
            
            # 调试日志
            print(f"原始文件名: {original_filename}")
            print(f"输出文件名: {output_filename}")
            print(f"输出路径: {output_path}")
            
            # 调用Word解析功能
            result = word_parser.extract_full_document(file_path, output_path)
            
            # 统计信息
            paragraphs = [item for item in result['document_structure'] if item['type'] == 'paragraph']
            tables = [item for item in result['document_structure'] if item['type'] == 'table']
            
            # 删除临时上传文件
            try:
                os.remove(file_path)
            except:
                pass  # 忽略删除失败
            
            return jsonify({
                'success': True,
                'message': '文档上传并解析成功',
                'data': {
                    'original_filename': original_filename,
                    'output_filename': output_filename,
                    'output_path': output_path,
                    'statistics': {
                        'total_items': len(result['document_structure']),
                        'paragraphs': len(paragraphs),
                        'tables': len(tables)
                    }
                }
            })
            
        except Exception as parse_error:
            # 删除上传的文件
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify({
                'success': False,
                'message': f'文档解析失败: {str(parse_error)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文件上传失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': 'API服务运行正常',
        'version': '1.0.0'
    })

@app.route('/api/test-update', methods=['POST', 'OPTIONS'])
def test_update():
    """测试更新接口"""
    if request.method == 'OPTIONS':
        # 处理预检请求
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response
    
    print("收到测试更新请求")
    try:
        request_data = request.get_json()
        print(f"测试请求数据: {request_data}")
        
        return jsonify({
            'success': True,
            'message': '测试接口工作正常',
            'received_data': request_data
        })
        
    except Exception as e:
        print(f"测试接口错误: {e}")
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

# 前端页面路由
@app.route('/')
def index():
    """主页 - 信息搜索页面"""
    return send_file(os.path.join(frontend_dir, 'index.html'))

@app.route('/history')
def history():
    """历史数据页面"""
    return send_file(os.path.join(frontend_dir, 'history.html'))

@app.route('/css/<path:filename>')
def css_files(filename):
    """CSS文件服务"""
    return send_from_directory(os.path.join(frontend_dir, 'css'), filename)

@app.route('/js/<path:filename>')
def js_files(filename):
    """JavaScript文件服务"""
    return send_from_directory(os.path.join(frontend_dir, 'js'), filename)

@app.route('/assets/<path:filename>')
def assets_files(filename):
    """静态资源文件服务"""
    return send_from_directory(os.path.join(frontend_dir, 'assets'), filename)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    print("🚀 启动综合信息查询服务...")
    print("🌐 前端页面:")
    print("  http://localhost:5006/ - 信息搜索页面")
    print("  http://localhost:5006/history - 历史数据页面")
    print()
    print("📋 API接口:")
    print("  POST /api/query - 数据查询")
    print("  GET  /api/history - 获取历史文件列表")
    print("  GET  /api/file/<filename> - 获取文件内容")
    print("  POST /api/update-data - 更新example_data.json数据")
    print("  DELETE /api/history/<filename> - 删除历史文件")
    print("  POST /api/parse-word - Word文档解析")
    print("  POST /api/upload-and-parse - 上传并解析Word文档")
    print("  GET  /api/health - 健康检查")
    print("-" * 50)
    print("✨ 服务已启动，可通过浏览器访问上述地址")
    
    app.run(debug=True, host='0.0.0.0', port=5006)