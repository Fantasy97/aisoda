"""案例质量评估Web服务"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.case_evaluator import CaseEvaluator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 全局评估器实例
evaluator = None


def get_evaluator():
    """获取或初始化评估器单例"""
    global evaluator
    if evaluator is None:
        logger.info("初始化案例评估器...")
        evaluator = CaseEvaluator()
        if not evaluator.initialize():
            logger.error("评估器初始化失败")
            raise Exception("评估器初始化失败，请检查网络和配置")
        logger.info("评估器初始化成功")
    return evaluator


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "message": "服务运行正常"
    })


@app.route('/api/evaluate', methods=['POST'])
def evaluate_case():
    """
    评估单个案例
    
    请求体:
    {
        "case_name": "CN2024011708976"
    }
    
    响应:
    {
        "success": true,
        "case_name": "CN2024011708976",
        "data": {
            "工单-流程": {...},
            "总分": 50
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        
        if not data or 'case_name' not in data:
            return jsonify({
                "success": False,
                "error": "缺少参数 case_name"
            }), 400
        
        case_name = data['case_name'].strip()
        
        if not case_name:
            return jsonify({
                "success": False,
                "error": "case_name 不能为空"
            }), 400
        
        logger.info(f"收到评估请求: {case_name}")
        
        # 获取评估器
        eval_instance = get_evaluator()
        
        # 执行评估
        result = eval_instance.evaluate_case_by_name(case_name)
        
        if result:
            logger.info(f"评估成功: {case_name}")
            return jsonify({
                "success": True,
                "case_name": case_name,
                "data": result
            })
        else:
            logger.warning(f"评估失败: {case_name}")
            return jsonify({
                "success": False,
                "case_name": case_name,
                "error": "评估失败，可能是案例不存在或API调用失败"
            }), 404
    
    except Exception as e:
        logger.error(f"评估异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


@app.route('/api/evaluate/batch', methods=['POST'])
def batch_evaluate():
    """
    批量评估案例
    
    请求体:
    {
        "case_names": ["CN2024011708976", "CN2024011708659"]
    }
    
    响应:
    {
        "success": true,
        "total": 2,
        "results": {
            "CN2024011708976": {...},
            "CN2024011708659": {...}
        }
    }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        
        if not data or 'case_names' not in data:
            return jsonify({
                "success": False,
                "error": "缺少参数 case_names"
            }), 400
        
        case_names = data['case_names']
        
        if not isinstance(case_names, list) or len(case_names) == 0:
            return jsonify({
                "success": False,
                "error": "case_names 必须是非空数组"
            }), 400
        
        # 限制批量数量
        if len(case_names) > 50:
            return jsonify({
                "success": False,
                "error": "批量评估最多支持50个案例"
            }), 400
        
        logger.info(f"收到批量评估请求: {len(case_names)} 个案例")
        
        # 获取评估器
        eval_instance = get_evaluator()
        
        # 执行批量评估
        results = eval_instance.batch_evaluate(case_names)
        
        # 统计成功失败数量
        success_count = sum(1 for r in results.values() if r is not None)
        
        logger.info(f"批量评估完成: 成功 {success_count}/{len(case_names)}")
        
        return jsonify({
            "success": True,
            "total": len(case_names),
            "success_count": success_count,
            "results": results
        })
    
    except Exception as e:
        logger.error(f"批量评估异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


@app.route('/api/query', methods=['POST'])
def query_case():
    """
    查询案例数据（不评估）
    
    请求体:
    {
        "case_name": "CN2024011708976"
    }
    
    响应:
    {
        "success": true,
        "case_name": "CN2024011708976",
        "data": {...}
    }
    """
    try:
        # 获取请求参数
        data = request.get_json()
        
        if not data or 'case_name' not in data:
            return jsonify({
                "success": False,
                "error": "缺少参数 case_name"
            }), 400
        
        case_name = data['case_name'].strip()
        
        if not case_name:
            return jsonify({
                "success": False,
                "error": "case_name 不能为空"
            }), 400
        
        logger.info(f"收到查询请求: {case_name}")
        
        # 获取评估器
        eval_instance = get_evaluator()
        
        # 查询案例数据
        case_data = eval_instance.query_case_by_name(case_name)
        
        if case_data:
            # 转换为中文字段
            from backend.fxiaoke_cases_list_query import convert_to_chinese_fields
            case_data_cn = convert_to_chinese_fields(
                case_data, 
                use_grouping=False, 
                translate_values=True
            )
            
            logger.info(f"查询成功: {case_name}")
            return jsonify({
                "success": True,
                "case_name": case_name,
                "data": case_data_cn
            })
        else:
            logger.warning(f"查询失败: {case_name}")
            return jsonify({
                "success": False,
                "case_name": case_name,
                "error": "案例不存在或查询失败"
            }), 404
    
    except Exception as e:
        logger.error(f"查询异常: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"服务器错误: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        "success": False,
        "error": "接口不存在"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器错误: {error}", exc_info=True)
    return jsonify({
        "success": False,
        "error": "服务器内部错误"
    }), 500


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║              案例质量评估 Web 服务                             ║
╚══════════════════════════════════════════════════════════════╝

API 接口:
  GET  /health                  - 健康检查
  POST /api/evaluate            - 评估单个案例
  POST /api/evaluate/batch      - 批量评估案例
  POST /api/query               - 查询案例数据

启动信息:
  • 服务地址: http://localhost:5000
  • 跨域支持: 已启用
  • 日志级别: INFO

""")
    
    try:
        # 预初始化评估器
        logger.info("正在预初始化评估器...")
        get_evaluator()
        logger.info("✓ 预初始化完成")
        
        # 启动Flask服务
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except Exception as e:
        logger.error(f"服务启动失败: {e}", exc_info=True)
        print(f"\n❌ 服务启动失败: {e}")
        sys.exit(1)
