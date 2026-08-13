# -*- coding: utf-8 -*-
"""
上传工作线程：在后台执行上传流程，避免阻塞 UI。

支持单文件/多文件模式：多文件时逐个顺序处理。
"""

from PySide6.QtCore import QThread, Signal

from app.services.upload_service import UploadService, UploadResult, UploadStatus
from app.utils.auth import Credentials
from app.utils.logger import logger


class UploadWorker(QThread):
    """后台上传线程。"""

    # (phase, message) - 全局流程消息
    progress = Signal(str, str)
    # 上传字节百分比 0-100（当前文件）
    upload_percent = Signal(int)
    # (index, count, filename, status) - 单个文件完成通知
    file_done = Signal(int, int, str, str)
    # 全部文件上传完成：list[UploadResult]
    all_done = Signal(list)
    # 存在性检查结果 (exists_count, total_count)
    exists_result = Signal(int, int)

    def __init__(self, file_paths: list, region_name: str,
                 overwrite: bool = True,
                 custom_dir: str = None,
                 check_only: bool = False,
                 config_path: str = None,
                 parent=None):
        super().__init__(parent)
        self._file_paths = file_paths
        self._region_name = region_name
        self._overwrite = overwrite
        self._custom_dir = custom_dir
        self._check_only = check_only
        self._config_path = config_path

    def run(self) -> None:
        service = UploadService(config_path=self._config_path)

        try:
            if self._check_only:
                # 检查所有文件是否存在
                exists_count = 0
                for fp in self._file_paths:
                    try:
                        if service.check_exists(fp, self._region_name, self._custom_dir):
                            exists_count += 1
                    except Exception:
                        pass
                self.exists_result.emit(exists_count, len(self._file_paths))
                return

            # 逐个上传
            results = []
            total = len(self._file_paths)
            for idx, fp in enumerate(self._file_paths):
                filename = fp.split("\\")[-1].split("/")[-1]
                self.progress.emit("file", f"[{idx + 1}/{total}] {filename}")

                result: UploadResult = service.upload(
                    file_path=fp,
                    region_name=self._region_name,
                    overwrite=self._overwrite,
                    custom_dir=self._custom_dir,
                    on_progress=lambda phase, msg: self.progress.emit(phase, msg),
                    on_upload_percent=lambda pct: self.upload_percent.emit(pct),
                )
                results.append(result)
                self.file_done.emit(idx, total, filename, result.status.value)

            self.all_done.emit(results)

        except Exception as e:
            logger.error(f"上传流程异常：{e}")
            self.all_done.emit([
                UploadResult(status=UploadStatus.FAILED, message=str(e))
            ])
