# -*- coding: utf-8 -*-
"""
主窗口：组合上传表单、日志区、结果区，编排上传工作线程（支持多文件）。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget, QSplitter,
)

from app.services.upload_service import UploadStatus
from app.ui.upload_widget import UploadWidget
from app.ui.result_widget import ResultWidget
from app.ui.worker import UploadWorker
from app.ui.settings_dialog import SettingsDialog
from app.utils.logger import logger


class LogPanel(QWidget):
    """日志面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel("日志")
        layout.addWidget(header)
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setMinimumHeight(120)
        layout.addWidget(self._text)

        logger.add_handler(self._on_log)

    def _on_log(self, level: str, line: str) -> None:
        color = {
            "ERROR": "#c62828",
            "WARN": "#ef6c00",
            "STEP": "#1565c0",
        }.get(level, "#444")
        self._text.append(f'<span style="color:{color};">{line}</span>')

    def append(self, text: str) -> None:
        self._text.append(text)


class MainWindow(QMainWindow):
    """主窗口。"""

    def __init__(self, config_path: str = None):
        super().__init__()
        self._config_path = config_path
        self._worker: UploadWorker = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("OBS Solution Uploader — 解决方案代码一键上传工具")
        self.resize(720, 780)

        central = QWidget()
        outer = QVBoxLayout(central)

        # 标题
        title = QLabel("OBS Solution Uploader")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:bold; padding:8px;")
        outer.addWidget(title)
        subtitle = QLabel("解决方案代码一键上传工具")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#666; padding-bottom:8px;")
        outer.addWidget(subtitle)

        # 设置按钮
        settings_row = QHBoxLayout()
        settings_row.addStretch()
        self._settings_btn = QPushButton("⚙️ 设置")
        self._settings_btn.clicked.connect(self._open_settings)
        settings_row.addWidget(self._settings_btn)
        outer.addLayout(settings_row)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._upload_widget = UploadWidget()
        self._result_widget = ResultWidget()
        self._log_panel = LogPanel()

        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(self._upload_widget)
        tl.addWidget(self._result_widget)

        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        tl.addWidget(self._progress_bar)

        splitter.addWidget(top)
        splitter.addWidget(self._log_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        outer.addWidget(splitter, stretch=1)

        self.setCentralWidget(central)

        # 信号连接
        self._upload_widget.upload_requested.connect(self._on_upload_requested)
        self._upload_widget.check_exists_requested.connect(self._on_check_exists)

    # ------------------------------------------------------------------
    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._upload_widget.refresh_regions()
            logger.info("设置已更新，区域列表已刷新。")

    # ------------------------------------------------------------------
    def _on_check_exists(self, file_paths: list, region_name: str,
                         custom_dir: str) -> None:
        """上传前检查对象是否已存在（批量检查）。"""
        self._worker = UploadWorker(
            file_paths=file_paths,
            region_name=region_name,
            custom_dir=custom_dir,
            config_path=self._config_path,
            check_only=True,
        )
        self._worker.exists_result.connect(
            lambda exists, total: self._on_exists_result(
                exists, total, file_paths, region_name, custom_dir
            )
        )
        self._worker.start()

    def _on_exists_result(self, exists: int, total: int,
                          file_paths: list, region_name: str,
                          custom_dir: str) -> None:
        if exists > 0:
            reply = QMessageBox.question(
                self, "对象已存在",
                f"{exists}/{total} 个文件已存在目标目录中，是否覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply == QMessageBox.StandardButton.No:
                logger.info(f"用户取消上传（{exists} 个文件已存在）。")
                return
        self._upload_widget.request_upload(overwrite=True)

    # ------------------------------------------------------------------
    def _on_upload_requested(self, file_paths: list, region_name: str,
                             overwrite: bool, custom_dir: str) -> None:
        self._result_widget.reset()
        self._upload_widget.set_uploading(True)
        self._log_panel.append(
            f"<b>开始上传 {len(file_paths)} 个文件到 {region_name}...</b>"
        )

        self._worker = UploadWorker(
            file_paths=file_paths,
            region_name=region_name,
            overwrite=overwrite,
            custom_dir=custom_dir or None,
            config_path=self._config_path,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.upload_percent.connect(self._on_upload_percent)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.all_done.connect(self._on_all_done)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._worker.start()

    def _on_progress(self, phase: str, message: str) -> None:
        pass  # 日志由 logger 输出

    def _on_upload_percent(self, pct: int) -> None:
        self._progress_bar.setValue(pct)

    def _on_file_done(self, idx: int, total: int, filename: str,
                      status: str) -> None:
        status_text = {
            "success": "✓ 成功",
            "uploaded_acl_failed": "✓ 已上传 ⚠ ACL 失败",
            "failed": "✗ 失败",
            "cancelled": "— 已取消",
        }.get(status, status)
        self._log_panel.append(f"  [{idx + 1}/{total}] {filename} — {status_text}")

    def _on_all_done(self, results: list) -> None:
        self._upload_widget.set_uploading(False)
        self._progress_bar.setVisible(False)
        self._result_widget.show_multi_results(results)

        success = sum(1 for r in results if r.status == UploadStatus.SUCCESS)
        acl_fail = sum(
            1 for r in results if r.status == UploadStatus.UPLOADED_ACL_FAILED
        )
        failed = sum(1 for r in results if r.status == UploadStatus.FAILED)
        cancelled = sum(1 for r in results if r.status == UploadStatus.CANCELLED)

        summary = f"完成：{success} 成功"
        if acl_fail:
            summary += f"，{acl_fail} 已上传但 ACL 失败"
        if failed:
            summary += f"，{failed} 失败"
        if cancelled:
            summary += f"，{cancelled} 已取消"

        logger.info(summary)
        if failed > 0:
            QMessageBox.critical(self, "上传结果", summary)
        elif acl_fail > 0:
            QMessageBox.warning(self, "上传结果", summary)
        else:
            QMessageBox.information(self, "上传结果", summary)
