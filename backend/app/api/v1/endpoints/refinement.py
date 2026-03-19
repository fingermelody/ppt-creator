"""
PPT 精修 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import uuid

from app.db import get_db
from app.core import get_current_user_id
from app.models import (
    RefinementTask, RefinedPage, PageModification, RefinementConversation,
    RefinementMessage, RefinementStatus, ModificationAction, Draft, DraftPage,
)
from app.schemas import (
    RefinementTaskDetailResponse, RefinedPageResponse, RefinedPageDetailResponse,
    CreateTaskRequest, CreateTaskResponse, SaveTaskResponse, ExportRefinedResponse,
    ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse,
    EditTextRequest, EditStyleRequest, MoveElementRequest, ResizeElementRequest,
    AddElementRequest, DuplicateElementRequest, ChangeOrderRequest,
    ElementOperationResponse, DeleteElementResponse, AddElementResponse,
    ModificationHistoryResponse, UndoRedoResponse, GoToStepRequest,
    SuggestionsResponse, QuickActionsResponse,
    BatchDeleteRequest, BatchDeleteResponse, BatchStyleRequest, BatchStyleResponse,
    AlignElementsRequest, AlignElementsResponse,
    RefinementTaskListItem, RefinementTaskListResponse,
)

router = APIRouter()


@router.get("/tasks", response_model=RefinementTaskListResponse, summary="获取精修任务列表")
async def get_tasks(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取当前用户的精修任务列表"""
    from sqlalchemy import func
    
    query = db.query(RefinementTask).filter(RefinementTask.owner_id == user_id)
    
    # 状态筛选
    if status:
        query = query.filter(RefinementTask.status == status)
    
    # 获取总数
    total = query.count()
    
    # 分页
    tasks = query.order_by(RefinementTask.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取每个任务的修改次数（通过 RefinedPage 关联）
    task_items = []
    for task in tasks:
        # 获取该任务所有页面的修改次数总和
        modification_count = db.query(func.count(PageModification.id)).join(
            RefinedPage, PageModification.page_id == RefinedPage.id
        ).filter(
            RefinedPage.task_id == task.id
        ).scalar() or 0
        
        task_items.append(RefinementTaskListItem(
            id=task.id,
            title=task.title,
            draft_id=task.draft_id,
            status=task.status,
            page_count=task.total_pages,
            modification_count=modification_count,
            created_at=task.created_at,
            updated_at=task.updated_at,
        ))
    
    return RefinementTaskListResponse(
        tasks=task_items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/tasks", response_model=CreateTaskResponse, summary="创建精修任务")
async def create_task(request: CreateTaskRequest, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    draft = db.query(Draft).filter(Draft.id == request.draft_id, Draft.owner_id == user_id, Draft.is_deleted == False).first()
    if not draft:
        raise HTTPException(status_code=404, detail="草稿不存在")
    
    # 获取草稿的页面
    from app.models.draft import DraftPage
    draft_pages = db.query(DraftPage).filter(DraftPage.draft_id == draft.id).order_by(DraftPage.order_index).all()
    
    # 创建精修任务
    task = RefinementTask(
        title=request.title or draft.title, 
        draft_id=request.draft_id, 
        total_pages=len(draft_pages) if draft_pages else draft.page_count, 
        owner_id=user_id
    )
    db.add(task)
    db.flush()  # 获取 task.id
    
    # 为每个草稿页面创建对应的精修页面
    for index, draft_page in enumerate(draft_pages):
        # 如果页面有关联章节，使用章节标题；否则使用页面标题
        page_title = draft_page.title
        if draft_page.section_id and draft_page.section:
            page_title = draft_page.section.title
        
        refined_page = RefinedPage(
            task_id=task.id,
            page_index=index,
            title=page_title,
            section_id=draft_page.section_id,  # 传递章节关联
            thumbnail_path=draft_page.thumbnail_path,
            content={},  # 初始内容为空
            elements=[],  # 初始元素为空
        )
        db.add(refined_page)
    
    # 如果没有草稿页面，创建占位页面
    if not draft_pages and draft.page_count > 0:
        for i in range(draft.page_count):
            refined_page = RefinedPage(
                task_id=task.id,
                page_index=i,
                title=f"页面 {i + 1}",
                content={},
                elements=[],
            )
            db.add(refined_page)
    
    db.commit()
    db.refresh(task)
    return CreateTaskResponse(task_id=task.id, total_pages=task.total_pages, created_at=task.created_at)


@router.get("/tasks/{task_id}", response_model=RefinementTaskDetailResponse, summary="获取任务详情")
async def get_task(task_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    task = db.query(RefinementTask).filter(RefinementTask.id == task_id, RefinementTask.owner_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    pages = db.query(RefinedPage).filter(RefinedPage.task_id == task_id).order_by(RefinedPage.page_index).all()
    response = RefinementTaskDetailResponse.model_validate(task)
    
    # 构建页面响应，包含章节标题
    page_responses = []
    for p in pages:
        page_dict = RefinedPageResponse.model_validate(p).model_dump()
        # 如果页面有关联章节，获取章节标题
        if p.section_id and p.section:
            page_dict['section_title'] = p.section.title
        page_responses.append(RefinedPageResponse(**page_dict))
    
    response.pages = page_responses
    return response


@router.post("/tasks/{task_id}/save", response_model=SaveTaskResponse)
async def save_task(task_id: str, title: Optional[str] = None, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    task = db.query(RefinementTask).filter(RefinementTask.id == task_id, RefinementTask.owner_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if title:
        task.title = title
    task.status = RefinementStatus.SAVED
    version_num = int(task.version[1:]) + 1 if task.version.startswith("v") else 2
    task.version = f"v{version_num}"
    db.commit()
    return SaveTaskResponse(success=True, saved_at=task.updated_at, version=task.version)


@router.post("/tasks/{task_id}/export", response_model=ExportRefinedResponse)
async def export_task(task_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    task = db.query(RefinementTask).filter(RefinementTask.id == task_id, RefinementTask.owner_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    from datetime import datetime
    task.status = RefinementStatus.EXPORTED
    db.commit()
    return ExportRefinedResponse(download_url=f"/api/downloads/refinement/{task_id}.pptx", file_size=0, exported_at=datetime.utcnow())


@router.get("/tasks/{task_id}/pages/{page_index}/content", response_model=RefinedPageDetailResponse)
async def get_page_content(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    page = db.query(RefinedPage).join(RefinementTask).filter(RefinedPage.task_id == task_id, RefinedPage.page_index == page_index, RefinementTask.owner_id == user_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    response = RefinedPageDetailResponse.model_validate(page)
    response.can_undo = page.history_step > 0
    response.can_redo = page.history_step < page.total_history_steps
    return response


@router.get("/tasks/{task_id}/pages/{page_index}/thumbnail")
async def get_page_thumbnail(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    page = db.query(RefinedPage).join(RefinementTask).filter(RefinedPage.task_id == task_id, RefinedPage.page_index == page_index, RefinementTask.owner_id == user_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    from datetime import datetime
    return {"image_url": page.thumbnail_path or "", "generated_at": datetime.utcnow().isoformat()}


@router.post("/tasks/{task_id}/pages/{page_index}/chat", response_model=ChatMessageResponse)
async def send_message(task_id: str, page_index: int, request: ChatMessageRequest, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return ChatMessageResponse(success=True, message_id=str(uuid.uuid4()), assistant_message="我理解了您的需求，正在处理中...", modification=None, updated_page=None)


@router.get("/tasks/{task_id}/pages/{page_index}/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return ChatHistoryResponse(conversation_id=str(uuid.uuid4()), messages=[])


@router.put("/tasks/{task_id}/pages/{page_index}/elements/{element_id}/text", response_model=ElementOperationResponse)
async def edit_text(task_id: str, page_index: int, element_id: str, request: EditTextRequest, user_id: str = Depends(get_current_user_id)):
    return ElementOperationResponse(success=True, modification_id=str(uuid.uuid4()), updated_element={"id": element_id, "text": request.text})


@router.put("/tasks/{task_id}/pages/{page_index}/elements/{element_id}/style", response_model=ElementOperationResponse)
async def edit_style(task_id: str, page_index: int, element_id: str, request: EditStyleRequest, user_id: str = Depends(get_current_user_id)):
    return ElementOperationResponse(success=True, modification_id=str(uuid.uuid4()), updated_element=None)


@router.put("/tasks/{task_id}/pages/{page_index}/elements/{element_id}/position", response_model=ElementOperationResponse)
async def move_element(task_id: str, page_index: int, element_id: str, request: MoveElementRequest, user_id: str = Depends(get_current_user_id)):
    return ElementOperationResponse(success=True, modification_id=str(uuid.uuid4()), updated_element=None)


@router.put("/tasks/{task_id}/pages/{page_index}/elements/{element_id}/size", response_model=ElementOperationResponse)
async def resize_element(task_id: str, page_index: int, element_id: str, request: ResizeElementRequest, user_id: str = Depends(get_current_user_id)):
    return ElementOperationResponse(success=True, modification_id=str(uuid.uuid4()), updated_element=None)


@router.delete("/tasks/{task_id}/pages/{page_index}/elements/{element_id}", response_model=DeleteElementResponse)
async def delete_element(task_id: str, page_index: int, element_id: str, user_id: str = Depends(get_current_user_id)):
    return DeleteElementResponse(success=True, modification_id=str(uuid.uuid4()))


@router.post("/tasks/{task_id}/pages/{page_index}/elements", response_model=AddElementResponse)
async def add_element(task_id: str, page_index: int, request: AddElementRequest, user_id: str = Depends(get_current_user_id)):
    element_id = str(uuid.uuid4())
    return AddElementResponse(success=True, element_id=element_id, modification_id=str(uuid.uuid4()), created_element={"id": element_id})


@router.post("/tasks/{task_id}/pages/{page_index}/elements/{element_id}/duplicate", response_model=AddElementResponse)
async def duplicate_element(task_id: str, page_index: int, element_id: str, request: DuplicateElementRequest, user_id: str = Depends(get_current_user_id)):
    new_id = str(uuid.uuid4())
    return AddElementResponse(success=True, element_id=new_id, modification_id=str(uuid.uuid4()), created_element={"id": new_id})


@router.put("/tasks/{task_id}/pages/{page_index}/elements/{element_id}/order", response_model=ElementOperationResponse)
async def change_element_order(task_id: str, page_index: int, element_id: str, request: ChangeOrderRequest, user_id: str = Depends(get_current_user_id)):
    return ElementOperationResponse(success=True, modification_id=str(uuid.uuid4()), updated_element=None)


@router.get("/tasks/{task_id}/pages/{page_index}/history", response_model=ModificationHistoryResponse)
async def get_history(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id)):
    return ModificationHistoryResponse(history=[], current_step=0, total_steps=0, can_undo=False, can_redo=False)


@router.post("/tasks/{task_id}/pages/{page_index}/undo", response_model=UndoRedoResponse)
async def undo(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    page = db.query(RefinedPage).join(RefinementTask).filter(RefinedPage.task_id == task_id, RefinedPage.page_index == page_index, RefinementTask.owner_id == user_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    response = RefinedPageDetailResponse.model_validate(page)
    return UndoRedoResponse(success=True, current_step=0, total_steps=0, updated_page=response, can_undo=False, can_redo=False)


@router.post("/tasks/{task_id}/pages/{page_index}/redo", response_model=UndoRedoResponse)
async def redo(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    page = db.query(RefinedPage).join(RefinementTask).filter(RefinedPage.task_id == task_id, RefinedPage.page_index == page_index, RefinementTask.owner_id == user_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    response = RefinedPageDetailResponse.model_validate(page)
    return UndoRedoResponse(success=True, current_step=0, total_steps=0, updated_page=response, can_undo=False, can_redo=False)


@router.post("/tasks/{task_id}/pages/{page_index}/history/goto", response_model=UndoRedoResponse)
async def goto_step(task_id: str, page_index: int, request: GoToStepRequest, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    page = db.query(RefinedPage).join(RefinementTask).filter(RefinedPage.task_id == task_id, RefinedPage.page_index == page_index, RefinementTask.owner_id == user_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    response = RefinedPageDetailResponse.model_validate(page)
    return UndoRedoResponse(success=True, current_step=request.step, total_steps=0, updated_page=response, can_undo=request.step > 0, can_redo=False)


@router.delete("/tasks/{task_id}/pages/{page_index}/history")
async def clear_history(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id)):
    return {"success": True}


@router.get("/tasks/{task_id}/pages/{page_index}/suggestions", response_model=SuggestionsResponse)
async def get_suggestions(task_id: str, page_index: int, user_id: str = Depends(get_current_user_id)):
    return SuggestionsResponse(suggestions=[])


@router.get("/tasks/{task_id}/pages/{page_index}/quick-actions", response_model=QuickActionsResponse)
async def get_quick_actions(task_id: str, page_index: int, selected_element: Optional[str] = None, user_id: str = Depends(get_current_user_id)):
    return QuickActionsResponse(actions=[])


@router.post("/tasks/{task_id}/pages/{page_index}/elements/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete(task_id: str, page_index: int, request: BatchDeleteRequest, user_id: str = Depends(get_current_user_id)):
    return BatchDeleteResponse(success=True, modification_id=str(uuid.uuid4()), deleted_count=len(request.element_ids))


@router.put("/tasks/{task_id}/pages/{page_index}/elements/batch-style", response_model=BatchStyleResponse)
async def batch_style(task_id: str, page_index: int, request: BatchStyleRequest, user_id: str = Depends(get_current_user_id)):
    return BatchStyleResponse(success=True, modification_id=str(uuid.uuid4()), updated_count=len(request.element_ids))


@router.post("/tasks/{task_id}/pages/{page_index}/elements/align", response_model=AlignElementsResponse)
async def align_elements(task_id: str, page_index: int, request: AlignElementsRequest, user_id: str = Depends(get_current_user_id)):
    return AlignElementsResponse(success=True, modification_id=str(uuid.uuid4()), updated_elements=[])


@router.get("/tasks/{task_id}/pages/{page_index}/chat/stream")
async def stream_chat(task_id: str, page_index: int, message: str, selected_element: Optional[str] = None, token: Optional[str] = None):
    async def event_generator():
        yield f"data: {json.dumps({'type': 'thinking', 'payload': {}})}\n\n"
        yield f"data: {json.dumps({'type': 'delta', 'payload': {'text': '正在分析您的需求...'}})}\\n\\n"
        yield f"data: {json.dumps({'type': 'complete', 'payload': {'message_id': str(uuid.uuid4()), 'assistant_message': '已完成处理'}})}\\n\\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})
