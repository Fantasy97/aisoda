"""
Flask 应用主文件
提供数据库表查询接口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from db.database import db

# 创建 Flask 应用
app = Flask(__name__)

# 配置 CORS，允许跨域请求
CORS(app)

# 允许操作的表名白名单（安全措施）
ALLOWED_TABLES = {
    'odm_bom_mapping',
    'odm_bom_record',
    'odm_bom_record_log',
    'odm_company_info',
    'odm_request_order',
    'odm_request_order_log'
}

# 禁止在WHERE子句中使用的危险关键字
DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE',
    'EXEC', 'EXECUTE', 'UNION', 'SCRIPT', '--', '/*', '*/', ';'
]


@app.route('/', methods=['GET'])
def root():
    """根路径"""
    return jsonify({
        "message": "ODM 数据库查询 API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/query",
            "distinct": "/api/query/distinct"
        }
    })


def validate_where_sql(where_sql):
    """
    验证WHERE子句是否安全
    
    Args:
        where_sql: WHERE子句字符串
        
    Returns:
        (is_valid, error_message)
    """
    if not where_sql:
        return True, None
    
    # 转换为大写进行关键字检查
    where_upper = where_sql.upper().strip()
    
    # 检查是否包含危险关键字
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in where_upper:
            return False, f"WHERE子句中包含禁止的关键字: {keyword}"
    
    # 检查是否以WHERE开头（可选，允许只传条件部分）
    # 如果以WHERE开头，去掉它（因为我们会自动添加）
    if where_upper.startswith('WHERE'):
        where_sql = where_sql[5:].strip()
    
    return True, None


@app.route('/api/query', methods=['POST'])
def query_table():
    """
    根据表名和WHERE条件查询数据
    
    请求体:
    {
        "table_name": "odm_bom_mapping",
        "where_sql": "id > 10 AND is_valid = 1"  // 可选，WHERE子句（不需要包含WHERE关键字）
    }
    
    响应:
    {
        "success": true,
        "message": "查询成功",
        "data": [...]
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证请求数据
        if not data:
            return jsonify({
                "success": False,
                "message": "请求体不能为空",
                "data": None
            }), 400
        
        table_name = data.get('table_name')
        where_sql = data.get('where_sql', '').strip() if data.get('where_sql') else ''
        
        # 验证表名是否存在
        if not table_name:
            return jsonify({
                "success": False,
                "message": "表名不能为空",
                "data": None
            }), 400
        
        # 验证表名是否在白名单中
        if table_name not in ALLOWED_TABLES:
            return jsonify({
                "success": False,
                "message": f"表名 '{table_name}' 不在允许的操作列表中",
                "data": None
            }), 400
        
        # 验证WHERE子句安全性
        if where_sql:
            is_valid, error_msg = validate_where_sql(where_sql)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "message": error_msg,
                    "data": None
                }), 400
        
        # 构建SQL查询
        sql = f"SELECT * FROM `{table_name}`"
        if where_sql:
            # 如果WHERE子句不以WHERE开头，自动添加
            if not where_sql.upper().strip().startswith('WHERE'):
                sql += f" WHERE {where_sql}"
            else:
                sql += f" {where_sql}"
        
        # 执行查询
        results = db.execute_query(sql)
        
        return jsonify({
            "success": True,
            "message": f"查询表 '{table_name}' 成功，共 {len(results)} 条记录",
            "data": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": None
        }), 500


@app.route('/api/query/distinct', methods=['POST'])
def query_distinct_values():
    """
    查询表中某个字段的所有不重复值
    
    请求体:
    {
        "table_name": "odm_company_info",
        "field_name": "company_name"
    }
    
    响应:
    {
        "success": true,
        "message": "查询成功",
        "data": ["值1", "值2", "值3", ...]
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证请求数据
        if not data:
            return jsonify({
                "success": False,
                "message": "请求体不能为空",
                "data": None
            }), 400
        
        table_name = data.get('table_name')
        field_name = data.get('field_name')
        
        # 验证表名是否存在
        if not table_name:
            return jsonify({
                "success": False,
                "message": "表名不能为空",
                "data": None
            }), 400
        
        # 验证字段名是否存在
        if not field_name:
            return jsonify({
                "success": False,
                "message": "字段名不能为空",
                "data": None
            }), 400
        
        # 验证表名是否在白名单中
        if table_name not in ALLOWED_TABLES:
            return jsonify({
                "success": False,
                "message": f"表名 '{table_name}' 不在允许的操作列表中",
                "data": None
            }), 400
        
        # 验证字段名是否包含危险字符（防止SQL注入）
        if not field_name.replace('_', '').replace('.', '').isalnum():
            return jsonify({
                "success": False,
                "message": "字段名包含非法字符",
                "data": None
            }), 400
        
        # 查询字段的所有不重复值
        # 使用 DISTINCT 和 ORDER BY 确保结果有序且去重
        sql = f"SELECT DISTINCT `{field_name}` FROM `{table_name}` WHERE `{field_name}` IS NOT NULL ORDER BY `{field_name}`"
        results = db.execute_query(sql)
        
        # 提取字段值（去除 None 值）
        distinct_values = [row[field_name] for row in results if row[field_name] is not None]
        
        return jsonify({
            "success": True,
            "message": f"查询表 '{table_name}' 字段 '{field_name}' 的不重复值成功，共 {len(distinct_values)} 个",
            "data": distinct_values
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"查询失败: {str(e)}",
            "data": None
        }), 500


if __name__ == '__main__':
    # 开发环境运行配置
    app.run(
        host='0.0.0.0',
        port=5010,
        debug=True
    )
