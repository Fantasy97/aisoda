import requests
import json
import re

def extract_implementation_date(text):
    """使用正则表达式提取施行日期"""
    # 优先匹配 **YYYY年MM月DD日** 格式的日期（加粗）
    pattern_bold = r'\*\*(\d{4}年\d{1,2}月\d{1,2}日)\*\*'
    match = re.search(pattern_bold, text)
    if match:
        return match.group(1)
    
    # 匹配普通的 YYYY年MM月DD日 格式（无加粗）
    pattern_normal = r'(\d{4}年\d{1,2}月\d{1,2}日)'
    match = re.search(pattern_normal, text)
    if match:
        return match.group(1)
    
    # 匹配不完整的日期格式 YYYY年MM月（缺少日）
    pattern_partial = r'(\d{4}年\d{1,2}月)'
    match = re.search(pattern_partial, text)
    if match:
        return match.group(1)
    
    return None

def test_chat_api():
    """测试聊天消息API"""
    url = "http://192.168.61.29/v1/chat-messages"
    headers = {
        "Authorization": "Bearer app-odgVGDvCcxfK1YiIpC2yxyrQ",
        "Content-Type": "application/json"
    }
    
    # 从HTML报告中提取的法规测试字段
    test_fields = [
        "企业安全生产责任体系五落实五到位规定",
        "国家安全监管总局关于加强精细化工反应安全风险评估工作的指导意见",
        "关于开展安全质量标准化活动的指导意见"
    ]
    
    print("=" * 60)
    print("聊天API测试开始")
    print(f"URL: {url}")
    print("=" * 60)
    
    conversation_id = ""  # 用于保持会话连续性
    
    for field in test_fields:
        data = {
            "inputs": {"checkpoint": "施行日期"},
            "query": field,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": "system"
        }
        
        print(f"\n测试字段: {field}")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False)}")
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60, stream=True)
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ 流式响应:")
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
                                # 获取conversation_id用于后续请求
                                if 'conversation_id' in chunk_data and not conversation_id:
                                    conversation_id = chunk_data['conversation_id']
                                    print(f"\n会话ID: {conversation_id}")
                                
                                if 'answer' in chunk_data:
                                    full_answer += chunk_data['answer']
                                    print(chunk_data['answer'], end='', flush=True)
                            except json.JSONDecodeError:
                                continue
                
                print(f"\n完整回答: {full_answer}")
                
                # 提取施行日期
                implementation_date = extract_implementation_date(full_answer)
                if implementation_date:
                    print(f"📅 提取的施行日期: {implementation_date}")
                else:
                    print("❌ 未找到施行日期")
            else:
                print(f"❌ 请求失败: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败")
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        
        print("-" * 40)
    
    print(f"\n聊天API测试完成")
    if conversation_id:
        print(f"最终会话ID: {conversation_id}")

if __name__ == "__main__":
    test_chat_api()