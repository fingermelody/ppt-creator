# -*- coding: utf-8 -*-
"""
SCF 事件函数入口
用于处理异步任务（如 PPT 文件处理、向量化等）
"""

import json
import os
import logging
from typing import Any, Dict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    SCF 主入口函数
    
    Args:
        event: 事件数据，包含触发源信息
        context: 运行上下文
    
    Returns:
        处理结果
    """
    logger.info(f"Received event: {json.dumps(event, ensure_ascii=False)}")
    
    try:
        # 判断触发源类型
        if "Records" in event:
            # COS 触发器
            return handle_cos_event(event, context)
        elif "Type" in event and event["Type"] == "Timer":
            # 定时触发器
            return handle_timer_event(event, context)
        elif "httpMethod" in event:
            # API 网关触发器（异步调用）
            return handle_api_event(event, context)
        else:
            # 自定义事件（手动调用）
            return handle_custom_event(event, context)
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "message": "Internal server error"
            })
        }


def handle_cos_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    处理 COS 对象存储事件
    当有新 PPTX 文件上传时触发
    """
    results = []
    
    for record in event.get("Records", []):
        cos_info = record.get("cos", {})
        cos_bucket = cos_info.get("cosBucket", {})
        cos_object = cos_info.get("cosObject", {})
        
        bucket_name = cos_bucket.get("name", "")
        object_key = cos_object.get("key", "")
        object_size = cos_object.get("size", 0)
        
        logger.info(f"Processing COS object: {object_key} from bucket: {bucket_name}")
        
        # 检查是否是 PPTX 文件
        if object_key.lower().endswith(".pptx"):
            result = process_pptx_file(bucket_name, object_key, object_size)
            results.append(result)
        else:
            logger.info(f"Skipping non-PPTX file: {object_key}")
            results.append({
                "key": object_key,
                "status": "skipped",
                "reason": "Not a PPTX file"
            })
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "COS event processed",
            "results": results
        }, ensure_ascii=False)
    }


def handle_timer_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    处理定时触发器事件
    用于定期清理、统计等任务
    """
    trigger_name = event.get("TriggerName", "unknown")
    trigger_time = event.get("Time", "")
    
    logger.info(f"Timer triggered: {trigger_name} at {trigger_time}")
    
    # 执行定时任务
    # TODO: 实现具体的定时任务逻辑
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Timer event processed",
            "trigger": trigger_name,
            "time": trigger_time
        })
    }


def handle_api_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    处理 API 网关异步调用事件
    """
    body = event.get("body", "{}")
    if isinstance(body, str):
        body = json.loads(body)
    
    task_type = body.get("task_type", "unknown")
    task_data = body.get("data", {})
    
    logger.info(f"API async task: {task_type}")
    
    # 根据任务类型分发
    if task_type == "process_pptx":
        result = process_pptx_task(task_data)
    elif task_type == "generate_ppt":
        result = generate_ppt_task(task_data)
    elif task_type == "vectorize_document":
        result = vectorize_document_task(task_data)
    else:
        result = {"error": f"Unknown task type: {task_type}"}
    
    return {
        "statusCode": 200,
        "body": json.dumps(result, ensure_ascii=False)
    }


def handle_custom_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    处理自定义事件
    """
    task_type = event.get("task_type", "unknown")
    task_data = event.get("data", {})
    
    logger.info(f"Custom event task: {task_type}")
    
    # 根据任务类型分发
    if task_type == "process_pptx":
        result = process_pptx_task(task_data)
    elif task_type == "generate_ppt":
        result = generate_ppt_task(task_data)
    elif task_type == "vectorize_document":
        result = vectorize_document_task(task_data)
    else:
        result = {"status": "unknown_task", "task_type": task_type}
    
    return {
        "statusCode": 200,
        "body": json.dumps(result, ensure_ascii=False)
    }


# ============================================
# 任务处理函数
# ============================================

def process_pptx_file(bucket: str, key: str, size: int) -> Dict[str, Any]:
    """
    处理上传的 PPTX 文件
    - 解析 PPTX 内容
    - 提取文本和图片
    - 生成缩略图
    - 向量化存储
    """
    logger.info(f"Processing PPTX: {key}, size: {size}")
    
    # TODO: 实现具体的 PPTX 处理逻辑
    # 1. 从 COS 下载文件
    # 2. 解析 PPTX
    # 3. 提取内容
    # 4. 存储到数据库
    # 5. 向量化
    
    return {
        "key": key,
        "bucket": bucket,
        "size": size,
        "status": "processed"
    }


def process_pptx_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理 PPTX 任务
    """
    file_id = data.get("file_id")
    file_path = data.get("file_path")
    
    logger.info(f"Processing PPTX task: {file_id}")
    
    # TODO: 实现处理逻辑
    
    return {
        "file_id": file_id,
        "status": "completed"
    }


def generate_ppt_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成 PPT 任务
    """
    task_id = data.get("task_id")
    template_id = data.get("template_id")
    content = data.get("content", {})
    
    logger.info(f"Generating PPT: {task_id}")
    
    # TODO: 实现 PPT 生成逻辑
    
    return {
        "task_id": task_id,
        "status": "completed"
    }


def vectorize_document_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    文档向量化任务
    """
    document_id = data.get("document_id")
    
    logger.info(f"Vectorizing document: {document_id}")
    
    # TODO: 实现向量化逻辑
    
    return {
        "document_id": document_id,
        "status": "vectorized"
    }
