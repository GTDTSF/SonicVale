from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class SectionCreateDTO(BaseModel):
    title: str
    chapter_id: int
    order_index: Optional[int] = None


class SectionResponseDTO(BaseModel):
    id: int
    title: str
    chapter_id: int
    order_index: Optional[int] = None
    text_content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SectionRenameDTO(BaseModel):
    title: str


class SectionUpdateDTO(BaseModel):
    title: Optional[str] = None
    text_content: Optional[str] = None
