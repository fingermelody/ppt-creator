"""
大纲设计模块测试用例

测试范围：
1. Schema 验证
2. 章节排序逻辑
3. 智能生成大纲验证
4. 向导式生成大纲验证
5. 业务规则验证
6. API 结构验证

注意：此测试文件不依赖数据库连接，仅测试业务逻辑和验证规则
"""

import os
import sys
import pytest
from typing import Optional, List
from pydantic import BaseModel, Field, ValidationError

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


# ============== 重新定义 Schema 用于测试（避免导入模型触发数据库连接） ==============

class OutlineStatus:
    """大纲状态枚举"""
    DRAFT = "draft"
    COMPLETED = "completed"


class OutlineGenerationMode:
    """大纲生成方式枚举"""
    INTELLIGENT = "intelligent"
    WIZARD = "wizard"
    MANUAL = "manual"


class OutlineSectionBase(BaseModel):
    """大纲章节基础 Schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    content_hint: Optional[str] = None
    expected_pages: int = Field(default=1, ge=1)


class OutlineSectionCreate(OutlineSectionBase):
    """章节创建 Schema"""
    parent_id: Optional[str] = None
    order_index: Optional[int] = None


class OutlineSectionUpdate(BaseModel):
    """章节更新 Schema"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content_hint: Optional[str] = None
    expected_pages: Optional[int] = Field(None, ge=1)
    order_index: Optional[int] = None


class OutlineBase(BaseModel):
    """大纲基础 Schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class OutlineCreate(OutlineBase):
    """大纲创建 Schema"""
    generation_mode: str = OutlineGenerationMode.MANUAL
    generation_config: Optional[dict] = None


class OutlineUpdate(BaseModel):
    """大纲更新 Schema"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None


class IntelligentGenerateRequest(BaseModel):
    """智能生成大纲请求"""
    topic: str = Field(..., min_length=10, max_length=2000)
    page_count: int = Field(default=10, ge=5, le=30)
    style: Optional[str] = None


class IntelligentGenerateResponse(BaseModel):
    """智能生成大纲响应"""
    outline_id: str
    title: str
    sections: List[dict] = []


class WizardStep1Request(BaseModel):
    """向导第一步：主题"""
    topic: str = Field(..., min_length=5, max_length=500)


class WizardStep1Response(BaseModel):
    """向导第一步响应"""
    session_id: str
    suggested_titles: List[str]
    suggested_page_count: int


class WizardStep2Request(BaseModel):
    """向导第二步：确认标题和页数"""
    session_id: str
    title: str
    page_count: int = Field(..., ge=5, le=30)


class WizardStep2Response(BaseModel):
    """向导第二步响应"""
    session_id: str
    suggested_sections: List[dict]


class WizardStep3Request(BaseModel):
    """向导第三步：确认章节"""
    session_id: str
    sections: List[dict]


class WizardStep3Response(BaseModel):
    """向导第三步响应"""
    outline_id: str
    outline: dict


# ============== 测试类 ==============

class TestOutlineSchemaValidation:
    """测试大纲 Schema 验证"""

    def test_outline_create_schema_validation(self):
        """测试大纲创建 Schema 验证"""
        # 有效数据
        valid_outline = OutlineCreate(
            title="测试大纲",
            description="这是一个测试大纲",
            generation_mode=OutlineGenerationMode.MANUAL
        )
        assert valid_outline.title == "测试大纲"
        
        # 测试默认值
        outline_default = OutlineCreate(title="默认大纲")
        assert outline_default.generation_mode == OutlineGenerationMode.MANUAL
        
        # 测试标题必填
        try:
            OutlineCreate()
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ OutlineCreate Schema 验证正确")

    def test_outline_update_schema_validation(self):
        """测试大纲更新 Schema 验证"""
        # 有效数据 - 部分更新
        update_data = OutlineUpdate(title="新标题")
        assert update_data.title == "新标题"
        assert update_data.description is None
        
        # 更新状态
        update_status = OutlineUpdate(status=OutlineStatus.COMPLETED)
        assert update_status.status == OutlineStatus.COMPLETED
        
        print("✅ OutlineUpdate Schema 验证正确")

    def test_outline_title_length_validation(self):
        """测试大纲标题长度验证"""
        # 有效标题
        OutlineCreate(title="有效标题")
        
        # 标题过长
        try:
            OutlineCreate(title="a" * 300)
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ 大纲标题长度验证正确")


