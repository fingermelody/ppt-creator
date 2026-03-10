"""
版本历史管理服务
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.version import VersionHistory, VersionComparison, VersionType
from app.models.refinement import RefinementTask, RefinedPage


class VersionService:
    """版本历史管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_version(
        self,
        task_id: str,
        user_id: str,
        description: Optional[str] = None,
        version_type: VersionType = VersionType.MANUAL
    ) -> VersionHistory:
        """
        创建新版本
        
        Args:
            task_id: 精修任务ID
            user_id: 用户ID
            description: 版本描述
            version_type: 版本类型
        
        Returns:
            新创建的版本记录
        """
        # 获取任务
        task = self.db.query(RefinementTask).filter(RefinementTask.id == task_id).first()
        if not task:
            raise ValueError("任务不存在")
        
        # 获取当前最大版本号
        max_version = self.db.query(VersionHistory).filter(
            VersionHistory.task_id == task_id
        ).order_by(VersionHistory.version_number.desc()).first()
        
        new_version_number = (max_version.version_number + 1) if max_version else 1
        
        # 获取所有页面的当前状态作为快照
        pages = self.db.query(RefinedPage).filter(
            RefinedPage.task_id == task_id
        ).order_by(RefinedPage.page_index).all()
        
        snapshot_data = {
            "task_info": {
                "title": task.title,
                "status": task.status.value if task.status else None,
                "total_pages": task.total_pages,
            },
            "pages": [
                {
                    "page_index": page.page_index,
                    "title": page.title,
                    "content": page.content,
                    "elements": page.elements,
                    "section_id": page.section_id,
                    "thumbnail_path": page.thumbnail_path,
                }
                for page in pages
            ]
        }
        
        # 计算快照大小和元素总数
        snapshot_json = json.dumps(snapshot_data, ensure_ascii=False)
        snapshot_size = len(snapshot_json.encode('utf-8'))
        total_elements = sum(
            len(page.elements) if page.elements else 0 
            for page in pages
        )
        
        # 创建版本记录
        version = VersionHistory(
            task_id=task_id,
            version_number=new_version_number,
            version_label=f"v{new_version_number}",
            version_type=version_type,
            description=description,
            snapshot_data=snapshot_data,
            page_count=len(pages),
            total_elements=total_elements,
            created_by=user_id,
            snapshot_size=snapshot_size,
        )
        
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        
        return version
    
    def get_versions(
        self,
        task_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[VersionHistory], int]:
        """
        获取任务的版本列表
        
        Args:
            task_id: 任务ID
            page: 页码
            page_size: 每页数量
        
        Returns:
            (版本列表, 总数)
        """
        query = self.db.query(VersionHistory).filter(
            VersionHistory.task_id == task_id
        )
        
        total = query.count()
        
        versions = query.order_by(
            VersionHistory.version_number.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return versions, total
    
    def get_version_detail(self, version_id: str) -> Optional[VersionHistory]:
        """获取版本详情"""
        return self.db.query(VersionHistory).filter(
            VersionHistory.id == version_id
        ).first()
    
    def rollback_to_version(
        self,
        task_id: str,
        version_id: str,
        user_id: str,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        回滚到指定版本
        
        Args:
            task_id: 任务ID
            version_id: 目标版本ID
            user_id: 用户ID
            create_backup: 是否创建当前状态的备份
        
        Returns:
            回滚结果
        """
        # 获取目标版本
        target_version = self.db.query(VersionHistory).filter(
            VersionHistory.id == version_id,
            VersionHistory.task_id == task_id
        ).first()
        
        if not target_version:
            raise ValueError("版本不存在")
        
        backup_version_id = None
        
        # 创建备份版本
        if create_backup:
            backup_version = self.create_version(
                task_id=task_id,
                user_id=user_id,
                description=f"回滚前的自动备份 (回滚到 {target_version.version_label})",
                version_type=VersionType.ROLLBACK
            )
            backup_version_id = backup_version.id
        
        # 恢复页面状态
        snapshot = target_version.snapshot_data
        pages_data = snapshot.get("pages", [])
        
        # 删除当前所有页面
        self.db.query(RefinedPage).filter(
            RefinedPage.task_id == task_id
        ).delete()
        
        # 重新创建页面
        for page_data in pages_data:
            page = RefinedPage(
                task_id=task_id,
                page_index=page_data.get("page_index", 0),
                title=page_data.get("title"),
                content=page_data.get("content"),
                elements=page_data.get("elements"),
                section_id=page_data.get("section_id"),
                thumbnail_path=page_data.get("thumbnail_path"),
            )
            self.db.add(page)
        
        # 更新任务信息
        task = self.db.query(RefinementTask).filter(
            RefinementTask.id == task_id
        ).first()
        
        if task:
            task_info = snapshot.get("task_info", {})
            task.total_pages = len(pages_data)
        
        self.db.commit()
        
        return {
            "success": True,
            "backup_version_id": backup_version_id,
            "restored_version_id": version_id,
            "restored_at": datetime.utcnow(),
            "pages_restored": len(pages_data),
        }
    
    def compare_versions(
        self,
        version_from_id: str,
        version_to_id: str
    ) -> Dict[str, Any]:
        """
        比较两个版本的差异
        
        Args:
            version_from_id: 起始版本ID
            version_to_id: 目标版本ID
        
        Returns:
            版本差异
        """
        version_from = self.db.query(VersionHistory).filter(
            VersionHistory.id == version_from_id
        ).first()
        
        version_to = self.db.query(VersionHistory).filter(
            VersionHistory.id == version_to_id
        ).first()
        
        if not version_from or not version_to:
            raise ValueError("版本不存在")
        
        pages_from = {
            p.get("page_index"): p 
            for p in version_from.snapshot_data.get("pages", [])
        }
        pages_to = {
            p.get("page_index"): p 
            for p in version_to.snapshot_data.get("pages", [])
        }
        
        page_diffs = []
        pages_added = 0
        pages_removed = 0
        pages_modified = 0
        elements_added = 0
        elements_removed = 0
        elements_modified = 0
        
        all_indices = set(pages_from.keys()) | set(pages_to.keys())
        
        for idx in sorted(all_indices):
            page_from = pages_from.get(idx)
            page_to = pages_to.get(idx)
            
            if page_from and not page_to:
                page_diffs.append({
                    "page_index": idx,
                    "status": "removed",
                    "changes": None
                })
                pages_removed += 1
                elements_removed += len(page_from.get("elements", []))
            elif not page_from and page_to:
                page_diffs.append({
                    "page_index": idx,
                    "status": "added",
                    "changes": None
                })
                pages_added += 1
                elements_added += len(page_to.get("elements", []))
            else:
                # 比较页面内容
                changes = self._compare_page_content(page_from, page_to)
                if changes:
                    page_diffs.append({
                        "page_index": idx,
                        "status": "modified",
                        "changes": changes
                    })
                    pages_modified += 1
                    # 简化的元素变更计算
                    elem_from = set(str(e) for e in page_from.get("elements", []))
                    elem_to = set(str(e) for e in page_to.get("elements", []))
                    elements_added += len(elem_to - elem_from)
                    elements_removed += len(elem_from - elem_to)
                else:
                    page_diffs.append({
                        "page_index": idx,
                        "status": "unchanged",
                        "changes": None
                    })
        
        return {
            "version_from": version_from,
            "version_to": version_to,
            "summary": {
                "pages_added": pages_added,
                "pages_removed": pages_removed,
                "pages_modified": pages_modified,
            },
            "page_diffs": page_diffs,
            "element_changes": {
                "added": elements_added,
                "removed": elements_removed,
                "modified": elements_modified,
            }
        }
    
    def _compare_page_content(
        self,
        page_from: Dict[str, Any],
        page_to: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """比较两个页面的内容差异"""
        changes = []
        
        # 比较标题
        if page_from.get("title") != page_to.get("title"):
            changes.append({
                "field": "title",
                "from": page_from.get("title"),
                "to": page_to.get("title")
            })
        
        # 比较内容
        if page_from.get("content") != page_to.get("content"):
            changes.append({
                "field": "content",
                "from": "...",
                "to": "..."
            })
        
        # 比较元素数量
        elem_from = page_from.get("elements", [])
        elem_to = page_to.get("elements", [])
        if len(elem_from) != len(elem_to):
            changes.append({
                "field": "elements_count",
                "from": len(elem_from),
                "to": len(elem_to)
            })
        
        return changes if changes else None
    
    def delete_version(self, version_id: str) -> bool:
        """删除版本"""
        version = self.db.query(VersionHistory).filter(
            VersionHistory.id == version_id
        ).first()
        
        if not version:
            return False
        
        self.db.delete(version)
        self.db.commit()
        return True
    
    def auto_save_version(
        self,
        task_id: str,
        user_id: str,
        max_auto_versions: int = 10
    ) -> Optional[VersionHistory]:
        """
        自动保存版本（带清理旧版本逻辑）
        
        Args:
            task_id: 任务ID
            user_id: 用户ID
            max_auto_versions: 保留的最大自动版本数
        
        Returns:
            新创建的版本（如果创建的话）
        """
        # 创建新的自动版本
        version = self.create_version(
            task_id=task_id,
            user_id=user_id,
            description="自动保存",
            version_type=VersionType.AUTO
        )
        
        # 清理旧的自动版本
        auto_versions = self.db.query(VersionHistory).filter(
            VersionHistory.task_id == task_id,
            VersionHistory.version_type == VersionType.AUTO
        ).order_by(VersionHistory.version_number.desc()).all()
        
        if len(auto_versions) > max_auto_versions:
            versions_to_delete = auto_versions[max_auto_versions:]
            for v in versions_to_delete:
                self.db.delete(v)
            self.db.commit()
        
        return version
