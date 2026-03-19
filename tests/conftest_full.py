"""
PPT-RSD 测试配置
pytest fixtures 和测试工具
"""

import os
import sys
import pytest
import tempfile
import shutil
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app
from app.db.base import Base
from app.db import get_db
from app.core.security import create_access_token


# ============================================
# 数据库 Fixtures
# ============================================

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库（内存 SQLite）"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db) -> Generator:
    """创建测试客户端"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


# ============================================
# 认证 Fixtures
# ============================================

@pytest.fixture
def test_user_id() -> str:
    """测试用户 ID"""
    return "test-user-001"


@pytest.fixture
def auth_headers(test_user_id: str) -> dict:
    """带认证的请求头"""
    token = create_access_token(data={"sub": test_user_id})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_auth_headers() -> dict:
    """模拟认证头（用于不需要真实认证的测试）"""
    return {"X-Test-User-Id": "test-user-001"}


# ============================================
# 文件 Fixtures
# ============================================

@pytest.fixture
def temp_upload_dir() -> Generator[str, None, None]:
    """临时上传目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pptx_file() -> bytes:
    """
    创建一个最小的有效 PPTX 文件用于测试
    注意：这是一个简化的 PPTX 结构
    """
    from io import BytesIO
    import zipfile
    
    buffer = BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # [Content_Types].xml
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
</Types>'''
        zf.writestr('[Content_Types].xml', content_types)
        
        # _rels/.rels
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels)
        
        # ppt/presentation.xml
        presentation = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" 
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId2"/>
  </p:sldIdLst>
</p:presentation>'''
        zf.writestr('ppt/presentation.xml', presentation)
        
        # ppt/_rels/presentation.xml.rels
        ppt_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>'''
        zf.writestr('ppt/_rels/presentation.xml.rels', ppt_rels)
        
        # ppt/slides/slide1.xml
        slide1 = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr/>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="2" name="Title"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:rPr lang="zh-CN"/>
              <a:t>测试 PPT 标题</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>'''
        zf.writestr('ppt/slides/slide1.xml', slide1)
    
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def large_sample_pptx(sample_pptx_file) -> bytes:
    """大文件 PPTX（用于分片上传测试）"""
    # 扩展到 > 5MB
    return sample_pptx_file + b'\x00' * (6 * 1024 * 1024)


# ============================================
# 数据 Fixtures
# ============================================

@pytest.fixture
def sample_document(test_db, test_user_id):
    """创建示例文档"""
    from app.models import Document, DocumentStatus
    import uuid
    
    doc = Document(
        id=str(uuid.uuid4()),
        owner_id=test_user_id,
        filename="test_doc.pptx",
        original_filename="测试文档.pptx",
        file_size=1024000,
        page_count=5,
        status=DocumentStatus.ready,
        storage_path="/data/uploads/test_doc.pptx"
    )
    test_db.add(doc)
    test_db.commit()
    test_db.refresh(doc)
    return doc


@pytest.fixture
def sample_slides(test_db, sample_document):
    """创建示例页面"""
    from app.models import Slide
    import uuid
    
    slides = []
    for i in range(1, 6):
        slide = Slide(
            id=str(uuid.uuid4()),
            document_id=sample_document.id,
            page_number=i,
            title=f"第 {i} 页标题",
            content_text=f"这是第 {i} 页的内容，包含测试文本。关键词：演示、测试、PPT",
            layout_type="title_and_content",
            thumbnail_path=f"/data/thumbnails/{sample_document.id}/slide_{i}.png"
        )
        slides.append(slide)
        test_db.add(slide)
    
    test_db.commit()
    return slides


@pytest.fixture
def sample_outline(test_db, test_user_id):
    """创建示例大纲"""
    from app.models import Outline, OutlineSection
    import uuid
    
    outline = Outline(
        id=str(uuid.uuid4()),
        owner_id=test_user_id,
        title="测试演示大纲",
        description="用于测试的 PPT 大纲"
    )
    test_db.add(outline)
    
    sections = []
    for i in range(1, 4):
        section = OutlineSection(
            id=str(uuid.uuid4()),
            outline_id=outline.id,
            order=i,
            title=f"第 {i} 章",
            description=f"第 {i} 章的描述内容",
            content_hint=f"关键词{i}"
        )
        sections.append(section)
        test_db.add(section)
    
    test_db.commit()
    test_db.refresh(outline)
    
    return {"outline": outline, "sections": sections}
