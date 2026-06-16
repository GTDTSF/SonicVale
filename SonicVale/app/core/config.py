import os
import sys
from pathlib import Path


def getAppRoot():
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(exe_dir, "..", "..", ".."))
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def getAppConfigPath():
    if getattr(sys, "frozen", False):
        return os.path.join(os.environ["APPDATA"], "SonicVale-D")
    else:
        return os.path.join(getAppRoot(), "SonicValeData")


def getSettingsPath():
    """始终从 %APPDATA%/SonicVale-D/ 读取配置文件，开发和生产模式一致"""
    return os.path.join(os.environ["APPDATA"], "SonicVale-D", "settings.json")


def getDataPath():
    try:
        from app.core.settings import load_settings
        s = load_settings()
        dp = s.get("data_path", "")
        if dp and os.path.isdir(dp):
            return dp
        if dp and not os.path.exists(dp):
            os.makedirs(dp, exist_ok=True)
            return dp
    except Exception:
        pass
    if getattr(sys, "frozen", False):
        return os.path.join(os.environ["APPDATA"], "SonicVale-D", "SonicValeData")
    else:
        return getAppConfigPath()


def getConfigPath():
    return getDataPath()


def getFfmpegPath():
    BASE_DIR = getattr(sys, "_MEIPASS", Path(os.path.abspath(".")))
    FFMPEG_PATH = os.path.join(BASE_DIR, "core", "ffmpeg", "ffmpeg.exe")
    return FFMPEG_PATH


def get_project_root(folder_name: str) -> str:
    """项目根目录绝对路径：data_path/projects/{folder_name}"""
    return os.path.join(getDataPath(), "projects", folder_name)


def resolve_path(stored_path: str) -> str:
    """将数据库中存储的相对路径转为基于 getDataPath() 的绝对路径。
    如果已是绝对路径则直接返回（兼容旧数据）。"""
    if not stored_path:
        return stored_path
    if os.path.isabs(stored_path):
        return stored_path
    return os.path.normpath(os.path.join(getDataPath(), stored_path))


def make_path_relative(abs_path: str) -> str:
    """将绝对路径转为相对于 getDataPath() 的相对路径。
    如果不是绝对路径或不在 data_path 下则原样返回。"""
    if not abs_path or not os.path.isabs(abs_path):
        return abs_path
    data_path = getDataPath()
    try:
        rel = os.path.relpath(abs_path, data_path)
    except ValueError:
        return abs_path
    if rel.startswith(".."):
        return abs_path
    return rel


def resolve_voice_path(reference_path):
    if not reference_path:
        return None
    if os.path.isabs(reference_path):
        return reference_path
    return os.path.join(getDataPath(), reference_path)
