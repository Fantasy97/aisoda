#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上传 Excel 文件到 OSS 并发送下载链接到飞书
集成功能：
1. 上传 Excel 文件到 OSS
2. 生成预签名下载链接
3. 将链接发送到飞书 webhook
"""

import argparse
import os
import sys
import traceback
from datetime import timedelta
from typing import Optional, Tuple
from pathlib import Path

import requests
import alibabacloud_oss_v2 as oss

# 默认配置
DEFAULT_REGION = "cn-hangzhou"
DEFAULT_BUCKET = "aiswei"
DEFAULT_OSS_KEY_PREFIX = "Lifetree/UAT/qis/"

# 飞书 Webhook 地址
FEISHU_WEBHOOK_URL = "https://aiswei-tech.feishu.cn/base/workflow/webhook/event/XM5SanPSOwbHvlh9kbzcPP7anyd"


class OSSUploader:
    """OSS 上传和下载链接生成工具"""
    
    def __init__(self, region: str, bucket: str, access_key_id: Optional[str] = None, 
                 access_key_secret: Optional[str] = None, endpoint: Optional[str] = None):
        """
        初始化 OSS 客户端
        
        Args:
            region: OSS 区域
            bucket: 存储空间名称
            access_key_id: 访问密钥ID（可选，从环境变量读取）
            access_key_secret: 访问密钥Secret（可选，从环境变量读取）
            endpoint: 自定义 endpoint（可选）
        """
        self.region = region
        self.bucket = bucket
        self.endpoint = endpoint
        
        # 配置凭证   
        if access_key_id and access_key_secret:
            print("使用命令行参数提供的凭证...")
            try:
                credentials_provider = oss.credentials.StaticCredentialsProvider(
                    access_key_id=access_key_id,
                    access_key_secret=access_key_secret
                )
            except Exception as e:
                raise ValueError(f"无法创建静态凭证提供者: {e}")
        else:
            print("尝试从环境变量读取凭证...")
            try:
                credentials_provider = oss.credentials.EnvironmentVariableCredentialsProvider()
            except Exception as e:
                raise ValueError(
                    f"无法从环境变量读取凭证: {e}\n"
                    "请设置环境变量 OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET"
                )
        
        # 创建配置
        cfg = oss.config.load_default()
        cfg.credentials_provider = credentials_provider
        cfg.region = region
        
        if endpoint:
            cfg.endpoint = endpoint
        
        # 创建客户端
        self.client = oss.Client(cfg)
    
    def upload_file(self, file_path: str, oss_key: str) -> dict:
        """
        上传文件到 OSS
        
        Args:
            file_path: 本地文件路径
            oss_key: OSS 对象键名
            
        Returns:
            dict: 上传结果信息
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 如果 key 是目录路径，自动添加文件名
        if oss_key.endswith('/'):
            filename = os.path.basename(file_path)
            oss_key = oss_key + filename
            print(f"注意: key已自动添加文件名: {oss_key}")
        
        print(f"\n开始上传文件...")
        print(f"  Bucket: {self.bucket}")
        print(f"  Key: {oss_key}")
        print(f"  文件路径: {file_path}")
        print(f"  文件大小: {os.path.getsize(file_path)} bytes")
        
        try:
            result = self.client.put_object_from_file(
                oss.PutObjectRequest(
                    bucket=self.bucket,
                    key=oss_key
                ),
                file_path
            )
            
            print(f"✓ 上传成功!")
            
            return {
                "success": True,
                "bucket": self.bucket,
                "key": oss_key,
                "status_code": result.status_code,
                "request_id": result.request_id,
                "etag": result.etag,
                "content_md5": result.content_md5
            }
        except Exception as e:
            print(f"✗ 上传失败: {type(e).__name__}: {str(e)}")
            raise
    
    def generate_presigned_url(self, oss_key: str, expires_seconds: int = 3600) -> dict:
        """
        生成预签名下载链接
        
        Args:
            oss_key: OSS 对象键名
            expires_seconds: 链接有效期（秒），默认 3600 秒（1小时）
            
        Returns:
            dict: 包含 URL 和过期时间的信息
        """
        print(f"\n生成预签名下载链接...")
        print(f"  Key: {oss_key}")
        print(f"  有效期: {expires_seconds} 秒 ({expires_seconds // 3600} 小时)")
        
        try:
            pre_result = self.client.presign(
                oss.GetObjectRequest(
                    bucket=self.bucket,
                    key=oss_key
                ),
                expires=timedelta(seconds=expires_seconds)
            )
            
            print(f"✓ 链接生成成功!")
            
            return {
                "success": True,
                "url": pre_result.url,
                "method": pre_result.method,
                "expiration": pre_result.expiration.strftime('%Y-%m-%d %H:%M:%S'),
                "expiration_utc": pre_result.expiration.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            }
        except Exception as e:
            print(f"✗ 生成链接失败: {type(e).__name__}: {str(e)}")
            raise


