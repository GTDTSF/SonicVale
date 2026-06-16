from typing import Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.po import SectionPO, LinePO


class SectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, section_id: int) -> Optional[SectionPO]:
        return self.db.get(SectionPO, section_id)

    def get_all(self, chapter_id: int) -> Sequence[SectionPO]:
        stmt = (select(SectionPO)
                .where(SectionPO.chapter_id == chapter_id)
                .order_by(SectionPO.order_index.asc()))
        return self.db.execute(stmt).scalars().all()

    def create(self, data: SectionPO) -> SectionPO:
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data

    def update(self, section_id: int, data: dict) -> Optional[SectionPO]:
        section = self.get_by_id(section_id)
        if not section:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(section, key, value)
        self.db.commit()
        self.db.refresh(section)
        return section

    def delete(self, section_id: int) -> bool:
        section = self.get_by_id(section_id)
        if not section:
            return False
        self.db.execute(
            update(LinePO).where(LinePO.section_id == section_id).values(section_id=None)
        )
        self.db.delete(section)
        self.db.commit()
        return True

    def get_by_name(self, title: str, chapter_id: int) -> Optional[SectionPO]:
        stmt = (select(SectionPO)
                .where(SectionPO.title == title)
                .where(SectionPO.chapter_id == chapter_id))
        return self.db.execute(stmt).scalar_one_or_none()

    def get_max_order_index(self, chapter_id: int) -> int:
        stmt = (select(SectionPO)
                .where(SectionPO.chapter_id == chapter_id)
                .order_by(SectionPO.order_index.desc())
                .limit(1))
        po = self.db.execute(stmt).scalar_one_or_none()
        return po.order_index if po else 0