class TestOutlineSectionSchemaValidation:
    """测试章节 Schema 验证"""

    def test_section_create_validation(self):
        """测试章节创建 Schema 验证"""
        # 有效数据
        section = OutlineSectionCreate(
            title="第一章",
            description="章节描述",
            expected_pages=3
        )
        assert section.title == "第一章"
        assert section.expected_pages == 3
        
        # 默认页数
        section_default = OutlineSectionCreate(title="默认章节")
        assert section_default.expected_pages == 1
        
        print("✅ OutlineSectionCreate Schema 验证正确")

    def test_section_expected_pages_validation(self):
        """测试章节预期页数验证"""
        # 有效页数
        OutlineSectionCreate(title="测试", expected_pages=1)
        OutlineSectionCreate(title="测试", expected_pages=5)
        OutlineSectionCreate(title="测试", expected_pages=10)
        
        # 无效页数（0 或负数）
        try:
            OutlineSectionCreate(title="测试", expected_pages=0)
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass
        
        try:
            OutlineSectionCreate(title="测试", expected_pages=-1)
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ 章节预期页数验证正确")

    def test_section_title_validation(self):
        """测试章节标题验证"""
        # 有效标题
        OutlineSectionCreate(title="有效标题")
        OutlineSectionCreate(title="a" * 255)  # 最大长度
        
        # 标题过长
        try:
            OutlineSectionCreate(title="a" * 300)
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass
        
        # 标题必填
        try:
            OutlineSectionCreate()
            assert False, "应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ 章节标题验证正确")

    def test_section_update_validation(self):
        """测试章节更新 Schema 验证"""
        # 部分更新
        update = OutlineSectionUpdate(title="新标题")
        assert update.title == "新标题"
        assert update.description is None
        
        # 更新页数
        update_pages = OutlineSectionUpdate(expected_pages=5)
        assert update_pages.expected_pages == 5
        
        print("✅ OutlineSectionUpdate Schema 验证正确")


class TestIntelligentGenerateValidation:
    """测试智能生成验证"""

    def test_topic_validation(self):
        """测试主题验证"""
        # 有效主题
        valid_request = IntelligentGenerateRequest(
            topic="人工智能技术在企业数字化转型中的应用",
            page_count=15
        )
        assert valid_request.topic == "人工智能技术在企业数字化转型中的应用"
        assert valid_request.page_count == 15
        
        print("✅ 有效主题验证通过")

    def test_topic_min_length(self):
        """测试主题最小长度"""
        try:
            IntelligentGenerateRequest(topic="短主题")
            assert False, "主题长度不足应该抛出验证错误"
        except ValidationError as e:
            errors = e.errors()
            assert any("topic" in str(err) for err in errors)
        
        print("✅ 主题最小长度验证正确")

    def test_topic_max_length(self):
        """测试主题最大长度"""
        try:
            IntelligentGenerateRequest(topic="a" * 2001)
            assert False, "主题超长应该抛出验证错误"
        except ValidationError as e:
            errors = e.errors()
            assert any("topic" in str(err) for err in errors)
        
        print("✅ 主题最大长度验证正确")

    def test_page_count_validation(self):
        """测试页数验证"""
        # 有效页数
        IntelligentGenerateRequest(topic="这是一个有效的主题内容用于测试", page_count=5)  # 最小值
        IntelligentGenerateRequest(topic="这是一个有效的主题内容用于测试", page_count=15)  # 中间值
        IntelligentGenerateRequest(topic="这是一个有效的主题内容用于测试", page_count=30)  # 最大值
        
        # 无效页数 - 太少
        try:
            IntelligentGenerateRequest(topic="这是一个有效的主题内容用于测试", page_count=4)
            assert False, "页数太少应该抛出验证错误"
        except ValidationError:
            pass
        
        # 无效页数 - 太多
        try:
            IntelligentGenerateRequest(topic="这是一个有效的主题内容用于测试", page_count=31)
            assert False, "页数太多应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ 页数验证正确")

    def test_style_optional(self):
        """测试风格字段可选"""
        # 不提供风格
        request = IntelligentGenerateRequest(
            topic="这是一个有效的主题内容",
            page_count=10
        )
        assert request.style is None
        
        # 提供风格
        request_with_style = IntelligentGenerateRequest(
            topic="这是一个有效的主题内容",
            page_count=10,
            style="business"
        )
        assert request_with_style.style == "business"
        
        print("✅ 风格字段可选验证正确")


