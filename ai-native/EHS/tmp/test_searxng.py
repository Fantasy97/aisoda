#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SearXNG搜索测试脚本
测试SearXNG搜索引擎的连接和搜索功能
"""

import requests
import json
from urllib.parse import urlencode


def get_available_engines(base_url="http://192.168.61.29:5004"):
    """
    获取SearXNG可用的搜索引擎列表
    
    Args:
        base_url: SearXNG服务器地址
    
    Returns:
        list: 可用的搜索引擎列表
    """
    try:
        # 尝试获取配置信息
        config_url = f"{base_url}/config"
        response = requests.get(config_url, timeout=10)
        if response.status_code == 200:
            config = response.json()
            engines = config.get('engines', [])
            print(f"找到 {len(engines)} 个搜索引擎")
            return engines
    except Exception as e:
        print(f"无法获取引擎列表: {e}")
    return []


def test_searxng_search(query, base_url="http://192.168.61.29:5004", engines="duckduckgo"):
    """
    测试SearXNG搜索功能
    
    Args:
        query: 搜索关键词
        base_url: SearXNG服务器地址
        engines: 使用的搜索引擎（可以用逗号分隔多个引擎）
    
    Returns:
        dict: 搜索结果
    """
    # 构建搜索URL
    search_url = f"{base_url}/search"
    
    # 设置查询参数
    params = {
        'q': query,
        'format': 'json',
        'engines': engines
    }
    
    print(f"正在测试SearXNG搜索...")
    print(f"URL: {search_url}")
    print(f"查询参数: {params}")
    print("-" * 60)
    
    try:
        # 发送GET请求
        response = requests.get(search_url, params=params, timeout=30)
        
        # 检查响应状态
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print("-" * 60)
        
        if response.status_code == 200:
            # 解析JSON响应
            result = response.json()
            
            print(f"搜索成功!")
            print(f"查询词: {result.get('query', 'N/A')}")
            print(f"结果数量: {len(result.get('results', []))}")
            print(f"搜索引擎: {result.get('engines', 'N/A')}")
            print("-" * 60)
            
            # 检查无响应的引擎
            unresponsive = result.get('unresponsive_engines', [])
            if unresponsive:
                print(f"\n⚠️  无响应的引擎:")
                for engine_info in unresponsive:
                    if isinstance(engine_info, list) and len(engine_info) >= 2:
                        print(f"   - {engine_info[0]}: {engine_info[1]}")
                    else:
                        print(f"   - {engine_info}")
            
            # 显示前5条搜索结果
            results = result.get('results', [])
            if results:
                print(f"\n前 {min(5, len(results))} 条搜索结果:")
                for i, item in enumerate(results[:5], 1):
                    print(f"\n{i}. 标题: {item.get('title', 'N/A')}")
                    print(f"   URL: {item.get('url', 'N/A')}")
                    print(f"   内容: {item.get('content', 'N/A')[:100]}...")
                    if 'engine' in item:
                        print(f"   来源: {item.get('engine', 'N/A')}")
            else:
                print("\n❌ 未找到搜索结果")
                if unresponsive:
                    print("   提示: 尝试使用其他搜索引擎")
            
            # 保存完整结果到文件
            output_file = "searxng_test_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n完整结果已保存到: {output_file}")
            
            return result
        else:
            print(f"搜索失败! 状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("错误: 请求超时")
        return None
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到SearXNG服务器")
        return None
    except requests.exceptions.RequestException as e:
        print(f"错误: 请求异常 - {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}")
        print(f"响应内容: {response.text[:500]}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None


def test_multiple_queries():
    """测试多个搜索查询"""
    test_queries = [
        "人工智能 教程",
        "Python programming",
        "环境健康安全 EHS"
    ]
    
    print("=" * 60)
    print("开始批量测试SearXNG搜索")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n\n测试 {i}/{len(test_queries)}: {query}")
        print("=" * 60)
        result = test_searxng_search(query)
        if result:
            print(f"✓ 测试成功")
        else:
            print(f"✗ 测试失败")


def test_multiple_engines():
    """测试多个搜索引擎"""
    base_url = "http://192.168.61.29:5004"
    query = "人工智能 教程"
    
    # 常用的搜索引擎列表
    engines_to_test = [
        "google",
        "bing",
        "brave",
        "qwant",
        "startpage",
        "yahoo",
        "wikipedia",
        "google,bing",  # 组合多个引擎
        "brave,qwant",
    ]
    
    print("\n" + "=" * 60)
    print("测试多个搜索引擎")
    print("=" * 60)
    
    successful_engines = []
    
    for engine in engines_to_test:
        print(f"\n\n🔍 测试引擎: {engine}")
        print("-" * 60)
        result = test_searxng_search(query, base_url, engine)
        
        if result and len(result.get('results', [])) > 0:
            successful_engines.append(engine)
            print(f"✅ 成功: 找到 {len(result.get('results', []))} 条结果")
            break  # 找到可用的引擎就停止
        else:
            print(f"❌ 失败: 无结果")
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    if successful_engines:
        print(f"✅ 可用的引擎: {', '.join(successful_engines)}")
    else:
        print("❌ 所有测试的引擎都无法返回结果")
        print("\n建议:")
        print("1. 检查SearXNG配置，确保引擎已启用")
        print("2. 尝试不指定引擎，让SearXNG自动选择")
        print("3. 检查网络连接和代理设置")


if __name__ == "__main__":
    # 测试单个查询 (与curl命令相同的查询)
    print("=" * 60)
    print("SearXNG 搜索测试脚本")
    print("=" * 60)
    
    base_url = "http://192.168.61.29:5004"
    
    # 首先尝试不指定引擎（让SearXNG自动选择）
    print("\n\n测试1: 不指定引擎（自动选择）")
    print("=" * 60)
    result = test_searxng_search(
        query="人工智能 教程",
        base_url=base_url,
        engines=""  # 空字符串表示不指定引擎
    )
    
    # 如果自动选择失败，测试多个引擎
    if not result or len(result.get('results', [])) == 0:
        print("\n\n自动选择失败，开始测试其他引擎...")
        test_multiple_engines()
    
    # 可选: 测试多个查询
    # test_multiple_queries()
