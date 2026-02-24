"""
简化的测试配置
用于运行不依赖完整后端的基础测试
"""

import pytest
import tempfile
import shutil
from typing import Generator


@pytest.fixture(scope="function")
def temp_upload_dir() -> Generator[str, None, None]:
    """临时上传目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_pptx_file() -> bytes:
    """创建一个最小的有效 PPTX 文件用于测试"""
    from io import BytesIO
    import zipfile
    
    buffer = BytesIO()
    
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
</Types>'''
        zf.writestr('[Content_Types].xml', content_types)
        
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels)
        
        presentation = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
</p:presentation>'''
        zf.writestr('ppt/presentation.xml', presentation)
    
    buffer.seek(0)
    return buffer.read()
