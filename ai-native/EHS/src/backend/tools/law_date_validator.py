#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
法律法规日期验证器
针对性地验证JSON数据中的施行日期，优先使用官方数据库，其他来源使用SearXNG
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import sys
from pathlib import Path

# 添加路径配置
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.append(str(current_dir.parent / "config"))

from enhanced_law_crawler import EnhancedLawCrawler
from html_report_generator import HTMLReportGenerator
from paths import PathConfig


def normalize_date(date_str: str) -> str:
    """标准化日期格式为 YYYY-MM-DD"""
    if not date_str:
        return ""
    
    # 移除时间部分
    date_str = date_str.replace(' 00:00:00', '').strip()
    
    # 处理不同的日期格式
    formats_to_try = [
        '%Y-%m-%d',      # 2023-05-01
        '%Y/%m/%d',      # 2023/05/01
        '%Y/%m/%d',      # 2023/5/1 (会被上面的格式处理)
        '%Y-%m-%d %H:%M:%S',  # 2023-05-01 00:00:00
    ]
    
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # 处理特殊格式 YYYY/M/D
    try:
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                year, month, day = parts
                # 补零
                month = month.zfill(2)
                day = day.zfill(2)
                return f"{year}-{month}-{day}"
    except:
        pass
    
    # 如果都无法解析，返回原始字符串
    return date_str


