"""
智能表单填充API模块
提供批量处理和单查询两种API接口，支持CLI工具模式
"""

import json
import logging
import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class CellData:
    """单元格数据结构"""
    row: int
    col: int
    content: str
    relationship: List[str]
    
    def is_empty(self) -> bool:
        """检查内容是否为空"""
        return not self.content.strip()
    
    def validate(self) -> bool:
        """验证数据结构是否有效"""
        if not isinstance(self.row, int) or self.row < 0:
            return False
        if not isinstance(self.col, int) or self.col < 0:
            return False
        if not isinstance(self.content, str):
            return False
        if not isinstance(self.relationship, list):
            return False
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CellData':
        """从字典创建CellData实例"""
        return cls(
            row=data.get('row', 0),
            col=data.get('col', 0),
            content=data.get('content', ''),
            relationship=data.get('relationship', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'row': self.row,
            'col': self.col,
            'content': self.content,
            'relationship': self.relationship
        }


@dataclass
class ProcessingStats:
    """处理统计信息"""
    total_processed: int = 0
    successful_fills: int = 0
    failed_fills: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_success(self) -> None:
        """添加成功记录"""
        self.successful_fills += 1
        self.total_processed += 1
    
    def add_failure(self, error_msg: str = "") -> None:
        """添加失败记录"""
        self.failed_fills += 1
        self.total_processed += 1
        if error_msg:
            self.errors.append(error_msg)
    
    def set_processing_time(self, start_time: float) -> None:
        """设置处理时间"""
        self.processing_time = time.time() - start_time
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_processed == 0:
            return 0.0
        return self.successful_fills / self.total_processed
    
    def print_summary(self) -> None:
        """打印统计摘要到控制台"""
        print(f"\n=== 处理统计 ===")
        print(f"总处理数量: {self.total_processed}")
        print(f"成功填充: {self.successful_fills}")
        print(f"失败数量: {self.failed_fills}")
        print(f"成功率: {self.get_success_rate():.2%}")
        print(f"处理时间: {self.processing_time:.2f}秒")
        
        if self.errors:
            print(f"错误数量: {len(self.errors)}")
            print("错误详情:")
            for i, error in enumerate(self.errors[:5], 1):  # 只显示前5个错误
                print(f"  {i}. {error}")
            if len(self.errors) > 5:
                print(f"  ... 还有 {len(self.errors) - 5} 个错误")
        print("================")


class DataProvider(ABC):
    """数据提供者抽象基类"""
    
    @abstractmethod
    def get_sample_data(self) -> Dict[str, Any]:
        """获取样本数据"""
        pass
    
    @abstractmethod
    def query_by_keyword(self, keyword: str) -> Optional[str]:
        """根据关键词查询数据"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        pass


class FileDataProvider(DataProvider):
    """文件数据提供者"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._cache = None
        self._cache_timestamp = None
        self.logger = logging.getLogger(f"{__name__}.FileDataProvider")
    
    def get_sample_data(self) -> Dict[str, Any]:
        """从文件加载样本数据，支持缓存"""
        try:
            # 检查文件是否存在
            if not os.path.exists(self.file_path):
                self.logger.error(f"样本数据文件不存在: {self.file_path}")
                return {}
            
            # 获取文件修改时间
            file_mtime = os.path.getmtime(self.file_path)
            
            # 如果缓存存在且文件未修改，返回缓存
            if (self._cache is not None and 
                self._cache_timestamp is not None and 
                file_mtime <= self._cache_timestamp):
                self.logger.debug("使用缓存的样本数据")
                return self._cache
            
            # 加载文件数据
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新缓存
            self._cache = data
            self._cache_timestamp = file_mtime
            
            self.logger.info(f"成功加载样本数据: {len(data)} 个字段")
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON格式错误: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"加载样本数据失败: {e}")
            return {}
    
    def query_by_keyword(self, keyword: str) -> Optional[str]:
        """从文件数据中根据关键词查询"""
        try:
            data = self.get_sample_data()
            
            # 精确匹配
            if keyword in data:
                return str(data[keyword])
            
            # 模糊匹配（包含关键词的键）
            for key, value in data.items():
                if keyword in key:
                    return str(value)
            
            # 在值中搜索
            for key, value in data.items():
                if isinstance(value, str) and keyword in value:
                    return str(value)
            
            return None
            
        except Exception as e:
            self.logger.error(f"查询关键词失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """检查文件数据源是否可用"""
        return os.path.exists(self.file_path) and os.path.isfile(self.file_path)
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._cache = None
        self._cache_timestamp = None
        self.logger.debug("缓存已清除")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "has_cache": self._cache is not None,
            "cache_timestamp": self._cache_timestamp,
            "file_path": self.file_path,
            "file_exists": self.is_available()
        }


class DatabaseDataProvider(DataProvider):
    """数据库数据提供者（预留接口）"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.connection_config = connection_config
        self.logger = logging.getLogger(f"{__name__}.DatabaseDataProvider")
    
    def get_sample_data(self) -> Dict[str, Any]:
        """从数据库加载样本数据"""
        # TODO: 实现数据库连接和查询逻辑
        self.logger.warning("数据库数据提供者尚未实现")
        return {}
    
    def query_by_keyword(self, keyword: str) -> Optional[str]:
        """从数据库查询"""
        # TODO: 实现数据库查询逻辑
        self.logger.warning("数据库查询功能尚未实现")
        return None
    
    def is_available(self) -> bool:
        """检查数据库连接是否可用"""
        # TODO: 实现数据库连接检查
        return False


class Matcher(ABC):
    """匹配器抽象基类"""
    
    @abstractmethod
    def match(self, keywords: List[str], data_provider: DataProvider, context: Dict[str, Any] = None) -> Optional[tuple]:
        """
        匹配方法
        
        Args:
            keywords: 关键词列表
            data_provider: 数据提供者
            context: 上下文信息
            
        Returns:
            tuple: (value, source, confidence) 或 None
        """
        pass


class ExactMatcher(Matcher):
    """精确匹配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ExactMatcher")
    
    def match(self, keywords: List[str], data_provider: DataProvider, context: Dict[str, Any] = None) -> Optional[tuple]:
        """
        精确匹配关键词与样本数据
        
        Args:
            keywords: 关键词列表
            data_provider: 数据提供者
            context: 上下文信息（未使用）
            
        Returns:
            tuple: (value, source, confidence) 或 None
        """
        try:
            sample_data = data_provider.get_sample_data()
            
            if not sample_data:
                self.logger.warning("样本数据为空")
                return None
            
            # 遍历关键词进行精确匹配
            for keyword in keywords:
                if keyword in sample_data:
                    value = sample_data[keyword]
                    self.logger.debug(f"精确匹配成功: {keyword} -> {value}")
                    return (value, f"exact:{keyword}", 1.0)
            
            self.logger.debug(f"精确匹配失败: {keywords}")
            return None
            
        except Exception as e:
            self.logger.error(f"精确匹配过程中发生错误: {e}")
            return None
    
    def get_matcher_info(self) -> Dict[str, Any]:
        """获取匹配器信息"""
        return {
            "name": "ExactMatcher",
            "description": "精确匹配器，进行关键词与样本数据的精确匹配",
            "priority": 1,  # 最高优先级
            "confidence_range": (1.0, 1.0)
        }


class SmartMatcher(Matcher):
    """智能匹配器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.synonyms = config.get('synonyms', {})
        self.context_rules = config.get('context_rules', {})
        self.similarity_threshold = config.get('similarity_threshold', 0.8)
        self.logger = logging.getLogger(f"{__name__}.SmartMatcher")
    
    def match(self, keywords: List[str], data_provider: DataProvider, context: Dict[str, Any] = None) -> Optional[tuple]:
        """
        智能匹配，包含同义词、上下文规则、模糊匹配和生成规则
        
        Args:
            keywords: 关键词列表
            data_provider: 数据提供者
            context: 上下文信息
            
        Returns:
            tuple: (value, source, confidence) 或 None
        """
        try:
            sample_data = data_provider.get_sample_data()
            
            if not sample_data:
                self.logger.warning("样本数据为空")
                return None
            
            # 1. 同义词匹配
            result = self._synonym_match(keywords, sample_data)
            if result:
                return result
            
            # 2. 上下文规则匹配
            result = self._context_match(keywords, sample_data, context)
            if result:
                return result
            
            # 3. 模糊匹配
            result = self._fuzzy_match(keywords, sample_data)
            if result:
                return result
            
            # 4. 生成规则匹配
            result = self._generation_match(keywords, sample_data, context)
            if result:
                return result
            
            self.logger.debug(f"智能匹配失败: {keywords}")
            return None
            
        except Exception as e:
            self.logger.error(f"智能匹配过程中发生错误: {e}")
            return None
    
    def _synonym_match(self, keywords: List[str], sample_data: Dict[str, Any]) -> Optional[tuple]:
        """同义词匹配"""
        for keyword in keywords:
            # 检查是否有同义词配置
            synonyms = self.synonyms.get(keyword, [])
            
            for synonym in synonyms:
                if synonym in sample_data:
                    value = sample_data[synonym]
                    self.logger.debug(f"同义词匹配成功: {keyword} -> {synonym} -> {value}")
                    return (value, f"synonym:{keyword}->{synonym}", 0.9)
        
        return None
    
    def _context_match(self, keywords: List[str], sample_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[tuple]:
        """上下文规则匹配"""
        if not context:
            return None
        
        for keyword in keywords:
            # 检查是否有上下文规则
            if keyword in self.context_rules:
                rule = self.context_rules[keyword]
                
                # 基于行位置的规则
                row = context.get('row', 0)
                row_key = f"row_{row}"
                
                # 基于区域的规则
                section = self._infer_section(context)
                
                # 尝试应用规则
                if isinstance(rule, dict):
                    # 复杂规则
                    if row_key in rule and rule[row_key] in sample_data:
                        value = sample_data[rule[row_key]]
                        return (value, f"context:row_{row}->{rule[row_key]}", 0.85)
                    
                    if section in rule and rule[section] in sample_data:
                        value = sample_data[rule[section]]
                        return (value, f"context:section_{section}->{rule[section]}", 0.8)
                
                elif isinstance(rule, str):
                    # 简单规则（生成规则）
                    if rule.startswith("generate_"):
                        generated_value = self._generate_value(rule, sample_data, context)
                        if generated_value:
                            return (generated_value, f"context:generated:{rule}", 0.75)
        
        return None
    
    def _fuzzy_match(self, keywords: List[str], sample_data: Dict[str, Any]) -> Optional[tuple]:
        """模糊匹配"""
        from difflib import SequenceMatcher
        
        best_match = None
        best_score = 0
        
        for keyword in keywords:
            for key in sample_data.keys():
                # 计算相似度
                score = SequenceMatcher(None, keyword, key).ratio()
                
                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = (sample_data[key], f"fuzzy:{keyword}->{key}", score * 0.8)  # 降低置信度
        
        if best_match:
            self.logger.debug(f"模糊匹配成功: {best_match}")
        
        return best_match
    
    def _generation_match(self, keywords: List[str], sample_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[tuple]:
        """生成规则匹配"""
        for keyword in keywords:
            if keyword in self.context_rules:
                rule = self.context_rules[keyword]
                
                if isinstance(rule, str) and rule.startswith("generate_"):
                    generated_value = self._generate_value(rule, sample_data, context)
                    if generated_value:
                        return (generated_value, f"generated:{rule}", 0.7)
        
        return None
    
    def _generate_value(self, generator_type: str, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成值"""
        try:
            if generator_type == "generate_social_benefit":
                product = data.get("主导产品名称（中文）", data.get("企业名称", ""))
                if product:
                    return f"通过{product}提升行业数字化水平，促进社会发展和进步"
                return "提升行业数字化水平，促进社会发展"
            
            elif generator_type == "generate_economic_benefit":
                product = data.get("主导产品名称（中文）", "")
                if product:
                    return f"通过{product}降低运营成本，提高经济效益和市场竞争力"
                return "降低运营成本，提高经济效益"
            
            elif generator_type == "generate_function_building":
                product = data.get("主导产品名称（中文）", data.get("企业名称", ""))
                if product:
                    return f"基于{product}的功能建设和技术开发，完善系统架构"
                return "完善系统功能建设和技术架构"
            
            elif generator_type == "generate_application_promotion":
                return "通过线上线下多渠道推广，扩大市场影响力和用户覆盖面"
            
            return ""
            
        except Exception as e:
            self.logger.error(f"生成值时发生错误: {e}")
            return ""
    
    def _infer_section(self, context: Dict[str, Any]) -> str:
        """推断所在区域"""
        row = context.get('row', 0)
        
        if row <= 3:
            return "基本信息"
        elif row <= 6:
            return "法人信息"
        elif row <= 10:
            return "联系人信息"
        else:
            return "其他信息"
    
    def get_matcher_info(self) -> Dict[str, Any]:
        """获取匹配器信息"""
        return {
            "name": "SmartMatcher",
            "description": "智能匹配器，支持同义词、上下文规则、模糊匹配和生成规则",
            "priority": 2,
            "confidence_range": (0.7, 0.9),
            "features": ["synonym", "context", "fuzzy", "generation"],
            "synonyms_count": len(self.synonyms),
            "context_rules_count": len(self.context_rules),
            "similarity_threshold": self.similarity_threshold
        }


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(f"{__name__}.CircuitBreaker")
    
    def call(self, func, *args, **kwargs):
        """执行函数调用"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                self.logger.info("熔断器状态变更为 HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """成功时重置计数器"""
        if self.failure_count > 0:
            self.logger.info("熔断器恢复正常")
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """失败时增加计数器"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            self.logger.warning(f"熔断器触发，失败次数: {self.failure_count}")
    
    def get_state(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "recovery_timeout": self.recovery_timeout
        }


class APIMatcher(Matcher):
    """API智能匹配器 - 适配新的工作流API接口"""
    
    def __init__(self, api_config: Dict[str, Any]):
        self.api_config = api_config
        self.cache = {}
        self.circuit_breaker = CircuitBreaker(
            api_config.get("circuit_breaker", {}).get("failure_threshold", 5),
            api_config.get("circuit_breaker", {}).get("recovery_timeout", 300)
        )
        self.logger = logging.getLogger(f"{__name__}.APIMatcher")
        
        # 验证必要的配置
        self._validate_config()
    
    def _validate_config(self) -> None:
        """验证API配置"""
        required_fields = ["url", "authorization"]
        for field in required_fields:
            if not self.api_config.get(field):
                self.logger.warning(f"API配置缺少字段: {field}")
    
    def match(self, keywords: List[str], data_provider: DataProvider, context: Dict[str, Any] = None) -> Optional[tuple]:
        """
        调用新的工作流API进行智能匹配
        
        Args:
            keywords: 关键词列表
            data_provider: 数据提供者
            context: 上下文信息
            
        Returns:
            tuple: (value, source, confidence) 或 None
        """
        try:
            # 检查API配置
            if not self.api_config.get("url") or not self.api_config.get("authorization"):
                self.logger.warning("API配置不完整")
                return None
            
            # 生成缓存键
            sample_data = data_provider.get_sample_data()
            cache_key = self._generate_cache_key(keywords, sample_data, context)
            
            # 检查缓存
            if cache_key in self.cache:
                self.logger.debug(f"使用缓存结果: {keywords}")
                return self.cache[cache_key]
            
            # 调用API
            result = self.circuit_breaker.call(self._call_workflow_api, keywords, sample_data, context)
            
            if result:
                # 缓存结果
                self.cache[cache_key] = result
                self.logger.debug(f"API匹配成功: {keywords} -> {result[0]}")
                return result
            
            self.logger.debug(f"API匹配失败: {keywords}")
            return None
            
        except Exception as e:
            self.logger.error(f"API匹配过程中发生错误: {e}")
            return None
    
    def _call_workflow_api(self, keywords: List[str], sample_data: Dict[str, Any], context: Dict[str, Any]) -> Optional[tuple]:
        """调用新的工作流API接口"""
        try:
            # 构建请求头
            headers = {
                "Authorization": self.api_config["authorization"],
                "Content-Type": "application/json"
            }
            
            # 构建请求数据 - 适配新的API格式
            text_input = self._prepare_text_input(keywords, sample_data, context)
            
            request_data = {
                "inputs": {
                    "text": text_input
                },
                "response_mode": "blocking",
                "user": self.api_config.get("user", "system")
            }
            
            self.logger.debug(f"发送API请求: {text_input}")
            
            # 发送请求
            response = requests.post(
                self.api_config["url"],
                headers=headers,
                json=request_data,
                timeout=self.api_config.get("timeout", 30)
            )
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"API响应状态码: {response.status_code}")
                
                # 解析新的响应格式
                return self._parse_workflow_response(result, keywords)
            else:
                self.logger.warning(f"API请求失败: {response.status_code} - {response.text}")
                return None
            
        except requests.exceptions.Timeout:
            self.logger.error("API请求超时")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求异常: {e}")
            raise
        except Exception as e:
            self.logger.error(f"API调用过程中发生未知错误: {e}")
            raise
    
    def _prepare_text_input(self, keywords: List[str], sample_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """准备文本输入，将关键词和上下文信息转换为API可理解的文本"""
        try:
            # 基础关键词
            text_parts = []
            
            # 主要关键词
            if keywords:
                primary_keyword = keywords[0]  # 使用第一个关键词作为主要查询
                text_parts.append(primary_keyword)
            
            # 可以根据需要添加更多上下文信息
            if context and context.get('row') is not None:
                text_parts.append(f"(第{context['row']}行)")
            
            # 如果有多个关键词，可以作为补充信息
            if len(keywords) > 1:
                additional_keywords = ", ".join(keywords[1:])
                text_parts.append(f"相关: {additional_keywords}")
            
            return " ".join(text_parts)
            
        except Exception as e:
            self.logger.error(f"准备文本输入时发生错误: {e}")
            # 降级处理：直接返回第一个关键词
            return keywords[0] if keywords else ""
    
    def _parse_workflow_response(self, response_data: Dict[str, Any], keywords: List[str]) -> Optional[tuple]:
        """解析新的工作流API响应格式"""
        try:
            # 检查响应结构
            if 'data' not in response_data:
                self.logger.warning("API响应缺少data字段")
                return None
            
            data = response_data['data']
            
            # 检查工作流状态
            status = data.get('status')
            if status != 'succeeded':
                self.logger.warning(f"工作流执行失败，状态: {status}")
                error_msg = data.get('error', '未知错误')
                if error_msg:
                    self.logger.error(f"工作流错误: {error_msg}")
                return None
            
            # 提取输出结果
            outputs = data.get('outputs', {})
            if 'text' not in outputs:
                self.logger.warning("API响应outputs中缺少text字段")
                return None
            
            result_text = outputs['text']
            if not result_text or not result_text.strip():
                self.logger.debug("API返回空结果")
                return None
            
            # 计算置信度（基于API响应的一些指标）
            confidence = self._calculate_confidence(data, keywords, result_text)
            
            # 构建来源信息
            workflow_id = data.get('workflow_id', 'unknown')
            source = f"api:workflow:{workflow_id[:8]}"  # 使用工作流ID的前8位
            
            self.logger.info(f"API匹配成功: {keywords} -> {result_text} (置信度: {confidence})")
            
            return (result_text.strip(), source, confidence)
            
        except Exception as e:
            self.logger.error(f"解析API响应时发生错误: {e}")
            return None
    
    def _calculate_confidence(self, data: Dict[str, Any], keywords: List[str], result_text: str) -> float:
        """计算置信度"""
        try:
            base_confidence = 0.8  # 基础置信度
            
            # 根据执行时间调整置信度
            elapsed_time = data.get('elapsed_time', 0)
            if elapsed_time > 0:
                if 1 <= elapsed_time <= 10:
                    time_factor = 1.0
                elif elapsed_time < 1:
                    time_factor = 0.9  # 太快可能不够准确
                else:
                    time_factor = max(0.7, 1.0 - (elapsed_time - 10) * 0.01)
                
                base_confidence *= time_factor
            
            # 根据token使用量调整
            total_tokens = data.get('total_tokens', 0)
            if total_tokens > 0:
                if 100 <= total_tokens <= 2000:
                    token_factor = 1.0
                elif total_tokens < 100:
                    token_factor = 0.9
                else:
                    token_factor = 0.95
                
                base_confidence *= token_factor
            
            # 根据结果长度调整
            if result_text:
                result_length = len(result_text.strip())
                if 1 <= result_length <= 100:
                    length_factor = 1.0
                elif result_length > 100:
                    length_factor = 0.95
                else:
                    length_factor = 0.8
                
                base_confidence *= length_factor
            
            # 确保置信度在合理范围内
            return max(0.6, min(1.0, base_confidence))
            
        except Exception as e:
            self.logger.error(f"计算置信度时发生错误: {e}")
            return 0.8  # 默认置信度
    
    def _generate_cache_key(self, keywords: List[str], sample_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """生成缓存键"""
        import hashlib
        
        # 创建唯一标识
        key_parts = [
            "|".join(sorted(keywords)),
            "|".join(sorted(sample_data.keys())),
            str(context) if context else ""
        ]
        
        key_string = "||".join(key_parts)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache.clear()
        self.logger.info("API匹配器缓存已清除")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            "cache_size": len(self.cache),
            "circuit_breaker_state": self.circuit_breaker.get_state()
        }
    
    def get_matcher_info(self) -> Dict[str, Any]:
        """获取匹配器信息"""
        return {
            "name": "APIMatcher",
            "description": "API智能匹配器，调用工作流API进行智能匹配",
            "priority": 3,
            "confidence_range": (0.6, 1.0),
            "features": ["workflow_api", "cache", "circuit_breaker", "confidence_calculation"],
            "api_url": self.api_config.get("url", "未配置"),
            "timeout": self.api_config.get("timeout", 30),
            "cache_info": self.get_cache_info(),
            "api_type": "workflow_blocking"
        }


class MatchingEngine:
    """匹配引擎核心"""
    
    def __init__(self, config: Dict[str, Any], data_provider: DataProvider):
        self.config = config
        self.data_provider = data_provider
        self.logger = logging.getLogger(f"{__name__}.MatchingEngine")
        
        # 初始化三层匹配器
        self.exact_matcher = ExactMatcher()
        self.smart_matcher = SmartMatcher(config.get('matching', {}))
        
        # API匹配器（可选）
        self.api_matcher = None
        if config.get('matching', {}).get('enable_api', False):
            api_config = config.get('api', {})
            if api_config.get('url'):
                self.api_matcher = APIMatcher(api_config)
            else:
                self.logger.warning("API匹配器已启用但未配置URL")
        
        # 匹配器列表（按优先级排序）
        self.matchers = [self.exact_matcher, self.smart_matcher]
        if self.api_matcher:
            self.matchers.append(self.api_matcher)
        
        self.logger.info(f"匹配引擎初始化完成，共 {len(self.matchers)} 个匹配器")
    
    def find_match(self, keywords: List[str], context: Dict[str, Any] = None) -> Optional[tuple]:
        """
        三层匹配策略：精确匹配 -> 智能匹配 -> API匹配
        
        Args:
            keywords: 关键词列表
            context: 上下文信息
            
        Returns:
            tuple: (value, source, confidence) 或 None
        """
        try:
            # 提取和清理关键词
            cleaned_keywords = self._extract_keywords(keywords)
            
            if not cleaned_keywords:
                self.logger.warning("没有有效的关键词")
                return None
            
            self.logger.debug(f"开始匹配: {cleaned_keywords}")
            
            # 按优先级依次尝试匹配器
            for matcher in self.matchers:
                try:
                    result = matcher.match(cleaned_keywords, self.data_provider, context)
                    
                    if result:
                        value, source, confidence = result
                        self.logger.info(f"匹配成功 [{matcher.__class__.__name__}]: {cleaned_keywords} -> {value} (置信度: {confidence})")
                        return result
                    
                except Exception as e:
                    self.logger.error(f"匹配器 {matcher.__class__.__name__} 执行失败: {e}")
                    continue
            
            self.logger.debug(f"所有匹配器都未找到匹配: {cleaned_keywords}")
            return None
            
        except Exception as e:
            self.logger.error(f"匹配引擎执行过程中发生错误: {e}")
            return None
    
    def _extract_keywords(self, keywords: List[str]) -> List[str]:
        """提取和清理关键词"""
        if not keywords:
            return []
        
        cleaned = []
        for keyword in keywords:
            if isinstance(keyword, str):
                # 清理空白字符
                cleaned_keyword = keyword.strip()
                if cleaned_keyword:
                    cleaned.append(cleaned_keyword)
        
        # 去重并保持顺序
        seen = set()
        result = []
        for keyword in cleaned:
            if keyword not in seen:
                seen.add(keyword)
                result.append(keyword)
        
        return result
    
    def batch_match(self, keyword_list: List[List[str]], contexts: List[Dict[str, Any]] = None) -> List[Optional[tuple]]:
        """
        批量匹配
        
        Args:
            keyword_list: 关键词列表的列表
            contexts: 上下文信息列表
            
        Returns:
            List[Optional[tuple]]: 匹配结果列表
        """
        results = []
        contexts = contexts or [None] * len(keyword_list)
        
        for i, keywords in enumerate(keyword_list):
            context = contexts[i] if i < len(contexts) else None
            result = self.find_match(keywords, context)
            results.append(result)
        
        return results
    
    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        matcher_info = []
        for matcher in self.matchers:
            if hasattr(matcher, 'get_matcher_info'):
                matcher_info.append(matcher.get_matcher_info())
        
        return {
            "name": "MatchingEngine",
            "description": "三层匹配引擎：精确匹配 -> 智能匹配 -> API匹配",
            "matcher_count": len(self.matchers),
            "matchers": matcher_info,
            "data_provider": self.data_provider.__class__.__name__,
            "api_enabled": self.api_matcher is not None
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_matchers": len(self.matchers),
            "exact_matcher": True,
            "smart_matcher": True,
            "api_matcher": self.api_matcher is not None
        }
        
        # 获取各匹配器的缓存信息
        if hasattr(self.smart_matcher, 'get_matcher_info'):
            smart_info = self.smart_matcher.get_matcher_info()
            stats["smart_matcher_features"] = smart_info.get("features", [])
        
        if self.api_matcher and hasattr(self.api_matcher, 'get_cache_info'):
            stats["api_cache_info"] = self.api_matcher.get_cache_info()
        
        return stats
    
    def clear_caches(self) -> None:
        """清除所有缓存"""
        # 清除数据提供者缓存
        if hasattr(self.data_provider, 'clear_cache'):
            self.data_provider.clear_cache()
        
        # 清除API匹配器缓存
        if self.api_matcher and hasattr(self.api_matcher, 'clear_cache'):
            self.api_matcher.clear_cache()
        
        self.logger.info("所有缓存已清除")


@dataclass
class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                # 创建默认配置
                self._config = self._get_default_config()
                self._save_config()
        except Exception as e:
            logging.error(f"加载配置文件失败: {e}")
            self._config = self._get_default_config()
    
    def _save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存配置文件失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "data_source": {
                "type": "file",
                "sample_data_path": "tools/example_data.json",
                "output_suffix": "_filled"
            },
            "matching": {
                "synonyms": {
                    "社会效益": ["社会价值", "社会贡献", "社会影响"],
                    "经济效益": ["经济价值", "经济贡献", "经济影响"],
                    "单位名称": ["企业名称", "公司名称", "机构名称"],
                    "法人代表": ["法定代表人", "法人"],
                    "联系电话": ["电话", "手机", "联系方式"]
                },
                "context_rules": {
                    "社会效益": "generate_social_benefit",
                    "经济效益": "generate_economic_benefit",
                    "功能建设": "generate_function_building",
                    "应用推广": "generate_application_promotion"
                },
                "similarity_threshold": 0.8,
                "enable_api": False,
                "enable_fuzzy": True
            },
            "processing": {
                "multi_value_separator": "@@@",
                "fill_blank_pattern": "_____",
                "multi_value_strategy": "first"
            },
            "api": {
                "url": "http://192.168.61.29/v1/workflows/run",
                "authorization": "Bearer app-KC0OMjV4xGLdmAfgUnn7w6yx",
                "timeout": 30,
                "user": "system",
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "recovery_timeout": 300
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def get_sample_data_path(self) -> str:
        """获取样本数据路径"""
        return self.get("data_source.sample_data_path", "example_data.json")
    
    def get_output_suffix(self) -> str:
        """获取输出文件后缀"""
        return self.get("data_source.output_suffix", "_filled")
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config if self._config is not None else {}


def setup_logging(config_manager: ConfigManager) -> None:
    """设置日志系统"""
    log_level = config_manager.get("logging.level", "INFO")
    log_format = config_manager.get("logging.format", 
                                   "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('form_filler.log', encoding='utf-8')
        ]
    )


def setup_logging(config_manager: ConfigManager) -> None:
    """设置日志系统"""
    log_level = config_manager.get("logging.level", "INFO")
    log_format = config_manager.get("logging.format", 
                                   "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('form_filler.log', encoding='utf-8')
        ]
    )


class ValueProcessor:
    """值处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ValueProcessor")
    
    def process(self, raw_value: Any, context: Dict[str, Any] = None) -> str:
        """
        处理复杂格式的值
        
        Args:
            raw_value: 原始值
            context: 上下文信息
            
        Returns:
            str: 处理后的值
        """
        try:
            if raw_value is None:
                return ""
            
            value_str = str(raw_value)
            
            # 处理多年度数据
            if self.config.get('multi_value_separator', '@@@') in value_str:
                value_str = self._handle_multi_value(value_str, context)
            
            # 提取填空格式
            if self.config.get('fill_blank_pattern', '_____') in value_str:
                value_str = self._extract_fill_in_blank(value_str)
            
            # 清理和格式化
            value_str = self._clean_and_format(value_str)
            
            return value_str.strip()
            
        except Exception as e:
            self.logger.error(f"处理值时发生错误: {e}")
            return str(raw_value) if raw_value is not None else ""
    
    def _handle_multi_value(self, value_str: str, context: Dict[str, Any]) -> str:
        """处理多值数据"""
        try:
            separator = self.config.get('multi_value_separator', '@@@')
            values = [v.strip() for v in value_str.split(separator)]
            
            if not values:
                return value_str
            
            strategy = self.config.get('multi_value_strategy', 'first')
            
            if strategy == 'first':
                return values[0]
            elif strategy == 'last':
                return values[-1]
            elif strategy == 'longest':
                return max(values, key=len)
            elif strategy == 'shortest':
                return min(values, key=len)
            elif strategy == 'context_based' and context:
                # 基于上下文选择最合适的值
                return self._select_by_context(values, context)
            elif strategy == 'context_based':
                # 没有上下文时使用默认策略
                return values[0]
            else:
                return values[0]  # 默认返回第一个
                
        except Exception as e:
            self.logger.error(f"处理多值数据时发生错误: {e}")
            return value_str
    
    def _select_by_context(self, values: List[str], context: Dict[str, Any]) -> str:
        """基于上下文选择最合适的值"""
        try:
            # 根据行位置选择
            row = context.get('row', 0)
            
            # 如果是前几行，选择较短的值（通常是基本信息）
            if row <= 5:
                return min(values, key=len)
            # 如果是后面的行，选择较长的值（通常是详细描述）
            else:
                return max(values, key=len)
                
        except Exception as e:
            self.logger.error(f"基于上下文选择值时发生错误: {e}")
            return values[0] if values else ""
    
    def _extract_fill_in_blank(self, value_str: str) -> str:
        """提取填空格式"""
        try:
            import re
            
            pattern = self.config.get('fill_blank_pattern', '_____')
            
            # 查找填空模式：_____内容_____
            match = re.search(f'{re.escape(pattern)}(.+?){re.escape(pattern)}', value_str)
            
            if match:
                extracted_value = match.group(1).strip()
                
                # 保留后续的单位信息
                remaining = value_str.split(pattern)[-1].strip()
                
                if remaining:
                    return f"{extracted_value} {remaining}"
                else:
                    return extracted_value
            
            # 如果没有找到完整的填空模式，尝试提取填空前后的内容
            parts = value_str.split(pattern)
            if len(parts) > 1:
                # 取最长的非空部分
                non_empty_parts = [part.strip() for part in parts if part.strip()]
                if non_empty_parts:
                    return max(non_empty_parts, key=len)
            
            return value_str
            
        except Exception as e:
            self.logger.error(f"提取填空格式时发生错误: {e}")
            return value_str
    
    def _clean_and_format(self, value_str: str) -> str:
        """清理和格式化值"""
        try:
            import re
            
            # 移除多余的空白字符
            value_str = re.sub(r'\s+', ' ', value_str)
            
            # 移除特殊字符（可配置）
            remove_chars = self.config.get('remove_characters', [])
            for char in remove_chars:
                value_str = value_str.replace(char, '')
            
            # 格式化数字（如果是数字）
            if self.config.get('format_numbers', False):
                value_str = self._format_numbers(value_str)
            
            # 格式化日期（如果是日期）
            if self.config.get('format_dates', False):
                value_str = self._format_dates(value_str)
            
            return value_str
            
        except Exception as e:
            self.logger.error(f"清理和格式化值时发生错误: {e}")
            return value_str
    
    def _format_numbers(self, value_str: str) -> str:
        """格式化数字"""
        try:
            import re
            
            # 查找数字模式
            number_pattern = r'\d+\.?\d*'
            numbers = re.findall(number_pattern, value_str)
            
            for number in numbers:
                try:
                    # 尝试格式化为浮点数
                    if '.' in number:
                        formatted = f"{float(number):.2f}"
                    else:
                        formatted = f"{int(number):,}"
                    
                    value_str = value_str.replace(number, formatted, 1)
                except ValueError:
                    continue
            
            return value_str
            
        except Exception as e:
            self.logger.error(f"格式化数字时发生错误: {e}")
            return value_str
    
    def _format_dates(self, value_str: str) -> str:
        """格式化日期"""
        try:
            import re
            from datetime import datetime
            
            # 常见日期格式
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # 2023-12-31
                r'\d{4}/\d{2}/\d{2}',  # 2023/12/31
                r'\d{2}-\d{2}-\d{4}',  # 31-12-2023
                r'\d{2}/\d{2}/\d{4}',  # 31/12/2023
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, value_str)
                for match in matches:
                    try:
                        # 尝试解析日期
                        if '-' in match:
                            if match.startswith('20'):  # YYYY-MM-DD
                                date_obj = datetime.strptime(match, '%Y-%m-%d')
                            else:  # DD-MM-YYYY
                                date_obj = datetime.strptime(match, '%d-%m-%Y')
                        else:  # 使用 /
                            if match.startswith('20'):  # YYYY/MM/DD
                                date_obj = datetime.strptime(match, '%Y/%m/%d')
                            else:  # DD/MM/YYYY
                                date_obj = datetime.strptime(match, '%d/%m/%Y')
                        
                        # 格式化为标准格式
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                        value_str = value_str.replace(match, formatted_date, 1)
                        
                    except ValueError:
                        continue
            
            return value_str
            
        except Exception as e:
            self.logger.error(f"格式化日期时发生错误: {e}")
            return value_str
    
    def batch_process(self, values: List[Any], contexts: List[Dict[str, Any]] = None) -> List[str]:
        """批量处理值"""
        try:
            if contexts is None:
                contexts = [None] * len(values)
            
            results = []
            for i, value in enumerate(values):
                context = contexts[i] if i < len(contexts) else None
                processed_value = self.process(value, context)
                results.append(processed_value)
            
            return results
            
        except Exception as e:
            self.logger.error(f"批量处理值时发生错误: {e}")
            return [str(v) if v is not None else "" for v in values]
    
    def get_processor_info(self) -> Dict[str, Any]:
        """获取处理器信息"""
        return {
            "name": "ValueProcessor",
            "description": "值处理器，处理多值数据和填空格式",
            "config": {
                "multi_value_separator": self.config.get('multi_value_separator', '@@@'),
                "fill_blank_pattern": self.config.get('fill_blank_pattern', '_____'),
                "multi_value_strategy": self.config.get('multi_value_strategy', 'first'),
                "format_numbers": self.config.get('format_numbers', False),
                "format_dates": self.config.get('format_dates', False),
                "remove_characters": self.config.get('remove_characters', [])
            }
        }


class FormFillService:
    """表单填充服务"""
    
    def __init__(self, config: Dict[str, Any], matching_engine: MatchingEngine):
        self.config = config
        self.matching_engine = matching_engine
        self.value_processor = ValueProcessor(config.get('processing', {}))
        self.logger = logging.getLogger(f"{__name__}.FormFillService")
    
    def process_batch(self, file_path: str) -> str:
        """
        批量处理空单元格文件，返回输出文件路径
        
        Args:
            file_path: 输入JSON文件路径
            
        Returns:
            str: 输出文件路径
            
        Raises:
            FileNotFoundError: 输入文件不存在
            InvalidDataFormatError: 数据格式无效
        """
        try:
            start_time = time.time()
            stats = ProcessingStats()
            
            self.logger.info(f"开始批量处理: {file_path}")
            
            # 1. 验证输入文件
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"输入文件不存在: {file_path}")
            
            # 2. 加载输入数据
            input_data = self._load_input_data(file_path)
            
            # 3. 解析单元格数据
            cell_data_list = self._parse_cell_data(input_data)
            self.logger.info(f"解析到 {len(cell_data_list)} 个单元格")
            
            # 4. 批量填充处理
            filled_results = self._batch_fill_cells(cell_data_list, stats)
            
            # 5. 生成输出数据
            output_data = self._generate_output_data(input_data, filled_results)
            
            # 6. 保存输出文件
            output_path = self._generate_output_path(file_path)
            self._save_output_data(output_data, output_path)
            
            # 7. 统计信息
            stats.set_processing_time(start_time)
            stats.print_summary()
            
            self.logger.info(f"批量处理完成: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"批量处理失败: {e}")
            raise
    
    def query_by_keyword(self, keyword: str) -> str:
        """
        根据关键词查询并返回最佳匹配值
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 匹配的值，如果没有匹配则返回空字符串
        """
        try:
            self.logger.info(f"单查询处理: {keyword}")
            
            # 使用匹配引擎查找匹配
            result = self.matching_engine.find_match([keyword])
            
            if result:
                value, source, confidence = result
                self.logger.info(f"查询成功: {keyword} -> {value} (来源: {source}, 置信度: {confidence})")
                return str(value)
            else:
                self.logger.info(f"查询无结果: {keyword}")
                return ""
                
        except Exception as e:
            self.logger.error(f"单查询处理失败: {e}")
            return ""
    
    def _load_input_data(self, file_path: str) -> Dict[str, Any]:
        """加载输入数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证数据格式
            if not isinstance(data, (dict, list)):
                raise ValueError("输入数据必须是字典或列表格式")
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON格式错误: {e}")
        except Exception as e:
            raise ValueError(f"加载输入数据失败: {e}")
    
    def _parse_cell_data(self, input_data: Dict[str, Any]) -> List[CellData]:
        """解析单元格数据，返回所有记录（包括非空记录）"""
        cell_data_list = []
        
        try:
            # 处理不同的输入格式
            if isinstance(input_data, list):
                # 直接是CellData列表
                for item in input_data:
                    if isinstance(item, dict):
                        cell_data = CellData.from_dict(item)
                        if cell_data.validate():
                            cell_data_list.append(cell_data)
            
            elif isinstance(input_data, dict):
                # 检查是否包含cells字段
                if 'cells' in input_data:
                    for item in input_data['cells']:
                        cell_data = CellData.from_dict(item)
                        if cell_data.validate():
                            cell_data_list.append(cell_data)
                
                # 检查是否是旧格式（tables结构）
                elif 'tables' in input_data:
                    cell_data_list = self._parse_legacy_format(input_data)
                
                # 直接作为单个CellData处理
                else:
                    cell_data = CellData.from_dict(input_data)
                    if cell_data.validate():
                        cell_data_list.append(cell_data)
            
            return cell_data_list
            
        except Exception as e:
            self.logger.error(f"解析单元格数据失败: {e}")
            return []
    
    def _parse_legacy_format(self, input_data: Dict[str, Any]) -> List[CellData]:
        """解析旧格式数据（兼容现有的tables结构）"""
        cell_data_list = []
        
        try:
            for table in input_data.get('tables', []):
                for row in table.get('rows', []):
                    row_index = row.get('row_index', 0)
                    
                    for fill in row.get('fills', []):
                        if fill.get('filled_value') == 'NULL' or not fill.get('filled_value'):
                            # 构造CellData
                            cell_data = CellData(
                                row=row_index,
                                col=fill.get('cell_index', 0),
                                content="",
                                relationship=[fill.get('filled_key', '')]
                            )
                            cell_data_list.append(cell_data)
            
            return cell_data_list
            
        except Exception as e:
            self.logger.error(f"解析旧格式数据失败: {e}")
            return []
    
    def _batch_fill_cells(self, cell_data_list: List[CellData], stats: ProcessingStats) -> Dict[int, tuple]:
        """批量填充单元格，只处理空单元格"""
        results = {}
        
        for i, cell_data in enumerate(cell_data_list):
            try:
                # 只处理空单元格
                if not cell_data.is_empty():
                    self.logger.debug(f"跳过非空单元格 [{i}]: {cell_data.content}")
                    continue
                
                # 构建上下文
                context = {
                    'row': cell_data.row,
                    'col': cell_data.col
                }
                
                # 使用匹配引擎查找匹配
                result = self.matching_engine.find_match(cell_data.relationship, context)
                
                if result:
                    raw_value, source, confidence = result
                    
                    # 使用值处理器处理原始值
                    processed_value = self.value_processor.process(raw_value, context)
                    
                    results[i] = (processed_value, source, confidence)
                    stats.add_success()
                    
                    self.logger.debug(f"填充成功 [{i}]: {cell_data.relationship} -> {processed_value}")
                else:
                    stats.add_failure(f"无法匹配关键词: {cell_data.relationship}")
                    self.logger.debug(f"填充失败 [{i}]: {cell_data.relationship}")
                
            except Exception as e:
                error_msg = f"处理单元格 [{i}] 时发生错误: {e}"
                stats.add_failure(error_msg)
                self.logger.error(error_msg)
        
        return results
    
    def _generate_output_data(self, input_data: Dict[str, Any], filled_results: Dict[int, tuple]) -> Dict[str, Any]:
        """生成输出数据，保持与输入数据完全一致的结构"""
        try:
            # 深拷贝输入数据
            import copy
            output_data = copy.deepcopy(input_data)
            
            # 处理不同的数据格式
            if isinstance(output_data, list):
                # 直接是CellData列表
                for i, result in filled_results.items():
                    if i < len(output_data):
                        value, source, confidence = result
                        output_data[i]['content'] = value
                        output_data[i]['fill_source'] = source
                        output_data[i]['confidence'] = confidence
            
            elif isinstance(output_data, dict):
                if 'cells' in output_data:
                    # 包含cells字段
                    for i, result in filled_results.items():
                        if i < len(output_data['cells']):
                            value, source, confidence = result
                            output_data['cells'][i]['content'] = value
                            output_data['cells'][i]['fill_source'] = source
                            output_data['cells'][i]['confidence'] = confidence
                
                elif 'tables' in output_data:
                    # 旧格式处理
                    self._update_legacy_format(output_data, filled_results)
                
                else:
                    # 单个CellData
                    if 0 in filled_results:
                        value, source, confidence = filled_results[0]
                        output_data['content'] = value
                        output_data['fill_source'] = source
                        output_data['confidence'] = confidence
            
            return output_data
            
        except Exception as e:
            self.logger.error(f"生成输出数据失败: {e}")
            return input_data
    
    def _update_legacy_format(self, output_data: Dict[str, Any], filled_results: Dict[int, tuple]) -> None:
        """更新旧格式数据"""
        try:
            result_index = 0
            
            for table in output_data.get('tables', []):
                for row in table.get('rows', []):
                    for fill in row.get('fills', []):
                        if fill.get('filled_value') == 'NULL' or not fill.get('filled_value'):
                            if result_index in filled_results:
                                value, source, confidence = filled_results[result_index]
                                fill['filled_value'] = value
                                fill['fill_source'] = source
                                fill['confidence'] = confidence
                            result_index += 1
                            
        except Exception as e:
            self.logger.error(f"更新旧格式数据失败: {e}")
    
    def _generate_output_path(self, input_path: str) -> str:
        """生成输出文件路径 - 输出到processed目录"""
        try:
            path_obj = Path(input_path)
            suffix = self.config.get('data_source', {}).get('output_suffix', '_filled')
            
            # 生成输出文件名
            output_name = f"{path_obj.stem}{suffix}{path_obj.suffix}"
            
            # 输出到相对路径的processed目录
            processed_dir = Path("../../data/processed")
            processed_dir.mkdir(parents=True, exist_ok=True)
            output_path = processed_dir / output_name
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"生成输出路径失败: {e}")
            return f"{input_path}_filled.json"
    
    def _save_output_data(self, output_data: Dict[str, Any], output_path: str) -> None:
        """保存输出数据"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"输出数据已保存: {output_path}")
            
        except Exception as e:
            self.logger.error(f"保存输出数据失败: {e}")
            raise
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "name": "FormFillService",
            "description": "表单填充服务，提供批量处理和单查询功能",
            "matching_engine": self.matching_engine.get_engine_info(),
            "config": {
                "output_suffix": self.config.get('data_source', {}).get('output_suffix', '_filled'),
                "sample_data_path": self.config.get('data_source', {}).get('sample_data_path', '')
            }
        }


# 自定义异常类
class FormFillerException(Exception):
    """基础异常类"""
    pass


class FileNotFoundError(FormFillerException):
    """文件未找到异常"""
    pass


class InvalidDataFormatError(FormFillerException):
    """无效数据格式异常"""
    pass


class MatchingFailedException(FormFillerException):
    """匹配失败异常"""
    pass


class BatchFillAPI:
    """批量填充API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.BatchFillAPI")
        
        # 初始化核心组件
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """初始化核心组件"""
        try:
            # 初始化数据提供者
            sample_data_path = self.config.get('data_source', {}).get('sample_data_path', 'example_data.json')
            self.data_provider = FileDataProvider(sample_data_path)
            
            # 初始化匹配引擎
            self.matching_engine = MatchingEngine(self.config, self.data_provider)
            
            # 初始化表单填充服务
            self.form_fill_service = FormFillService(self.config, self.matching_engine)
            
            self.logger.info("批量填充API组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化组件失败: {e}")
            raise
    
    def batch_fill(self, file_path: str) -> str:
        """
        批量填充API
        
        Args:
            file_path: 包含空单元格数据的JSON文件路径
            
        Returns:
            str: 输出JSON文件的路径
            
        Raises:
            FileNotFoundError: 输入文件不存在
            InvalidDataFormatError: 数据格式无效
            MatchingFailedException: 匹配过程失败
            
        Note:
            - 样本数据从配置的默认目录加载，无需用户指定
            - 输出JSON格式与输入格式一致，仅填充content字段
            - 统计信息通过print输出到控制台
        """
        try:
            self.logger.info(f"开始批量填充API调用: {file_path}")
            
            # 输入验证
            self._validate_input(file_path)
            
            # 检查数据源可用性
            if not self.data_provider.is_available():
                raise FileNotFoundError(f"样本数据文件不可用: {self.data_provider.file_path}")
            
            # 调用表单填充服务
            output_path = self.form_fill_service.process_batch(file_path)
            
            self.logger.info(f"批量填充API调用完成: {output_path}")
            return output_path
            
        except FileNotFoundError as e:
            self.logger.error(f"文件未找到: {e}")
            raise
        except InvalidDataFormatError as e:
            self.logger.error(f"数据格式无效: {e}")
            raise
        except Exception as e:
            self.logger.error(f"批量填充API调用失败: {e}")
            raise MatchingFailedException(f"批量填充过程失败: {e}")
    
    def _validate_input(self, file_path: str) -> None:
        """验证输入参数"""
        if not file_path:
            raise InvalidDataFormatError("文件路径不能为空")
        
        if not isinstance(file_path, str):
            raise InvalidDataFormatError("文件路径必须是字符串")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"输入文件不存在: {file_path}")
        
        # 验证文件扩展名
        if not file_path.lower().endswith('.json'):
            raise InvalidDataFormatError("输入文件必须是JSON格式")
        
        # 验证文件可读性
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            raise InvalidDataFormatError(f"JSON格式错误: {e}")
        except Exception as e:
            raise InvalidDataFormatError(f"文件读取失败: {e}")
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            "name": "BatchFillAPI",
            "description": "批量填充API，处理包含空单元格数据的JSON文件",
            "version": "1.0.0",
            "methods": {
                "batch_fill": {
                    "description": "批量填充空单元格",
                    "parameters": {
                        "file_path": {
                            "type": "str",
                            "required": True,
                            "description": "输入JSON文件路径"
                        }
                    },
                    "returns": {
                        "type": "str",
                        "description": "输出JSON文件路径"
                    },
                    "exceptions": [
                        "FileNotFoundError",
                        "InvalidDataFormatError", 
                        "MatchingFailedException"
                    ]
                }
            },
            "config": {
                "sample_data_path": self.config.get('data_source', {}).get('sample_data_path', ''),
                "output_suffix": self.config.get('data_source', {}).get('output_suffix', '_filled')
            },
            "components": {
                "data_provider": self.data_provider.__class__.__name__,
                "matching_engine": self.matching_engine.get_engine_info(),
                "form_fill_service": self.form_fill_service.get_service_info()
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {}
            }
            
            # 检查数据提供者
            try:
                data_available = self.data_provider.is_available()
                sample_data = self.data_provider.get_sample_data()
                health_status["components"]["data_provider"] = {
                    "status": "healthy" if data_available else "unhealthy",
                    "available": data_available,
                    "sample_data_count": len(sample_data)
                }
            except Exception as e:
                health_status["components"]["data_provider"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查匹配引擎
            try:
                engine_stats = self.matching_engine.get_statistics()
                health_status["components"]["matching_engine"] = {
                    "status": "healthy",
                    "statistics": engine_stats
                }
            except Exception as e:
                health_status["components"]["matching_engine"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查表单填充服务
            try:
                service_info = self.form_fill_service.get_service_info()
                health_status["components"]["form_fill_service"] = {
                    "status": "healthy",
                    "info": service_info
                }
            except Exception as e:
                health_status["components"]["form_fill_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 判断整体状态
            component_statuses = [comp.get("status") for comp in health_status["components"].values()]
            if "unhealthy" in component_statuses:
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def clear_caches(self) -> Dict[str, Any]:
        """清除所有缓存"""
        try:
            # 清除匹配引擎缓存
            self.matching_engine.clear_caches()
            
            return {
                "status": "success",
                "message": "所有缓存已清除",
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"清除缓存失败: {e}",
                "timestamp": time.time()
            }


class SingleQueryAPI:
    """单查询API"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SingleQueryAPI")
        
        # 初始化核心组件
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """初始化核心组件"""
        try:
            # 初始化数据提供者
            sample_data_path = self.config.get('data_source', {}).get('sample_data_path', 'example_data.json')
            self.data_provider = FileDataProvider(sample_data_path)
            
            # 初始化匹配引擎
            self.matching_engine = MatchingEngine(self.config, self.data_provider)
            
            # 初始化表单填充服务
            self.form_fill_service = FormFillService(self.config, self.matching_engine)
            
            self.logger.info("单查询API组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化组件失败: {e}")
            raise
    
    def single_query(self, keyword: str) -> str:
        """
        单查询API
        
        Args:
            keyword: 搜索关键词，如"社会效益"、"总目标描述"
            
        Returns:
            str: 最合适的填充值
            
        Raises:
            InvalidDataFormatError: 输入参数无效
            MatchingFailedException: 查询过程失败
            
        Note:
            自动从配置的默认目录加载样本数据进行匹配
        """
        try:
            self.logger.info(f"开始单查询API调用: {keyword}")
            
            # 输入验证
            self._validate_keyword(keyword)
            
            # 检查数据源可用性
            if not self.data_provider.is_available():
                raise FileNotFoundError(f"样本数据文件不可用: {self.data_provider.file_path}")
            
            # 调用表单填充服务进行查询
            result = self.form_fill_service.query_by_keyword(keyword)
            
            self.logger.info(f"单查询API调用完成: {keyword} -> {result}")
            return result
            
        except InvalidDataFormatError as e:
            self.logger.error(f"输入参数无效: {e}")
            raise
        except Exception as e:
            self.logger.error(f"单查询API调用失败: {e}")
            raise MatchingFailedException(f"单查询过程失败: {e}")
    
    def _validate_keyword(self, keyword: str) -> None:
        """验证关键词参数"""
        if not keyword:
            raise InvalidDataFormatError("关键词不能为空")
        
        if not isinstance(keyword, str):
            raise InvalidDataFormatError("关键词必须是字符串")
        
        # 检查关键词长度
        if len(keyword.strip()) == 0:
            raise InvalidDataFormatError("关键词不能只包含空白字符")
        
        # 检查关键词长度限制
        max_length = self.config.get('validation', {}).get('max_keyword_length', 100)
        if len(keyword) > max_length:
            raise InvalidDataFormatError(f"关键词长度不能超过 {max_length} 个字符")
    
    def batch_query(self, keywords: List[str]) -> Dict[str, str]:
        """
        批量查询API
        
        Args:
            keywords: 关键词列表
            
        Returns:
            Dict[str, str]: 关键词到匹配值的映射
            
        Raises:
            InvalidDataFormatError: 输入参数无效
            MatchingFailedException: 查询过程失败
        """
        try:
            self.logger.info(f"开始批量查询API调用: {len(keywords)} 个关键词")
            
            # 输入验证
            self._validate_keywords_list(keywords)
            
            # 检查数据源可用性
            if not self.data_provider.is_available():
                raise FileNotFoundError(f"样本数据文件不可用: {self.data_provider.file_path}")
            
            # 批量查询
            results = {}
            for keyword in keywords:
                try:
                    result = self.form_fill_service.query_by_keyword(keyword)
                    results[keyword] = result
                except Exception as e:
                    self.logger.warning(f"查询关键词 '{keyword}' 失败: {e}")
                    results[keyword] = ""
            
            self.logger.info(f"批量查询API调用完成: {len(results)} 个结果")
            return results
            
        except InvalidDataFormatError as e:
            self.logger.error(f"输入参数无效: {e}")
            raise
        except Exception as e:
            self.logger.error(f"批量查询API调用失败: {e}")
            raise MatchingFailedException(f"批量查询过程失败: {e}")
    
    def _validate_keywords_list(self, keywords: List[str]) -> None:
        """验证关键词列表"""
        if not keywords:
            raise InvalidDataFormatError("关键词列表不能为空")
        
        if not isinstance(keywords, list):
            raise InvalidDataFormatError("关键词必须是列表格式")
        
        # 检查列表长度限制
        max_batch_size = self.config.get('validation', {}).get('max_batch_size', 50)
        if len(keywords) > max_batch_size:
            raise InvalidDataFormatError(f"批量查询关键词数量不能超过 {max_batch_size} 个")
        
        # 验证每个关键词
        for i, keyword in enumerate(keywords):
            try:
                self._validate_keyword(keyword)
            except InvalidDataFormatError as e:
                raise InvalidDataFormatError(f"第 {i+1} 个关键词无效: {e}")
    
    def search_related_fields(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索相关字段
        
        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            List[Dict[str, Any]]: 相关字段信息列表
        """
        try:
            self.logger.info(f"搜索相关字段: {keyword}")
            
            # 输入验证
            self._validate_keyword(keyword)
            
            if limit <= 0 or limit > 100:
                raise InvalidDataFormatError("结果数量限制必须在 1-100 之间")
            
            # 获取样本数据
            sample_data = self.data_provider.get_sample_data()
            
            if not sample_data:
                return []
            
            # 搜索相关字段
            related_fields = []
            
            # 精确匹配
            if keyword in sample_data:
                related_fields.append({
                    "field": keyword,
                    "value": sample_data[keyword],
                    "match_type": "exact",
                    "confidence": 1.0
                })
            
            # 模糊匹配
            from difflib import SequenceMatcher
            
            for field, value in sample_data.items():
                if field == keyword:  # 跳过已经精确匹配的
                    continue
                
                # 计算相似度
                similarity = SequenceMatcher(None, keyword.lower(), field.lower()).ratio()
                
                if similarity >= 0.3:  # 相似度阈值
                    related_fields.append({
                        "field": field,
                        "value": value,
                        "match_type": "fuzzy",
                        "confidence": similarity
                    })
            
            # 按置信度排序并限制数量
            related_fields.sort(key=lambda x: x["confidence"], reverse=True)
            return related_fields[:limit]
            
        except Exception as e:
            self.logger.error(f"搜索相关字段失败: {e}")
            return []
    
    def get_api_info(self) -> Dict[str, Any]:
        """获取API信息"""
        return {
            "name": "SingleQueryAPI",
            "description": "单查询API，根据关键词查询匹配值",
            "version": "1.0.0",
            "methods": {
                "single_query": {
                    "description": "单个关键词查询",
                    "parameters": {
                        "keyword": {
                            "type": "str",
                            "required": True,
                            "description": "搜索关键词"
                        }
                    },
                    "returns": {
                        "type": "str",
                        "description": "匹配的值"
                    },
                    "exceptions": [
                        "InvalidDataFormatError",
                        "MatchingFailedException"
                    ]
                },
                "batch_query": {
                    "description": "批量关键词查询",
                    "parameters": {
                        "keywords": {
                            "type": "List[str]",
                            "required": True,
                            "description": "关键词列表"
                        }
                    },
                    "returns": {
                        "type": "Dict[str, str]",
                        "description": "关键词到匹配值的映射"
                    }
                },
                "search_related_fields": {
                    "description": "搜索相关字段",
                    "parameters": {
                        "keyword": {
                            "type": "str",
                            "required": True,
                            "description": "搜索关键词"
                        },
                        "limit": {
                            "type": "int",
                            "required": False,
                            "default": 10,
                            "description": "返回结果数量限制"
                        }
                    },
                    "returns": {
                        "type": "List[Dict[str, Any]]",
                        "description": "相关字段信息列表"
                    }
                }
            },
            "config": {
                "sample_data_path": self.config.get('data_source', {}).get('sample_data_path', ''),
                "max_keyword_length": self.config.get('validation', {}).get('max_keyword_length', 100),
                "max_batch_size": self.config.get('validation', {}).get('max_batch_size', 50)
            },
            "components": {
                "data_provider": self.data_provider.__class__.__name__,
                "matching_engine": self.matching_engine.get_engine_info(),
                "form_fill_service": self.form_fill_service.get_service_info()
            }
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": time.time(),
                "components": {}
            }
            
            # 检查数据提供者
            try:
                data_available = self.data_provider.is_available()
                sample_data = self.data_provider.get_sample_data()
                health_status["components"]["data_provider"] = {
                    "status": "healthy" if data_available else "unhealthy",
                    "available": data_available,
                    "sample_data_count": len(sample_data)
                }
            except Exception as e:
                health_status["components"]["data_provider"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查匹配引擎
            try:
                engine_stats = self.matching_engine.get_statistics()
                health_status["components"]["matching_engine"] = {
                    "status": "healthy",
                    "statistics": engine_stats
                }
            except Exception as e:
                health_status["components"]["matching_engine"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 检查表单填充服务
            try:
                service_info = self.form_fill_service.get_service_info()
                health_status["components"]["form_fill_service"] = {
                    "status": "healthy",
                    "info": service_info
                }
            except Exception as e:
                health_status["components"]["form_fill_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
            
            # 判断整体状态
            component_statuses = [comp.get("status") for comp in health_status["components"].values()]
            if "unhealthy" in component_statuses:
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }


class CLIInterface:
    """命令行接口"""
    
    def __init__(self):
        self.config = ConfigManager()
        setup_logging(self.config)
        self.logger = logging.getLogger(f"{__name__}.CLIInterface")
        
        # 初始化API实例
        self.batch_api = BatchFillAPI(self.config._config)
        self.single_query_api = SingleQueryAPI(self.config._config)
    
    def run(self, args: List[str] = None) -> None:
        """运行CLI接口"""
        try:
            import argparse
            
            parser = self._create_argument_parser()
            parsed_args = parser.parse_args(args)
            
            # 根据命令执行相应操作
            if parsed_args.command == 'batch':
                self._handle_batch_command(parsed_args)
            elif parsed_args.command == 'query':
                self._handle_query_command(parsed_args)
            elif parsed_args.command == 'interactive':
                self._handle_interactive_command()
            else:
                # 默认进入交互模式
                self._handle_interactive_command()
                
        except KeyboardInterrupt:
            print("\n操作已取消")
        except Exception as e:
            self.logger.error(f"CLI执行失败: {e}")
            print(f"错误: {e}")
    
    def _create_argument_parser(self) -> 'argparse.ArgumentParser':
        """创建命令行参数解析器"""
        import argparse
        
        parser = argparse.ArgumentParser(
            description="智能表单填充工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
 使用示例:
  # 批量填充模式
  python intelligent_form_filler_api.py batch --input empty_cells.json
  
  # 单查询模式
  python intelligent_form_filler_api.py query --keyword "社会效益"
  
  # 交互模式
  python intelligent_form_filler_api.py interactive
  python intelligent_form_filler_api.py  # 默认进入交互模式
            """
        )
        
        # 添加子命令
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # 批量填充命令
        batch_parser = subparsers.add_parser('batch', help='批量填充模式')
        batch_parser.add_argument(
            '--input', '-i',
            required=True,
            help='输入JSON文件路径'
        )
        batch_parser.add_argument(
            '--output', '-o',
            help='输出文件路径（可选，默认自动生成）'
        )
        batch_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='显示详细输出'
        )
        
        # 单查询命令
        query_parser = subparsers.add_parser('query', help='单查询模式')
        query_parser.add_argument(
            '--keyword', '-k',
            required=True,
            help='搜索关键词'
        )
        query_parser.add_argument(
            '--related', '-r',
            action='store_true',
            help='显示相关字段'
        )
        query_parser.add_argument(
            '--limit', '-l',
            type=int,
            default=10,
            help='相关字段数量限制（默认10）'
        )
        
        # 交互模式命令
        interactive_parser = subparsers.add_parser('interactive', help='交互模式')
        
        # 全局选项
        parser.add_argument(
            '--config', '-c',
            help='配置文件路径（默认: config.json）'
        )
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            default='INFO',
            help='日志级别'
        )
        
        return parser
    
    def _handle_batch_command(self, args) -> None:
        """处理批量填充命令"""
        try:
            print(f"开始批量填充: {args.input}")
            
            # 设置详细输出
            if args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
            
            # 执行批量填充
            output_path = self.batch_api.batch_fill(args.input)
            
            # 如果指定了输出路径，移动文件
            if args.output and args.output != output_path:
                import shutil
                shutil.move(output_path, args.output)
                output_path = args.output
            
            print(f"批量填充完成!")
            print(f"输出文件: {output_path}")
            
            # 显示简要统计
            self._show_batch_summary(output_path)
            
        except Exception as e:
            print(f"批量填充失败: {e}")
            self.logger.error(f"批量填充命令执行失败: {e}")
    
    def _handle_query_command(self, args) -> None:
        """处理单查询命令"""
        try:
            print(f"查询关键词: {args.keyword}")
            
            # 执行单查询
            result = self.single_query_api.single_query(args.keyword)
            
            if result:
                print(f"匹配结果: {result}")
            else:
                print("未找到匹配结果")
            
            # 显示相关字段
            if args.related:
                print("\n相关字段:")
                related_fields = self.single_query_api.search_related_fields(
                    args.keyword, 
                    args.limit
                )
                
                if related_fields:
                    for i, field_info in enumerate(related_fields, 1):
                        print(f"  {i}. {field_info['field']}: {field_info['value']}")
                        print(f"     匹配类型: {field_info['match_type']}, 置信度: {field_info['confidence']:.2f}")
                else:
                    print("  未找到相关字段")
            
        except Exception as e:
            print(f"查询失败: {e}")
            self.logger.error(f"查询命令执行失败: {e}")
    
    def _handle_interactive_command(self) -> None:
        """处理交互模式命令"""
        try:
            self._run_interactive_mode()
        except Exception as e:
            print(f"交互模式失败: {e}")
            self.logger.error(f"交互模式执行失败: {e}")
    
    def _run_interactive_mode(self) -> None:
        """运行交互模式"""
        print("=" * 50)
        print("智能表单填充工具")
        print("=" * 50)
        
        while True:
            try:
                print("\n请选择操作模式:")
                print("1. 批量填充")
                print("2. 单字段查询")
                print("3. 批量查询")
                print("4. 健康检查")
                print("5. 系统信息")
                print("0. 退出")
                
                choice = input("\n请输入选择 (0-5): ").strip()
                
                if choice == '0':
                    print("感谢使用，再见!")
                    break
                elif choice == '1':
                    self._interactive_batch_fill()
                elif choice == '2':
                    self._interactive_single_query()
                elif choice == '3':
                    self._interactive_batch_query()
                elif choice == '4':
                    self._interactive_health_check()
                elif choice == '5':
                    self._interactive_system_info()
                else:
                    print("无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n\n操作已取消")
                break
            except Exception as e:
                print(f"操作失败: {e}")
                self.logger.error(f"交互模式操作失败: {e}")
    
    def _interactive_batch_fill(self) -> None:
        """交互式批量填充"""
        print("\n=== 批量填充模式 ===")
        
        file_path = input("请输入JSON文件路径: ").strip()
        if not file_path:
            print("文件路径不能为空")
            return
        
        try:
            print("正在处理...")
            output_path = self.batch_api.batch_fill(file_path)
            print(f"批量填充完成!")
            print(f"输出文件: {output_path}")
            
            # 显示简要统计
            self._show_batch_summary(output_path)
            
        except Exception as e:
            print(f"批量填充失败: {e}")
    
    def _interactive_single_query(self) -> None:
        """交互式单查询"""
        print("\n=== 单字段查询模式 ===")
        
        keyword = input("请输入查询关键词: ").strip()
        if not keyword:
            print("关键词不能为空")
            return
        
        try:
            result = self.single_query_api.single_query(keyword)
            
            if result:
                print(f"匹配结果: {result}")
            else:
                print("未找到匹配结果")
            
            # 询问是否显示相关字段
            show_related = input("是否显示相关字段? (y/n): ").strip().lower()
            if show_related in ['y', 'yes', '是']:
                related_fields = self.single_query_api.search_related_fields(keyword, 10)
                
                if related_fields:
                    print("\n相关字段:")
                    for i, field_info in enumerate(related_fields, 1):
                        print(f"  {i}. {field_info['field']}: {field_info['value']}")
                        print(f"     匹配类型: {field_info['match_type']}, 置信度: {field_info['confidence']:.2f}")
                else:
                    print("未找到相关字段")
            
        except Exception as e:
            print(f"查询失败: {e}")
    
    def _interactive_batch_query(self) -> None:
        """交互式批量查询"""
        print("\n=== 批量查询模式 ===")
        print("请输入多个关键词，每行一个，输入空行结束:")
        
        keywords = []
        while True:
            keyword = input().strip()
            if not keyword:
                break
            keywords.append(keyword)
        
        if not keywords:
            print("未输入任何关键词")
            return
        
        try:
            print(f"正在查询 {len(keywords)} 个关键词...")
            results = self.single_query_api.batch_query(keywords)
            
            print("\n查询结果:")
            for keyword, result in results.items():
                if result:
                    print(f"  {keyword}: {result}")
                else:
                    print(f"  {keyword}: 未找到匹配")
            
        except Exception as e:
            print(f"批量查询失败: {e}")
    
    def _interactive_health_check(self) -> None:
        """交互式健康检查"""
        print("\n=== 系统健康检查 ===")
        
        try:
            # 检查批量API
            batch_health = self.batch_api.health_check()
            print(f"批量填充API: {batch_health['status']}")
            
            # 检查单查询API
            query_health = self.single_query_api.health_check()
            print(f"单查询API: {query_health['status']}")
            
            # 显示组件状态
            print("\n组件状态:")
            for component, status in batch_health.get('components', {}).items():
                print(f"  {component}: {status.get('status', 'unknown')}")
            
        except Exception as e:
            print(f"健康检查失败: {e}")
    
    def _interactive_system_info(self) -> None:
        """交互式系统信息"""
        print("\n=== 系统信息 ===")
        
        try:
            # 批量API信息
            batch_info = self.batch_api.get_api_info()
            print(f"批量填充API: {batch_info['name']} v{batch_info['version']}")
            
            # 单查询API信息
            query_info = self.single_query_api.get_api_info()
            print(f"单查询API: {query_info['name']} v{query_info['version']}")
            
            # 配置信息
            print(f"\n配置信息:")
            print(f"  样本数据路径: {self.config.get_sample_data_path()}")
            print(f"  输出文件后缀: {self.config.get_output_suffix()}")
            
        except Exception as e:
            print(f"获取系统信息失败: {e}")
    
    def _show_batch_summary(self, output_path: str) -> None:
        """显示批量处理摘要"""
        try:
            import json
            
            # 读取输出文件获取统计信息
            with open(output_path, 'r', encoding='utf-8') as f:
                output_data = json.load(f)
            
            if isinstance(output_data, list):
                total_count = len(output_data)
                filled_count = sum(1 for item in output_data if item.get('content'))
            else:
                # 简化统计
                total_count = 1
                filled_count = 1 if output_data.get('content') else 0
            
            print(f"\n处理摘要:")
            print(f"  总记录数: {total_count}")
            print(f"  填充记录数: {filled_count}")
            print(f"  填充率: {filled_count/total_count*100:.1f}%" if total_count > 0 else "  填充率: 0%")
            
        except Exception as e:
            self.logger.debug(f"显示摘要失败: {e}")


def main():
    """主函数"""
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()