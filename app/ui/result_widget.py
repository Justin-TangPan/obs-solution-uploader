# -*- coding: utf-8 -*-
"""
上传结果展示组件：单文件/多文件步骤状态、公网 URL、复制/打开按钮。
"""

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QGroupBox, QSizePolicy, QTextEdit,
)

from app.services.upload_service import UploadResult, UploadStatus


class ResultWidget(QFrame):
    """上传结果展示区。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._public_url = ""
        self._all_urls: list = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._group = QGroupBox("✅ 上传结果")
        group_layout = QVBoxLayout(self._group)
        group_layout.setSpacing(7)

        # 步骤状态列表（多行）
        self._steps_text = QTextEdit()
        self._steps_text.setObjectName("StepsText")
        self._steps_text.setReadOnly(True)
        self._steps_text.setMinimumHeight(80)
        self._steps_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._steps_text.setPlaceholderText("尚未上传")
        group_layout.addWidget(self._steps_text)

        # 公网 URL
        url_label = QLabel("公网访问地址（最后一个文件）")
        url_label.setObjectName("SectionLabel")
        group_layout.addWidget(url_label)

        url_row = QHBoxLayout()
        url_row.setSpacing(6)
        self._url_combo = QPushButton("▼ 查看全部 URL")
        self._url_combo.setObjectName("GhostBtn")
        self._url_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._url_combo.setVisible(False)
        self._url_combo.clicked.connect(self._show_all_urls)
        url_row.addWidget(self._url_combo)

        self._url_edit = QLineEdit()
        self._url_edit.setReadOnly(True)
        self._url_edit.setPlaceholderText("上传成功后在此显示公网 URL")
        url_row.addWidget(self._url_edit, stretch=1)

        self._copy_btn = QPushButton("📋 复制链接")
        self._copy_btn.setObjectName("GhostBtn")
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setEnabled(False)
        self._copy_btn.clicked.connect(self._copy_url)
        url_row.addWidget(self._copy_btn)

        self._open_btn = QPushButton("🔗 打开链接")
        self._open_btn.setObjectName("GhostBtn")
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_url)
        url_row.addWidget(self._open_btn)

        group_layout.addLayout(url_row)
        layout.addWidget(self._group)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    # ------------------------------------------------------------------
    def show_result(self, result: UploadResult) -> None:
        """单文件结果。"""
        self._all_urls = []
        self._update_steps(result.steps)
        self._set_url(result.public_url)

    def show_multi_results(self, results: list) -> None:
        """多文件结果。"""
        self._all_urls = []
        lines = []
        last_ok_url = ""

        for r in results:
            mark = "✓" if r.status == UploadStatus.SUCCESS else "⚠" if r.status == UploadStatus.UPLOADED_ACL_FAILED else "✗"
            lines.append(f"<b>{r.filename or '?'}</b>  {mark} {r.message}")
            for ok, text in r.steps:
                m = "✓" if ok else "✗"
                c = "#2e7d32" if ok else "#c62828"
                lines.append(f'&nbsp;&nbsp;<span style="color:{c};">{m} {text}</span>')
            if r.public_url:
                self._all_urls.append(r.public_url)
                last_ok_url = r.public_url

        self._steps_text.setHtml("<br>".join(lines))
        self._set_url(last_ok_url)
        if len(self._all_urls) > 1:
            self._url_combo.setVisible(True)
        else:
            self._url_combo.setVisible(False)

    # ------------------------------------------------------------------
    def _update_steps(self, steps: list) -> None:
        lines = []
        for ok, text in steps:
            mark = "✓" if ok else "✗"
            color = "#2e7d32" if ok else "#c62828"
            lines.append(f'<span style="color:{color};">{mark} {text}</span>')
        self._steps_text.setHtml("<br>".join(lines) if lines else "尚未上传")

    def _set_url(self, url: str) -> None:
        self._public_url = url
        if url:
            self._url_edit.setText(url)
            self._copy_btn.setEnabled(True)
            self._open_btn.setEnabled(True)
        else:
            self._url_edit.clear()
            self._copy_btn.setEnabled(False)
            self._open_btn.setEnabled(False)

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self._steps_text.clear()
        self._url_edit.clear()
        self._copy_btn.setEnabled(False)
        self._open_btn.setEnabled(False)
        self._url_combo.setVisible(False)
        self._public_url = ""
        self._all_urls = []

    # ------------------------------------------------------------------
    def _copy_url(self) -> None:
        if self._public_url:
            QGuiApplication.clipboard().setText(self._public_url)
            self._copy_btn.setText("已复制 ✓")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("复制链接"))

    def _open_url(self) -> None:
        if self._public_url:
            webbrowser.open(self._public_url)

    def _show_all_urls(self) -> None:
        """弹出对话框显示所有 URL。"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit

        dlg = QDialog(self)
        dlg.setWindowTitle("全部文件公网 URL")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setText("\n".join(self._all_urls))
        layout.addWidget(text)
        close = QPushButton("关闭")
        close.setObjectName("GhostBtn")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.clicked.connect(dlg.accept)
        layout.addWidget(close)
        # 自适应：根据内容行数估算高度，限制在合理范围
        line_count = max(1, len(self._all_urls))
        dlg.setMinimumSize(500, 200)
        dlg.resize(620, min(600, 120 + line_count * 22))
        dlg.exec()
        layout.addWidget(close)
        dlg.exec()