class FeishuNotifier:
    """飞书通知工具"""
    
    def __init__(self, webhook_url: str = FEISHU_WEBHOOK_URL):
        """
        初始化飞书通知器
        
        Args:
            webhook_url: 飞书 webhook 地址
        """
        self.webhook_url = webhook_url
    
    def send_url(self, url: str, title: str = "OSS 下载链接", description: str = "") -> bool:
        """
        发送 URL 到飞书 webhook
        
        Args:
            url: 要发送的 URL
            title: 消息标题
            description: 消息描述
            
        Returns:
            bool: 是否发送成功
        """
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"{title}\n{description}\n下载链接: {url}"
            }
        }
        
        try:
            print(f"\n正在发送链接到飞书...")
            print(f"  Webhook: {self.webhook_url}")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"  响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("code") == 0 or result.get("StatusCode") == 0:
                        print(f"✓ 发送成功!")
                        return True
                    else:
                        print(f"✗ 发送失败: {result.get('msg', '未知错误')}")
                        return False
                except:
                    if response.status_code == 200:
                        print(f"✓ 发送成功!")
                        return True
                    return False
            else:
                print(f"✗ 发送失败: HTTP {response.status_code}")
                print(f"  响应内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ 发送失败: {type(e).__name__}: {str(e)}")
            return False


