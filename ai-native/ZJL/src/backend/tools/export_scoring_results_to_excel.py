#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从数据库导出质检评分结果到Excel文件
支持按时间段筛选，按照模板格式导出
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp140989qmt1xbk0a6o.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'uat1688',
    'password': 'DFfe2&!Kj890J',
    'database': 'lifetree',
    'charset': 'utf8mb4'
}

# 数据库字段到Excel列名的映射（按照模板格式）
DB_TO_EXCEL_MAPPING = {
    # 基础业务字段
    'related_order_no': '关联单号',
    'quality_check_type': '质检类型',
    'business_type': '业务类型（必填）',
    'quality_check_record': '质检记录',
    
    # 400电话评分项
    'call_standard_script_score': '400-标准话术（0-15分）',
    'call_language_skill_score': '400-语言技巧(0-·15分）',
    'call_communication_skill_score': '400-沟通技巧(0-20分）',
    'call_service_attitude_score': '400-服务态度(0-25分）',
    'call_business_answer_score': '400-业务解答(0-25分）',
    'call_issue_notes': '400问题记录',
    
    # 公众号评分项
    'wechat_standard_script_score': '公众号-标准话术（0-20分）',
    'wechat_language_skill_score': '公众号-语言技巧（0-30分）',
    'wechat_service_attitude_score': '公众号-服务态度（0-20分）',
    'wechat_business_answer_score': '公众号-业务解答（0-30分）',
    'wechat_issue_notes': '公众号问题记录',
    
    # 工单评分项
    'ticket_process_score': '工单-流程（0-30分）',
    'ticket_basic_info_score': '工单-基本信息（0-20分）',
    'ticket_issue_record_score': '工单-问题记录(0-35分)',
    'ticket_shipping_detail_score': '工单-发货明细(0-15分)',
    'ticket_issue_notes': '工单问题记录',
    
    # 责任人
    'responsible_person': '负责人（必填）',
    'created_time': '新建时间',
    
    # 组织权限字段
    'readonly_member_user': '人员-普通成员-只读',
    'readwrite_member_user': '人员-普通成员-读写',
    'readonly_member_dept': '部门-普通成员-只读',
    'readwrite_member_dept': '部门-普通成员-读写',
    'readonly_member_group': '用户组-普通成员-只读',
    'readwrite_member_group': '用户组-普通成员-读写',
    'readonly_member_role': '角色-普通成员-只读',
    'readwrite_member_role': '角色-普通成员-读写',
}

# Excel模板的列名顺序
EXCEL_COLUMNS = [
    '关联单号', '质检类型', '业务类型（必填）', '质检记录',
    '400-标准话术（0-15分）', '400-语言技巧(0-·15分）', '400-沟通技巧(0-20分）',
    '400-服务态度(0-25分）', '400-业务解答(0-25分）', '400问题记录',
    '公众号-标准话术（0-20分）', '公众号-语言技巧（0-30分）', '公众号-服务态度（0-20分）',
    '公众号-业务解答（0-30分）', '公众号问题记录',
    '工单-流程（0-30分）', '工单-基本信息（0-20分）', '工单-问题记录(0-35分)',
    '工单-发货明细(0-15分)', '工单问题记录',
    '负责人（必填）', '新建时间',
    '人员-普通成员-只读', '人员-普通成员-读写', '部门-普通成员-只读', '部门-普通成员-读写',
    '用户组-普通成员-只读', '用户组-普通成员-读写', '角色-普通成员-只读', '角色-普通成员-读写'
]


def format_datetime(dt: Any) -> Optional[str]:
    """格式化日期时间为字符串"""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(dt, str):
        return dt
    return str(dt)


