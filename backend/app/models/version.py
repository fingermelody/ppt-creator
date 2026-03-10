"""
版本历史管理模型
记录 PPT 的所有修改历史，支持版本回滚
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class VersionType(str, enum.Enum):
    """版本类型"""
    AUTO = "auto"           # 自动保存
    MANUAL = "manual"       # 手动保存
    EXPORT = "export"       # 导出时保存
    ROLLBACK = "rollback"   # 回滚创建


class VersionHistory(BaseModel):
    """版本历史表"""
    __tablename__ = "version_histories"
    
    # 所属精修任务
    task_id = Column(String(36), ForeignKey("refinement_tasks.id"), nullable=False, index=True)
    task = relationship("RefinementTask", backref="versions")
    
    # 版本信息
    version_number = Column(Integer, nullable=False)
    version_label = Column(String(50), nullable=False)  # v1, v2, ...
    
    # 版本类型
    version_type = Column(
        SQLEnum(VersionType),
        default=VersionType.AUTO,
        nullable=False
    )
    
    # 版本描述
    description = Column(Text, nullable=True)
    
    # 快照数据 - 存储当时所有页面的完整状态
    snapshot_data = Column(JSON, nullable=False)
    
    # 元数据
    page_count = Column(Integer, default=0, nullable=False)
    total_elements = Column(Integer, default=0, nullable=False)
    
    # 创建者
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    creator = relationship("User")
    
    # 大小（字节）
    snapshot_size = Column(Integer, default=0, nullable=False)


class VersionComparison(BaseModel):
    """版本比较记录表"""
    __tablename__ = "version_comparisons"
    
    # 比较的两个版本
    version_from_id = Column(String(36), ForeignKey("version_histories.id"), nullable=False, index=True)
    version_to_id = Column(String(36), ForeignKey("version_histories.id"), nullable=False, index=True)
    
    version_from = relationship("VersionHistory", foreign_keys=[version_from_id])
    version_to = relationship("VersionHistory", foreign_keys=[version_to_id])
    
    # 差异摘要
    diff_summary = Column(JSON, nullable=True)
    
    # 变更统计
    pages_added = Column(Integer, default=0, nullable=False)
    pages_removed = Column(Integer, default=0, nullable=False)
    pages_modified = Column(Integer, default=0, nullable=False)
    elements_added = Column(Integer, default=0, nullable=False)
    elements_removed = Column(Integer, default=0, nullable=False)
    elements_modified = Column(Integer, default=0, nullable=False)