def upload_and_notify(
    file_path: str,
    oss_key: Optional[str] = None,
    region: str = DEFAULT_REGION,
    bucket: str = DEFAULT_BUCKET,
    access_key_id: Optional[str] = None,
    access_key_secret: Optional[str] = None,
    endpoint: Optional[str] = None,
    expires_seconds: int = 3600,
    feishu_webhook: Optional[str] = None,
    title: str = "OSS 下载链接",
    description: str = "",
    send_to_feishu: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    上传文件到 OSS，生成下载链接，并发送到飞书
    
    Args:
        file_path: 本地文件路径
        oss_key: OSS 对象键名（可选，默认使用文件名的完整路径）
        region: OSS 区域
        bucket: 存储空间名称
        access_key_id: 访问密钥ID（可选）
        access_key_secret: 访问密钥Secret（可选）
        endpoint: 自定义 endpoint（可选）
        expires_seconds: 预签名链接有效期（秒）
        feishu_webhook: 飞书 webhook 地址（可选）
        title: 飞书消息标题
        description: 飞书消息描述
        send_to_feishu: 是否发送到飞书
        
    Returns:
        Tuple[bool, Optional[str]]: (是否成功, 下载链接URL)
    """
    try:
        # 1. 初始化 OSS 上传器
        uploader = OSSUploader(
            region=region,
            bucket=bucket,
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            endpoint=endpoint
        )
        
        # 2. 确定 OSS key
        if not oss_key:
            # 使用默认前缀 + 文件名
            filename = os.path.basename(file_path)
            oss_key = DEFAULT_OSS_KEY_PREFIX + filename
            print(f"未指定 OSS key，使用默认: {oss_key}")
        
        # 3. 上传文件
        upload_result = uploader.upload_file(file_path, oss_key)
        
        if not upload_result["success"]:
            return False, None
        
        # 4. 生成预签名链接
        url_result = uploader.generate_presigned_url(oss_key, expires_seconds)
        
        if not url_result["success"]:
            return False, None
        
        download_url = url_result["url"]
        
        # 5. 发送到飞书（如果需要）
        if send_to_feishu:
            notifier = FeishuNotifier(webhook_url=feishu_webhook or FEISHU_WEBHOOK_URL)
            send_success = notifier.send_url(download_url, title=title, description=description)
            
            if not send_success:
                print("警告: 飞书通知发送失败，但文件已成功上传")
        
        # 6. 输出结果
        print(f"\n{'='*80}")
        print(f"完成!")
        print(f"{'='*80}")
        print(f"文件已上传到 OSS:")
        print(f"  Bucket: {bucket}")
        print(f"  Key: {oss_key}")
        print(f"\n下载链接:")
        print(f"  {download_url}")
        print(f"\n链接有效期至: {url_result['expiration']}")
        print(f"{'='*80}")
        
        return True, download_url
        
    except Exception as e:
        print(f"\n✗ 操作失败: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        return False, None


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="上传 Excel 文件到 OSS 并发送下载链接到飞书",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本使用（使用环境变量中的凭证）
  python upload_excel_to_oss_and_notify.py --file_path "data/exports/质检结果.xlsx"
  
  # 指定 OSS key
  python upload_excel_to_oss_and_notify.py --file_path "data/exports/质检结果.xlsx" --oss_key "Lifetree/UAT/qis/质检结果.xlsx"
  
  # 使用命令行参数提供凭证
  python upload_excel_to_oss_and_notify.py --file_path "data/exports/质检结果.xlsx" --access_key_id "xxx" --access_key_secret "xxx"
  
  # 只上传，不发送到飞书
  python upload_excel_to_oss_and_notify.py --file_path "data/exports/质检结果.xlsx" --no-feishu
        """
    )
    
    # 必需参数
    parser.add_argument('--file_path', required=True, help='要上传的 Excel 文件路径')
    
    # OSS 配置参数
    parser.add_argument('--region', default=DEFAULT_REGION, help=f'OSS 区域，默认: {DEFAULT_REGION}')
    parser.add_argument('--bucket', default=DEFAULT_BUCKET, help=f'存储空间名称，默认: {DEFAULT_BUCKET}')
    parser.add_argument('--oss_key', help='OSS 对象键名（可选，默认使用文件名的完整路径）')
    parser.add_argument('--endpoint', help='自定义 endpoint（可选）')
    parser.add_argument('--access_key_id', help='访问密钥ID（可选，从环境变量读取）')
    parser.add_argument('--access_key_secret', help='访问密钥Secret（可选，从环境变量读取）')
    
    # 预签名链接配置
    parser.add_argument('--expires', type=int, default=3600, help='预签名链接有效期（秒），默认: 3600（1小时）')
    
    # 飞书配置参数
    parser.add_argument('--feishu_webhook', default=FEISHU_WEBHOOK_URL, help=f'飞书 webhook 地址，默认: {FEISHU_WEBHOOK_URL}')
    parser.add_argument('--title', default='OSS 下载链接', help='飞书消息标题，默认: "OSS 下载链接"')
    parser.add_argument('--description', default='', help='飞书消息描述')
    parser.add_argument('--no-feishu', action='store_true', help='不上传到飞书，只上传到 OSS 并生成链接')
    
    # 解析参数
    args = parser.parse_args()
    
    # 执行上传和通知
    success, url = upload_and_notify(
        file_path=args.file_path,
        oss_key=args.oss_key,
        region=args.region,
        bucket=args.bucket,
        access_key_id=args.access_key_id,
        access_key_secret=args.access_key_secret,
        endpoint=args.endpoint,
        expires_seconds=args.expires,
        feishu_webhook=args.feishu_webhook,
        title=args.title,
        description=args.description,
        send_to_feishu=not args.no_feishu
    )
    
    # 根据结果退出
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