def convert_db_record_to_excel(db_record: Dict[str, Any]) -> Dict[str, Any]:
    """将数据库记录转换为Excel格式"""
    excel_record = {}
    
    for db_field, excel_column in DB_TO_EXCEL_MAPPING.items():
        value = db_record.get(db_field)
        
        # 处理日期时间字段
        if db_field == 'created_time':
            excel_record[excel_column] = format_datetime(value)
        # 处理评分字段（确保是整数）
        elif db_field.endswith('_score'):
            if value is None:
                excel_record[excel_column] = 0
            else:
                try:
                    excel_record[excel_column] = int(value)
                except (ValueError, TypeError):
                    excel_record[excel_column] = 0
        # 处理其他字段
        else:
            if value is None:
                excel_record[excel_column] = ''
            else:
                excel_record[excel_column] = str(value)
    
    return excel_record


def render_html_report(excel_rows: List[Dict[str, Any]], output_file: str):
    """
    将已转换为 Excel 结构的数据生成 HTML 报告
    
    Args:
        excel_rows: 已按照 EXCEL_COLUMNS 顺序包含所有字段的行数据
        output_file: 输出的 HTML 文件路径
    """
    # 简单表格渲染，保持字段顺序
    columns = EXCEL_COLUMNS
    html_head = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>质检评分报告</title>
  <style>
    body { font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Arial; padding:16px; background:#f5f5f7; }
    h1 { font-size:20px; margin-bottom:12px; }
    table { border-collapse: collapse; width: 100%; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 10px 24px rgba(0,0,0,0.05); }
    th, td { border: 1px solid #e5e7eb; padding: 8px 10px; font-size: 12px; }
    th { background: #f9fafb; text-align: left; white-space: nowrap; }
    tr:nth-child(even) { background: #fafafa; }
  </style>
</head>
<body>
  <h1>质检评分报告</h1>
  <table>
    <thead>
      <tr>
"""
    head_cols = "".join([f"        <th>{c}</th>\n" for c in columns])
    html_body_start = """      </tr>
    </thead>
    <tbody>
"""
    # 生成表格行
    rows_html = []
    for row in excel_rows:
        tds = "".join([f"        <td>{row.get(col, '')}</td>\n" for col in columns])
        rows_html.append("      <tr>\n" + tds + "      </tr>\n")
    html_end = """    </tbody>
  </table>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_head)
        f.write(head_cols)
        f.write(html_body_start)
        f.writelines(rows_html)
        f.write(html_end)


def query_records_by_time_range(start_time: datetime, end_time: datetime, 
                                quality_check_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    从数据库查询指定时间范围内的记录
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        quality_check_type: 质检类型筛选（可选）
    
    Returns:
        记录列表
    """
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 构建SQL查询
        sql = """
            SELECT * FROM `qis_scoring_results`
            WHERE `created_time` >= %s AND `created_time` <= %s
        """
        params = [start_time, end_time]
        
        # 如果指定了质检类型，添加筛选条件
        if quality_check_type:
            sql += " AND `quality_check_type` = %s"
            params.append(quality_check_type)
        
        sql += " ORDER BY `created_time` DESC"
        
        cursor.execute(sql, params)
        records = cursor.fetchall()
        
        return records
    finally:
        cursor.close()
        connection.close()


def apply_excel_formatting(workbook, worksheet):
    """应用Excel格式（标题行样式等）"""
    # 定义样式
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 应用标题行样式
    for col_idx, col_name in enumerate(EXCEL_COLUMNS, 1):
        cell = worksheet.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border
    
    # 设置列宽（根据列名长度自动调整）
    for col_idx, col_name in enumerate(EXCEL_COLUMNS, 1):
        col_letter = get_column_letter(col_idx)
        # 根据列名长度设置宽度，最小10，最大50
        width = min(max(len(col_name) + 2, 10), 50)
        worksheet.column_dimensions[col_letter].width = width
    
    # 设置行高
    worksheet.row_dimensions[1].height = 30  # 标题行
    for row_idx in range(2, worksheet.max_row + 1):
        worksheet.row_dimensions[row_idx].height = 20
    
    # 应用边框和数据对齐
    for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
        for cell in row:
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=True)


def export_to_excel(start_time: datetime, end_time: datetime,
                   output_file: Optional[str] = None,
                   quality_check_type: Optional[str] = None,
                   template_file: Optional[str] = None,
                   html_report_file: Optional[str] = None):
    """
    导出数据到Excel文件
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        output_file: 输出文件路径（如果为None则自动生成）
        quality_check_type: 质检类型筛选（可选）
        template_file: 模板文件路径（可选，用于复制格式）
    """
    print(f"开始查询数据: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 查询数据
    records = query_records_by_time_range(start_time, end_time, quality_check_type)
    print(f"查询到 {len(records)} 条记录")
    
    if not records:
        print("没有数据需要导出")
        return None
    
    # 转换为Excel格式
    excel_data = []
    for db_record in records:
        excel_record = convert_db_record_to_excel(db_record)
        excel_data.append(excel_record)
    
    # 创建DataFrame，确保列顺序与模板一致
    df = pd.DataFrame(excel_data)
    
    # 确保所有列都存在（缺失的列填充空值）
    for col in EXCEL_COLUMNS:
        if col not in df.columns:
            df[col] = ''
    
    # 按照模板列顺序重新排列
    df = df[EXCEL_COLUMNS]
    
    # 确定输出文件路径
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        output_file = f'data/服务质检对象导出结果_{timestamp}.xlsx'
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 导出到Excel
    print(f"正在导出到: {output_file}")
    
    # 使用openpyxl引擎以便后续格式化
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
        
        # 获取worksheet进行格式化
        worksheet = writer.sheets['Sheet1']
        apply_excel_formatting(writer.book, worksheet)
    
    # 导出 HTML 报告（可选）
    if html_report_file:
        html_path = Path(html_report_file)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        render_html_report(excel_data, str(html_path))
        print(f"✓ HTML 报告已生成: {html_path.absolute()}")

    print(f"✓ 导出完成! 共导出 {len(records)} 条记录")
    print(f"文件路径: {output_path.absolute()}")
    
    return output_file


def export_to_excel_interactive():
    """交互式导出函数"""
    print("=" * 60)
    print("质检评分结果导出工具")
    print("=" * 60)
    
    # 输入开始时间
    while True:
        start_date_str = input("\n请输入开始日期 (格式: YYYY-MM-DD，例如: 2025-01-01): ").strip()
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            break
        except ValueError:
            print("日期格式错误，请重新输入")
    
    # 输入结束时间
    while True:
        end_date_str = input("请输入结束日期 (格式: YYYY-MM-DD，例如: 2025-01-31): ").strip()
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # 设置为当天的23:59:59
            end_date = end_date.replace(hour=23, minute=59, second=59)
            break
        except ValueError:
            print("日期格式错误，请重新输入")
    
    # 验证时间范围
    if start_date > end_date:
        print("错误: 开始时间不能晚于结束时间")
        return
    
    # 可选：质检类型筛选
    quality_type = input("请输入质检类型筛选（可选，直接回车跳过）: ").strip()
    if not quality_type:
        quality_type = None
    
    # 执行导出
    try:
        output_file = export_to_excel(
            start_time=start_date,
            end_time=end_date,
            quality_check_type=quality_type
        )
        if output_file:
            print(f"\n✓ 导出成功!")
    except Exception as e:
        print(f"\n✗ 导出失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 示例1: 交互式导出
    # export_to_excel_interactive()
    
    # 示例2: 程序化导出
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    end_time = datetime(2025, 1, 31, 23, 59, 59)
    
    export_to_excel(
        start_time=start_time,
        end_time=end_time,
        quality_check_type='工单',  # 可选：筛选特定质检类型
    )
    
    print("\n提示: 可以调用 export_to_excel_interactive() 进行交互式导出")

