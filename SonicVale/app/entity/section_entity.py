
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SectionEntity:
    """业务实体：章节子分段"""
    chapter_id: int
    title: str
    id: Optional[int] = None
    order_index: Optional[int] = None
    text_content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
