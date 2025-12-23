"""聊天API客户端模块"""
import json
import logging
import requests
from typing import Optional, Dict, Any


class ChatAPIClient:
    """聊天API客户端"""

    def __init__(self, api_url: str = "http://192.168.61.29/v1/chat-messages"):
        """
        初始化聊天API客户端
        
        Args:
            api_url: API接口地址
        """
        self.api_url = api_url
        self.headers = {
            "Authorization": "Bearer app-lG9ujTDSSqUDLf7KGpfLYSDc",
            "Content-Type": "application/json"
        }
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def evaluate_case(self, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        评估案例质量并返回评分结果
        
        Args:
            case_data: 案例数据字典
            
        Returns:
            评分结果字典，失败则返回None
        """
        try:
            # 将案例数据转换为JSON字符串
            case_json = json.dumps(case_data, ensure_ascii=False, indent=2)
            
            self.logger.info(f"评估案例: {case_data.get('案例名称', 'Unknown')}")
            
            # 发送到聊天API
            response_text = self.send_message(case_json)
            
            if response_text:
                # 尝试从响应中提取JSON评分结果
                try:
                    # 查找JSON块
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        result = json.loads(json_str)
                        self.logger.info(f"案例评估完成: {case_data.get('案例名称', 'Unknown')}")
                        return result
                    else:
                        self.logger.warning(f"未能从响应中提取JSON: {response_text}")
                        return None
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON解析失败: {e}")
                    return None
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"案例评估异常: {e}")
            return None

    def send_message(self, query: str, inputs: Optional[dict] = None, conversation_id: str = "") -> Optional[str]:
        """
        发送消息到聊天API并获取完整回答
        
        Args:
            query: 查询内容
            inputs: 额外的输入参数
            conversation_id: 会话ID，用于保持上下文
            
        Returns:
            API返回的完整回答文本，失败则返回None
        """
        try:
            data = {
                "inputs": inputs or {},
                "query": query,
                "response_mode": "streaming",
                "conversation_id": conversation_id,
                "user": "system"
            }

            self.logger.info(f"发送聊天请求: {query}")

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

                self.logger.info(f"聊天API响应成功")
                return full_answer
            else:
                self.logger.error(f"聊天API请求失败，状态码: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"聊天API调用异常: {query}, 错误: {e}")
            return None


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 示例用法
    client = ChatAPIClient()
    
    # 测试案例数据
    test_case = {
        "案例名称": "CN2024011708659",
        "创建时间": "2024-01-17 10:52:58",
        "问题记录": "火零接反，让师傅检查接线",
        "问题类型": "设备问题",
        "提报人": "空",
        "提报人电话": "65a740ed1da06400018b84cc",
        "公众号用户": "空",
        "微信昵称": "空",
        "企微用户/群": "空",
        "需求来源": "67NYnAQ8s",
        "关联设备": "64e57aa68e14ec0001cc2827",
        "公司名称": "63a2ba4995e44b00015d5cce",
        "设备类型": "1BGku5lv3",
        "问题归类": "p1D42UEmW",
        "关联产品": "832124972026363906",
        "设备名称": "23K三相并网逆变器",
        "机型分类": "SP 3~30K",
        "质保期至": "2030-03-01",
        "辅助属性": "CN-ENGG(China)",
        "负责人ID": "空",
        "对象数据ID": "空"
    }
    
    # 测试案例评估
    result = client.evaluate_case(test_case)
    print("评估结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
