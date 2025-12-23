"""
Flask应用 - 智能Word表单填充API
提供Word文档上传、解析、匹配、回填和下载的完整服务
"""

import os
import json
import logging
import tempfile
import sys
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template_string, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# 设置当前工作目录为脚本所在目录
current_dir = Path(__file__).parent.absolute()
os.chdir(current_dir)

# 添加tools目录到Python路径
tools_dir = current_dir / "tools"
sys.path.insert(0, str(tools_dir))

# 导入现有工具模块
from word_parser import WordParser
from intelligent_form_filler_api import BatchFillAPI, SingleQueryAPI, ConfigManager
from word_form_filler import WordFormFiller
from update_example_data import DataUpdater

# 配置日志 - 将日志文件保存到data/processed目录
log_dir = '../../data/processed'
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'app.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__, 
           static_folder='../frontend',
           static_url_path='/static')
logger = logging.getLogger(__name__)

# 配置 - 使用相对路径指向项目根目录的data文件夹
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = '../../data/input'  # 上传文件目录
app.config['OUTPUT_FOLDER'] = '../../data/output'  # 最终输出目录
app.config['PROCESSED_FOLDER'] = '../../data/processed'  # 中间处理目录
app.config['ALLOWED_EXTENSIONS'] = {'docx', 'doc'}

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

# 初始化工具
config_path = "tools/config.json"
config_manager = ConfigManager(config_path)
batch_api = BatchFillAPI(config_manager.get_config())
single_api = SingleQueryAPI(config_manager.get_config())
word_parser = WordParser()
word_filler = WordFormFiller()
data_updater = DataUpdater()


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(original_filename):
    """生成唯一的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(original_filename)
    return f"{name}_{timestamp}{ext}"


@app.errorhandler(413)
def too_large(e):
    """处理文件过大错误"""
    return jsonify({
        'success': False,
        'error': '文件大小超过限制（最大16MB）'
    }), 413


@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理"""
    logger.error(f"未处理的异常: {e}", exc_info=True)
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500


