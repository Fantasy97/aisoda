#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BOMUploader:
    """BOM上传工具类"""
    
    def __init__(self, base_url="http://localhost:8080"):
        """
        初始化BOM上传器
        
        Args:
            base_url: PLM系统的基础URL
        """
        self.base_url = base_url
        self.upload_endpoint = "/sipmweb/api/PushBomInfo"
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def convert_bom_to_plm_format(self, bom_data, parent_id, owner="adm", creator="adm"):
        """
        将BOM数据转换为PLM系统要求的格式
        
        Args:
            bom_data: BOM数据字典
            parent_id: 父件ID
            owner: 所有者，默认"adm"
            creator: 创建者，默认"adm"
            
        Returns:
            list: PLM格式的BOM数据列表
        """
        plm_data = []
        bom_sequence = 1
        current_time = datetime.now().strftime("%Y%m%d")
        
        # 遍历BOM数据的所有分类
        for category, parts in bom_data.items():
            if isinstance(parts, list):
                for part in parts:
                    # 提取物料信息
                    part_no = part.get('MPART.NO', '')
                    quantity = str(part.get('MBOM.BNUM', '1.0'))
                    
                    if part_no:  # 确保物料编号不为空
                        plm_item = {
                            "PID": parent_id,
                            "CID": part_no,
                            "BNUM": quantity,
                            "BOMPST": str(bom_sequence),
                            "OWNER": owner,
                            "CREATOR": creator,
                            "ASMEMO": f"外部接口导入{current_time}"
                        }
                        plm_data.append(plm_item)
                        bom_sequence += 1
        
        return plm_data
    
    def upload_bom_to_plm(self, plm_data):
        """
        上传BOM数据到PLM系统
        
        Args:
            plm_data: PLM格式的BOM数据列表
            
        Returns:
            dict: 上传结果
        """
        try:
            url = f"{self.base_url}{self.upload_endpoint}"
            
            logger.info(f"正在上传BOM数据到: {url}")
            logger.info(f"数据条数: {len(plm_data)}")
            
            response = requests.post(
                url=url,
                headers=self.headers,
                json=plm_data,
                timeout=30
            )
            
            # 检查HTTP状态码
            if response.status_code == 200:
                result = response.json()
                logger.info(f"上传成功: {result}")
                return {
                    'success': True,
                    'message': '上传成功',
                    'data': result,
                    'uploaded_count': len(plm_data)
                }
            else:
                logger.error(f"上传失败，HTTP状态码: {response.status_code}")
                return {
                    'success': False,
                    'message': f'上传失败，HTTP状态码: {response.status_code}',
                    'error': response.text
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求异常: {str(e)}")
            return {
                'success': False,
                'message': '网络请求失败',
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"上传过程中发生异常: {str(e)}")
            return {
                'success': False,
                'message': '上传过程中发生异常',
                'error': str(e)
            }
    
    def upload_bom_from_file(self, bom_file_path, parent_id, owner="adm", creator="adm"):
        """
        从文件上传BOM数据
        
        Args:
            bom_file_path: BOM文件路径
            parent_id: 父件ID
            owner: 所有者
            creator: 创建者
            
        Returns:
            dict: 上传结果
        """
        try:
            # 读取BOM文件
            with open(bom_file_path, 'r', encoding='utf-8') as f:
                bom_data = json.load(f)
            
            # 转换为PLM格式
            plm_data = self.convert_bom_to_plm_format(bom_data, parent_id, owner, creator)
            
            if not plm_data:
                return {
                    'success': False,
                    'message': 'BOM数据为空或格式不正确'
                }
            
            # 上传到PLM系统
            return self.upload_bom_to_plm(plm_data)
            
        except FileNotFoundError:
            return {
                'success': False,
                'message': f'文件不存在: {bom_file_path}'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'message': f'JSON文件格式错误: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'处理文件时发生错误: {str(e)}'
            }

def upload_bom_data(bom_data, parent_id, plm_base_url="http://localhost:8080", owner="adm", creator="adm"):
    """
    上传BOM数据的便捷函数
    
    Args:
        bom_data: BOM数据字典或文件路径
        parent_id: 父件ID
        plm_base_url: PLM系统基础URL
        owner: 所有者
        creator: 创建者
        
    Returns:
        dict: 上传结果
    """
    uploader = BOMUploader(plm_base_url)
    
    if isinstance(bom_data, str):
        # 如果是字符串，当作文件路径处理
        return uploader.upload_bom_from_file(bom_data, parent_id, owner, creator)
    elif isinstance(bom_data, dict):
        # 如果是字典，直接转换并上传
        plm_data = uploader.convert_bom_to_plm_format(bom_data, parent_id, owner, creator)
        return uploader.upload_bom_to_plm(plm_data)
    else:
        return {
            'success': False,
            'message': 'BOM数据格式不支持，请提供文件路径或数据字典'
        }

if __name__ == "__main__":
    # 测试代码
    test_bom_data = {
        "category1": [
            {
                "MPART.NO": "WK_200001",
                "MPART.NAME": "测试物料1",
                "MBOM.BNUM": "2.0"
            },
            {
                "MPART.NO": "WK_200002", 
                "MPART.NAME": "测试物料2",
                "MBOM.BNUM": "1.0"
            }
        ]
    }
    
    result = upload_bom_data(test_bom_data, "WK_100001")
    print(json.dumps(result, indent=2, ensure_ascii=False))