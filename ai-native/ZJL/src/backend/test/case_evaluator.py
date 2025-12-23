"""案例质量评估工具 - 整合查询与评估"""
import json
import logging
import sys
from typing import Optional, Dict, Any
from chat_api_client import ChatAPIClient
from fxiaoke_cases_list_query import FXiaoKeListQueryClient, convert_to_chinese_fields


class CaseEvaluator:
    """案例质量评估器 - 整合纷享销客查询和AI评估"""
    
    def __init__(self, 
                 chat_api_url: str = "http://192.168.61.29/v1/chat-messages"):
        """
        初始化评估器
        
        Args:
            chat_api_url: 聊天API地址
        """
        self.fxiaoke_client = FXiaoKeListQueryClient()
        self.chat_client = ChatAPIClient(api_url=chat_api_url)
        self.logger = logging.getLogger(__name__)
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        初始化纷享销客客户端（获取token和用户ID）
        
        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True
        
        self.logger.info("初始化纷享销客API客户端...")
        
        # 获取令牌
        if not self.fxiaoke_client.get_token():
            self.logger.error("获取令牌失败")
            return False
        
        # 获取用户ID
        if not self.fxiaoke_client.get_user_id():
            self.logger.error("获取用户ID失败")
            return False
        
        self._initialized = True
        self.logger.info("初始化成功")
        return True
    
    def query_case_by_name(self, case_name: str) -> Optional[Dict[str, Any]]:
        """
        根据案例名称查询案例数据
        
        Args:
            case_name: 案例名称（如 CN2024011708976）
            
        Returns:
            案例数据字典，未找到返回None
        """
        self.logger.info(f"查询案例: {case_name}")
        
        # 查询案例列表
        result = self.fxiaoke_client.query_cases_list(
            limit=10,
            offset=0,
            field_projection=[
                "name", "create_time", "owner_id", "objectDataId",
                "field_Utj19__c",  # 问题记录
                "field_0uAwt__c",  # 问题类型
                "field_iywKQ__c",  # 提报人
                "field_93r62__c",  # 提报人电话
                "field_o1oCe__c",  # 公众号用户
                "field_3ff0E__c",  # 微信昵称
                "field_812NN__c",  # 企微用户/群
                "field_Mc0p7__c",  # 需求来源
                "field_glsb__c",   # 关联设备
                "account_id",      # 公司名称
                "field_sZHpO__c",  # 设备类型
                "field_toFhx__c",  # 问题归类
                "field_glcp__c",   # 关联产品
                "field_FGMjJ__c",  # 设备名称
                "field_wJsp4__c",  # 机型分类
                "field_qT1uy__c",  # 质保期至
                "field_7jD1u__c"   # 辅助属性
            ],
            filters=[{
                "operator": "EQ",
                "field_name": "name",
                "field_values": [case_name]
            }]
        )
        
        # 检查查询结果
        if not result or result.get("errorCode") != 0:
            self.logger.error(f"查询失败: {result.get('errorMessage') if result else '请求失败'}")
            return None
        
        # 提取数据
        data = result.get("data", {})
        data_list = data.get("dataList", [])
        
        if not data_list:
            self.logger.warning(f"未找到案例: {case_name}")
            return None
        
        # 返回第一条数据（案例名称应该唯一）
        case_data = data_list[0]
        self.logger.info(f"成功查询到案例数据")
        
        return case_data
    
    def evaluate_case_by_name(self, case_name: str) -> Optional[Dict[str, Any]]:
        """
        根据案例名称评估案例质量
        
        Args:
            case_name: 案例名称（如 CN2024011708976）
            
        Returns:
            评分结果字典，失败返回None
        """
        # 确保已初始化
        if not self._initialized and not self.initialize():
            return None
        
        # 1. 查询案例数据
        case_data = self.query_case_by_name(case_name)
        if not case_data:
            return None
        
        # 2. 转换为中文字段
        case_data_cn = convert_to_chinese_fields(
            case_data, 
            use_grouping=False, 
            translate_values=True
        )
        
        self.logger.info(f"案例数据转换完成，准备评估...")
        
        # 3. 发送给AI评估
        evaluation_result = self.chat_client.evaluate_case(case_data_cn)
        
        if evaluation_result:
            self.logger.info(f"评估完成: {case_name}")
            return evaluation_result
        else:
            self.logger.error(f"评估失败: {case_name}")
            return None
    
    def batch_evaluate(self, case_names: list) -> Dict[str, Any]:
        """
        批量评估多个案例
        
        Args:
            case_names: 案例名称列表
            
        Returns:
            评估结果字典 {case_name: evaluation_result}
        """
        results = {}
        
        for idx, case_name in enumerate(case_names, 1):
            self.logger.info(f"[{idx}/{len(case_names)}] 评估案例: {case_name}")
            
            result = self.evaluate_case_by_name(case_name)
            results[case_name] = result
            
            if result:
                total_score = result.get("总分", "N/A")
                self.logger.info(f"  ✓ 完成，总分: {total_score}")
            else:
                self.logger.warning(f"  ✗ 失败")
        
        return results


def main():
    """主函数 - 命令行使用示例"""
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                   案例质量评估工具                             ║
╚══════════════════════════════════════════════════════════════╝

功能说明:
  ✓ 输入案例名称，自动查询纷享销客数据
  ✓ AI智能评估工单质量
  ✓ 返回详细评分结果
""")
    
    # 创建评估器
    evaluator = CaseEvaluator()
    
    # 初始化
    if not evaluator.initialize():
        print("❌ 初始化失败，请检查网络和配置")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # 命令行参数处理
    if len(sys.argv) > 1:
        # 从命令行参数获取案例名称
        case_name = sys.argv[1]
        print(f"📋 评估案例: {case_name}\n")
        
        result = evaluator.evaluate_case_by_name(case_name)
        
        if result:
            print("\n✅ 评估结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 保存结果
            output_file = f"evaluation_{case_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "案例名称": case_name,
                    "评估结果": result
                }, f, ensure_ascii=False, indent=2)
            print(f"\n💾 结果已保存: {output_file}")
        else:
            print("\n❌ 评估失败")
            sys.exit(1)
    else:
        # 交互模式
        print("💡 使用方式:")
        print("   python case_evaluator.py CN2024011708976")
        print("\n或输入案例名称进行评估 (输入 q 退出):\n")
        
        while True:
            case_name = input("请输入案例名称: ").strip()
            
            if case_name.lower() == 'q':
                print("👋 再见!")
                break
            
            if not case_name:
                continue
            
            print(f"\n{'='*60}")
            print(f"📋 评估案例: {case_name}")
            print('='*60 + "\n")
            
            result = evaluator.evaluate_case_by_name(case_name)
            
            if result:
                print("\n✅ 评估结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                # 保存结果
                output_file = f"evaluation_{case_name}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "案例名称": case_name,
                        "评估结果": result
                    }, f, ensure_ascii=False, indent=2)
                print(f"\n💾 结果已保存: {output_file}")
            else:
                print("\n❌ 评估失败")
            
            print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
