#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 /api/score-case 接口
根据工单号从数据库读取数据并进行评分
"""

import requests
import json
from typing import Dict, Any


# API 基础URL
# BASE_URL = "https://ai-uat.aiswei-tech.com/qis"
BASE_URL = "http://localhost:5009"


def test_score_case(case_number: str) -> Dict[str, Any]:
    """
    测试评分接口
    
    Args:
        case_number: 工单号
        
    Returns:
        响应结果
    """
    url = f"{BASE_URL}/api/score-case"
    payload = {
        "case_number": case_number
    }
    
    print(f"\n{'='*80}")
    print(f"测试工单评分接口")
    print(f"{'='*80}")
    print(f"URL: {url}")
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    print(f"{'-'*80}")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"状态码: {response.status_code}")
        print(f"{'-'*80}")
        
        # 解析响应
        try:
            result = response.json()
            print(f"响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 检查响应结构
            if result.get("success"):
                print(f"\n✓ 测试成功")
                if "case_info" in result:
                    print(f"  - 原始工单信息已返回")
                if "result" in result:
                    scoring_result = result["result"]
                    print(f"  - 评分结果:")
                    print(f"    工单-流程: {scoring_result.get('工单-流程', 'N/A')}")
                    print(f"    工单-基本信息: {scoring_result.get('工单-基本信息', 'N/A')}")
                    print(f"    工单-问题记录: {scoring_result.get('工单-问题记录', 'N/A')}")
                    print(f"    工单-发货明细: {scoring_result.get('工单-发货明细', 'N/A')}")
            else:
                print(f"\n✗ 测试失败: {result.get('error', '未知错误')}")
            
            return result
            
        except json.JSONDecodeError:
            print(f"响应不是有效的JSON格式")
            print(f"响应内容: {response.text}")
            return {"success": False, "error": "响应不是有效的JSON格式"}
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ 连接失败: 无法连接到服务器 {BASE_URL}")
        print(f"  请确保服务已启动")
        return {"success": False, "error": "连接失败"}
    except requests.exceptions.Timeout:
        print(f"\n✗ 请求超时")
        return {"success": False, "error": "请求超时"}
    except Exception as e:
        print(f"\n✗ 请求异常: {str(e)}")
        return {"success": False, "error": str(e)}


def test_empty_case_number():
    """测试空工单号的情况"""
    print(f"\n{'='*80}")
    print(f"测试: 空工单号")
    print(f"{'='*80}")
    
    url = f"{BASE_URL}/api/score-case"
    payload = {
        "case_number": ""
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 400 and not result.get("success"):
            print(f"\n✓ 测试通过: 正确返回400错误")
        else:
            print(f"\n✗ 测试失败: 应该返回400错误")
            
    except Exception as e:
        print(f"\n✗ 测试异常: {str(e)}")


def test_missing_case_number():
    """测试缺少工单号参数的情况"""
    print(f"\n{'='*80}")
    print(f"测试: 缺少工单号参数")
    print(f"{'='*80}")
    
    url = f"{BASE_URL}/api/score-case"
    payload = {}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 400 and not result.get("success"):
            print(f"\n✓ 测试通过: 正确返回400错误")
        else:
            print(f"\n✗ 测试失败: 应该返回400错误")
            
    except Exception as e:
        print(f"\n✗ 测试异常: {str(e)}")


def test_nonexistent_case_number():
    """测试不存在的工单号"""
    print(f"\n{'='*80}")
    print(f"测试: 不存在的工单号")
    print(f"{'='*80}")
    
    url = f"{BASE_URL}/api/score-case"
    payload = {
        "case_number": "CN9999999999999"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 404 and not result.get("success"):
            print(f"\n✓ 测试通过: 正确返回404错误")
        else:
            print(f"\n✗ 测试失败: 应该返回404错误")
            
    except Exception as e:
        print(f"\n✗ 测试异常: {str(e)}")


def main():
    """主测试函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║           工单评分接口测试脚本                                 ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # 测试用例1: 正常情况（需要替换为实际存在的工单号）
    print("\n【测试用例1】正常情况 - 有效工单号")
    test_case_number = "CN20251221606002"  # 请替换为实际存在的工单号
    print(f"提示: 请将 test_case_number 替换为数据库中实际存在的工单号")
    result = test_score_case(test_case_number)
    
    # # 测试用例2: 空工单号
    # print("\n【测试用例2】错误情况 - 空工单号")
    # test_empty_case_number()
    
    # # 测试用例3: 缺少工单号参数
    # print("\n【测试用例3】错误情况 - 缺少工单号参数")
    # test_missing_case_number()
    
    # # 测试用例4: 不存在的工单号
    # print("\n【测试用例4】错误情况 - 不存在的工单号")
    # test_nonexistent_case_number()
    
    print(f"\n{'='*80}")
    print("测试完成!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # 可以在这里直接指定要测试的工单号
    import sys
    
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，直接测试该工单号
        case_number = sys.argv[1]
        print(f"测试指定工单号: {case_number}")
        test_score_case(case_number)
    else:
        # 否则运行所有测试用例
        main()