class LawDateValidator:
    """法律法规日期验证器"""
    
    def __init__(self, json_file: str, enable_searxng: bool = True, enable_chat_api: bool = True):
        self.json_file = json_file
        self.crawler = EnhancedLawCrawler(
            cache_enabled=True,
            enable_searxng=True,  # 生产环境禁用SearXNG
            searxng_url="http://192.168.61.29:5004",
            enable_chat_api=True,  # 生产环境禁用ChatAPI
            chat_api_url="http://192.168.61.29/v1/chat-messages"
        )
        self.html_generator = HTMLReportGenerator()
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(PathConfig.get_validation_log_file(), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = {
            'total_laws': 0,
            'official_db_laws': 0,
            'other_source_laws': 0,
            'official_db_matches': 0,
            'other_source_matches': 0,
            'official_db_found': 0,
            'other_source_found': 0,
            'date_mismatches': [],
            'not_found': []
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_laws': 0,
            'official_db_laws': 0,
            'other_source_laws': 0,
            'official_db_matches': 0,
            'other_source_matches': 0,
            'official_db_found': 0,
            'other_source_found': 0,
            'date_mismatches': [],
            'not_found': []
        }
    
    def load_data(self) -> Dict:
        """加载JSON数据"""
        try:
            # 检查文件是否存在
            if not Path(self.json_file).exists():
                self.logger.error(f"JSON文件不存在: {self.json_file}")
                print(f"❌ 错误：文件不存在 - {self.json_file}")
                return {}
            
            # 检查文件大小
            file_size = Path(self.json_file).stat().st_size
            if file_size == 0:
                self.logger.error(f"JSON文件为空: {self.json_file}")
                print(f"❌ 错误：文件为空 - {self.json_file}")
                return {}
            
            self.logger.info(f"正在加载JSON文件: {self.json_file} (大小: {file_size} 字节)")
            
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"成功加载JSON数据，包含 {len(data)} 个顶级键")
                return data
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON格式错误: {e}")
            print(f"❌ 错误：JSON格式错误 - {e}")
            return {}
        except PermissionError as e:
            self.logger.error(f"文件权限错误: {e}")
            print(f"❌ 错误：无权限访问文件 - {e}")
            return {}
        except Exception as e:
            self.logger.error(f"加载JSON文件失败: {e}")
            print(f"❌ 错误：加载文件失败 - {e}")
            return {}
    
    def clean_date(self, date_str: str) -> str:
        """清理日期格式"""
        if not date_str or date_str is None:
            return ""
        
        # 移除时间部分
        if ' 00:00:00' in str(date_str):
            return str(date_str).replace(' 00:00:00', '')
        
        return str(date_str).strip()
    
    def validate_single_law(self, law_item: Dict, category: str, subcategory: str) -> Dict:
        """验证单个法律的日期"""
        law_name = law_item.get('法律、法规、标准及其他要求', '') or ''
        original_date = self.clean_date(law_item.get('施行（修改）日期', ''))
        source = law_item.get('获取途径', '') or ''
        seq_no = law_item.get('序号', '') or ''
        
        self.logger.info(f"验证法律: {law_name}")
        self.logger.info(f"原始日期: {original_date}")
        self.logger.info(f"获取途径: {source}")
        
        # 检查法律名称是否有效
        if not law_name or law_name.strip() == '':
            self.logger.warning(f"跳过空法律名称: 序号 {seq_no}")
            return {
                '序号': seq_no,
                '法律名称': '空法律名称',
                '原始日期': original_date,
                '原始来源': source,
                '分类': f"{category or '未知'}-{subcategory or '未知'}",
                '查询结果': None,
                '查询来源': None,
                '日期匹配': False,
                '状态': '跳过',
                '网址': law_item.get('网址')
            }
        
        # 根据获取途径决定查询策略
        is_official_db = source == "国家法律法规数据库"
        
        if is_official_db:
            self.stats['official_db_laws'] += 1
            # 官方数据库：仅使用官方查询，不使用SearXNG备用
            law_info = self.crawler.search_law(law_name, use_searxng_fallback=False)
        else:
            self.stats['other_source_laws'] += 1
            # 其他来源：优先官方，失败时使用SearXNG
            law_info = self.crawler.search_law(law_name, use_searxng_fallback=True)
        
        # 分析结果
        result = {
            '序号': seq_no,
            '法律名称': law_name,
            '原始日期': original_date,
            '原始来源': source,
            '分类': f"{category}-{subcategory}",
            '查询结果': None,
            '查询来源': None,
            '获取途径': None,  # 新增获取途径字段
            '日期匹配': False,
            '状态': '未找到',
            '网址': law_item.get('网址')
        }
        
        if law_info:
            web_date = law_info.effect_date
            search_source = law_info.search_source
            
            result.update({
                '查询结果': web_date,
                '查询来源': search_source,
                '获取途径': law_info.source_website or '',  # 添加获取途径信息
                '法律状态': law_info.status_desc,
                '状态': '找到'
            })
            
            # 统计找到的数量
            if is_official_db:
                self.stats['official_db_found'] += 1
            else:
                self.stats['other_source_found'] += 1
            
            # 比较日期
            if original_date and web_date:
                # 标准化日期格式
                normalized_original = normalize_date(original_date)
                normalized_web = normalize_date(web_date)
                
                # 精确匹配
                exact_match = normalized_original == normalized_web
                
                # 新规则：如果搜索到的日期比原始日期旧，也视为匹配成功
                try:
                    original_dt = datetime.strptime(normalized_original, '%Y-%m-%d')
                    web_dt = datetime.strptime(normalized_web, '%Y-%m-%d')
                    older_date_match = web_dt <= original_dt
                except ValueError:
                    older_date_match = False
                
                # 匹配成功的条件：精确匹配 或 搜索日期更旧
                date_match = exact_match or older_date_match
                result['日期匹配'] = date_match
                
                if date_match:
                    if is_official_db:
                        self.stats['official_db_matches'] += 1
                    else:
                        self.stats['other_source_matches'] += 1
                    
                    if exact_match:
                        self.logger.info(f"✓ 日期精确匹配: {normalized_original}")
                    else:
                        self.logger.info(f"✓ 日期匹配(搜索日期更旧): {normalized_web} <= {normalized_original}")
                else:
                    self.stats['date_mismatches'].append(result)
                    self.logger.warning(f"✗ 日期不匹配: {normalized_original} vs {normalized_web} (原始: {original_date} vs {web_date})")
            else:
                self.logger.warning(f"✗ 缺少日期信息进行比较")
        else:
            self.stats['not_found'].append(result)
            self.logger.warning(f"✗ 未找到法律信息")
        
        return result
    
    def validate_all_laws(self) -> List[Dict]:
        """验证所有法律"""
        # 重置统计信息
        self.reset_stats()
        
        data = self.load_data()
        if not data:
            self.logger.error("数据加载失败或为空")
            print("❌ 错误：无法加载JSON数据文件")
            return []
        
        # 检查数据结构
        if '分类数据' not in data:
            self.logger.error("数据中没有找到'分类数据'键")
            print("❌ 错误：JSON文件格式不正确，缺少'分类数据'键")
            return []
        
        classification_data = data.get('分类数据', {})
        if not classification_data:
            self.logger.error("分类数据为空")
            print("❌ 错误：分类数据为空")
            return []
        
        results = []
        
        print("开始验证法律法规日期...")
        print("=" * 80)
        print(f"📊 数据概览：共 {len(classification_data)} 个分类")
        
        # 遍历所有分类数据
        for category, subcategories in classification_data.items():
            print(f"\n处理分类: {category}")
            
            for subcategory, items in subcategories.items():
                print(f"  处理子分类: {subcategory} ({len(items)} 条)")
                
                for item in items:
                    self.stats['total_laws'] += 1
                    
                    try:
                        result = self.validate_single_law(item, category, subcategory)
                        results.append(result)
                        
                        # 显示进度
                        status_icon = "✓" if result['状态'] == '找到' else "✗"
                        match_icon = "✓" if result['日期匹配'] else "✗"
                        law_name_display = (result['法律名称'] or '')[:40]
                        print(f"    [{self.stats['total_laws']:3d}] {status_icon} {law_name_display:<40} {match_icon}")
                        
                        # 请求间隔
                        time.sleep(1)
                        
                    except Exception as e:
                        law_name = item.get('法律、法规、标准及其他要求', '') or '未知法律'
                        self.logger.error(f"验证失败: {law_name}, 错误: {e}")
                        # 创建错误结果记录
                        error_result = {
                            '序号': item.get('序号', '') or '',
                            '法律名称': law_name,
                            '原始日期': self.clean_date(item.get('施行（修改）日期', '')),
                            '原始来源': item.get('获取途径', '') or '',
                            '分类': f"{category or '未知'}-{subcategory or '未知'}",
                            '查询结果': None,
                            '查询来源': None,
                            '日期匹配': False,
                            '状态': '错误',
                            '网址': item.get('网址')
                        }
                        results.append(error_result)
                        continue
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """生成验证报告"""
        report_lines = []
        
        # 标题
        report_lines.append("法律法规日期验证报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # 统计概览
        report_lines.append("## 统计概览")
        report_lines.append(f"总法律数量: {self.stats['total_laws']}")
        report_lines.append(f"官方数据库来源: {self.stats['official_db_laws']} 条")
        report_lines.append(f"其他来源: {self.stats['other_source_laws']} 条")
        report_lines.append("")
        
        # 查询成功率
        official_success_rate = (self.stats['official_db_found'] / self.stats['official_db_laws'] * 100) if self.stats['official_db_laws'] > 0 else 0
        other_success_rate = (self.stats['other_source_found'] / self.stats['other_source_laws'] * 100) if self.stats['other_source_laws'] > 0 else 0
        
        report_lines.append("## 查询成功率")
        report_lines.append(f"官方数据库: {self.stats['official_db_found']}/{self.stats['official_db_laws']} ({official_success_rate:.1f}%)")
        report_lines.append(f"其他来源: {self.stats['other_source_found']}/{self.stats['other_source_laws']} ({other_success_rate:.1f}%)")
        report_lines.append("")
        
        # 日期匹配率
        official_match_rate = (self.stats['official_db_matches'] / self.stats['official_db_found'] * 100) if self.stats['official_db_found'] > 0 else 0
        other_match_rate = (self.stats['other_source_matches'] / self.stats['other_source_found'] * 100) if self.stats['other_source_found'] > 0 else 0
        
        report_lines.append("## 日期匹配率")
        report_lines.append(f"官方数据库: {self.stats['official_db_matches']}/{self.stats['official_db_found']} ({official_match_rate:.1f}%)")
        report_lines.append(f"其他来源: {self.stats['other_source_matches']}/{self.stats['other_source_found']} ({other_match_rate:.1f}%)")
        report_lines.append("")
        
        # 详细结果表格
        report_lines.append("## 详细验证结果")
        report_lines.append(f"{'序号':<4} {'法律名称':<35} {'原始日期':<12} {'查询日期':<12} {'原始来源':<15} {'查询来源':<10} {'匹配':<4}")
        report_lines.append("-" * 100)
        
        for result in results:
            law_name = (result['法律名称'] or '')[:33] if len(result['法律名称'] or '') > 33 else (result['法律名称'] or '')
            original_source = (result['原始来源'] or '')[:13] if len(result['原始来源'] or '') > 13 else (result['原始来源'] or '')
            query_source = (result.get('查询来源', '') or '无')[:8]
            match_status = "✓" if result['日期匹配'] else "✗"
            
            report_lines.append(
                f"{result['序号'] or '':<4} {law_name:<35} {result['原始日期'] or '':<12} "
                f"{result.get('查询结果', '未找到') or '未找到':<12} {original_source:<15} {query_source:<10} {match_status:<4}"
            )
        
        # 日期不匹配详情
        if self.stats['date_mismatches']:
            report_lines.append("")
            report_lines.append("## 日期不匹配详情")
            for mismatch in self.stats['date_mismatches']:
                report_lines.append(f"- {mismatch['法律名称'] or '未知法律'}")
                report_lines.append(f"  原始: {mismatch['原始日期'] or '无'} | 查询: {mismatch.get('查询结果', '无') or '无'}")
                report_lines.append(f"  来源: {mismatch['原始来源'] or '无'} -> {mismatch.get('查询来源', '无') or '无'}")
                report_lines.append("")
        
        # 未找到的法律
        if self.stats['not_found']:
            report_lines.append("## 未找到的法律")
            for not_found in self.stats['not_found']:
                report_lines.append(f"- {not_found['法律名称'] or '未知法律'} (来源: {not_found['原始来源'] or '未知'})")
        
        return "\n".join(report_lines)
    
    def save_results(self, results: List[Dict], report: str):
        """保存验证结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成并保存HTML报告
        html_content = self.html_generator.generate_html_report(results, self.stats)
        html_file = PathConfig.get_validation_html_file(timestamp)
        html_file = self.html_generator.save_html_report(html_content, str(html_file))
        
        # 保存未找到的法规到指定JSON文件
        self.save_not_found_laws(results)
        
        print(f"\n验证结果已保存:")
        print(f"HTML报告: {html_file}")
        
        return html_file
    
    def save_not_found_laws(self, results: List[Dict]):
        """将未找到的法规保存到指定JSON文件"""
        # 筛选未找到的法规
        not_found_laws = [result for result in results if result['状态'] == '未找到']
        
        if not not_found_laws:
            print("\n✓ 所有法规都已找到，无需保存未找到列表")
            return
        
        # 转换为简化格式
        simplified_laws = []
        for law in not_found_laws:
            simplified_laws.append(law['法律名称'])
        
        # 使用PathConfig获取输出文件路径
        output_file = PathConfig.get_not_found_laws_file()
        
        try:
            # 尝试读取现有数据
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {}
            
            # 添加未找到的法规列表
            existing_data['未找到的法规'] = {
                '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '数量': len(simplified_laws),
                '法规列表': simplified_laws
            }
            
            # 保存更新后的数据
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ 已将 {len(simplified_laws)} 个未找到的法规保存到: {output_file}")
            
        except Exception as e:
            print(f"\n⚠ 保存未找到法规文件时出错: {e}")
            # 创建新的文件
            not_found_data = {
                '未找到的法规': {
                    '更新时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '数量': len(simplified_laws),
                    '法规列表': simplified_laws
                }
            }
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(not_found_data, f, ensure_ascii=False, indent=2)
                print(f"\n✓ 已创建新的未找到法规文件: {output_file}")
            except Exception as e2:
                print(f"\n✗ 无法创建未找到法规文件: {e2}")


def main():
    """主函数"""
    json_file = str(PathConfig.get_law_json_file())
    
    print("法律法规日期验证器")
    print("=" * 50)
    print("功能说明:")
    print("- 官方数据库来源: 仅使用 flk.npc.gov.cn 查询")
    print("- 其他来源: 优先官方数据库，失败时依次使用 SearXNG 和 ChatAPI 备用搜索")
    print("- 对比原始日期与查询结果的一致性")
    print("")
    
    # 创建验证器
    validator = LawDateValidator(json_file, enable_searxng=True, enable_chat_api=True)
    
    # 测试SearXNG连接
    if validator.crawler.enable_searxng:
        print("测试SearXNG连接...")
        if validator.crawler.test_searxng_connection():
            print("✓ SearXNG连接正常")
        else:
            print("✗ SearXNG连接失败，将仅使用官方数据库")
            validator.crawler.enable_searxng = False
    
    # 测试ChatAPI连接
    if validator.crawler.enable_chat_api:
        print("测试ChatAPI连接...")
        if validator.crawler.test_chat_api_connection():
            print("✓ ChatAPI连接正常")
        else:
            print("✗ ChatAPI连接失败，将不使用ChatAPI")
            validator.crawler.enable_chat_api = False
    
    print("")
    
    try:
        # 执行验证
        results = validator.validate_all_laws()
        
        # 生成报告
        report = validator.generate_report(results)
        
        # 显示报告
        print("\n" + "=" * 80)
        print(report)
        
        # 保存结果
        validator.save_results(results, report)
        
    except KeyboardInterrupt:
        print("\n用户中断验证")
    except Exception as e:
        print(f"\n验证过程出错: {e}")


if __name__ == "__main__":
    main()
