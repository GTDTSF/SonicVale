from fastapi import APIRouter, Depends, HTTPException
from typing import List

from sqlalchemy.orm import Session

from app.core.response import Res
from app.db.database import get_db
from app.dto.section_dto import SectionCreateDTO, SectionResponseDTO, SectionRenameDTO, SectionUpdateDTO
from app.entity.section_entity import SectionEntity
from app.repositories.section_repository import SectionRepository
from app.services.section_service import SectionService

router = APIRouter(prefix="/sections", tags=["Sections"])


def get_section_service(db: Session = Depends(get_db)) -> SectionService:
    return SectionService(SectionRepository(db))


@router.post("", response_model=Res[SectionResponseDTO],
             summary="创建子分段",
             description="在章节下创建子分段")
def create_section(dto: SectionCreateDTO, service: SectionService = Depends(get_section_service)):
    try:
        entity = SectionEntity(**dto.__dict__)
        res = service.create_section(entity)
        if res:
            return Res(data=SectionResponseDTO(**res.__dict__), code=200, message="创建成功")
        else:
            return Res(data=None, code=400, message="分段已存在")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chapter/{chapter_id}", response_model=Res[List[SectionResponseDTO]],
            summary="查询章节下所有分段",
            description="根据章节ID查询所有子分段")
def get_all_sections(chapter_id: int, service: SectionService = Depends(get_section_service)):
    entities = service.get_all_sections(chapter_id)
    dtos = [SectionResponseDTO(**e.__dict__) for e in entities]
    return Res(data=dtos, code=200, message="查询成功")


@router.get("/{section_id}", response_model=Res[SectionResponseDTO],
            summary="查询分段详情",
            description="根据ID查询分段详细信息")
def get_section(section_id: int, service: SectionService = Depends(get_section_service)):
    entity = service.get_section(section_id)
    if entity:
        return Res(data=SectionResponseDTO(**entity.__dict__), code=200, message="查询成功")
    return Res(data=None, code=404, message="分段不存在")


@router.put("/{section_id}/content", response_model=Res[SectionResponseDTO],
            summary="更新分段内容",
            description="更新分段的标题或正文")
def update_section_content(section_id: int, dto: SectionUpdateDTO, service: SectionService = Depends(get_section_service)):
    data = {k: v for k, v in dto.__dict__.items() if v is not None}
    success = service.update_section(section_id, data)
    if success:
        entity = service.get_section(section_id)
        return Res(data=SectionResponseDTO(**entity.__dict__), code=200, message="更新成功")
    return Res(data=None, code=400, message="分段不存在")


@router.put("/{section_id}", response_model=Res[SectionResponseDTO],
            summary="重命名分段",
            description="修改分段名称")
def rename_section(section_id: int, dto: SectionRenameDTO, service: SectionService = Depends(get_section_service)):
    success = service.update_section(section_id, {"title": dto.title})
    if success:
        entity = service.get_section(section_id)
        return Res(data=SectionResponseDTO(**entity.__dict__), code=200, message="更新成功")
    else:
        return Res(data=None, code=400, message="分段不存在")


@router.delete("/{section_id}", response_model=Res,
               summary="删除分段",
               description="根据ID删除子分段")
def delete_section(section_id: int, service: SectionService = Depends(get_section_service)):
    success = service.delete_section(section_id)
    if success:
        return Res(data=None, code=200, message="删除成功")
    else:
        return Res(data=None, code=400, message="分段不存在")
