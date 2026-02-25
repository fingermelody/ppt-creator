#!/usr/bin/env python3
"""
创建和配置 COS 存储桶用于前端静态托管
"""

import os
import sys
from qcloud_cos import CosConfig, CosS3Client

# 配置 - 从环境变量读取
SECRET_ID = os.getenv("TENCENT_SECRET_ID")
SECRET_KEY = os.getenv("TENCENT_SECRET_KEY")
REGION = os.getenv("REGION", "ap-guangzhou")
APP_ID = os.getenv("TENCENT_APP_ID", "1253851367")
BUCKET_NAME = f"ppt-rsd-frontend-{APP_ID}"

if not SECRET_ID or not SECRET_KEY:
    print("错误: 请设置环境变量 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY")
    sys.exit(1)

def main():
    # 创建 COS 客户端
    config = CosConfig(
        Region=REGION,
        SecretId=SECRET_ID,
        SecretKey=SECRET_KEY,
    )
    client = CosS3Client(config)
    
    # 1. 检查存储桶是否存在
    print(f"检查存储桶 {BUCKET_NAME}...")
    try:
        client.head_bucket(Bucket=BUCKET_NAME)
        print(f"✅ 存储桶 {BUCKET_NAME} 已存在")
    except Exception as e:
        if 'NoSuchBucket' in str(e):
            print(f"创建存储桶 {BUCKET_NAME}...")
            try:
                client.create_bucket(
                    Bucket=BUCKET_NAME,
                    ACL='public-read'  # 公有读
                )
                print(f"✅ 存储桶创建成功")
            except Exception as e2:
                print(f"❌ 创建存储桶失败: {e2}")
                return False
        else:
            print(f"❌ 检查存储桶失败: {e}")
            return False
    
    # 2. 配置静态网站
    print("配置静态网站托管...")
    try:
        website_config = {
            'IndexDocument': {
                'Suffix': 'index.html'
            },
            'ErrorDocument': {
                'Key': 'index.html'  # SPA 路由支持
            }
        }
        client.put_bucket_website(
            Bucket=BUCKET_NAME,
            WebsiteConfiguration=website_config
        )
        print("✅ 静态网站配置成功")
    except Exception as e:
        print(f"⚠️ 配置静态网站失败: {e}")
    
    # 3. 配置 CORS
    print("配置 CORS...")
    try:
        cors_config = {
            'CORSRule': [{
                'AllowedOrigin': ['*'],
                'AllowedMethod': ['GET', 'HEAD'],
                'AllowedHeader': ['*'],
                'MaxAgeSeconds': 3600
            }]
        }
        client.put_bucket_cors(
            Bucket=BUCKET_NAME,
            CORSConfiguration=cors_config
        )
        print("✅ CORS 配置成功")
    except Exception as e:
        print(f"⚠️ 配置 CORS 失败: {e}")
    
    # 输出信息
    print("\n" + "=" * 50)
    print("📦 COS 存储桶配置完成")
    print("=" * 50)
    print(f"存储桶名称: {BUCKET_NAME}")
    print(f"地域: {REGION}")
    print(f"静态网站域名: {BUCKET_NAME}.cos-website.{REGION}.myqcloud.com")
    print(f"COS 域名: {BUCKET_NAME}.cos.{REGION}.myqcloud.com")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
