"""
路径配置模块
集中管理所有文件路径配置，确保项目的可移植性
"""

import os
from pathlib import Path
from typing import Union


class PathConfig:
    """路径配置类，提供统一的路径管理"""
    
    @staticmethod
    def get_project_root() -> Path:
        """
        获取项目根目录
        从当前文件位置向上查找到项目根目录
        """
        current_file = Path(__file__)
        # 从 src/backend/config/paths.py 向上三级到达项目根目录
        # src/backend/config/paths.py -> src/backend/config -> src/backend -> src -> 项目根目录
        return current_file.parent.parent.parent.parent
    
    @staticmethod
    def get_data_dir() -> Path:
        """获取数据目录"""
        data_dir = PathConfig.get_project_root() / "data"
        PathConfig._ensure_directory_exists(data_dir)
        return data_dir
    
    @staticmethod
    def get_input_dir() -> Path:
        """获取输入数据目录"""
        input_dir = PathConfig.get_data_dir() / "input"
        PathConfig._ensure_directory_exists(input_dir)
        return input_dir
    
    @staticmethod
    def get_output_dir() -> Path:
        """获取输出数据目录"""
        output_dir = PathConfig.get_data_dir() / "output"
        PathConfig._ensure_directory_exists(output_dir)
        return output_dir
    
    @staticmethod
    def get_processed_dir() -> Path:
        """获取处理后数据目录（缓存和日志）"""
        processed_dir = PathConfig.get_data_dir() / "processed"
        PathConfig._ensure_directory_exists(processed_dir)
        return processed_dir
    
    # 输入文件路径
    @staticmethod
    def get_law_json_file() -> Path:
        """获取法律法规JSON输入文件路径"""
        return PathConfig.get_input_dir() / "EHS适用法律法规及其他要求清单-分类版.json"
    
    # 输出文件路径
    @staticmethod
    def get_not_found_laws_file() -> Path:
        """获取未找到法规输出文件路径"""
        return PathConfig.get_output_dir() / "not_found_laws.json"
    
    @staticmethod
    def get_validation_results_file(timestamp: str) -> Path:
        """获取验证结果JSON文件路径"""
        return PathConfig.get_output_dir() / f"law_validation_results_{timestamp}.json"
    
    @staticmethod
    def get_validation_report_file(timestamp: str) -> Path:
        """获取验证报告文本文件路径"""
        return PathConfig.get_output_dir() / f"law_validation_report_{timestamp}.txt"
    
    @staticmethod
    def get_validation_html_file(timestamp: str) -> Path:
        """获取验证报告HTML文件路径"""
        return PathConfig.get_output_dir() / f"law_validation_report_{timestamp}.html"
    
    # 缓存文件路径
    @staticmethod
    def get_law_cache_file() -> Path:
        """获取法律缓存文件路径"""
        return PathConfig.get_processed_dir() / "law_cache.json"
    
    # 日志文件路径
    @staticmethod
    def get_validation_log_file() -> Path:
        """获取验证器日志文件路径"""
        return PathConfig.get_processed_dir() / "law_validation.log"
    
    @staticmethod
    def get_crawler_log_file() -> Path:
        """获取爬虫日志文件路径"""
        return PathConfig.get_processed_dir() / "law_crawler.log"
    
    @staticmethod
    def _ensure_directory_exists(directory: Union[str, Path]) -> None:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            directory: 目录路径
        """
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def initialize_project_structure(verbose: bool = False) -> None:
        """
        初始化项目目录结构
        创建所有必要的目录
        """
        # 创建主要目录
        PathConfig.get_data_dir()
        PathConfig.get_input_dir()
        PathConfig.get_output_dir()
        PathConfig.get_processed_dir()
        
        if verbose:
            print("项目目录结构初始化完成:")
            print(f"- 数据目录: {PathConfig.get_data_dir()}")
            print(f"- 输入目录: {PathConfig.get_input_dir()}")
            print(f"- 输出目录: {PathConfig.get_output_dir()}")
            print(f"- 处理目录: {PathConfig.get_processed_dir()}")


if __name__ == "__main__":
    # 测试路径配置
    print("路径配置测试:")
    print(f"项目根目录: {PathConfig.get_project_root()}")
    print(f"数据目录: {PathConfig.get_data_dir()}")
    print(f"输入目录: {PathConfig.get_input_dir()}")
    print(f"输出目录: {PathConfig.get_output_dir()}")
    print(f"处理目录: {PathConfig.get_processed_dir()}")
    print(f"法律JSON文件: {PathConfig.get_law_json_file()}")
    print(f"缓存文件: {PathConfig.get_law_cache_file()}")
    
    # 初始化项目结构
    PathConfig.initialize_project_structure(verbose=True)