@app.route('/')
def index():
    """主页 - 提供静态HTML文件"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/api/report/<filename>')
def serve_report(filename):
    """提供HTML报告文件"""
    return send_from_directory('../../data/output', filename)


@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/upload', methods=['POST'])
def upload_and_process():
    """
    完整的文档上传和处理流程
    1. 上传Word文档
    2. 解析空白单元格
    3. 智能填充内容
    4. 生成填充后的文档
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': '不支持的文件格式，请上传.docx或.doc文件'
            }), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        
        logger.info(f"文件上传成功: {upload_path}")
        
        # 如果是.doc文件，先转换为.docx
        if filename.lower().endswith('.doc'):
            try:
                docx_path = word_parser.convert_doc_to_docx(upload_path)
                upload_path = docx_path
                logger.info(f"文档转换成功: {docx_path}")
            except Exception as e:
                logger.error(f"文档转换失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'文档转换失败: {str(e)}'
                }), 500
        
        # 步骤1: 解析空白单元格
        logger.info("开始解析空白单元格...")
        empty_cells_path = os.path.join(app.config['PROCESSED_FOLDER'], f"empty_cells_{unique_filename}.json")
        
        try:
            empty_cells = word_parser.extract_empty_cells(upload_path, empty_cells_path)
            logger.info(f"解析到 {len(empty_cells)} 个空白单元格")
        except Exception as e:
            logger.error(f"解析空白单元格失败: {e}")
            return jsonify({
                'success': False,
                'error': f'解析文档失败: {str(e)}'
            }), 500
        
        # 步骤2: 智能填充
        logger.info("开始智能填充...")
        try:
            filled_data_path = batch_api.batch_fill(empty_cells_path)
            logger.info(f"智能填充完成，结果保存到: {filled_data_path}")
        except Exception as e:
            logger.error(f"智能填充失败: {e}")
            return jsonify({
                'success': False,
                'error': f'智能填充失败: {str(e)}'
            }), 500
        
        # 步骤3: 回填到Word文档
        logger.info("开始回填到Word文档...")
        output_filename = f"filled_{unique_filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        try:
            # 加载填充后的数据
            with open(filled_data_path, 'r', encoding='utf-8') as f:
                filled_data = json.load(f)
            
            # 使用WordFormFiller进行回填
            success = word_filler.fill_word_document(upload_path, filled_data, output_path)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': '回填Word文档失败'
                }), 500
            
            # 获取统计信息
            statistics = word_filler.get_statistics()
            
            logger.info(f"Word文档回填完成: {output_path}")
            
            # 生成HTML报告
            report_filename = None
            try:
                # 生成报告文件名：report_原始文件名_时间戳.html
                base_name = unique_filename.replace('.docx', '').replace('.doc', '')
                report_filename = f"report_{base_name}.html"
                report_path = os.path.join(app.config['OUTPUT_FOLDER'], report_filename)
                download_url = f'/api/download/{output_filename}'
                word_filler.generate_report(report_path, download_url)
                logger.info(f"HTML报告生成完成: {report_path}")
            except Exception as e:
                logger.warning(f"生成HTML报告失败: {e}")
                report_filename = None
            
            # 注意：上传的文件保存在data/input目录中，不需要删除
            logger.info(f"上传文件保存在: {upload_path}")
            
            return jsonify({
                'success': True,
                'message': '文档处理完成',
                'output_filename': output_filename,
                'report_filename': report_filename,
                'statistics': statistics,
                'download_url': f'/api/download/{output_filename}',
                'report_url': f'/api/report/{report_filename}' if report_filename else None
            })
            
        except Exception as e:
            logger.error(f"回填Word文档失败: {e}")
            return jsonify({
                'success': False,
                'error': f'回填文档失败: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"处理请求失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500


@app.route('/api/parse', methods=['POST'])
def parse_document():
    """
    仅解析文档结构，不进行填充
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': '不支持的文件格式'
            }), 400
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            file.save(tmp_file.name)
            
            # 解析文档
            try:
                empty_cells = word_parser.extract_empty_cells(tmp_file.name)
                
                return jsonify({
                    'success': True,
                    'empty_cells_count': len(empty_cells),
                    'empty_cells': empty_cells[:10],  # 只返回前10个作为预览
                    'message': f'解析完成，发现 {len(empty_cells)} 个空白单元格'
                })
                
            finally:
                os.unlink(tmp_file.name)
    
    except Exception as e:
        logger.error(f"解析文档失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fill', methods=['POST'])
def fill_data():
    """
    对提供的数据进行智能填充
    """
    try:
        data = request.get_json()
        
        if not data or 'cells' not in data:
            return jsonify({
                'success': False,
                'error': '请提供要填充的单元格数据'
            }), 400
        
        cells = data['cells']
        
        # 创建临时JSON文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
            json.dump(cells, tmp_file, ensure_ascii=False, indent=2)
            tmp_path = tmp_file.name
        
        try:
            # 执行批量填充
            filled_path = batch_api.batch_fill(tmp_path)
            
            # 读取结果
            with open(filled_path, 'r', encoding='utf-8') as f:
                filled_data = json.load(f)
            
            return jsonify({
                'success': True,
                'filled_data': filled_data,
                'message': '数据填充完成'
            })
            
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
                if 'filled_path' in locals():
                    os.unlink(filled_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"数据填充失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def cleanup_data_directories(exclude_files=None):
    """
    清理data目录下的文件，保留日志文件和example_data.json
    
    Args:
        exclude_files (list): 额外要保留的文件名列表
    """
    try:
        # 定义要清理的目录
        directories_to_clean = [
            app.config['UPLOAD_FOLDER'],    # data/input
            app.config['OUTPUT_FOLDER'],    # data/output
            app.config['PROCESSED_FOLDER']  # data/processed
        ]
        
        # 定义要保留的文件（在processed目录中）
        files_to_keep_processed = {
            'app.log',
            'word_form_filler.log',
            'example_data.json'
        }
        
        # 如果有额外要保留的文件，添加到保留列表中
        exclude_files = exclude_files or []
        
        cleaned_count = 0
        
        for directory in directories_to_clean:
            if not os.path.exists(directory):
                continue
                
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # 检查是否需要保留此文件
                should_keep = False
                
                # 如果是processed目录，检查默认保留文件
                if directory == app.config['PROCESSED_FOLDER'] and filename in files_to_keep_processed:
                    should_keep = True
                    logger.info(f"保留默认文件: {file_path}")
                
                # 检查是否在额外保留列表中
                if filename in exclude_files:
                    should_keep = True
                    logger.info(f"保留指定文件: {file_path}")
                
                if should_keep:
                    continue
                
                # 删除文件
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    cleaned_count += 1
                    logger.info(f"清理文件: {file_path}")
                elif os.path.isdir(file_path):
                    # 如果是目录，递归删除
                    import shutil
                    shutil.rmtree(file_path)
                    cleaned_count += 1
                    logger.info(f"清理目录: {file_path}")
        
        logger.info(f"清理完成，共清理 {cleaned_count} 个文件/目录")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"清理文件失败: {e}")
        return 0


@app.route('/api/download/<filename>')
def download_file(filename):
    """
    下载处理后的文件，下载完成后清理临时文件
    """
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '文件不存在'
            }), 404

        logger.info(f"开始下载文件: {filename}")
        
        # 确保文件名有正确的扩展名
        download_name = filename
        if not filename.lower().endswith(('.docx', '.doc')):
            download_name = f"{filename}.docx"
        
        # 读取文件内容到内存
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # 立即清理临时文件，但保留当前下载的文件和相关报告
        logger.info("下载开始，准备清理临时文件...")
        try:
            # 生成可能的报告文件名
            base_name = filename.replace('filled_', '').replace('.docx', '').replace('.doc', '')
            possible_report_name = f"report_{base_name}.html"
            
            # 保留当前下载的文件和对应的报告文件
            exclude_files = [filename, possible_report_name]
            cleaned_count = cleanup_data_directories(exclude_files=exclude_files)
            logger.info(f"文件清理完成，共清理 {cleaned_count} 个文件，保留了: {exclude_files}")
        except Exception as cleanup_error:
            logger.warning(f"清理文件时出现警告: {cleanup_error}")
        
        # 创建响应并返回文件
        from flask import Response
        response = Response(
            file_data,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={
                'Content-Disposition': f'attachment; filename="{download_name}"'
            }
        )
        
        return response
    
    except Exception as e:
        logger.error(f"下载文件失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def single_query():
    """
    单个关键词查询接口
    """
    try:
        data = request.get_json()
        
        if not data or 'keyword' not in data:
            return jsonify({
                'success': False,
                'error': '请提供查询关键词'
            }), 400
        
        keyword = data['keyword']
        result = single_api.single_query(keyword)
        
        return jsonify({
            'success': True,
            'keyword': keyword,
            'result': result,
            'message': '查询完成'
        })
    
    except Exception as e:
        logger.error(f"单查询失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/update-data', methods=['POST'])
def update_example_data():
    """
    更新example_data.json接口
    用户上传两个Word文件，分别生成empty_cells.json和full_cells.json，然后更新example_data.json
    """
    try:
        # 检查上传的文件
        if 'empty_cells_doc' not in request.files or 'full_cells_doc' not in request.files:
            return jsonify({
                'success': False,
                'error': '请上传两个Word文件：empty_cells_doc（空单元格文档）和 full_cells_doc（完整数据文档）'
            }), 400
        
        empty_cells_file = request.files['empty_cells_doc']
        full_cells_file = request.files['full_cells_doc']
        
        # 验证文件
        if empty_cells_file.filename == '' or full_cells_file.filename == '':
            return jsonify({
                'success': False,
                'error': '请选择有效的文件'
            }), 400
        
        if not (allowed_file(empty_cells_file.filename) and allowed_file(full_cells_file.filename)):
            return jsonify({
                'success': False,
                'error': '不支持的文件格式，请上传.docx或.doc文件'
            }), 400
        
        logger.info("开始处理上传的Word文件...")
        
        # 保存上传的文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        empty_filename = secure_filename(empty_cells_file.filename)
        empty_unique_filename = f"empty_{timestamp}_{empty_filename}"
        empty_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], empty_unique_filename)
        empty_cells_file.save(empty_upload_path)
        
        full_filename = secure_filename(full_cells_file.filename)
        full_unique_filename = f"full_{timestamp}_{full_filename}"
        full_upload_path = os.path.join(app.config['UPLOAD_FOLDER'], full_unique_filename)
        full_cells_file.save(full_upload_path)
        
        logger.info(f"文件保存完成: {empty_upload_path}, {full_upload_path}")
        
        # 处理.doc文件转换
        if empty_filename.lower().endswith('.doc'):
            try:
                empty_upload_path = word_parser.convert_doc_to_docx(empty_upload_path)
                logger.info(f"空单元格文档转换完成: {empty_upload_path}")
            except Exception as e:
                logger.error(f"空单元格文档转换失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'空单元格文档转换失败: {str(e)}'
                }), 500
        
        if full_filename.lower().endswith('.doc'):
            try:
                full_upload_path = word_parser.convert_doc_to_docx(full_upload_path)
                logger.info(f"完整数据文档转换完成: {full_upload_path}")
            except Exception as e:
                logger.error(f"完整数据文档转换失败: {e}")
                return jsonify({
                    'success': False,
                    'error': f'完整数据文档转换失败: {str(e)}'
                }), 500
        
        # 步骤1: 解析空单元格文档 (mode=empty)
        logger.info("开始解析空单元格文档...")
        empty_cells_json_path = os.path.join(app.config['PROCESSED_FOLDER'], f"empty_cells_{timestamp}.json")
        
        try:
            empty_cells_result = word_parser.extract_empty_cells(empty_upload_path, empty_cells_json_path)
            logger.info(f"空单元格解析完成，发现 {len(empty_cells_result)} 个空单元格")
        except Exception as e:
            logger.error(f"解析空单元格文档失败: {e}")
            return jsonify({
                'success': False,
                'error': f'解析空单元格文档失败: {str(e)}'
            }), 500
        
        # 步骤2: 解析完整数据文档 (mode=full)
        logger.info("开始解析完整数据文档...")
        full_cells_json_path = os.path.join(app.config['PROCESSED_FOLDER'], f"full_cells_{timestamp}.json")
        
        try:
            full_cells_result = word_parser.extract_full_document(full_upload_path, full_cells_json_path)
            logger.info("完整数据文档解析完成")
        except Exception as e:
            logger.error(f"解析完整数据文档失败: {e}")
            return jsonify({
                'success': False,
                'error': f'解析完整数据文档失败: {str(e)}'
            }), 500
        
        # 步骤3: 使用生成的JSON文件更新example_data.json
        logger.info("开始更新example_data.json...")
        example_data_path = os.path.join(app.config['PROCESSED_FOLDER'], 'example_data.json')
        
        try:
            update_result = data_updater.update_example_data(
                empty_cells_path=empty_cells_json_path,
                full_cells_path=full_cells_json_path,
                example_data_path=example_data_path
            )
            
            logger.info(f"数据更新完成: 成功更新 {update_result['successfully_updated']} 个字段")
            
            return jsonify({
                'success': True,
                'message': '数据更新完成',
                'result': {
                    'empty_cells_count': len(empty_cells_result),
                    'update_result': update_result,
                    'files_generated': {
                        'empty_cells_json': empty_cells_json_path,
                        'full_cells_json': full_cells_json_path,
                        'updated_example_data': example_data_path
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"更新example_data.json失败: {e}")
            return jsonify({
                'success': False,
                'error': f'更新数据失败: {str(e)}'
            }), 500
    
    except Exception as e:
        logger.error(f"处理请求失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500


@app.route('/api/update-status')
def get_update_status():
    """
    获取最近的数据更新状态
    """
    try:
        # 读取更新摘要文件
        summary_path = os.path.join('../../tmp', 'update_summary.json')
        
        if not os.path.exists(summary_path):
            return jsonify({
                'success': False,
                'error': '没有找到更新记录'
            }), 404
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    
    except Exception as e:
        logger.error(f"获取更新状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    logger.info("启动Flask应用...")
    logger.info(f"上传目录: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"输出目录: {app.config['OUTPUT_FOLDER']}")
    
    # 开发模式运行
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )