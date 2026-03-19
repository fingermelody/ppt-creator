"""
重新向量化已有文档脚本

为已上传的文档重新进行向量化，补充源 PPT 地址信息（source_url, source_filename）。
这是为了让已有文档也能支持基于向量搜索的 PPT 组装功能。

使用方法：
    cd backend
    python scripts/revectorize_documents.py

可选参数：
    --document-id: 只处理指定的文档
    --force: 强制重新向量化（即使已向量化）
"""

import sys
import os
import argparse
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models import Document, Slide, DocumentStatus
from app.services.vectorization import get_vectorization_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def revectorize_document(db, document: Document, force: bool = False):
    """
    重新向量化单个文档的所有页面
    
    Args:
        db: 数据库会话
        document: 文档对象
        force: 是否强制重新向量化
    """
    vectorization_service = get_vectorization_service()
    
    if not vectorization_service.enabled:
        logger.error("向量化服务未启用")
        return False
    
    # 获取文档的所有页面
    slides = db.query(Slide).filter(Slide.document_id == document.id).order_by(Slide.page_number).all()
    
    if not slides:
        logger.warning(f"文档 {document.id} ({document.original_filename}) 没有页面")
        return True
    
    logger.info(f"开始处理文档: {document.original_filename} ({document.id})")
    logger.info(f"  - 页数: {len(slides)}")
    logger.info(f"  - COS URL: {document.cos_url}")
    
    vectorized_count = 0
    skipped_count = 0
    error_count = 0
    
    for slide in slides:
        # 如果已向量化且不强制，则跳过
        if slide.is_vectorized and slide.vector_id and not force:
            # 检查是否需要更新元数据（添加 source_url）
            # 注：删除后重新添加向量
            logger.debug(f"  页面 {slide.page_number} 已向量化，将更新元数据")
        
        if not slide.content_text:
            logger.debug(f"  页面 {slide.page_number} 内容为空，跳过")
            skipped_count += 1
            continue
        
        try:
            # 如果已有向量，先删除
            if slide.vector_id:
                try:
                    vectorization_service._vector_client.delete([slide.vector_id])
                except Exception as e:
                    logger.warning(f"  删除旧向量失败: {e}")
            
            # 重新向量化，包含源 PPT 信息
            vector_id = vectorization_service.vectorize_slide(
                slide_id=slide.id,
                document_id=document.id,
                page_number=slide.page_number,
                content_text=slide.content_text,
                title=slide.title,
                source_url=document.cos_url,  # 添加源 PPT URL
                source_filename=document.original_filename  # 添加源 PPT 文件名
            )
            
            if vector_id:
                slide.vector_id = vector_id
                slide.is_vectorized = 1
                vectorized_count += 1
                logger.info(f"  ✓ 页面 {slide.page_number}: {slide.title or '(无标题)'}")
            else:
                error_count += 1
                logger.warning(f"  ✗ 页面 {slide.page_number} 向量化失败")
                
        except Exception as e:
            error_count += 1
            logger.error(f"  ✗ 页面 {slide.page_number} 处理异常: {e}")
    
    # 更新文档的向量化页数
    document.vectorized_pages = vectorized_count
    db.commit()
    
    logger.info(f"文档 {document.original_filename} 处理完成:")
    logger.info(f"  - 成功: {vectorized_count}")
    logger.info(f"  - 跳过: {skipped_count}")
    logger.info(f"  - 失败: {error_count}")
    
    return error_count == 0


def main():
    parser = argparse.ArgumentParser(description='重新向量化已有文档')
    parser.add_argument('--document-id', type=str, help='只处理指定的文档 ID')
    parser.add_argument('--force', action='store_true', help='强制重新向量化')
    parser.add_argument('--status', type=str, default='ready', help='只处理指定状态的文档 (默认: ready)')
    args = parser.parse_args()
    
    db = SessionLocal()
    
    try:
        # 构建查询
        query = db.query(Document).filter(Document.is_deleted == False)
        
        if args.document_id:
            query = query.filter(Document.id == args.document_id)
        elif args.status:
            try:
                status = DocumentStatus(args.status)
                query = query.filter(Document.status == status)
            except ValueError:
                logger.error(f"无效的状态: {args.status}")
                return 1
        
        documents = query.all()
        
        if not documents:
            logger.info("没有找到需要处理的文档")
            return 0
        
        logger.info(f"找到 {len(documents)} 个文档需要处理")
        logger.info("=" * 60)
        
        success_count = 0
        fail_count = 0
        
        for document in documents:
            if revectorize_document(db, document, args.force):
                success_count += 1
            else:
                fail_count += 1
            logger.info("-" * 60)
        
        logger.info("=" * 60)
        logger.info(f"处理完成: 成功 {success_count} 个，失败 {fail_count} 个")
        
        return 0 if fail_count == 0 else 1
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
