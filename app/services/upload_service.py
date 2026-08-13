# -*- coding: utf-8 -*-
"""
上传编排服务：串联文件解析 → Bucket 检查 → 存在性检查 → 上传 → ACL → 验证 → URL。

UI 无关：通过 progress 回调通知进度，通过 UploadResult 返回结构化结果。
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from app.config.regions import RegionConfig, get_region_config
from app.services.obs_service import ObsService, ObsError
from app.services.url_service import generate_public_url
from app.utils.auth import Credentials, load_credentials
from app.utils.file_utils import (
    generate_object_key,
    generate_solution_name,
    parse_filename,
    is_primary_extension,
)
from app.utils.logger import logger


class UploadStatus(Enum):
    SUCCESS = "success"
    UPLOADED_ACL_FAILED = "uploaded_acl_failed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UploadResult:
    status: UploadStatus
    object_key: str = ""
    public_url: str = ""
    bucket: str = ""
    region_name: str = ""
    solution_name: str = ""
    filename: str = ""
    message: str = ""
    steps: list = field(default_factory=list)  # [(ok: bool, text: str), ...]


# 进度回调类型：phase(str), message(str)
ProgressCallback = Callable[[str, str], None]


class UploadService:
    """上传流程编排。"""

    def __init__(self, credentials: Optional[Credentials] = None,
                 config_path: Optional[str] = None):
        self._credentials_override = credentials
        self._config_path = config_path

    # ------------------------------------------------------------------
    def prepare(self, file_path: str, region_name: str,
                custom_dir: str = None) -> tuple:
        """
        上传前准备：解析文件、区域、生成 object key。

        :param custom_dir: 自定义目录名，默认用 solution-name
        :return: (solution_name, filename, object_key, region_config)
        :raises ObsError / FileNotFoundError
        """
        region_config = get_region_config(region_name)
        if not region_config:
            raise ObsError(f"未知的区域：{region_name}")

        solution_name, filename, _ = parse_filename(file_path)
        object_key = generate_object_key(file_path, custom_dir)

        if not is_primary_extension(file_path):
            logger.warn(f"文件 {filename} 不是 .tf 文件，仍将上传。")

        return solution_name, filename, object_key, region_config

    # ------------------------------------------------------------------
    def upload(self,
               file_path: str,
               region_name: str,
               overwrite: bool = True,
               custom_dir: str = None,
               on_progress: Optional[ProgressCallback] = None,
               on_upload_percent: Optional[Callable[[int], None]] = None) -> UploadResult:
        """
        执行完整上传流程。

        :param file_path:        本地文件路径
        :param region_name:      区域显示名称
        :param overwrite:        对象已存在时是否覆盖
        :param custom_dir:       自定义目录名，默认用 solution-name
        :param on_progress:      流程阶段进度回调 (phase, message)
        :param on_upload_percent: 文件字节上传百分比回调 (0-100)
        """
        def notify(phase: str, msg: str) -> None:
            logger.step(msg)
            if on_progress:
                on_progress(phase, msg)

        steps: list = []

        try:
            # 1. 解析文件与区域
            notify("parse", "开始上传")
            solution_name, filename, object_key, region = self.prepare(
                file_path, region_name, custom_dir
            )
            notify("parse", f"文件：{filename}")
            notify("parse", f"区域：{region_name}")
            notify("parse", f"Bucket：{region.bucket}")
            notify("parse", f"Object Key：{object_key}")

            # 2. 加载凭证（优先级：UI 输入 > 设置面板保存 > 环境变量 > config.yaml）
            from app.config.config_manager import config_manager
            user_cred = config_manager.get_credentials()
            creds = load_credentials(
                self._config_path, self._credentials_override, user_cred
            )
            if not creds or not creds.is_valid():
                raise ObsError(
                    "未找到华为云凭证。请通过环境变量、config.yaml 或界面输入设置 "
                    "Access Key / Secret Key。"
                )

            # 3. 初始化 OBS 客户端并检查 Bucket
            notify("bucket", "检查 Bucket 可访问性")
            obs = ObsService(creds, region)
            obs.check_bucket_accessible()

            # 4. 检查对象是否存在
            notify("exists", "检查对象是否已存在")
            exists = obs.object_exists(object_key)
            if exists and not overwrite:
                notify("exists", "对象已存在，用户选择取消")
                steps.append((False, "对象已经存在，已取消上传"))
                return UploadResult(
                    status=UploadStatus.CANCELLED,
                    object_key=object_key,
                    bucket=region.bucket,
                    region_name=region_name,
                    solution_name=solution_name,
                    filename=filename,
                    message="对象已经存在，已取消上传。",
                    steps=steps,
                )
            if exists:
                notify("exists", "对象已存在，将覆盖")

            # 5. 上传文件
            notify("upload", "正在上传文件")

            def _on_bytes(transferred: int, total: int) -> None:
                if on_upload_percent and total > 0:
                    on_upload_percent(int(transferred * 100 / total))

            obs.upload_file(object_key, file_path, on_progress=_on_bytes)
            if on_upload_percent:
                on_upload_percent(100)
            steps.append((True, "文件上传成功"))
            notify("upload", "文件上传成功")

            # 6. 设置公共读 ACL
            notify("acl", "设置对象公共读权限")
            try:
                obs.set_public_read(object_key)
                steps.append((True, "对象权限设置成功"))
                notify("acl", "公共读设置成功")
                acl_ok = True
            except ObsError as e:
                steps.append((False, f"公共读设置失败：{e}"))
                notify("acl", f"公共读设置失败：{e}")
                acl_ok = False

            # 7. 验证对象
            notify("verify", "验证对象是否上传成功")
            verified = obs.verify_object(object_key)
            if not verified:
                steps.append((False, "对象验证失败"))
                notify("verify", "对象验证失败")
                return UploadResult(
                    status=UploadStatus.FAILED,
                    object_key=object_key,
                    bucket=region.bucket,
                    region_name=region_name,
                    solution_name=solution_name,
                    filename=filename,
                    message="对象验证失败，上传可能未成功。",
                    steps=steps,
                )

            # 8. 生成公网 URL
            public_url = generate_public_url(region, object_key)
            notify("url", "公网 URL 生成成功")
            notify("done", "上传完成")

            if acl_ok:
                steps.append((True, "公网 URL 生成成功"))
                return UploadResult(
                    status=UploadStatus.SUCCESS,
                    object_key=object_key,
                    public_url=public_url,
                    bucket=region.bucket,
                    region_name=region_name,
                    solution_name=solution_name,
                    filename=filename,
                    message="上传完成，公共读设置成功。",
                    steps=steps,
                )
            else:
                steps.append((True, "公网 URL 生成成功"))
                return UploadResult(
                    status=UploadStatus.UPLOADED_ACL_FAILED,
                    object_key=object_key,
                    public_url=public_url,
                    bucket=region.bucket,
                    region_name=region_name,
                    solution_name=solution_name,
                    filename=filename,
                    message="文件已上传，但公共读权限设置失败。",
                    steps=steps,
                )

        except FileNotFoundError as e:
            notify("error", str(e))
            return UploadResult(status=UploadStatus.FAILED, message=str(e), steps=steps)
        except ObsError as e:
            notify("error", str(e))
            return UploadResult(status=UploadStatus.FAILED, message=str(e), steps=steps)
        except Exception as e:
            # 兜底：不把 traceback 抛给用户
            logger.error(f"未知异常：{type(e).__name__}")
            notify("error", "发生未知错误，请查看日志。")
            return UploadResult(
                status=UploadStatus.FAILED,
                message="发生未知错误，请查看日志或稍后重试。",
                steps=steps,
            )

    # ------------------------------------------------------------------
    def check_exists(self, file_path: str, region_name: str,
                     custom_dir: str = None) -> bool:
        """仅检查对象是否已存在（用于 UI 提示覆盖）。"""
        try:
            _, _, object_key, region = self.prepare(file_path, region_name, custom_dir)
            from app.config.config_manager import config_manager
            user_cred = config_manager.get_credentials()
            creds = load_credentials(
                self._config_path, self._credentials_override, user_cred
            )
            if not creds or not creds.is_valid():
                raise ObsError("未找到华为云凭证。")
            obs = ObsService(creds, region)
            return obs.object_exists(object_key)
        except ObsError:
            raise
        except Exception as e:
            raise ObsError(f"检查对象存在性失败：{e}")
