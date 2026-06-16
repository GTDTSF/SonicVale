import os
import re
import logging
import shutil

from sqlalchemy import Sequence

from app.core.config import getDataPath, get_project_root, make_path_relative
from app.entity.project_entity import ProjectEntity
from app.models.po import ProjectPO, ChapterPO, LinePO

from app.repositories.project_repository import ProjectRepository


class ProjectService:

    def __init__(self, repository: ProjectRepository):
        """注入 repository"""
        self.repository = repository

    def create_project(self,  entity: ProjectEntity):
        """创建新项目
        - 检查同名项目是否存在
        - project_root_path 由 folder_name 自动生成
        - 如果文件夹已存在，导入已有数据
        """
        project = self.repository.get_by_name(entity.name)
        if project:
            return None, "项目已存在"

        folder_name = entity.folder_name if hasattr(entity, 'folder_name') and entity.folder_name else entity.name
        safe_folder = re.sub(r'[<>:"/\\|?*]', '_', folder_name)

        data_path = getDataPath()
        project_root = os.path.join(data_path, "projects", safe_folder)

        if os.path.exists(project_root):
            return self._import_existing_project(entity, project_root)

        os.makedirs(project_root, exist_ok=True)
        entity.folder_name = safe_folder
        po = ProjectPO(**entity.__dict__)
        max_order = self.repository.get_max_sort_order()
        po.sort_order = max_order + 1
        res = self.repository.create(po)

        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = ProjectEntity(**data)

        return entity, "创建成功"

    def _import_existing_project(self, entity: ProjectEntity, project_root: str):
        """导入已有文件夹里的项目数据"""
        db = self.repository.db

        folder_name = entity.folder_name if hasattr(entity, 'folder_name') and entity.folder_name else entity.name
        safe_folder = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
        entity.folder_name = safe_folder
        po = ProjectPO(**entity.__dict__)
        max_order = self.repository.get_max_sort_order()
        po.sort_order = max_order + 1
        db.add(po)
        db.flush()
        project_id = po.id

        existing_dirs = [d for d in os.listdir(project_root) if os.path.isdir(os.path.join(project_root, d)) and d.isdigit()]
        for old_dir in existing_dirs:
            target_path = os.path.join(project_root, str(project_id))
            if old_dir == str(project_id):
                continue
            old_path = os.path.join(project_root, old_dir)
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.move(old_path, target_path)
            break

        project_dir = os.path.join(project_root, str(project_id))
        imported_chapters = 0
        imported_lines = 0
        if os.path.exists(project_dir):
            for order_dir in sorted(os.listdir(project_dir)):
                order_path = os.path.join(project_dir, order_dir)
                if not os.path.isdir(order_path) or not order_dir.isdigit():
                    continue
                order_index = int(order_dir)
                audio_dir = os.path.join(order_path, "audio")
                if not os.path.exists(audio_dir):
                    continue
                chapter_po = ChapterPO(
                    project_id=project_id,
                    title=f"第{order_index}章",
                    order_index=order_index,
                )
                db.add(chapter_po)
                db.flush()
                imported_chapters += 1

                audio_files = sorted([
                    f for f in os.listdir(audio_dir)
                    if f.endswith('.wav') or f.endswith('.mp3')
                ])
                for line_order, af in enumerate(audio_files, 1):
                    line_po = LinePO(
                        chapter_id=chapter_po.id,
                        line_order=line_order,
                        audio_path=make_path_relative(os.path.join(audio_dir, af)),
                    )
                    db.add(line_po)
                db.flush()
                imported_lines += len(audio_files)

        db.commit()
        db.refresh(po)

        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        entity = ProjectEntity(**data)
        msg = f"导入成功（{imported_chapters}个章节，{imported_lines}条台词）"
        logging.info("项目 %s 从 %s %s", entity.name, project_root, msg)
        return entity, msg


    def get_project(self, project_id: int) -> ProjectEntity | None:
        """根据 ID 查询项目"""
        po = self.repository.get_by_id(project_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = ProjectEntity(**data)
        if not res.folder_name and res.project_root_path:
            res.folder_name = os.path.basename(res.project_root_path.rstrip("\\/"))
        return res

    def get_all_projects(self) -> Sequence[ProjectEntity]:
        """获取所有项目列表"""
        pos = self.repository.get_all()
        entities = [
            ProjectEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        for e in entities:
            if not e.folder_name and e.project_root_path:
                e.folder_name = os.path.basename(e.project_root_path.rstrip("\\/"))
        return entities

    def update_project(self, project_id: int, data:dict) -> bool:
        """更新项目
        - 可以只更新部分字段
        - 检查同名冲突
        """
        name = data["name"]
        if self.repository.get_by_name(name) and self.repository.get_by_name(name).id != project_id:
            return False
        if "project_root_path" in data and data["project_root_path"]:
            data["project_root_path"] = make_path_relative(data["project_root_path"])
        # folder_name 直接存储，不做路径转换（它就是纯名字）
        self.repository.update(project_id, data)
        return True

    def delete_project(self, project_id: int) -> bool:
        """删除项目
        - 可以添加业务校验，例如项目下有章节是否允许删除
        - 后续需要级联删除所有章节内容
        """
        res = self.repository.delete(project_id)
        return res


    def reorder_project(self, project_id: int, direction: str) -> bool:
        return self.repository.swap_sort_order(project_id, direction)

    def search_projects(self, keyword: str) -> Sequence[ProjectEntity]:
        """模糊搜索项目"""

    # 解析content，按照章节
    def parse_content(self, content):
        """解析内容，按照章节"""
        # 正则匹配常见章节格式（支持中英文数字）
        chapter_pattern = re.compile(
            r'(第[\d一二三四五六七八九十百千]+[章回节部卷].*?)(?=\n|$)'
        )
        # 找到所有章节标题位置
        matches = list(chapter_pattern.finditer(content))
        chapters = []
        # 如果没找到章节，直接返回整个文本
        if not matches:
            return chapters

        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

            chapter_name = match.group(1).strip()
            chapter_content = content[start:end].strip()
            chapters.append({
                "chapter_name": chapter_name,
                "content": chapter_content
            })
        # 排序
        # chapters.sort(key=lambda x: x["chapter_name"])
        # 不需要排序了，因为是顺序解析得到的
        return  chapters
