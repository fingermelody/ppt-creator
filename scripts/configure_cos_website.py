#!/usr/bin/env python3
"""
配置腾讯云 COS 静态网站托管
"""

import os
import json
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

# 从环境变量或 coscmd 配置文件获取凭证
def get_credentials():
    # 尝试从 coscmd 配置读取
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
    print("无法获取 COS 凭证，请确保已配置 coscmd")
    exit(1)

# 配置客户端
config = CosConfig(
    Region=credentials['region'],
    SecretId=credentials['secret_id'],
    SecretKey=credentials['secret_key'],
)
client = CosS3Client(config)

bucket = credentials['bucket']
print(f"配置存储桶: {bucket}")

# 配置静态网站托管
website_config = {
    'IndexDocument': {
        'Suffix': 'index.html'
    },
    'ErrorDocument': {
        'Key': 'index.html'  # SPA 应用将所有错误都指向 index.html
    }
}

try:
    response = client.put_bucket_website(
        Bucket=bucket,
        WebsiteConfiguration=website_config
    )
    print("✅ 静态网站托管配置成功！")
    print(f"索引文档: index.html")
    print(f"错误文档: index.html (用于 SPA 路由)")
    print(f"静态网站访问地址: https://{bucket}.cos-website.{credentials['region']}.myqcloud.com/")
except Exception as e:
    print(f"❌ 配置失败: {e}")
    exit(1)