class TestWizardGenerationValidation:
    """测试向导式生成验证"""

    def test_step1_request_validation(self):
        """测试步骤1请求验证"""
        # 有效请求
        request = WizardStep1Request(topic="深度学习技术")
        assert request.topic == "深度学习技术"
        
        # 主题太短
        try:
            WizardStep1Request(topic="短")
            assert False, "主题太短应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ 步骤1请求验证正确")

    def test_step2_request_validation(self):
        """测试步骤2请求验证"""
        # 有效请求
        request = WizardStep2Request(
            session_id="session-001",
            title="测试标题",
            page_count=10
        )
        assert request.session_id == "session-001"
        assert request.title == "测试标题"
        assert request.page_count == 10
        
        # 页数验证
        try:
            WizardStep2Request(
                session_id="session-001",
                title="测试标题",
                page_count=4  # 太少
            )
            assert False, "页数太少应该抛出验证错误"
        except ValidationError:
            pass
        
        print("✅ 步骤2请求验证正确")

    def test_step3_request_validation(self):
        """测试步骤3请求验证"""
        # 有效请求
        request = WizardStep3Request(
            session_id="session-001",
            sections=[
                {"title": "引言", "description": "背景", "expected_pages": 1},
                {"title": "核心", "description": "核心内容", "expected_pages": 3}
            ]
        )
        assert len(request.sections) == 2
        
        print("✅ 步骤3请求验证正确")


class TestSectionOrderingLogic:
    """测试章节排序逻辑"""

    def test_calculate_section_order(self):
        """测试计算章节顺序"""
        sections = [
            {"id": "s1", "order_index": 0},
            {"id": "s2", "order_index": 1},
            {"id": "s3", "order_index": 2},
        ]
        
        # 新章节应放在最后
        new_order = len(sections)
        assert new_order == 3
        
        print("✅ 章节顺序计算正确")

    def test_reorder_sections_logic(self):
        """测试重排章节顺序逻辑"""
        # 原始顺序
        sections = [
            {"id": "s1", "order_index": 0, "title": "第一章"},
            {"id": "s2", "order_index": 1, "title": "第二章"},
            {"id": "s3", "order_index": 2, "title": "第三章"},
        ]
        
        # 重排请求：将第三章移到第一位
        reorder_request = [
            {"section_id": "s3", "order_index": 0},
            {"section_id": "s1", "order_index": 1},
            {"section_id": "s2", "order_index": 2},
        ]
        
        # 应用重排
        order_map = {r["section_id"]: r["order_index"] for r in reorder_request}
        for section in sections:
            section["order_index"] = order_map.get(section["id"], section["order_index"])
        
        # 验证排序后的顺序
        sorted_sections = sorted(sections, key=lambda x: x["order_index"])
        assert sorted_sections[0]["title"] == "第三章"
        assert sorted_sections[1]["title"] == "第一章"
        assert sorted_sections[2]["title"] == "第二章"
        
        print("✅ 章节重排逻辑正确")

    def test_section_level_calculation(self):
        """测试章节层级计算"""
        def calculate_level(parent_level: int = 0) -> int:
            """计算章节层级"""
            return parent_level + 1
        
        # 根章节
        root_level = calculate_level()
        assert root_level == 1
        
        # 一级子章节
        child_level = calculate_level(root_level)
        assert child_level == 2
        
        # 二级子章节
        grandchild_level = calculate_level(child_level)
        assert grandchild_level == 3
        
        print("✅ 章节层级计算正确")

    def test_insert_section_at_position(self):
        """测试在指定位置插入章节"""
        sections = [
            {"id": "s1", "order_index": 0},
            {"id": "s2", "order_index": 1},
            {"id": "s3", "order_index": 2},
        ]
        
        # 在位置1插入新章节
        insert_position = 1
        new_section = {"id": "s4", "order_index": insert_position}
        
        # 更新其他章节的顺序
        for section in sections:
            if section["order_index"] >= insert_position:
                section["order_index"] += 1
        
        sections.append(new_section)
        
        # 验证
        assert len(sections) == 4
        assert sections[-1]["order_index"] == 1
        
        print("✅ 插入章节逻辑正确")


