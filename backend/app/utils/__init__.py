"""
工具函数模块
"""

import hashlib
from typing import List


def calculate_md5(data: bytes) -> str:
    """计算 MD5 哈希"""
    return hashlib.md5(data).hexdigest()


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分割为指定大小的块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
