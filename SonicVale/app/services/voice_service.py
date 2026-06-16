import json
import os
import shutil
import tempfile
import uuid
import zipfile
from typing import List, Tuple

from sqlalchemy import Sequence

from app.core.audio_engin import AudioProcessor
from app.core.config import getDataPath, resolve_path
from app.dto.voice_dto import VoiceAudioProcessDTO
from app.entity.voice_entity import VoiceEntity
from app.models.po import VoicePO
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository
from app.repositories.voice_repository import VoiceRepository


class VoiceService:

    def __init__(self, repository: VoiceRepository,multi_emotion_voice_repository: MultiEmotionVoiceRepository):
        """注入 repository"""
        self.repository = repository
        self.multi_emotion_voice_repository = multi_emotion_voice_repository

    def create_voice(self,  entity: VoiceEntity):
        """创建新音色
        - 检查同名音色是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        voice = self.repository.get_by_name(entity.name, entity.tts_provider_id)
        if voice:
            return None

        # 如果有参考音频，复制到项目 voices 目录，保存相对路径
        if entity.reference_path and os.path.exists(entity.reference_path):
            voices_dir = os.path.join(getDataPath(), "voices")
            os.makedirs(voices_dir, exist_ok=True)
            ext = os.path.splitext(entity.reference_path)[1] or ".wav"
            new_filename = f"{entity.name}_{uuid.uuid4().hex[:8]}{ext}"
            new_path = os.path.join(voices_dir, new_filename)
            shutil.copy2(entity.reference_path, new_path)
            # 保存相对路径
            entity.reference_path = f"voices/{new_filename}"

        # 手动将 entity 转化为 po
        po = VoicePO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = VoiceEntity(**data)

        # 将 po 转化为 entity
        return entity


    def get_voice(self, voice_id: int) -> VoiceEntity | None:
        """根据 ID 查询音色"""
        po = self.repository.get_by_id(voice_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = VoiceEntity(**data)
        return res

    def get_all_voices(self,tts_provider_id: int) -> Sequence[VoiceEntity]:
        """获取所有音色列表"""
        pos = self.repository.get_all(tts_provider_id)
        # pos -> entities

        entities = [
            VoiceEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_voice(self, voice_id: int, data:dict) -> bool:
        """更新音色
        - 可以只更新部分字段
        - 检查同名冲突
        - 检查 project_id 不能改变
        - 如果有新 reference_path，复制文件并转为相对路径
        """
        name = data["name"]
        tts_provider_id = data["tts_provider_id"]
        if self.repository.get_by_name(name, tts_provider_id) and self.repository.get_by_name(name,tts_provider_id).id != voice_id:
            return False
        po = self.repository.get_by_id(voice_id)
        # 防止改变 project_id
        if po.tts_provider_id != tts_provider_id:
            return False
        
        # 如果有新的参考音频（绝对路径），复制到 voices 目录并保存相对路径
        reference_path = data.get("reference_path")
        if reference_path and os.path.exists(reference_path) and os.path.isabs(reference_path):
            voices_dir = os.path.join(getDataPath(), "voices")
            os.makedirs(voices_dir, exist_ok=True)
            ext = os.path.splitext(reference_path)[1] or ".wav"
            new_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
            new_path = os.path.join(voices_dir, new_filename)
            shutil.copy2(reference_path, new_path)
            data["reference_path"] = f"voices/{new_filename}"
        
        self.repository.update(voice_id, data)
        return True

    def delete_voice(self, voice_id: int) -> bool:
        """删除音色,需要保证事务
        """

        res = self.repository.delete(voice_id)
        self.multi_emotion_voice_repository.delete_multi_emotion_voice_by_voice_id(voice_id)
        return res

    def export_voices(self, tts_provider_id: int, export_path: str, ids: List[int] | None = None) -> str:
        """导出音色库到zip文件
        - 获取所有音色
        - 将音色信息和对应的音频文件打包到zip
        - 返回zip文件路径
        """
        if ids is None:
            voices = self.get_all_voices(tts_provider_id)
        else:
            pos = self.repository.get_by_ids(tts_provider_id, ids)
            voices = [
                VoiceEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
                for po in pos
            ]
        if not voices:
            return None

        # 确保导出目录存在
        os.makedirs(os.path.dirname(export_path) if os.path.dirname(export_path) else ".", exist_ok=True)

        # 创建zip文件
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 准备音色元数据
            voices_metadata = []
            
            for voice in voices:
                voice_data = {
                    "name": voice.name,
                    "description": voice.description,
                    "is_multi_emotion": voice.is_multi_emotion,
                    "reference_file": None
                }
                
                # 如果有参考音频文件，添加到 zip
                if voice.reference_path:
                    # 如果是相对路径，转为绝对路径
                    abs_path = voice.reference_path
                    if not os.path.isabs(abs_path):
                        abs_path = os.path.join(getDataPath(), abs_path)
                    
                    if os.path.exists(abs_path):
                        # 保持原文件名
                        file_name = os.path.basename(abs_path)
                        # 使用音色名称作为子目录，避免文件名冲突
                        archive_path = f"voices/{voice.name}/{file_name}"
                        zipf.write(abs_path, archive_path)
                        voice_data["reference_file"] = archive_path
                
                voices_metadata.append(voice_data)
            
            # 写入元数据文件
            metadata_json = json.dumps(voices_metadata, ensure_ascii=False, indent=2)
            zipf.writestr("voices_metadata.json", metadata_json)
        
        return export_path

    def import_voices(self, tts_provider_id: int, zip_path: str, target_dir: str) -> Tuple[int, int, List[str]]:
        """从zip文件导入音色库
        - 解压zip文件
        - 将音频文件复制到指定目录
        - 添加音色到数据库（跳过重名的）
        - 返回: (成功数量, 跳过数量, 跳过的音色名称列表)
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"zip文件不存在: {zip_path}")
        
        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)
        
        success_count = 0
        skipped_count = 0
        skipped_names = []
        
        # 创建临时目录解压
        with tempfile.TemporaryDirectory() as temp_dir:
            # 解压zip文件
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # 读取元数据
            metadata_path = os.path.join(temp_dir, "voices_metadata.json")
            if not os.path.exists(metadata_path):
                raise ValueError("无效的音色库文件：缺少voices_metadata.json")
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                voices_metadata = json.load(f)
            
            for voice_data in voices_metadata:
                voice_name = voice_data["name"]
                
                # 检查是否已存在同名音色
                existing = self.repository.get_by_name(voice_name, tts_provider_id)
                if existing:
                    skipped_count += 1
                    skipped_names.append(voice_name)
                    continue
                
                reference_path = None
                
                # 如果有参考音频文件，复制到目标目录
                if voice_data.get("reference_file"):
                    source_file = os.path.join(temp_dir, voice_data["reference_file"])
                    if os.path.exists(source_file):
                        # 使用音色名称作为文件名，保留原扩展名
                        file_ext = os.path.splitext(source_file)[1]
                        file_name = f"{voice_name}{file_ext}"
                        dest_file = os.path.join(target_dir, file_name)
                        shutil.copy2(source_file, dest_file)
                        # 如果目标目录是 voices 目录，保存相对路径
                        if os.path.abspath(target_dir) == os.path.abspath(os.path.join(getDataPath(), "voices")):
                            reference_path = f"voices/{file_name}"
                        else:
                            reference_path = dest_file
                
                # 创建音色实体
                entity = VoiceEntity(
                    name=voice_name,
                    tts_provider_id=tts_provider_id,
                    reference_path=reference_path,
                    description=voice_data.get("description"),
                    is_multi_emotion=voice_data.get("is_multi_emotion", 0)
                )
                
                # 保存到数据库
                po = VoicePO(**entity.__dict__)
                self.repository.create(po)
                success_count += 1
        
        return success_count, skipped_count, skipped_names

    def process_audio(self, dto: VoiceAudioProcessDTO) -> bool:
        """处理音色参考音频
        - 变速、音量调整
        - 裁剪/删除区间
        - 添加/裁剪末尾静音
        - 指定位置插入静音
        """
        audio_path = resolve_path(dto.audio_path)
        if not os.path.exists(audio_path):
            raise FileNotFoundError(audio_path)
        
        processor = AudioProcessor(audio_path)
        
        start_ms = dto.start_ms
        end_ms = dto.end_ms
        speed = dto.speed
        volume = dto.volume
        current_ms = dto.current_ms
        silence_sec = dto.silence_sec
        
        # ---------- (1) 优先裁剪 ----------
        if start_ms is not None and end_ms is not None and end_ms > start_ms:
            processor.cut(start_ms, end_ms)
        
        # ---------- (2) 插入静音 ----------
        elif current_ms is not None and silence_sec is not None and silence_sec != 0:
            processor.insert_silence(current_ms, silence_sec)
        
        # ---------- (3) 末尾静音/裁剪 ----------
        elif current_ms is None and silence_sec is not None and silence_sec != 0:
            processor.append_silence(silence_sec)
        
        # ---------- (4) 音量 + 变速 ----------
        if speed != 1.0:
            processor.change_speed(speed)
        if volume != 1.0:
            processor.change_volume(volume)
        
        return True

    def copy_voice(self, source_voice_id: int, new_name: str, target_dir: str = None) -> VoiceEntity:
        """复制音色
        - 获取源音色信息
        - 复制音频文件到目标目录
        - 创建新音色记录
        - 返回新音色实体
        """
        # 获取源音色
        source_voice = self.get_voice(source_voice_id)
        if not source_voice:
            raise ValueError("源音色不存在")
        
        # 检查新名称是否已存在
        existing = self.repository.get_by_name(new_name, source_voice.tts_provider_id)
        if existing:
            raise ValueError(f"音色名称 '{new_name}' 已存在")
        
        new_reference_path = None
        
        # 处理音频文件复制
        if source_voice.reference_path:
            # 如果是相对路径，转为绝对路径
            source_abs_path = source_voice.reference_path
            if not os.path.isabs(source_abs_path):
                source_abs_path = os.path.join(getDataPath(), source_abs_path)
            
            if os.path.exists(source_abs_path):
                # 保存到 voices 目录，使用相对路径
                voices_dir = os.path.join(getDataPath(), "voices")
                os.makedirs(voices_dir, exist_ok=True)
                
                # 获取源文件扩展名
                file_ext = os.path.splitext(source_abs_path)[1]
                # 使用新音色名作为文件名
                new_file_name = f"{new_name}{file_ext}"
                new_abs_path = os.path.join(voices_dir, new_file_name)
                
                # 复制文件
                shutil.copy2(source_abs_path, new_abs_path)
                # 保存相对路径
                new_reference_path = f"voices/{new_file_name}"
        
        # 创建新音色实体
        new_entity = VoiceEntity(
            name=new_name,
            tts_provider_id=source_voice.tts_provider_id,
            reference_path=new_reference_path,
            description=source_voice.description,
            is_multi_emotion=source_voice.is_multi_emotion
        )
        
        # 保存到数据库
        po = VoicePO(**new_entity.__dict__)
        res = self.repository.create(po)
        
        # 返回新建的音色实体
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        return VoiceEntity(**data)
