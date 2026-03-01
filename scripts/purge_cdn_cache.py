#!/usr/bin/env python3
"""
刷新腾讯云 CDN 缓存
"""

import os
import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cdn.v20180606 import cdn_client, models

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
            }
    return None

credentials = get_credentials()
if not credentials:
    print("无法获取凭证，请确保已配置 coscmd")
    exit(1)

# CDN 域名
CDN_DOMAIN = "ppt.bottlepeace.com"

# 初始化 CDN 客户端
cred = credential.Credential(credentials['secret_id'], credentials['secret_key'])
httpProfile = HttpProfile()
httpProfile.endpoint = "cdn.tencentcloudapi.com"
clientProfile = ClientProfile()
clientProfile.httpProfile = httpProfile
client = cdn_client.CdnClient(cred, "", clientProfile)

# 刷新目录
print(f"正在刷新 CDN 缓存: https://{CDN_DOMAIN}/")

try:
    # 使用目录刷新
    req = models.PurgePathCacheRequest()
    params = {
        "Paths": [f"https://{CDN_DOMAIN}/"],
        "FlushType": "flush"
    }
    req.from_json_string(json.dumps(params))
    resp = client.PurgePathCache(req)
    print("✅ CDN 目录刷新提交成功！")
    print(f"任务 ID: {resp.TaskId}")
    print("注意: CDN 刷新需要 5-10 分钟生效")
except TencentCloudSDKException as e:
    print(f"目录刷新失败: {e}")
    # 尝试 URL 刷新
    print("\n尝试 URL 刷新...")
    try:
        req = models.PurgeUrlsCacheRequest()
        params = {
            "Urls": [
                f"https://{CDN_DOMAIN}/",
                f"https://{CDN_DOMAIN}/index.html",
                f"https://{CDN_DOMAIN}/assets/index-JtqxaA8-.js",
                f"https://{CDN_DOMAIN}/assets/index-CmgLaQog.css",
            ]
        }
        req.from_json_string(json.dumps(params))
        resp = client.PurgeUrlsCache(req)
        print("✅ CDN URL 刷新提交成功！")
        print(f"任务 ID: {resp.TaskId}")
    except TencentCloudSDKException as e2:
        print(f"URL 刷新也失败: {e2}")
