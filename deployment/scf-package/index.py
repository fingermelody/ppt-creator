# -*- coding: utf-8 -*-
"""
SCF 入口函数 - 处理 API 网关事件
"""
import json
from app.main import handler as mangum_handler

def handler(event, context):
    """
    SCF 入口函数
    转换腾讯云 API 网关事件为 AWS API Gateway 格式
    """
    print("Event:", json.dumps(event, default=str))
    
    # 腾讯云 API 网关事件转换为 AWS Lambda 格式
    # Mangum 期望的是 AWS API Gateway v1 或 v2 格式
    
    # 转换事件格式
    aws_event = {
        "version": "1.0",
        "resource": event.get("path", "/"),
        "path": event.get("path", "/"),
        "httpMethod": event.get("httpMethod", "GET"),
        "headers": event.get("headers", {}),
        "multiValueHeaders": {},
        "queryStringParameters": event.get("queryStringParameters") or {},
        "multiValueQueryStringParameters": {},
        "pathParameters": event.get("pathParameters") or {},
        "stageVariables": {},
        "requestContext": {
            "resourceId": "resource-id",
            "resourcePath": event.get("path", "/"),
            "httpMethod": event.get("httpMethod", "GET"),
            "path": event.get("path", "/"),
            "protocol": "HTTP/1.1",
            "stage": "release",
            "requestId": event.get("requestContext", {}).get("requestId", ""),
            "identity": {
                "sourceIp": event.get("requestContext", {}).get("sourceIp", "")
            }
        },
        "body": event.get("body"),
        "isBase64Encoded": event.get("isBase64Encoded", False)
    }
    
    print("Converted AWS Event:", json.dumps(aws_event, default=str))
    
    # 调用 Mangum 处理
    response = mangum_handler(aws_event, context)
    
    print("Mangum Response:", json.dumps(response, default=str))
    
    # 转换响应格式为腾讯云 API 网关格式
    return {
        "isBase64Encoded": response.get("isBase64Encoded", False),
        "statusCode": response.get("statusCode", 200),
        "headers": response.get("headers", {}),
        "body": response.get("body", "")
    }