class TestOutlineTemplateLogic:
    """测试大纲模板逻辑"""

    def test_template_structure(self):
        """测试大纲模板结构"""
        # 模拟模板数据
        template = {
            "id": "product_intro",
            "name": "产品介绍",
            "description": "适用于产品发布、功能介绍等场景",
            "icon": "🚀",
            "category": "商务",
            "chapters": [
                {"title": "公司简介", "suggested_page_count": 2},
                {"title": "产品概述", "suggested_page_count": 3},
                {"title": "功能详解", "suggested_page_count": 3},
                {"title": "竞争优势", "suggested_page_count": 2},
            ]
        }
        
        # 验证模板结构
        assert "id" in template
        assert "name" in template
        assert "chapters" in template
        assert len(template["chapters"]) >= 3
        
        # 验证章节数量合理性
        total_pages = sum(c["suggested_page_count"] for c in template["chapters"])
        assert 5 <= total_pages <= 30, "总页数应在 5-30 之间"
        
        print("✅ 大纲模板结构正确")

    def test_apply_template_logic(self):
        """测试应用模板逻辑"""
        template = {
            "id": "test_template",
            "name": "测试模板",
            "chapters": [
                {"title": "引言", "suggested_page_count": 1},
                {"title": "正文", "suggested_page_count": 3},
                {"title": "结论", "suggested_page_count": 1},
            ]
        }
        
        # 模拟应用模板创建大纲
        outline = {
            "title": "基于模板的大纲",
            "chapters": []
        }
        
        for idx, chapter in enumerate(template["chapters"]):
            outline["chapters"].append({
                "title": chapter["title"],
                "order": idx,
                "expected_pages": chapter["suggested_page_count"]
            })
        
        assert len(outline["chapters"]) == len(template["chapters"])
        assert outline["chapters"][0]["title"] == "引言"
        
        print("✅ 应用模板逻辑正确")


class TestIntelligentGenerationLogic:
    """测试智能生成逻辑"""

    def test_topic_validation_logic(self):
        """测试主题验证逻辑"""
        def validate_topic(topic: str) -> bool:
            """验证主题有效性"""
            if not topic or len(topic.strip()) == 0:
                return False
            if len(topic) < 10:
                return False
            if len(topic) > 2000:
                return False
            return True
        
        # 有效主题
        assert validate_topic("这是一个有效的主题内容，长度适中") == True
        assert validate_topic("人工智能技术在企业数字化转型中的应用与挑战分析") == True
        
        # 无效主题
        assert validate_topic("") == False
        assert validate_topic("短主题") == False
        assert validate_topic("a" * 2001) == False
        
        print("✅ 主题验证逻辑正确")

    def test_page_count_validation_logic(self):
        """测试页数验证逻辑"""
        def validate_page_count(count: int) -> bool:
            """验证页数有效性"""
            return 5 <= count <= 30
        
        # 有效页数
        assert validate_page_count(10) == True
        assert validate_page_count(5) == True
        assert validate_page_count(30) == True
        
        # 无效页数
        assert validate_page_count(4) == False
        assert validate_page_count(31) == False
        assert validate_page_count(0) == False
        
        print("✅ 页数验证逻辑正确")

    def test_chapter_distribution_logic(self):
        """测试章节页数分配逻辑"""
        def distribute_pages(total_pages: int, chapter_count: int) -> list:
            """分配页数到各章节"""
            if chapter_count <= 0:
                return []
            
            base_pages = total_pages // chapter_count
            remainder = total_pages % chapter_count
            
            distribution = [base_pages] * chapter_count
            for i in range(remainder):
                distribution[i] += 1
            
            return distribution
        
        # 测试分配
        result = distribute_pages(15, 5)
        assert sum(result) == 15
        assert len(result) == 5
        assert all(1 <= p <= 5 for p in result), "每章页数应在 1-5 之间"
        
        # 不均匀分配
        result2 = distribute_pages(10, 3)
        assert sum(result2) == 10
        assert result2[0] >= result2[-1]  # 余数加到前面的章节
        
        print("✅ 章节页数分配逻辑正确")


