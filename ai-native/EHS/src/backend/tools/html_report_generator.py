#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML报告生成器
为法律法规日期验证生成美观的HTML报告
"""

import json
from datetime import datetime
from typing import List, Dict
from urllib.parse import quote_plus


class HTMLReportGenerator:
    """HTML报告生成器"""
    
    def __init__(self):
        self.template = self._get_html_template()
    
    def _get_html_template(self) -> str:
        """获取HTML模板"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>法律法规日期验证报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .header .subtitle {{
            text-align: center;
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }}
        
        .stat-card .percentage {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .section-header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        .section-header h2 {{
            color: #333;
            font-size: 1.5em;
            display: flex;
            align-items: center;
        }}
        
        .section-header .icon {{
            margin-right: 10px;
            font-size: 1.2em;
        }}
        
        .section-content {{
            padding: 0;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        
        th, td {{
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .status-match {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .status-mismatch {{
            color: #dc3545;
            font-weight: bold;
        }}
        
        .status-not-found {{
            color: #6c757d;
            font-weight: bold;
        }}
        
        .source-official {{
            background-color: #d4edda;
            color: #155724;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
        }}
        
        .source-searxng {{
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
        }}
        
        .source-none {{
            background-color: #f8d7da;
            color: #721c24;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
        }}
        
        .law-link {{
            color: #007bff;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .law-link:hover {{
            text-decoration: underline;
        }}
        
        .date-highlight {{
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        .date-match {{
            background-color: #d4edda;
            color: #155724;
        }}
        
        .date-mismatch {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .summary-box {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        
        .summary-box h3 {{
            margin-bottom: 15px;
            font-size: 1.3em;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .summary-item {{
            text-align: center;
        }}
        
        .summary-item .label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .summary-item .value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        .badge {{
            display: inline-block;
            padding: 0.25em 0.6em;
            font-size: 0.75em;
            font-weight: 700;
            line-height: 1;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.25rem;
        }}
        
        .badge-success {{
            color: #fff;
            background-color: #28a745;
        }}
        
        .badge-danger {{
            color: #fff;
            background-color: #dc3545;
        }}
        
        .badge-secondary {{
            color: #fff;
            background-color: #6c757d;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 0.8em;
            }}
            
            th, td {{
                padding: 8px 4px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
        """
    
    def _generate_law_link(self, law_name: str, source: str, original_url: str = None) -> str:
        """生成法律链接"""
        if original_url and original_url.strip():
            return f'<a href="{original_url}" target="_blank" class="law-link">{law_name}</a>'
        
        # 根据来源生成不同的链接
        if source == "国家法律法规数据库":
            # 官方数据库搜索链接
            search_url = f"https://flk.npc.gov.cn/search?searchContent={quote_plus(law_name)}"
            return f'<a href="{search_url}" target="_blank" class="law-link">{law_name}</a>'
        else:
            # 通用搜索链接
            search_query = quote_plus(f"{law_name} 法律法规")
            search_url = f"https://www.baidu.com/s?wd={search_query}"
            return f'<a href="{search_url}" target="_blank" class="law-link">{law_name}</a>'
    
    def _get_source_badge(self, source: str) -> str:
        """获取来源标签"""
        if source == "official":
            return '<span class="source-official">官方数据库</span>'
        elif source == "searxng":
            return '<span class="source-searxng">SearXNG</span>'
        else:
            return '<span class="source-none">未找到</span>'
    
    def _get_status_badge(self, is_match: bool, found: bool) -> str:
        """获取状态标签"""
        if not found:
            return '<span class="badge badge-secondary">未找到</span>'
        elif is_match:
            return '<span class="badge badge-success">匹配</span>'
        else:
            return '<span class="badge badge-danger">不匹配</span>'
    
    def _format_date(self, date_str: str, is_match: bool = None) -> str:
        """格式化日期显示"""
        if not date_str or date_str == "未找到":
            return date_str
        
        if is_match is None:
            return date_str
        
        css_class = "date-match" if is_match else "date-mismatch"
        return f'<span class="date-highlight {css_class}">{date_str}</span>'
    
    def generate_html_report(self, results: List[Dict], stats: Dict) -> str:
        """生成HTML报告"""
        # 分类结果
        matched_results = [r for r in results if r['日期匹配'] and r['状态'] == '找到']
        mismatched_results = [r for r in results if not r['日期匹配'] and r['状态'] == '找到']
        not_found_results = [r for r in results if r['状态'] == '未找到']
        
        # 计算统计数据
        total_laws = stats['total_laws']
        total_found = stats['official_db_found'] + stats['other_source_found']
        total_matches = stats['official_db_matches'] + stats['other_source_matches']
        
        success_rate = (total_found / total_laws * 100) if total_laws > 0 else 0
        match_rate = (total_matches / total_found * 100) if total_found > 0 else 0
        
        # 生成内容
        content = f"""
        <div class="header">
            <h1>法律法规日期验证报告</h1>
            <div class="subtitle">生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</div>
        </div>
        
        <div class="summary-box">
            <h3>📊 验证概览</h3>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="label">总法律数量</div>
                    <div class="value">{total_laws}</div>
                </div>
                <div class="summary-item">
                    <div class="label">查询成功</div>
                    <div class="value">{total_found}</div>
                </div>
                <div class="summary-item">
                    <div class="label">日期匹配</div>
                    <div class="value">{total_matches}</div>
                </div>
                <div class="summary-item">
                    <div class="label">匹配率</div>
                    <div class="value">{match_rate:.1f}%</div>
                </div>
            </div>
        </div>
        
        """
        
        # 日期不匹配的法规（优先显示）
        if mismatched_results:
            content += f"""
            <div class="section">
                <div class="section-header">
                    <h2><span class="icon">⚠️</span>日期不匹配的法规 ({len(mismatched_results)} 条)</h2>
                </div>
                <div class="section-content">
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>序号</th>
                                    <th>法律名称</th>
                                    <th>原始日期</th>
                                    <th>查询日期</th>
                                    <th>原始来源</th>
                                    <th>查询来源</th>
                                    <th>获取途径</th>
                                    <th>分类</th>
                                    <th>状态</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for result in mismatched_results:
                law_link = self._generate_law_link(
                    result['法律名称'], 
                    result['原始来源'],
                    result.get('网址')
                )
                
                original_date = result['原始日期'] or '未知'
                query_date = result['查询结果'] or '未找到'
                source_website = result.get('获取途径', '') or ''
                
                # 生成来源标签
                source_badge = self._get_source_badge(result.get('查询来源', ''))
                
                # 生成状态标签
                status_badge = self._get_status_badge(False, True)
                
                content += f"""
                                <tr>
                                    <td>{result['序号']}</td>
                                    <td>{law_link}</td>
                                    <td>{original_date}</td>
                                    <td>{query_date}</td>
                                    <td>{result['原始来源']}</td>
                                    <td>{source_badge}</td>
                                    <td>{source_website}</td>
                                    <td>{result['分类']}</td>
                                    <td>{status_badge}</td>
                                </tr>
                """
            
            content += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """
        
        # 日期匹配的法规
        if matched_results:
            content += f"""
            <div class="section">
                <div class="section-header">
                    <h2><span class="icon">✅</span>日期匹配的法规 ({len(matched_results)} 条)</h2>
                </div>
                <div class="section-content">
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>序号</th>
                                    <th>法律名称</th>
                                    <th>原始日期</th>
                                    <th>查询日期</th>
                                    <th>原始来源</th>
                                    <th>查询来源</th>
                                    <th>获取途径</th>
                                    <th>分类</th>
                                    <th>状态</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for result in matched_results:
                law_link = self._generate_law_link(
                    result['法律名称'], 
                    result['原始来源'],
                    result.get('网址')
                )
                source_badge = self._get_source_badge(result.get('查询来源', ''))
                status_badge = self._get_status_badge(True, True)
                original_date = self._format_date(result['原始日期'], True)
                query_date = self._format_date(result.get('查询结果', ''), True)
                source_website = result.get('获取途径', '') or ''
                
                content += f"""
                                <tr>
                                    <td>{result['序号']}</td>
                                    <td>{law_link}</td>
                                    <td>{original_date}</td>
                                    <td>{query_date}</td>
                                    <td>{result['原始来源']}</td>
                                    <td>{source_badge}</td>
                                    <td>{source_website}</td>
                                    <td>{result['分类']}</td>
                                    <td>{status_badge}</td>
                                </tr>
                """
            
            content += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """
        
        
        # 未找到的法规
        if not_found_results:
            content += f"""
            <div class="section">
                <div class="section-header">
                    <h2><span class="icon">❌</span>未找到的法规 ({len(not_found_results)} 条)</h2>
                </div>
                <div class="section-content">
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>序号</th>
                                    <th>法律名称</th>
                                    <th>原始日期</th>
                                    <th>原始来源</th>
                                    <th>分类</th>
                                    <th>状态</th>
                                </tr>
                            </thead>
                            <tbody>
            """
            
            for result in not_found_results:
                law_link = self._generate_law_link(
                    result['法律名称'], 
                    result['原始来源'],
                    result.get('网址')
                )
                status_badge = self._get_status_badge(False, False)
                
                content += f"""
                                <tr>
                                    <td>{result['序号']}</td>
                                    <td>{law_link}</td>
                                    <td>{result['原始日期']}</td>
                                    <td>{result['原始来源']}</td>
                                    <td>{result['分类']}</td>
                                    <td>{status_badge}</td>
                                </tr>
                """
            
            content += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """
        
        # 页脚
        content += f"""
        <div class="footer">
            <p>本报告由法律法规日期验证器自动生成 | 数据来源: 国家法律法规数据库 & SearXNG</p>
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """
        
        return self.template.format(content=content)
    
    def save_html_report(self, html_content: str, filename: str = None) -> str:
        """保存HTML报告"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"law_validation_report_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filename
    
    def merge_html_reports(self, old_html_file: str, incremental_html_file: str, output_file: str = None) -> str:
        """合并HTML报告，将增量的HTML更新到老的HTML中"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            print("需要安装 beautifulsoup4: pip install beautifulsoup4")
            return None
        
        try:
            # 读取老的HTML文件
            with open(old_html_file, 'r', encoding='utf-8') as f:
                old_html = f.read()
            
            # 读取增量的HTML文件
            with open(incremental_html_file, 'r', encoding='utf-8') as f:
                incremental_html = f.read()
            
            # 解析HTML
            old_soup = BeautifulSoup(old_html, 'html.parser')
            incremental_soup = BeautifulSoup(incremental_html, 'html.parser')
            
            # 更新标题和时间
            old_title = old_soup.find('h1')
            if old_title:
                old_title.string = "法律法规日期验证报告（合并版）"
            
            old_subtitle = old_soup.find('div', class_='subtitle')
            if old_subtitle:
                old_subtitle.string = f"更新时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}"
            
            # 合并统计数据
            self._merge_summary_data(old_soup, incremental_soup)
            
            # 合并表格数据
            self._merge_table_data(old_soup, incremental_soup)
            
            # 生成输出文件名
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"merged_law_validation_report_{timestamp}.html"
            
            # 保存合并后的HTML
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(str(old_soup))
            
            print(f"✓ HTML报告合并完成: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"⚠ HTML报告合并失败: {e}")
            return None
    
    def _merge_summary_data(self, old_soup, incremental_soup):
        """合并统计数据"""
        try:
            # 获取老数据的统计值
            old_values = old_soup.find_all('div', class_='value')
            incremental_values = incremental_soup.find_all('div', class_='value')
            
            if len(old_values) >= 4 and len(incremental_values) >= 4:
                # 更新统计数据（简单相加）
                old_total = int(old_values[0].get_text())
                old_found = int(old_values[1].get_text())
                old_matched = int(old_values[2].get_text())
                
                inc_total = int(incremental_values[0].get_text())
                inc_found = int(incremental_values[1].get_text())
                inc_matched = int(incremental_values[2].get_text())
                
                new_total = old_total + inc_total
                new_found = old_found + inc_found
                new_matched = old_matched + inc_matched
                new_match_rate = (new_matched / new_found * 100) if new_found > 0 else 0
                
                old_values[0].string = str(new_total)
                old_values[1].string = str(new_found)
                old_values[2].string = str(new_matched)
                old_values[3].string = f"{new_match_rate:.1f}%"
                
        except Exception as e:
            print(f"⚠ 合并统计数据失败: {e}")
    
    def _merge_table_data(self, old_soup, incremental_soup):
        """合并表格数据"""
        try:
            # 获取所有section
            old_sections = old_soup.find_all('div', class_='section')
            incremental_sections = incremental_soup.find_all('div', class_='section')
            
            # 为每个增量的section找到对应的老section
            for inc_section in incremental_sections:
                inc_header = inc_section.find('h2')
                if not inc_header:
                    continue
                
                inc_title = inc_header.get_text().strip()
                
                # 找到对应的老section
                matching_old_section = None
                for old_section in old_sections:
                    old_header = old_section.find('h2')
                    if old_header and self._is_similar_section(old_header.get_text().strip(), inc_title):
                        matching_old_section = old_section
                        break
                
                if matching_old_section:
                    # 合并表格数据
                    self._merge_section_table(matching_old_section, inc_section)
                else:
                    # 如果没有对应的section，就添加新的section
                    container = old_soup.find('div', class_='container')
                    footer = container.find('div', class_='footer')
                    if footer:
                        footer.insert_before(inc_section)
                    else:
                        container.append(inc_section)
                        
        except Exception as e:
            print(f"⚠ 合并表格数据失败: {e}")
    
    def _is_similar_section(self, title1: str, title2: str) -> bool:
        """判断两个section是否相似"""
        # 简单的相似度判断，基于关键词
        keywords = ['日期不匹配', '日期匹配', '未找到']
        
        for keyword in keywords:
            if keyword in title1 and keyword in title2:
                return True
        return False
    
    def _merge_section_table(self, old_section, inc_section):
        """合并section中的表格数据"""
        try:
            old_tbody = old_section.find('tbody')
            inc_tbody = inc_section.find('tbody')
            
            if old_tbody and inc_tbody:
                # 获取增量表格的所有行
                inc_rows = inc_tbody.find_all('tr')
                
                # 将增量的行添加到老表格中
                for row in inc_rows:
                    # 检查是否已存在相同的法律
                    law_name_cell = row.find('td')
                    if law_name_cell:
                        law_name = law_name_cell.get_text().strip()
                        if not self._law_exists_in_table(old_tbody, law_name):
                            old_tbody.append(row)
                
                # 更新section标题中的数量
                old_header = old_section.find('h2')
                if old_header:
                    new_count = len(old_tbody.find_all('tr'))
                    import re
                    old_header.string = re.sub(r'\(\d+\s*条\)', f'({new_count} 条)', old_header.get_text())
                    
        except Exception as e:
            print(f"⚠ 合并section表格失败: {e}")
    
    def _law_exists_in_table(self, tbody, law_name: str) -> bool:
        """检查法律是否已存在于表格中"""
        try:
            rows = tbody.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) > 1:  # 第二列是法律名称
                    existing_law = cells[1].get_text().strip()
                    if law_name in existing_law or existing_law in law_name:
                        return True
            return False
        except:
            return False


def main():
    """测试HTML报告生成器"""
    import sys
    
    if len(sys.argv) == 4 and sys.argv[1] == 'merge':
        # 合并模式
        old_html = sys.argv[2]
        incremental_html = sys.argv[3]
        
        generator = HTMLReportGenerator()
        result = generator.merge_html_reports(old_html, incremental_html)
        
        if result:
            print(f"✓ HTML报告合并成功: {result}")
        else:
            print("⚠ HTML报告合并失败")
        return
    
    # 示例数据
    test_results = [
        {
            '序号': '1',
            '法律名称': '中华人民共和国宪法',
            '原始日期': '2018-03-11',
            '查询结果': '2018-03-11',
            '原始来源': '国家法律法规数据库',
            '查询来源': 'official',
            '分类': '安全生产法律-其他',
            '日期匹配': True,
            '状态': '找到',
            '网址': 'https://flk.npc.gov.cn/'
        },
        {
            '序号': '2',
            '法律名称': '中华人民共和国职业病防治法',
            '原始日期': '2018-12-29',
            '查询结果': '2019-01-01',
            '原始来源': '江苏省应急管理厅网站',
            '查询来源': 'searxng',
            '分类': '安全生产法律-其他',
            '日期匹配': False,
            '状态': '找到'
        }
    ]
    
    test_stats = {
        'total_laws': 2,
        'official_db_laws': 1,
        'other_source_laws': 1,
        'official_db_found': 1,
        'other_source_found': 1,
        'official_db_matches': 1,
        'other_source_matches': 0
    }
    
    generator = HTMLReportGenerator()
    html_content = generator.generate_html_report(test_results, test_stats)
    filename = generator.save_html_report(html_content)
    
    print(f"测试HTML报告已生成: {filename}")
    print("\n使用方法:")
    print("python html_report_generator.py merge old_report.html incremental_report.html")


if __name__ == "__main__":
    main()
