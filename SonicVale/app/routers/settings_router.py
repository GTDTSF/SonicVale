from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.core.response import Res
from app.core.settings import get_setting, set_setting

router = APIRouter(prefix="/settings", tags=["Settings"])


class UpdateSettingDTO(BaseModel):
    data_path: Optional[str] = None


@router.get("/", response_model=Res)
def get_settings():
    data = {
        "data_path": get_setting("data_path", ""),
    }
    return Res(data=data, code=200, message="查询成功")


@router.put("/", response_model=Res)
def update_settings(dto: UpdateSettingDTO):
    data_path_changed = False
    if dto.data_path is not None:
        set_setting("data_path", dto.data_path)
        data_path_changed = True
    data = {
        "data_path": get_setting("data_path", ""),
        "data_path_changed": data_path_changed,
    }
    return Res(data=data, code=200, message="更新成功")
