# -*- coding: utf-8 -*-
"""
主窗口：组合上传表单、日志区、结果区，编排上传工作线程（支持多文件）。
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QSizePolicy, QTextEdit, QVBoxLayout,
    QWidget, QSplitter,
)

from app.services.upload_service import UploadStatus
from app.ui.upload_widget import UploadWidget
from app.ui.result_widget import ResultWidget
from app.ui.worker import UploadWorker, ListDirsWorker
from app.ui.settings_dialog import SettingsDialog
from app.utils.logger import logger


class LogPanel(QWidget):
    """日志面板。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QLabel("📋 运行日志")
        header.setStyleSheet("font-size:13px; font-weight:600; color:#6b7280; padding-left:2px;")
        layout.addWidget(header)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setMinimumHeight(110)
        layout.addWidget(self._text)

        logger.add_handler(self._on_log)

    def _on_log(self, level: str, line: str) -> None:
        color = {
            "ERROR": "#dc2626",
            "WARN": "#d97706",
            "STEP": "#2563eb",
        }.get(level, "#6b7280")
        self._text.append(f'<span style="color:{color};">{line}</span>')

    def append(self, text: str) -> None:
        self._text.append(text)


class MainWindow(QMainWindow):
    """主窗口。"""

    def __init__(self, config_path: str = None):
        super().__init__()
        self._config_path = config_path
        self._worker: UploadWorker = None
        self._dirs_worker: ListDirsWorker = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("OBS Solution Uploader — 解决方案代码一键上传工具")
        self.resize(740, 820)
        self.setMinimumSize(680, 700)

        central = QWidget()
        central.setObjectName("CentralWidget")
        outer = QVBoxLayout(central)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.setSpacing(12)

        # ---- 顶部标题栏 ----
        header = self._build_header()
        outer.addWidget(header)

        # ---- 主体（可拖拽分隔） ----
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(6)

        self._upload_widget = UploadWidget()
        self._result_widget = ResultWidget()
        self._log_panel = LogPanel()

        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(10)
        tl.addWidget(self._upload_widget)
        tl.addWidget(self._result_widget)

        # 进度条
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(14)
        tl.addWidget(self._progress_bar)

        splitter.addWidget(top)
        splitter.addWidget(self._log_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)

        outer.addWidget(splitter, stretch=1)

        self.setCentralWidget(central)

        # 信号连接
        self._upload_widget.upload_requested.connect(self._on_upload_requested)
        self._upload_widget.check_exists_requested.connect(self._on_check_exists)
        self._upload_widget.list_dirs_requested.connect(self._on_list_dirs)

    # ------------------------------------------------------------------
    def _build_header(self) -> QWidget:
        """构建顶部标题栏。"""
        bar = QFrame()
        bar.setObjectName("HeaderBar")
        bar.setStyleSheet("""
            QFrame#HeaderBar {
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        # 左侧：图标 + 标题
        left = QVBoxLayout()
        left.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        icon = QLabel("☁️")
        icon.setStyleSheet("font-size: 24px;")
        title_row.addWidget(icon)

        title = QLabel("OBS Solution Uploader")
        title.setObjectName("AppTitle")
        title_row.addWidget(title)
        title_row.addStretch()
        left.addLayout(title_row)

        subtitle = QLabel("解决方案代码一键上传工具  ·  选择文件 → 选区域 → 一键上传")
        subtitle.setObjectName("AppSubtitle")
        left.addWidget(subtitle)

        layout.addLayout(left, stretch=1)

        # 右侧：设置按钮
        self._settings_btn = QPushButton("⚙️  设置")
        self._settings_btn.setObjectName("SettingsBtn")
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(self._settings_btn, alignment=Qt.AlignmentFlag.AlignTop)

        return bar

    # ------------------------------------------------------------------
    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._upload_widget.refresh_regions()
            logger.info("设置已更新，区域列表已刷新。")

    # ------------------------------------------------------------------
    def _on_list_dirs(self, region_name: str, prefix: str) -> None:
        """后台列举 OBS 桶内已有子目录。"""
        self._dirs_worker = ListDirsWorker(
            region_name=region_name,
            prefix=prefix,
            config_path=self._config_path,
        )
        self._dirs_worker.finished_dirs.connect(self._on_list_dirs_done)
        self._dirs_worker.start()

    def _on_list_dirs_done(self, dirs: list, error: str) -> None:
        self._upload_widget.show_existing_dirs(dirs, error)
        if error:
            logger.warn(f"列举目录失败：{error}")
        else:
            logger.info(f"列举到 {len(dirs)} 个已有目录。")

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
            f'<b style="color:#2563eb;">开始上传 {len(file_paths)} 个文件到 {region_name}...</b>'
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
