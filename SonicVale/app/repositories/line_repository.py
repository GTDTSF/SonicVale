from typing import Optional, List

from sqlalchemy import Sequence, select, update
from sqlalchemy.orm import Session

from app.dto.line_dto import LineOrderDTO
from app.models.po import LinePO


class LineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: int) -> Optional[LinePO]:
        """根据 ID 查询单行台词"""
        return self.db.get(LinePO, id)

    def get_all(self, chapter_id: int) -> Sequence[LinePO]:
        """获取章节下所有单行台词，按 line_order 排序"""
        stmt = (
            select(LinePO)
            .where(LinePO.chapter_id == chapter_id)
            .order_by(LinePO.line_order.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_by_section(self, section_id: int) -> Sequence[LinePO]:
        """获取分段下的台词"""
        stmt = (
            select(LinePO)
            .where(LinePO.section_id == section_id)
            .order_by(LinePO.line_order.asc())
        )
        return self.db.execute(stmt).scalars().all()


    def create(self, data: LinePO) -> LinePO:
        """新增单行台词"""
        self.db.add(data)
        self.db.commit()
        self.db.refresh(data)
        return data


    def update(self, line_id: int, line_data: dict) -> Optional[LinePO]:
        """更新单行台词信息"""
        line = self.get_by_id(line_id)
        if not line:
            return None
        for key, value in line_data.items():
            if value is not None:  # 只更新不为空的字段
                setattr(line, key, value)

        self.db.commit()
        self.db.refresh(line)
        return line

    def delete(self, line_id: int) -> bool:
        """删除台词"""
        line = self.get_by_id(line_id)
        if not line:
            return False
        self.db.delete(line)
        self.db.commit()
        return True
    def delete_all_by_chapter_id(self, chapter_id: int) -> bool:
        """删除章节下的所有台词"""
        lines = self.get_all(chapter_id)
        for line in lines:
            self.db.delete(line)
        self.db.commit()
        return True

    def get_lines_by_role_id(self, role_id: int):
        return self.db.execute(select(LinePO).where(LinePO.role_id == role_id)).scalars().all()

    def batch_update_line_order(self, line_orders:List[LineOrderDTO])-> int:
        """批量更新台词的顺序"""
        if not line_orders:
            return 0

        from sqlalchemy import bindparam
        stmt = (
            update(LinePO)
            .where(LinePO.id == bindparam("id"))
            .values(line_order=bindparam("line_order"))
        )
        params = [{"id": it.id, "line_order": it.line_order} for it in line_orders]
        res = self.db.execute(stmt, params)  # executemany
        self.db.commit()
        return res.rowcount if res.rowcount not in (None, -1) else len(params)

    def batch_replace_role(self, chapter_id: int, from_role_id: int, to_role_id: int, section_id: int = None) -> int:
        stmt = (update(LinePO)
                .where(LinePO.chapter_id == chapter_id)
                .where(LinePO.role_id == from_role_id))
        if section_id is not None:
            stmt = stmt.where(LinePO.section_id == section_id)
        stmt = stmt.values(role_id=to_role_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount
