#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版国家法律法规数据库爬虫
功能: 根据法律名称查询施行日期，支持缓存、重试、模糊匹配等功能
"""

import requests
import json
import re
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import quote_plus

# 导入路径配置模块
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from paths import PathConfig


@dataclass
class LawInfo:
    """法律信息数据类"""
    title: str
    effect_date: str
    status: int
    status_desc: str
    publish_date: Optional[str] = None
    source_url: Optional[str] = None
    search_source: str = "official"  # official, searxng, manual
    source_website: Optional[str] = None  # 获取途径/来源网站


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_file: str = None, expire_days: int = 30):
        # 使用PathConfig获取缓存文件路径
        if cache_file is None:
            cache_file = PathConfig.get_law_cache_file()
        self.cache_file = Path(cache_file)
        self.expire_days = expire_days
        self.cache = self._load_cache()
        self._lock = threading.Lock()
    
    def _load_cache(self) -> Dict:
        """加载缓存文件"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_cache(self):
        """保存缓存到文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.warning(f"保存缓存失败: {e}")
    
    def _get_cache_key(self, law_name: str) -> str:
        """生成缓存键"""
        return hashlib.md5(law_name.encode('utf-8')).hexdigest()
    
    def get(self, law_name: str) -> Optional[LawInfo]:
        """获取缓存的法律信息"""
        with self._lock:
            key = self._get_cache_key(law_name)
            if key in self.cache:
                cached_data = self.cache[key]
                # 检查是否过期
                cache_time = datetime.fromisoformat(cached_data['cached_at'])
                if datetime.now() - cache_time < timedelta(days=self.expire_days):
                    return LawInfo(**cached_data['data'])
                else:
                    # 删除过期缓存
                    del self.cache[key]
        return None
    
    def set(self, law_name: str, law_info: LawInfo):
        """设置缓存"""
        with self._lock:
            key = self._get_cache_key(law_name)
            self.cache[key] = {
                'data': {
                    'title': law_info.title,
                    'effect_date': law_info.effect_date,
                    'status': law_info.status,
                    'status_desc': law_info.status_desc,
                    'publish_date': law_info.publish_date,
                    'search_source': law_info.search_source,
                    'source_website': law_info.source_website
                },
                'cached_at': datetime.now().isoformat()
            }
            self._save_cache()
    
    def clear(self):
        """清除所有缓存"""
        with self._lock:
            self.cache.clear()
            self._save_cache()
    
    def size(self) -> int:
        """获取缓存条目数量"""
        return len(self.cache)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        with self._lock:
            total_entries = len(self.cache)
            expired_entries = 0
            
            current_time = datetime.now()
            for cached_data in self.cache.values():
                cache_time = datetime.fromisoformat(cached_data['cached_at'])
                if current_time - cache_time >= timedelta(days=self.expire_days):
                    expired_entries += 1
            
            return {
                'total_entries': total_entries,
                'expired_entries': expired_entries,
                'valid_entries': total_entries - expired_entries,
                'cache_file': str(self.cache_file),
                'expire_days': self.expire_days
            }


class SearXNGSearcher:
    """SearXNG搜索器"""
    
    def __init__(self, base_url: str = "http://localhost:5004"):
        self.base_url = base_url.rstrip('/')
        self.search_url = f"{self.base_url}/search"
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    def search_law_info(self, law_name: str) -> List[Dict[str, Any]]:
        """通过SearXNG搜索法律信息"""
        try:
            # 构造搜索查询
            query = f"{law_name} 施行日期 法律法规"
            
            params = {
                'q': query,
                'format': 'json',
                'categories': 'general',
                'engines': 'bing,google,baidu',  # 指定搜索引擎
                'time_range': '',
                'safesearch': '1'
            }
            
            response = self.session.get(
                self.search_url,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                self.logger.info(f"SearXNG找到 {len(results)} 条结果: {law_name}")
                return results
            else:
                self.logger.warning(f"SearXNG搜索失败，状态码: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"SearXNG搜索异常: {e}")
            return []
    
    def extract_date_from_results(self, results: List[Dict], law_name: str) -> Optional[str]:
        """从搜索结果中提取施行日期"""
        # 改进的日期匹配模式，按优先级排序
        date_patterns = [
            # 匹配 "本办法自发布之日起施行" 附近的发布日期
            r'(?:发布|印发|公布).*?(\d{4})年(\d{1,2})月(\d{1,2})日.*?(?:本办法自发布之日起施行|自发布之日起施行)',
            # 匹配文件头部的发布日期（如：2025年3月29日）
            r'(?:应急管理部|财政部|金融监管总局).*?(\d{4})年(\d{1,2})月(\d{1,2})日',
            # 匹配 "2017年12月12日公布" 这种格式
            r'(\d{4})年(\d{1,2})月(\d{1,2})日(?:公布|发布|施行|生效|实施)',
            # 匹配 "自2017年12月12日起施行"
            r'自(\d{4})年(\d{1,2})月(\d{1,2})日起(?:施行|生效|实施)',
            # 匹配 "施行日期：2017-12-12"
            r'施行[日期时间]*[：:](\d{4})[年-](\d{1,2})[月-](\d{1,2})[日号]?',
            # 匹配 "发布日期：2025-04-02" 
            r'发布日期[：:].*?(\d{4})[年-](\d{1,2})[月-](\d{1,2})[日号]?',
            # 匹配 "成文日期：2025-04-02"
            r'成文日期[：:].*?(\d{4})[年-](\d{1,2})[月-](\d{1,2})[日号]?',
            # 通用日期格式
            r'(\d{4})[年-](\d{1,2})[月-](\d{1,2})[日号]?(?:施行|生效|实施)',
            r'(\d{4})-(\d{1,2})-(\d{1,2})(?:施行|生效|实施)',
        ]
        
        for result in results:
            content = result.get('content', '') + ' ' + result.get('title', '')
            
            # 检查是否包含目标法律名称
            if law_name in content or any(part in content for part in law_name.split() if len(part) > 2):
                for pattern in date_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        match = matches[0]
                        if isinstance(match, tuple) and len(match) >= 3:
                            year, month, day = match[0], match[1], match[2]
                            try:
                                # 验证日期有效性
                                date_obj = datetime(int(year), int(month), int(day))
                                formatted_date = date_obj.strftime('%Y-%m-%d')
                                self.logger.info(f"从SearXNG提取到日期: {formatted_date}")
                                return formatted_date
                            except ValueError:
                                continue
        
        return None
    
    def extract_source_from_results(self, results: List[Dict], law_name: str) -> Optional[str]:
        """从搜索结果中提取获取途径信息"""
        # 定义常见的政府网站域名模式
        gov_patterns = [
            r'([^\s]+\.gov\.cn)',  # 政府网站
            r'([^\s]+应急管理厅[^\s]*)',  # 应急管理厅
            r'([^\s]+人民政府[^\s]*)',  # 人民政府
            r'([^\s]+发改委[^\s]*)',  # 发改委
            r'([^\s]+安监局[^\s]*)',  # 安监局
            r'([^\s]+环保局[^\s]*)',  # 环保局
            r'([^\s]+生态环境[^\s]*)',  # 生态环境部门
        ]
        
        for result in results:
            content = result.get('content', '') + ' ' + result.get('title', '')
            url = result.get('url', '')
            
            # 检查是否包含目标法律名称
            if law_name in content or any(part in content for part in law_name.split() if len(part) > 2):
                # 首先尝试从URL中提取域名
                if url:
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc
                        
                        # 如果是政府网站，提取更友好的名称
                        if '.gov.cn' in domain:
                            # 提取省市名称和部门
                            if 'yjgl' in domain or '应急' in domain:
                                if 'jiangsu' in domain or 'js' in domain:
                                    return "江苏省应急管理厅网站"
                                elif 'beijing' in domain or 'bj' in domain:
                                    return "北京市应急管理厅网站"
                                else:
                                    return f"{domain}(应急管理部门)"
                            elif 'huanbao' in domain or 'sthjt' in domain or '环保' in domain:
                                return f"{domain}(生态环境部门)"
                            else:
                                return f"{domain}(政府网站)"
                        else:
                            return f"{domain}网站"
                    except:
                        pass
                
                # 从内容中提取机构名称
                for pattern in gov_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        source = matches[0]
                        # 清理和格式化来源信息
                        if '应急管理厅' in source:
                            if '江苏' in source:
                                return "江苏省应急管理厅网站"
                            else:
                                return f"{source}网站"
                        elif '人民政府' in source:
                            return f"{source}网站"
                        elif '.gov.cn' in source:
                            return f"{source}(政府网站)"
                        else:
                            return f"{source}网站"
        
        return None
    
    def extract_law_info_with_source(self, results: List[Dict], law_name: str) -> tuple[Optional[str], Optional[str]]:
        """从搜索结果中同时提取施行日期和获取途径"""
        effect_date = self.extract_date_from_results(results, law_name)
        source = self.extract_source_from_results(results, law_name)
        return effect_date, source


class ChatAPISearcher:
    """聊天API搜索器"""
    
    def __init__(self, api_url: str = "http://192.168.61.29/v1/chat-messages"):
        self.api_url = api_url
        self.headers = {
            "Authorization": "Bearer app-odgVGDvCcxfK1YiIpC2yxyrQ",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
    
    def extract_implementation_date(self, text: str) -> Optional[str]:
        """使用正则表达式提取施行日期"""
        date_str = None
        
        # 优先匹配 **YYYY年MM月DD日** 格式的日期（加粗）
        pattern_bold = r'\*\*(\d{4}年\d{1,2}月\d{1,2}日)\*\*'
        match = re.search(pattern_bold, text)
        if match:
            date_str = match.group(1)
        else:
            # 匹配普通的 YYYY年MM月DD日 格式（无加粗）
            pattern_normal = r'(\d{4}年\d{1,2}月\d{1,2}日)'
            match = re.search(pattern_normal, text)
            if match:
                date_str = match.group(1)
            else:
                # 匹配不完整的日期格式 YYYY年MM月（缺少日，默认为1日）
                pattern_partial = r'(\d{4}年\d{1,2}月)'
                match = re.search(pattern_partial, text)
                if match:
                    date_str = match.group(1) + '1日'  # 补充日期为1日
        
        if date_str:
            try:
                # 转换为标准格式 YYYY-MM-DD
                year_match = re.search(r'(\d{4})年', date_str)
                month_match = re.search(r'(\d{1,2})月', date_str)
                day_match = re.search(r'(\d{1,2})日', date_str)
                
                if year_match and month_match and day_match:
                    year = year_match.group(1)
                    month = month_match.group(1).zfill(2)
                    day = day_match.group(1).zfill(2)
                    return f"{year}-{month}-{day}"
            except Exception as e:
                self.logger.warning(f"日期格式转换失败: {e}")
        
        return None
    
    def search_law_date(self, law_name: str) -> Optional[str]:
        """通过聊天API查询法律施行日期"""
        try:
            data = {
                "inputs": {"checkpoint": "施行日期"},
                "query": law_name,
                "response_mode": "streaming",
                "conversation_id": "",
                "user": "system"
            }
            
            self.logger.info(f"使用聊天API查询: {law_name}")
            
            response = self.session.post(
                self.api_url, 
                headers=self.headers, 
                json=data, 
                timeout=60, 
                stream=True
            )
            
            if response.status_code == 200:
                full_answer = ""
                
                # 处理流式响应
                for line in response.iter_lines():
                    if line:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('data: '):
                            data_part = line_text[6:].strip()
                            if data_part == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data_part)
                                if 'answer' in chunk_data:
                                    full_answer += chunk_data['answer']
                            except json.JSONDecodeError:
                                continue
                
                # 提取施行日期
                implementation_date = self.extract_implementation_date(full_answer)
                if implementation_date:
                    self.logger.info(f"聊天API找到施行日期: {law_name} -> {implementation_date}")
                    return implementation_date
                else:
                    self.logger.warning(f"聊天API未能提取施行日期: {law_name}")
                    self.logger.debug(f"完整回答: {full_answer}")
                    return None
            else:
                self.logger.error(f"聊天API请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"聊天API查询异常: {law_name}, 错误: {e}")
            return None


class EnhancedLawCrawler:
    """增强版法律爬虫"""
    
    def __init__(self, cache_enabled: bool = True, max_workers: int = 5, enable_searxng: bool = True, searxng_url: str = "http://localhost:5004", enable_chat_api: bool = True, chat_api_url: str = "http://localhost/v1/chat-messages"):
        self.base_url = "https://flk.npc.gov.cn"
        self.search_url = f"{self.base_url}/law-search/search/list"
        self.detail_url = f"{self.base_url}/law-search/search/detail"
        
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://flk.npc.gov.cn',
            'Referer': 'https://flk.npc.gov.cn/search',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 配置
        self.max_retries = 3
        self.retry_delay = 2
        self.request_timeout = 15
        self.max_workers = max_workers
        
        # 缓存管理
        self.cache_enabled = cache_enabled
        self.cache_manager = CacheManager() if cache_enabled else None
        
        # 状态映射
        self.status_map = {
            1: '已废止',
            2: '已修改', 
            3: '有效',
            4: '尚未生效'
        }
        
        # 状态优先级
        self.status_priority = {3: 1, 4: 2, 2: 3, 1: 4}
        
        # SearXNG搜索器
        self.enable_searxng = enable_searxng
        self.searxng = SearXNGSearcher(searxng_url) if enable_searxng else None
        
        # ChatAPI搜索器
        self.enable_chat_api = enable_chat_api
        self.chat_api = ChatAPISearcher(chat_api_url) if enable_chat_api else None
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 使用PathConfig获取日志文件路径
        log_file = PathConfig.get_crawler_log_file()
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _make_request_with_retry(self, url: str, data: Dict = None, method: str = 'POST') -> Optional[requests.Response]:
        """带重试机制的请求"""
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'POST':
                    response = self.session.post(url, json=data, timeout=self.request_timeout)
                else:
                    response = self.session.get(url, params=data, timeout=self.request_timeout)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # 请求过于频繁
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"请求频率限制，等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                else:
                    self.logger.warning(f"请求失败，状态码: {response.status_code}")
                    
            except requests.RequestException as e:
                self.logger.warning(f"请求异常 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def _normalize_law_name(self, law_name: str) -> List[str]:
        """法律名称标准化，生成可能的变体"""
        variants = [law_name.strip()]
        
        # 去除常见前缀
        prefixes = ['中华人民共和国', '国务院', '最高人民法院', '最高人民检察院']
        for prefix in prefixes:
            if law_name.startswith(prefix):
                short_name = law_name[len(prefix):].strip()
                if short_name:
                    variants.append(short_name)
        
        # 去除常见后缀
        suffixes = ['实施条例', '实施细则', '暂行规定', '暂行办法', '管理办法']
        for suffix in suffixes:
            if law_name.endswith(suffix):
                base_name = law_name[:-len(suffix)].strip()
                if base_name:
                    variants.append(base_name)
        
        return list(set(variants))  # 去重
    
    def search_law(self, law_name: str, fuzzy_match: bool = True, use_searxng_fallback: bool = True) -> Optional[LawInfo]:
        """
        搜索法律并返回法律信息
        
        Args:
            law_name: 法律名称
            fuzzy_match: 是否启用模糊匹配
            use_searxng_fallback: 官方数据库查找失败时是否使用SearXNG备用搜索
            
        Returns:
            LawInfo对象或None
        """
        # 检查缓存
        if self.cache_enabled and self.cache_manager:
            cached_result = self.cache_manager.get(law_name)
            if cached_result:
                self.logger.info(f"从缓存获取: {law_name}")
                return cached_result
        
        try:
            # 构造搜索参数
            search_params = {
                "searchRange": 1,
                "sxrq": [],
                "gbrq": [],
                "searchType": 2,
                "sxx": [],
                "gbrqYear": [],
                "flfgCodeId": [],
                "zdjgCodeId": [],
                "searchContent": law_name,
                "xgzlSearch": False,
                "orderByParam": {
                    "order": "-1",
                    "sort": ""
                },
                "pageNum": 1,
                "pageSize": 50  # 增加页面大小以获取更多结果
            }
            
            # 发送搜索请求
            response = self._make_request_with_retry(self.search_url, search_params)
            
            if not response:
                self.logger.error(f"搜索请求失败: {law_name}")
                return None
                
            # 解析响应数据
            data = response.json()
            
            # 检查是否有错误
            if 'error' in data or not data.get('rows'):
                self.logger.warning(f"搜索无结果: {law_name}")
                return None
                
            # 提取搜索结果
            results = data.get('rows', [])
            total = data.get('total', 0)
            
            self.logger.info(f"找到 {total} 条相关结果: {law_name}")
            
            if not results:
                return None
                
            # 查找最匹配的结果
            target_law = self._find_best_match(results, law_name, fuzzy_match)
            
            if target_law:
                law_info = self._extract_law_info(target_law)
                law_info.search_source = "official"
                
                # 保存到缓存
                if self.cache_enabled and self.cache_manager:
                    self.cache_manager.set(law_name, law_info)
                
                return law_info
            else:
                self.logger.warning(f"官方数据库未找到匹配的法律: {law_name}")
                
                # 尝试SearXNG备用搜索
                if use_searxng_fallback and self.enable_searxng and self.searxng:
                    searxng_result = self._search_with_searxng(law_name)
                    if searxng_result:
                        return searxng_result
                
                # 尝试ChatAPI备用搜索
                if self.enable_chat_api and self.chat_api:
                    return self._search_with_chat_api(law_name)
                
                return None
                
        except Exception as e:
            self.logger.error(f"搜索异常: {law_name}, 错误: {e}")
            return None
    
    def _find_best_match(self, results: List[Dict], target_name: str, fuzzy_match: bool = True) -> Optional[Dict]:
        """从搜索结果中找到最佳匹配项"""
        exact_matches = []
        fuzzy_matches = []
        
        # 生成目标名称的变体
        target_variants = self._normalize_law_name(target_name)
        
        for item in results:
            # 清理HTML标签
            title = re.sub(r'<[^>]+>', '', item.get('title', '')).strip()
            status = item.get('sxx', 0)
            
            # 精确匹配
            if title == target_name or title in target_variants:
                exact_matches.append((item, status))
            # 模糊匹配
            elif fuzzy_match:
                for variant in target_variants:
                    if variant in title or title in variant:
                        fuzzy_matches.append((item, status))
                        break
        
        # 优先返回精确匹配
        if exact_matches:
            exact_matches.sort(key=lambda x: self.status_priority.get(x[1], 5))
            return exact_matches[0][0]
        
        # 其次返回模糊匹配
        if fuzzy_matches:
            fuzzy_matches.sort(key=lambda x: self.status_priority.get(x[1], 5))
            return fuzzy_matches[0][0]
        
        return None
    
    def _extract_law_info(self, law_data: Dict) -> LawInfo:
        """从法律数据中提取信息"""
        title = re.sub(r'<[^>]+>', '', law_data.get('title', '')).strip()
        effect_date = law_data.get('sxrq') or law_data.get('gbrq', '')
        status = law_data.get('sxx', 0)
        status_desc = self.status_map.get(status, '未知状态')
        publish_date = law_data.get('gbrq', '')
        
        return LawInfo(
            title=title,
            effect_date=effect_date,
            status=status,
            status_desc=status_desc,
            publish_date=publish_date,
            search_source="official"
        )
    
    def batch_search(self, law_names: List[str], progress_callback=None) -> Dict[str, Optional[LawInfo]]:
        """批量搜索法律信息"""
        results = {}
        
        def search_single(law_name: str) -> Tuple[str, Optional[LawInfo]]:
            """单个搜索任务"""
            time.sleep(1)  # 请求间隔
            result = self.search_law(law_name)
            if progress_callback:
                progress_callback(law_name, result)
            return law_name, result
        
        # 使用线程池进行并发搜索
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_name = {executor.submit(search_single, name): name for name in law_names}
            
            for future in as_completed(future_to_name):
                law_name, result = future.result()
                results[law_name] = result
        
        return results
    
    def get_law_effect_date(self, law_name: str) -> Optional[str]:
        """获取法律施行日期的主要接口（兼容原接口）"""
        law_info = self.search_law(law_name)
        return law_info.effect_date if law_info else None
    
    def _search_with_searxng(self, law_name: str) -> Optional[LawInfo]:
        """使用SearXNG进行备用搜索"""
        try:
            self.logger.info(f"使用SearXNG备用搜索: {law_name}")
            
            # 搜索相关信息
            search_results = self.searxng.search_law_info(law_name)
            
            if not search_results:
                self.logger.warning(f"SearXNG未找到相关结果: {law_name}")
                return None
            
            # 同时提取施行日期和获取途径
            effect_date, source_website = self.searxng.extract_law_info_with_source(search_results, law_name)
            
            if effect_date:
                # 创建基于SearXNG搜索的法律信息
                law_info = LawInfo(
                    title=law_name,
                    effect_date=effect_date,
                    status=3,  # 假设为有效状态
                    status_desc="有效(SearXNG)",
                    search_source="searxng",
                    source_website=source_website
                )
                
                self.logger.info(f"SearXNG找到施行日期: {law_name} -> {effect_date}")
                if source_website:
                    self.logger.info(f"SearXNG找到获取途径: {law_name} -> {source_website}")
                
                # 保存到缓存
                if self.cache_enabled and self.cache_manager:
                    self.cache_manager.set(law_name, law_info)
                
                return law_info
            else:
                self.logger.warning(f"SearXNG未能提取施行日期: {law_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"SearXNG搜索异常: {law_name}, 错误: {e}")
            return None
    
    def _search_with_chat_api(self, law_name: str) -> Optional[LawInfo]:
        """使用ChatAPI进行备用搜索"""
        try:
            self.logger.info(f"使用ChatAPI备用搜索: {law_name}")
            
            # 查询施行日期
            effect_date = self.chat_api.search_law_date(law_name)
            
            if effect_date:
                # 创建基于ChatAPI搜索的法律信息
                law_info = LawInfo(
                    title=law_name,
                    effect_date=effect_date,
                    status=3,  # 假设为有效状态
                    status_desc="有效(ChatAPI)",
                    search_source="chat_api",
                    source_website="AI聊天接口"
                )
                
                self.logger.info(f"ChatAPI找到施行日期: {law_name} -> {effect_date}")
                
                # 保存到缓存
                if self.cache_enabled and self.cache_manager:
                    self.cache_manager.set(law_name, law_info)
                
                return law_info
            else:
                self.logger.warning(f"ChatAPI未能提取施行日期: {law_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"ChatAPI搜索异常: {law_name}, 错误: {e}")
            return None
    
    def test_chat_api_connection(self) -> bool:
        """测试ChatAPI连接"""
        if not self.enable_chat_api or not self.chat_api:
            return False
        
        try:
            test_result = self.chat_api.search_law_date("中华人民共和国安全生产法")
            if test_result:
                self.logger.info(f"ChatAPI连接测试成功，返回日期: {test_result}")
                return True
            else:
                self.logger.warning("ChatAPI连接测试失败，未返回日期")
                return False
        except Exception as e:
            self.logger.error(f"ChatAPI连接测试失败: {e}")
            return False
    
    def test_searxng_connection(self) -> bool:
        """测试SearXNG连接"""
        if not self.enable_searxng or not self.searxng:
            return False
        
        try:
            test_results = self.searxng.search_law_info("测试连接")
            self.logger.info(f"SearXNG连接测试成功，返回 {len(test_results)} 条结果")
            return True
        except Exception as e:
            self.logger.error(f"SearXNG连接测试失败: {e}")
            return False
    
    def clear_cache(self):
        """清空缓存"""
        if self.cache_manager:
            self.cache_manager.cache.clear()
            self.cache_manager._save_cache()
            self.logger.info("缓存已清空")


def enhanced_compare_dates_from_json(json_file: str = None):
    """增强版日期对比功能"""
    if not json_file:
        # 使用PathConfig获取默认输入文件路径
        json_file = PathConfig.get_law_json_file()
    
    crawler = EnhancedLawCrawler(cache_enabled=True)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {e}")
        return
    
    # 收集所有需要查询的法律
    law_list = []
    for category, subcategories in data.get('分类数据', {}).items():
        for subcategory, items in subcategories.items():
            for item in items:
                if item.get('获取途径') == '国家法律法规数据库':
                    law_list.append({
                        'name': item.get('法律、法规、标准及其他要求', ''),
                        'original_date': item.get('施行（修改）日期', ''),
                        'item': item,
                        'category': f"{category}-{subcategory}"
                    })
    
    print(f"共需查询 {len(law_list)} 条法律法规")
    
    # 进度回调函数
    completed_count = 0
    def progress_callback(law_name: str, result: Optional[LawInfo]):
        nonlocal completed_count
        completed_count += 1
        status = "✓" if result else "✗"
        print(f"[{completed_count}/{len(law_list)}] {status} {law_name}")
    
    # 批量查询
    law_names = [item['name'] for item in law_list]
    search_results = crawler.batch_search(law_names, progress_callback)
    
    # 生成对比结果
    results = []
    match_count = 0
    
    for law_item in law_list:
        law_name = law_item['name']
        original_date = law_item['original_date']
        law_info = search_results.get(law_name)
        
        web_date = law_info.effect_date if law_info else None
        
        # 比较日期
        date_match = False
        if web_date and original_date:
            try:
                original_date_clean = original_date.replace(' 00:00:00', '') if ' 00:00:00' in original_date else original_date
                date_match = original_date_clean == web_date
            except:
                date_match = False
        
        if date_match:
            match_count += 1
        
        result = {
            '序号': law_item['item'].get('序号', ''),
            '法律名称': law_name,
            '原始日期': original_date,
            '网站日期': web_date or '未找到',
            '日期匹配': '✓' if date_match else '✗',
            '法律状态': law_info.status_desc if law_info else '未知',
            '分类': law_item['category']
        }
        results.append(result)
    
    # 输出汇总结果
    print("\n" + "="*100)
    print("=== 汇总结果 ===")
    print(f"{'序号':<5} {'法律名称':<35} {'原始日期':<12} {'网站日期':<12} {'状态':<8} {'匹配':<5}")
    print("-" * 100)
    
    for result in results:
        print(f"{result['序号']:<5} {result['法律名称'][:33]:<35} {result['原始日期'][:10]:<12} {result['网站日期'][:10]:<12} {result['法律状态'][:6]:<8} {result['日期匹配']:<5}")
    
    print("-" * 100)
    total_count = len(results)
    print(f"总计: {total_count} 条记录，匹配: {match_count} 条，不匹配: {total_count - match_count} 条")
    print(f"匹配率: {match_count/total_count*100:.1f}%" if total_count > 0 else "匹配率: 0%")
    
    # 保存详细结果到文件
    output_file = f"law_comparison_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果已保存到: {output_file}")


def main():
    """主函数"""
    print("增强版法律爬虫启动")
    print("1. 单个查询")
    print("2. 批量对比")
    print("3. 清空缓存")
    print("4. 测试连接")
    
    choice = input("请选择功能 (1-4): ").strip()
    
    if choice == "1":
        law_name = input("请输入法律名称: ").strip()
        crawler = EnhancedLawCrawler()
        law_info = crawler.search_law(law_name)
        
        if law_info:
            print(f"\n查询结果:")
            print(f"法律名称: {law_info.title}")
            print(f"施行日期: {law_info.effect_date}")
            print(f"法律状态: {law_info.status_desc}")
            if law_info.publish_date:
                print(f"发布日期: {law_info.publish_date}")
        else:
            print(f"未找到法律: {law_name}")
    
    elif choice == "2":
        enhanced_compare_dates_from_json()
    
    elif choice == "3":
        crawler = EnhancedLawCrawler()
        crawler.clear_cache()
        print("缓存已清空")
    
    elif choice == "4":
        crawler = EnhancedLawCrawler()
        print("正在测试连接...")
        
        # 测试SearXNG连接
        if crawler.test_searxng_connection():
            print("✓ SearXNG连接正常")
        else:
            print("✗ SearXNG连接失败")
        
        # 测试ChatAPI连接
        if crawler.test_chat_api_connection():
            print("✓ ChatAPI连接正常")
        else:
            print("✗ ChatAPI连接失败")
    
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
