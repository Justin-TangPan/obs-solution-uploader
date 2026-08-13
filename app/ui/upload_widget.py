# -*- coding: utf-8 -*-
"""
上传表单组件：多文件选择（含拖拽）、自定义目录、区域选择、目标预览、上传按钮。
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMessageBox, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget, QAbstractItemView,
)

from app.config.regions import get_region_config, list_region_names
from app.config.settings import object_key_prefix
from app.utils.file_utils import generate_object_key, generate_solution_name, is_primary_extension


# ======================================================================
class MultiFileDropArea(QFrame):
    """支持多文件选择与拖拽的文件区。"""

    files_changed = Signal(list)  # [file_path, ...]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("FileDropArea")
        self.setMinimumHeight(80)
        self._file_paths: list = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # 拖拽/点击提示
        self._hint_label = QLabel("点击选择文件，或将文件拖拽到此处（支持多文件）")
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint_label.setStyleSheet("color:#888;")
        layout.addWidget(self._hint_label)

        # 已选文件列表
        self._file_list = QListWidget()
        self._file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._file_list.setMinimumHeight(60)
        self._file_list.setMaximumHeight(150)
        self._file_list.setVisible(False)
        layout.addWidget(self._file_list)

        # 操作按钮行
        self._action_row = QHBoxLayout()
        self._select_btn = QPushButton("选择文件")
        self._select_btn.clicked.connect(self._pick_files)
        self._action_row.addWidget(self._select_btn)

        self._clear_btn = QPushButton("清空")
        self._clear_btn.setVisible(False)
        self._clear_btn.clicked.connect(self._clear_all)
        self._action_row.addWidget(self._clear_btn)

        self._remove_btn = QPushButton("移除选中")
        self._remove_btn.setVisible(False)
        self._remove_btn.clicked.connect(self._remove_selected)
        self._action_row.addWidget(self._remove_btn)

        self._action_row.addStretch()
        layout.addLayout(self._action_row)

    # ---- 文件操作 ----
    def file_count(self) -> int:
        return len(self._file_paths)

    def file_paths(self) -> list:
        return list(self._file_paths)

    # ---- 添加 / 移除 ----
    def _add_files(self, paths: list) -> None:
        added = False
        for p in paths:
            if os.path.isfile(p) and p not in self._file_paths:
                self._file_paths.append(p)
                icon = "⚠️" if not is_primary_extension(p) else "📄"
                item = QListWidgetItem(f"{icon} {os.path.basename(p)}")
                item.setToolTip(p)
                self._file_list.addItem(item)
                added = True
        if added:
            self._sync_visibility()
            self.files_changed.emit(self.file_paths())

    def _clear_all(self) -> None:
        self._file_paths.clear()
        self._file_list.clear()
        self._sync_visibility()
        self.files_changed.emit([])

    def _remove_selected(self) -> None:
        indices = sorted(
            {self._file_list.row(item) for item in self._file_list.selectedItems()},
            reverse=True,
        )
        for idx in indices:
            if 0 <= idx < len(self._file_paths):
                self._file_paths.pop(idx)
                self._file_list.takeItem(idx)
        self._sync_visibility()
        self.files_changed.emit(self.file_paths())

    def _sync_visibility(self) -> None:
        has_files = len(self._file_paths) > 0
        self._hint_label.setVisible(not has_files)
        self._file_list.setVisible(has_files)
        self._clear_btn.setVisible(has_files)
        self._remove_btn.setVisible(has_files)
        self._select_btn.setText("添加文件" if has_files else "选择文件")

    # ---- 拖拽 ----
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = []
        for url in event.mimeData().urls():
            p = url.toLocalFile()
            if os.path.isfile(p):
                paths.append(p)
        if paths:
            self._add_files(paths)

    # ---- 点击选择 ----
    def mousePressEvent(self, event) -> None:
        self._pick_files()

    def _pick_files(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        paths, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "Terraform / All Files (*.tf *.yaml *.yml *.json *.zip *.md);;All Files (*.*)"
        )
        if paths:
            self._add_files(paths)


# ======================================================================
class UploadWidget(QWidget):
    """上传表单。"""

    # 信号：(file_paths: list, region_name, overwrite, custom_dir)
    upload_requested = Signal(list, str, bool, str)
    # 请求检查对象是否存在：(file_paths: list, region_name, custom_dir)
    check_exists_requested = Signal(list, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._file_paths: list = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        group = QGroupBox("上传配置")
        gl = QVBoxLayout(group)

        # ---- 文件（多文件） ----
        gl.addWidget(QLabel("文件（支持多选）"))
        self._file_area = MultiFileDropArea()
        self._file_area.files_changed.connect(self._on_files_changed)
        gl.addWidget(self._file_area)

        # ---- 目录（自定义） ----
        dir_row = QHBoxLayout()
        dir_label = QLabel("目录")
        dir_label.setToolTip("自定义存储目录，默认使用文件名（去掉扩展名）")
        dir_row.addWidget(dir_label)
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("默认：文件名（不含扩展名）")
        self._dir_edit.textChanged.connect(self._update_preview)
        dir_row.addWidget(self._dir_edit, stretch=1)
        self._reset_dir_btn = QPushButton("↺ 还原")
        self._reset_dir_btn.setToolTip("还原为文件名（去掉扩展名）")
        self._reset_dir_btn.clicked.connect(self._reset_dir)
        dir_row.addWidget(self._reset_dir_btn)
        gl.addLayout(dir_row)

        # ---- 区域 ----
        gl.addWidget(QLabel("区域"))
        self._region_combo = QComboBox()
        for name in list_region_names():
            self._region_combo.addItem(name)
        self._region_combo.currentTextChanged.connect(self._on_region_changed)
        gl.addWidget(self._region_combo)

        # 目标 Bucket
        gl.addWidget(QLabel("目标 Bucket"))
        self._bucket_label = QLabel("—")
        self._bucket_label.setStyleSheet("color:#555; padding:2px 4px;")
        gl.addWidget(self._bucket_label)

        # 区域代码 / Endpoint
        meta_row = QHBoxLayout()
        meta_row.addWidget(QLabel("Region："))
        self._region_code_label = QLabel("—")
        self._region_code_label.setStyleSheet("color:#555;")
        meta_row.addWidget(self._region_code_label, stretch=1)
        meta_row.addWidget(QLabel("Endpoint："))
        self._endpoint_label = QLabel("—")
        self._endpoint_label.setStyleSheet("color:#555;")
        meta_row.addWidget(self._endpoint_label, stretch=2)
        gl.addLayout(meta_row)

        # ---- 目标路径预览 ----
        gl.addWidget(QLabel("目标路径（第一文件示例）"))
        self._path_label = QLabel("—")
        self._path_label.setStyleSheet(
            "color:#555; padding:2px 4px; word-wrap:break-word; font-size:12px;"
        )
        self._path_label.setWordWrap(True)
        gl.addWidget(self._path_label)

        # ---- 凭证提示 ----
        cred_hint = QLabel("💡 华为云凭证请在右上角「⚙️ 设置」中配置")
        cred_hint.setStyleSheet("color:#888; font-size:11px; padding:2px 0;")
        gl.addWidget(cred_hint)

        # ---- 上传按钮 ----
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._upload_btn = QPushButton("🚀 上传到 OBS")
        self._upload_btn.setMinimumHeight(40)
        self._upload_btn.clicked.connect(self._on_upload_clicked)
        btn_row.addWidget(self._upload_btn)
        btn_row.addStretch()
        gl.addLayout(btn_row)

        layout.addWidget(group)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        # 初始化预览
        self._on_region_changed(self._region_combo.currentText())

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _on_files_changed(self, paths: list) -> None:
        self._file_paths = paths
        if paths:
            # 仅当用户未手动修改目录名时，自动填充第一个文件的 solution-name
            if not self._dir_edit.text().strip():
                try:
                    default_dir = generate_solution_name(paths[0])
                    self._dir_edit.setText(default_dir)
                except Exception:
                    pass
        self._update_preview()

    def _on_region_changed(self, name: str) -> None:
        self._update_preview()

    def _reset_dir(self) -> None:
        """还原为第一个文件的 solution-name。"""
        if self._file_paths:
            try:
                default_dir = generate_solution_name(self._file_paths[0])
                self._dir_edit.setText(default_dir)
            except Exception:
                pass
        else:
            self._dir_edit.clear()

    # ------------------------------------------------------------------
    def _update_preview(self) -> None:
        name = self._region_combo.currentText()
        rc = get_region_config(name)
        if rc:
            self._bucket_label.setText(rc.bucket)
            self._region_code_label.setText(rc.region)
            self._endpoint_label.setText(rc.endpoint)

        custom_dir = self._dir_edit.text().strip() or None
        if self._file_paths:
            try:
                key = generate_object_key(self._file_paths[0], custom_dir)
                self._path_label.setText(key)
            except Exception:
                self._path_label.setText("—")
        else:
            if custom_dir:
                self._path_label.setText(
                    f"{object_key_prefix()}/{custom_dir}/{{filename}}"
                )
            else:
                self._path_label.setText(
                    f"{object_key_prefix()}/{{solution-name}}/{{filename}}"
                )

    # ------------------------------------------------------------------
    def set_uploading(self, uploading: bool) -> None:
        self._upload_btn.setEnabled(not uploading)
        self._upload_btn.setText("上传中…" if uploading else "🚀 上传到 OBS")

    # ------------------------------------------------------------------
    def _on_upload_clicked(self) -> None:
        if not self._file_paths or not all(os.path.isfile(p) for p in self._file_paths):
            QMessageBox.warning(self, "提示", "请先选择要上传的文件。")
            return
        region_name = self._region_combo.currentText()
        custom_dir = self._dir_edit.text().strip()
        # 先检查是否存在，由主窗口决定覆盖流程
        self.check_exists_requested.emit(self._file_paths, region_name, custom_dir)

    # ------------------------------------------------------------------
    def request_upload(self, overwrite: bool = True) -> None:
        """主窗口确认覆盖后调用此方法真正发起上传。"""
        if not self._file_paths:
            return
        region_name = self._region_combo.currentText()
        custom_dir = self._dir_edit.text().strip()
        self.upload_requested.emit(self._file_paths, region_name, overwrite, custom_dir)

    # ------------------------------------------------------------------
    def current_region(self) -> str:
        return self._region_combo.currentText()

    def current_custom_dir(self) -> str:
        return self._dir_edit.text().strip()

    # ------------------------------------------------------------------
    def refresh_regions(self) -> None:
        """设置变更后重新填充区域下拉框，尽量保留原选择。"""
        prev = self._region_combo.currentText()
        self._region_combo.blockSignals(True)
        self._region_combo.clear()
        for name in list_region_names():
            self._region_combo.addItem(name)
        idx = self._region_combo.findText(prev)
        if idx >= 0:
            self._region_combo.setCurrentIndex(idx)
        self._region_combo.blockSignals(False)
        self._update_preview()
