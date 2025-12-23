"""
生成数据库表结构文档
"""

from database import db
from datetime import datetime


# 需要生成文档的表名列表
TABLES = [
    'odm_bom_mapping',
    'odm_bom_record',
    'odm_bom_record_log',
    'odm_company_info',
    'odm_request_order',
    'odm_request_order_log'
]


def get_table_create_sql(table_name: str) -> str:
    """获取表的 CREATE TABLE SQL 语句"""
    sql = f"SHOW CREATE TABLE {table_name}"
    result = db.execute_one(sql)
    return result.get('Create Table', '') if result else ''


def format_column_info(column: dict) -> str:
    """格式化列信息"""
    field = column.get('Field', '')
    type_info = column.get('Type', '')
    null = column.get('Null', '')
    key = column.get('Key', '')
    default = column.get('Default', '')
    extra = column.get('Extra', '')
    
    # 构建列描述
    parts = [f"**{field}**"]
    parts.append(f"`{type_info}`")
    
    if key == 'PRI':
        parts.append("PRIMARY KEY")
    elif key == 'UNI':
        parts.append("UNIQUE")
    elif key == 'MUL':
        parts.append("INDEX")
    
    if null == 'NO':
        parts.append("NOT NULL")
    
    if default is not None and default != '':
        parts.append(f"DEFAULT {default}")
    
    if extra:
        parts.append(extra.upper())
    
    return " | ".join(parts)


def generate_table_doc(table_name: str) -> str:
    """生成单个表的文档"""
    try:
        # 获取表结构
        columns = db.get_table_columns(table_name)
        create_sql = get_table_create_sql(table_name)
        
        doc = f"## {table_name}\n\n"
        doc += f"### 表说明\n\n"
        doc += f"（待补充表的具体用途说明）\n\n"
        
        doc += f"### 字段列表\n\n"
        doc += f"| 字段名 | 类型 | 约束 | 说明 |\n"
        doc += f"|--------|------|------|------|\n"
        
        for col in columns:
            field = col.get('Field', '')
            type_info = col.get('Type', '')
            null = col.get('Null', '')
            key = col.get('Key', '')
            default = col.get('Default', '')
            extra = col.get('Extra', '')
            
            # 约束信息
            constraints = []
            if key == 'PRI':
                constraints.append("主键")
            elif key == 'UNI':
                constraints.append("唯一")
            elif key == 'MUL':
                constraints.append("索引")
            if null == 'NO':
                constraints.append("非空")
            if extra == 'auto_increment':
                constraints.append("自增")
            
            constraint_str = ", ".join(constraints) if constraints else "-"
            
            doc += f"| `{field}` | `{type_info}` | {constraint_str} | （待补充字段说明） |\n"
        
        doc += f"\n### 建表语句\n\n"
        doc += f"```sql\n{create_sql}\n```\n\n"
        
        return doc
        
    except Exception as e:
        return f"## {table_name}\n\n**错误**: 无法获取表结构 - {str(e)}\n\n"


def main():
    """主函数"""
    print("正在连接数据库并获取表结构...")
    
    if not db.test_connection():
        print("❌ 数据库连接失败！")
        return
    
    print("✓ 数据库连接成功！\n")
    
    # 生成文档内容
    doc_content = f"# 数据库表结构文档\n\n"
    doc_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    doc_content += f"**数据库**: lifetree\n\n"
    doc_content += f"---\n\n"
    
    # 为每个表生成文档
    for i, table_name in enumerate(TABLES, 1):
        print(f"正在处理表 {i}/{len(TABLES)}: {table_name}...")
        doc_content += generate_table_doc(table_name)
        if i < len(TABLES):
            doc_content += "\n---\n\n"
    
    # 保存文档
    output_file = "D:\\code\\odm\\src\\backend\\db\\数据库表结构文档.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    print(f"\n✓ 文档已生成: {output_file}")


if __name__ == "__main__":
    main()