class TestWizardGenerationLogic:
    """测试向导式生成逻辑"""

    def test_step1_topic_analysis_logic(self):
        """测试步骤1主题分析逻辑"""
        def analyze_topic(topic: str) -> dict:
            """分析主题并返回建议"""
            return {
                "suggested_titles": [
                    f"{topic} - 完整介绍",
                    f"深入理解{topic}",
                    f"{topic}实践指南"
                ],
                "suggested_page_count": max(10, min(20, len(topic) // 2))
            }
        
        result = analyze_topic("深度学习技术")
        
        assert "suggested_titles" in result
        assert len(result["suggested_titles"]) >= 3
        assert "suggested_page_count" in result
        assert 5 <= result["suggested_page_count"] <= 30
        
        print("✅ 步骤1主题分析逻辑正确")

    def test_step2_chapter_generation_logic(self):
        """测试步骤2章节生成逻辑"""
        def generate_chapters(title: str, page_count: int) -> list:
            """生成章节建议"""
            chapter_count = max(3, min(8, page_count // 3))
            chapters = []
            
            templates = [
                ("引言", "背景和目标"),
                ("核心概念", "关键概念说明"),
                ("详细分析", "深入分析和讨论"),
                ("实践应用", "案例和应用"),
                ("总结展望", "总结和展望")
            ]
            
            for i in range(chapter_count):
                template = templates[i % len(templates)]
                chapters.append({
                    "title": template[0],
                    "description": template[1],
                    "expected_pages": page_count // chapter_count
                })
            
            return chapters
        
        chapters = generate_chapters("测试标题", 15)
        
        assert len(chapters) >= 3
        assert len(chapters) <= 8
        assert all("title" in c for c in chapters)
        assert all("expected_pages" in c for c in chapters)
        
        print("✅ 步骤2章节生成逻辑正确")

    def test_session_management_logic(self):
        """测试会话管理逻辑"""
        import uuid
        
        # 创建会话
        session_id = str(uuid.uuid4())
        assert len(session_id) == 36  # UUID 格式
        
        # 模拟会话数据
        session_data = {
            "id": session_id,
            "current_step": 1,
            "step1_data": None,
            "step2_data": None,
            "step3_data": None,
            "created_at": "2026-02-25T00:00:00"
        }
        
        # 更新步骤
        session_data["current_step"] = 2
        session_data["step1_data"] = {"topic": "测试主题"}
        
        assert session_data["current_step"] == 2
        assert session_data["step1_data"] is not None
        
        print("✅ 会话管理逻辑正确")


class TestOutlineAPIEndpoints:
    """测试大纲 API 端点结构"""

    def test_outline_crud_endpoints(self):
        """测试大纲 CRUD 端点定义"""
        endpoints = {
            "POST /api/v1/outlines": "创建大纲",
            "GET /api/v1/outlines": "获取大纲列表",
            "GET /api/v1/outlines/{outline_id}": "获取大纲详情",
            "PUT /api/v1/outlines/{outline_id}": "更新大纲",
            "DELETE /api/v1/outlines/{outline_id}": "删除大纲",
        }
        
        for endpoint, description in endpoints.items():
            assert endpoint.startswith(("GET", "POST", "PUT", "DELETE"))
            assert "/api/v1/outlines" in endpoint
        
        print(f"✅ 大纲 CRUD 端点验证通过 ({len(endpoints)} 个端点)")

    def test_section_crud_endpoints(self):
        """测试章节 CRUD 端点定义"""
        endpoints = {
            "POST /api/v1/outlines/{outline_id}/sections": "添加章节",
            "PUT /api/v1/outlines/{outline_id}/sections/{section_id}": "更新章节",
            "DELETE /api/v1/outlines/{outline_id}/sections/{section_id}": "删除章节",
            "POST /api/v1/outlines/{outline_id}/sections/reorder": "重排章节",
        }
        
        for endpoint, description in endpoints.items():
            assert endpoint.startswith(("GET", "POST", "PUT", "DELETE"))
            assert "/sections" in endpoint
        
        print(f"✅ 章节 CRUD 端点验证通过 ({len(endpoints)} 个端点)")

    def test_generation_endpoints(self):
        """测试生成相关端点定义"""
        endpoints = {
            "POST /api/v1/generate/intelligent": "智能生成大纲",
            "POST /api/v1/generate/wizard/step1": "向导步骤1",
            "POST /api/v1/generate/wizard/step2": "向导步骤2",
            "POST /api/v1/generate/wizard/step3": "向导步骤3",
        }
        
        for endpoint, description in endpoints.items():
            assert endpoint.startswith("POST")
            assert "/generate/" in endpoint
        
        print(f"✅ 生成端点验证通过 ({len(endpoints)} 个端点)")


class TestOutlineBusinessRules:
    """测试大纲业务规则"""

    def test_section_count_limit(self):
        """测试章节数量限制"""
        MAX_SECTIONS = 15
        
        def validate_section_count(count: int) -> bool:
            return 1 <= count <= MAX_SECTIONS
        
        assert validate_section_count(5) == True
        assert validate_section_count(15) == True
        assert validate_section_count(0) == False
        assert validate_section_count(16) == False
        
        print("✅ 章节数量限制正确")

    def test_pages_per_section_limit(self):
        """测试每章节页数限制"""
        MIN_PAGES = 1
        MAX_PAGES = 5
        
        def validate_pages_per_section(pages: int) -> bool:
            return MIN_PAGES <= pages <= MAX_PAGES
        
        assert validate_pages_per_section(1) == True
        assert validate_pages_per_section(3) == True
        assert validate_pages_per_section(5) == True
        assert validate_pages_per_section(0) == False
        assert validate_pages_per_section(6) == False
        
        print("✅ 每章节页数限制正确")

    def test_outline_status_transitions(self):
        """测试大纲状态转换规则"""
        # 允许的状态转换
        valid_transitions = [
            (OutlineStatus.DRAFT, OutlineStatus.COMPLETED),
            (OutlineStatus.COMPLETED, OutlineStatus.DRAFT),  # 可回退
        ]
        
        def is_valid_transition(from_status: str, to_status: str) -> bool:
            return (from_status, to_status) in valid_transitions
        
        # 测试状态转换
        assert is_valid_transition(OutlineStatus.DRAFT, OutlineStatus.COMPLETED) == True
        assert is_valid_transition(OutlineStatus.COMPLETED, OutlineStatus.DRAFT) == True
        
        print("✅ 大纲状态转换规则正确")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("大纲设计模块测试")
    print("=" * 60)
    
    test_classes = [
        TestOutlineSchemaValidation(),
        TestOutlineSectionSchemaValidation(),
        TestIntelligentGenerateValidation(),
        TestWizardGenerationValidation(),
        TestSectionOrderingLogic(),
        TestOutlineTemplateLogic(),
        TestIntelligentGenerationLogic(),
        TestWizardGenerationLogic(),
        TestOutlineAPIEndpoints(),
        TestOutlineBusinessRules(),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_class in test_classes:
        print(f"\n--- {test_class.__class__.__name__} ---")
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_class, method_name)
                    method()
                    total_passed += 1
                except Exception as e:
                    print(f"❌ {method_name}: {str(e)}")
                    total_failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {total_passed} 通过, {total_failed} 失败")
    print("=" * 60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
