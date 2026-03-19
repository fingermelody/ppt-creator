#!/usr/bin/env python3
"""
检查 COS 静态网站托管配置
"""

import os
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

def get_credentials():
    config_path = os.path.expanduser('~/.cos.conf')
    if os.path.exists(config_path):
        import configparser
        config = configparser.ConfigParser()
        config.read(config_path)
        if 'common' in config:
            return {
                'secret_id': config['common'].get('secret_id'),
                'secret_key': config['common'].get('secret_key'),
                'region': config['common'].get('region'),
                'bucket': config['common'].get('bucket'),
            }
    return None

credentials = get_credentials()
if not credentials:
    print("无法获取 COS 凭证")
    exit(1)

config = CosConfig(
    Region=credentials['region'],
    SecretId=credentials['secret_id'],
    SecretKey=credentials['secret_key'],
)
client = CosS3Client(config)
bucket = credentials['bucket']

print(f"检查存储桶: {bucket}")

# 获取静态网站配置
try:
    response = client.get_bucket_website(Bucket=bucket)
    print("\n当前静态网站配置:")
    print(response)
except Exception as e:
    print(f"获取配置失败: {e}")
