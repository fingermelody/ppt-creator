"""
数据库迁移脚本：添加 COS 存储和向量化相关字段

运行方式：
cd backend && python scripts/migrate_add_cos_fields.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db import engine


def migrate():
    """执行迁移"""
    
    migrations = [
        # Document 表新增字段
        ("ALTER TABLE documents ADD COLUMN cos_object_key VARCHAR(500)", "documents.cos_object_key"),
        ("ALTER TABLE documents ADD COLUMN cos_url VARCHAR(1000)", "documents.cos_url"),
        ("ALTER TABLE documents ADD COLUMN vectorized_pages INTEGER DEFAULT 0", "documents.vectorized_pages"),
        
        # Slide 表新增字段
        ("ALTER TABLE slides ADD COLUMN thumbnail_cos_key VARCHAR(500)", "slides.thumbnail_cos_key"),
        ("ALTER TABLE slides ADD COLUMN thumbnail_url VARCHAR(1000)", "slides.thumbnail_url"),
        ("ALTER TABLE slides ADD COLUMN is_vectorized INTEGER DEFAULT 0", "slides.is_vectorized"),
        
        # 修改 documents.file_path 为可空
        # SQLite 不支持直接修改列，跳过
    ]
    
    # 添加新的状态值（如果使用的是 SQLite，枚举类型是字符串，无需修改）
    # PostgreSQL 需要添加新的枚举值
    postgres_enum_migrations = [
        "ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'processing'",
    ]
    
    with engine.connect() as conn:
        for sql, field_name in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✓ 添加字段成功: {field_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"- 字段已存在，跳过: {field_name}")
                else:
                    print(f"✗ 添加字段失败: {field_name}, 错误: {e}")
        
        # 尝试 PostgreSQL 枚举迁移
        for sql in postgres_enum_migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✓ 枚举值添加成功")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print(f"- 非 PostgreSQL 数据库，跳过枚举迁移")
                elif "already exists" in str(e).lower():
                    print(f"- 枚举值已存在，跳过")
                else:
                    print(f"- 枚举迁移跳过: {e}")
    
    print("\n迁移完成！")


if __name__ == "__main__":
    print("开始数据库迁移...\n")
    migrate()
