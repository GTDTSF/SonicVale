import logging

from app.entity.section_entity import SectionEntity
from app.models.po import SectionPO
from app.repositories.section_repository import SectionRepository


class SectionService:
    def __init__(self, repository: SectionRepository):
        self.repository = repository

    def create_section(self, entity: SectionEntity):
        existing = self.repository.get_by_name(entity.title, entity.chapter_id)
        if existing:
            logging.info("同名分段已存在")
            return None
        po = SectionPO(**entity.__dict__)
        max_order = self.repository.get_max_order_index(entity.chapter_id)
        po.order_index = max_order + 1
        res = self.repository.create(po)
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        return SectionEntity(**data)

    def get_section(self, section_id: int) -> SectionEntity | None:
        po = self.repository.get_by_id(section_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        return SectionEntity(**data)

    def get_all_sections(self, chapter_id: int):
        pos = self.repository.get_all(chapter_id)
        return [SectionEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")}) for po in pos]

    def update_section(self, section_id: int, data: dict) -> bool:
        return self.repository.update(section_id, data) is not None

    def delete_section(self, section_id: int) -> bool:
        return self.repository.delete(section_id)
