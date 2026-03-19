"""
腾讯云 ADP 智能文档解析服务
使用 ReconstructDocumentSSE API 解析 PPT 文件，提取每页内容
"""

import os
import re
import json
import logging
import tempfile
import zipfile
import requests
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class SlideContentADP:
    """ADP 解析结果的页面内容数据类"""
    def __init__(
        self,
        page_number: int,
        title: Optional[str] = None,
        content_text: str = "",
        markdown_text: str = "",
        layout_type: Optional[str] = None,
        elements: Optional[List[Dict]] = None,
        images: Optional[List[str]] = None,
    ):
        self.page_number = page_number
        self.title = title
        self.content_text = content_text
        self.markdown_text = markdown_text
        self.layout_type = layout_type
        self.elements = elements or []
        self.images = images or []


class ADPDocumentParser:
    """
    腾讯云 ADP 智能文档解析器
    
    使用 lkeap API (ReconstructDocumentSSE) 解析 PPT 文件。
    通过 COS URL 传入文件，返回结构化的每页内容。
    """
    
    def __init__(self):
        from app.core.config import settings
        
        self.enabled = False
        self.secret_id = settings.TENCENT_SECRET_ID or settings.COS_SECRET_ID
        self.secret_key = settings.TENCENT_SECRET_KEY or settings.COS_SECRET_KEY
        self.region = settings.ADP_REGION or settings.TENCENT_REGION or "ap-guangzhou"
        
        if settings.ADP_ENABLED and self.secret_id and self.secret_key:
            try:
                from tencentcloud.common import credential
                from tencentcloud.common.profile.client_profile import ClientProfile
                from tencentcloud.common.profile.http_profile import HttpProfile
                from tencentcloud.lkeap.v20240522 import lkeap_client
                
                cred = credential.Credential(self.secret_id, self.secret_key)
                
                http_profile = HttpProfile()
                http_profile.endpoint = "lkeap.tencentcloudapi.com"
                
                client_profile = ClientProfile()
                client_profile.httpProfile = http_profile
                
                self.client = lkeap_client.LkeapClient(cred, self.region, client_profile)
                self.enabled = True
                logger.info(f"ADP 文档解析服务初始化成功，区域: {self.region}")
            except ImportError:
                logger.warning("tencentcloud-sdk-python-lkeap 未安装，ADP 解析不可用")
            except Exception as e:
                logger.error(f"ADP 服务初始化失败: {e}")
        else:
            missing = []
            if not settings.ADP_ENABLED:
                missing.append("ADP_ENABLED=false")
            if not self.secret_id:
                missing.append("TENCENT_SECRET_ID")
            if not self.secret_key:
                missing.append("TENCENT_SECRET_KEY")
            logger.warning(f"ADP 配置不完整，缺少: {', '.join(missing)}")
    
    def parse_ppt(
        self,
        cos_url: str,
        file_type: str = "PPTX",
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> List[SlideContentADP]:
        """
        使用 ADP 解析 PPT 文件
        
        Args:
            cos_url: PPT 文件的 COS 访问 URL
            file_type: 文件类型（PPTX, PPT）
            start_page: 起始页码（可选）
            end_page: 结束页码（可选）
            
        Returns:
            SlideContentADP 列表
        """
        if not self.enabled:
            raise RuntimeError("ADP 文档解析服务未启用")
        
        from tencentcloud.lkeap.v20240522 import models
        
        logger.info(f"开始 ADP 解析: {cos_url}, 类型: {file_type}")
        
        req = models.ReconstructDocumentSSERequest()
        req.FileType = file_type.upper()
        req.FileUrl = cos_url
        
        if start_page is not None:
            req.FileStartPageNumber = start_page
        if end_page is not None:
            req.FileEndPageNumber = end_page
        
        # 调用 SSE 流式接口
        result_url = None
        success_pages = 0
        failed_pages = []
        
        try:
            resp = self.client.ReconstructDocumentSSE(req)
            
            # 处理 SSE 流式响应
            for event in resp:
                logger.debug(
                    f"ADP 进度: {event.Progress}% - {event.ProgressMessage}"
                )
                
                if event.ResponseType == "TASK_RSP":
                    result_url = event.DocumentRecognizeResultUrl
                    success_pages = event.SuccessPageNum or 0
                    failed_pages = event.FailedPages or []
                    logger.info(
                        f"ADP 解析完成: 成功 {success_pages} 页, "
                        f"失败 {len(failed_pages)} 页"
                    )
                    break
            
        except Exception as e:
            logger.error(f"ADP API 调用失败: {e}")
            raise
        
        if not result_url:
            raise RuntimeError("ADP 解析未返回结果 URL")
        
        # 下载并解析结果 ZIP
        slides = self._download_and_parse_result(result_url, failed_pages)
        
        logger.info(f"ADP 解析结果: 共提取 {len(slides)} 页内容")
        return slides
    
    def _download_and_parse_result(
        self,
        result_url: str,
        failed_pages: List[int],
    ) -> List[SlideContentADP]:
        """
        下载 ADP 结果 ZIP 并解析内容
        
        Args:
            result_url: 结果下载 URL
            failed_pages: 失败的页码列表
            
        Returns:
            SlideContentADP 列表
        """
        slides = []
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 下载 ZIP 文件
            zip_path = os.path.join(tmp_dir, "result.zip")
            logger.info(f"下载 ADP 结果: {result_url[:100]}...")
            
            resp = requests.get(result_url, timeout=120)
            resp.raise_for_status()
            
            with open(zip_path, "wb") as f:
                f.write(resp.content)
            
            # 解压
            extract_dir = os.path.join(tmp_dir, "extracted")
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)
            
            # 查找 markdown 文件
            md_files = list(Path(extract_dir).rglob("*.md"))
            json_files = list(Path(extract_dir).rglob("*.json"))
            
            logger.info(
                f"ADP 结果: {len(md_files)} 个 .md 文件, "
                f"{len(json_files)} 个 .json 文件"
            )
            
            # 解析 Markdown 内容（按页分割）
            if md_files:
                md_content = md_files[0].read_text(encoding="utf-8")
                slides = self._parse_markdown_by_pages(md_content)
            
            # 尝试从 JSON 补充结构化信息
            if json_files:
                try:
                    json_content = json.loads(
                        json_files[0].read_text(encoding="utf-8")
                    )
                    self._enrich_from_json(slides, json_content)
                except Exception as e:
                    logger.debug(f"解析 JSON 结果时出错: {e}")
        
        return slides
    
    def _parse_markdown_by_pages(
        self, md_content: str
    ) -> List[SlideContentADP]:
        """
        按页分割 Markdown 内容
        
        ADP 输出的 Markdown 通常以 --- 或 # 标题 分割页面。
        对于 PPT，每页通常以一级标题或分隔符开始。
        
        Args:
            md_content: 完整的 Markdown 文本
            
        Returns:
            SlideContentADP 列表
        """
        slides = []
        
        # 按分页符分割（ADP 通常用 --- 或 \n---\n 分割页面）
        # 也尝试按一级标题分割
        page_sections = re.split(r'\n---+\n|\n(?=# [^\n]+\n)', md_content.strip())
        
        # 如果无法有效分割，将整个内容作为一页
        if len(page_sections) <= 1 and md_content.strip():
            page_sections = [md_content.strip()]
        
        for i, section in enumerate(page_sections):
            section = section.strip()
            if not section:
                continue
            
            page_number = i + 1
            
            # 提取标题（第一个 # 标题或第一行）
            title = self._extract_title_from_markdown(section)
            
            # 提取纯文本内容（去除 Markdown 格式）
            content_text = self._markdown_to_plain_text(section)
            
            slides.append(SlideContentADP(
                page_number=page_number,
                title=title,
                content_text=content_text,
                markdown_text=section,
                layout_type="adp_parsed",
            ))
        
        return slides
    
    def _extract_title_from_markdown(self, section: str) -> Optional[str]:
        """从 Markdown 段落提取标题"""
        lines = section.strip().split("\n")
        for line in lines:
            line = line.strip()
            # 匹配 Markdown 标题
            match = re.match(r'^#{1,3}\s+(.+)$', line)
            if match:
                return match.group(1).strip()
        
        # 如果没有标题，取第一行非空文本
        for line in lines:
            line = line.strip()
            if line and not line.startswith("!") and not line.startswith("---"):
                text = re.sub(r'[#*_`\[\]]', '', line).strip()
                if text and len(text) < 100:
                    return text
        
        return None
    
    def _markdown_to_plain_text(self, md_text: str) -> str:
        """将 Markdown 转为纯文本"""
        text = md_text
        # 移除图片标记
        text = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', r'\1', text)
        # 移除链接，保留文本
        text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
        # 移除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 移除加粗、斜体
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # 移除代码块标记
        text = re.sub(r'```[^\n]*\n', '', text)
        text = re.sub(r'```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 移除分隔符
        text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
        # 移除多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _enrich_from_json(
        self,
        slides: List[SlideContentADP],
        json_data: Any,
    ):
        """从 JSON 结果补充结构化信息"""
        try:
            if isinstance(json_data, dict):
                pages = json_data.get("pages", [])
                for page_data in pages:
                    page_num = page_data.get("page_number", 0)
                    for slide in slides:
                        if slide.page_number == page_num:
                            # 补充元素信息
                            if "elements" in page_data:
                                slide.elements = page_data["elements"]
                            if "layout" in page_data:
                                slide.layout_type = page_data["layout"]
                            break
        except Exception as e:
            logger.debug(f"补充 JSON 信息时出错: {e}")


# 全局单例（延迟初始化）
_adp_parser: Optional[ADPDocumentParser] = None


def get_adp_parser() -> ADPDocumentParser:
    """获取 ADP 解析器单例"""
    global _adp_parser
    if _adp_parser is None:
        _adp_parser = ADPDocumentParser()
    return _adp_parser
