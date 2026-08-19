# -*- coding: utf-8 -*-
"""
设置对话框：凭证 / 目标路径前缀 / 区域映射表 全部前端可配置。

保存到 user_settings.json（通过 config_manager），默认值即当前商定的值。
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QSizePolicy, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.config.config_manager import config_manager
from app.config.regions import REGIONS as DEFAULT_REGIONS


class SettingsDialog(QDialog):
    """应用设置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(720, 620)
        self.setMinimumSize(560, 480)
        self._init_ui()
        self._load_from_config()
        self._auto_fit_table()

    # ------------------------------------------------------------------
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # ---- 凭证 ----
        cred_group = QGroupBox("🔐 华为云凭证（保存到本地 user_settings.json，不进 Git）")
        cred_form = QFormLayout(cred_group)
        cred_form.setSpacing(8)
        self._ak_edit = QLineEdit()
        self._ak_edit.setPlaceholderText("Access Key ID")
        cred_form.addRow("Access Key", self._ak_edit)

        self._sk_edit = QLineEdit()
        self._sk_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._sk_edit.setPlaceholderText("Secret Access Key")
        cred_form.addRow("Secret Key", self._sk_edit)

        self._token_edit = QLineEdit()
        self._token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_edit.setPlaceholderText("临时凭证才填，普通 AK/SK 留空")
        cred_form.addRow("Security Token", self._token_edit)

        hint = QLabel("提示：留空则回退到环境变量 / config.yaml。Secret Key 以密码形式显示。")
        hint.setStyleSheet("color:#9ca3af; font-size:11px;")
        hint.setWordWrap(True)
        cred_form.addRow(hint)
        layout.addWidget(cred_group)

        # ---- 目标路径前缀 ----
        path_group = QGroupBox("📁 目标路径前缀（Object Key 的固定根目录）")
        path_form = QFormLayout(path_group)
        path_form.setSpacing(8)
        self._root_edit = QLineEdit()
        self._root_edit.setPlaceholderText("solution-as-code-publicbucket")
        path_form.addRow("根目录 (root_prefix)", self._root_edit)

        self._module_edit = QLineEdit()
        self._module_edit.setPlaceholderText("solution-as-code-moudle")
        path_form.addRow("模块目录 (module_prefix)", self._module_edit)

        path_hint = QLabel("最终路径：{root}/{module}/{solution-name}/{filename}")
        path_hint.setStyleSheet("color:#9ca3af; font-size:11px;")
        path_form.addRow(path_hint)
        layout.addWidget(path_group)

        # ---- 区域映射表 ----
        region_group = QGroupBox("🌐 区域映射表（显示名称 / Region Code / Bucket / Endpoint）")
        region_layout = QVBoxLayout(region_group)
        region_layout.setSpacing(8)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["显示名称", "Region Code", "Bucket", "Endpoint"])
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        self._table.setMinimumHeight(180)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        region_layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self._add_btn = QPushButton("＋ 新增区域")
        self._add_btn.setObjectName("GhostBtn")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._add_row)
        btn_row.addWidget(self._add_btn)

        self._del_btn = QPushButton("－ 删除选中")
        self._del_btn.setObjectName("GhostBtn")
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.clicked.connect(self._del_row)
        btn_row.addWidget(self._del_btn)

        self._reset_btn = QPushButton("↺ 恢复默认区域")
        self._reset_btn.setObjectName("GhostBtn")
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.clicked.connect(self._reset_regions)
        btn_row.addWidget(self._reset_btn)

        btn_row.addStretch()
        region_layout.addLayout(btn_row)
        layout.addWidget(region_group, stretch=1)

        # ---- 底部按钮 ----
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("GhostBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        footer.addWidget(cancel_btn)

        save_btn = QPushButton("💾  保存")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setMinimumHeight(38)
        save_btn.clicked.connect(self._on_save)
        footer.addWidget(save_btn)
        layout.addLayout(footer)

    # ------------------------------------------------------------------
    def _load_from_config(self) -> None:
        """从配置管理器加载当前生效值到控件。"""
        settings = config_manager.get_all_settings()

        creds = settings.get("credentials", {})
        self._ak_edit.setText(creds.get("access_key", ""))
        self._sk_edit.setText(creds.get("secret_key", ""))
        self._token_edit.setText(creds.get("security_token", ""))

        prefix = settings.get("path_prefix", {})
        self._root_edit.setText(prefix.get("root_prefix", ""))
        self._module_edit.setText(prefix.get("module_prefix", ""))

        regions = settings.get("regions", {})
        self._fill_table(regions)

    # ------------------------------------------------------------------
    def _fill_table(self, regions: dict) -> None:
        self._table.setRowCount(0)
        for name, cfg in regions.items():
            self._add_row_data(
                name,
                cfg.get("region", ""),
                cfg.get("bucket", ""),
                cfg.get("endpoint", ""),
            )

    def _auto_fit_table(self) -> None:
        """根据内容自动调整列宽，并自适应行高。"""
        self._table.resizeColumnsToContents()
        # 给前 3 列留一点余量，最后一列 Stretch 自动撑满
        for col in range(3):
            w = self._table.columnWidth(col)
            self._table.setColumnWidth(col, w + 16)
        self._table.resizeRowsToContents()

    def _add_row_data(self, name: str, region: str, bucket: str,
                      endpoint: str) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._table.setItem(row, 0, QTableWidgetItem(name))
        self._table.setItem(row, 1, QTableWidgetItem(region))
        self._table.setItem(row, 2, QTableWidgetItem(bucket))
        self._table.setItem(row, 3, QTableWidgetItem(endpoint))

    def _add_row(self) -> None:
        self._add_row_data("", "", "", "")
        self._auto_fit_table()
        self._table.editItem(self._table.item(self._table.rowCount() - 1, 0))

    def _del_row(self) -> None:
        rows = sorted({idx.row() for idx in self._table.selectedIndexes()},
                      reverse=True)
        for r in rows:
            self._table.removeRow(r)
        self._auto_fit_table()

    def _reset_regions(self) -> None:
        """恢复区域表为代码内默认值。"""
        default = {
            name: {"bucket": rc.bucket, "region": rc.region, "endpoint": rc.endpoint}
            for name, rc in DEFAULT_REGIONS.items()
        }
        self._fill_table(default)
        self._auto_fit_table()

    # ------------------------------------------------------------------
    def _collect_regions(self) -> dict:
        regions = {}
        for row in range(self._table.rowCount()):
            name = self._table.item(row, 0).text().strip() if self._table.item(row, 0) else ""
            region = self._table.item(row, 1).text().strip() if self._table.item(row, 1) else ""
            bucket = self._table.item(row, 2).text().strip() if self._table.item(row, 2) else ""
            endpoint = self._table.item(row, 3).text().strip() if self._table.item(row, 3) else ""
            if not name:
                continue
            regions[name] = {"bucket": bucket, "region": region, "endpoint": endpoint}
        return regions

    # ------------------------------------------------------------------
    def _on_save(self) -> None:
        # 校验路径前缀
        root = self._root_edit.text().strip()
        module = self._module_edit.text().strip()
        if not root or not module:
            QMessageBox.warning(self, "提示", "目标路径前缀不能为空。")
            return

        regions = self._collect_regions()
        if not regions:
            QMessageBox.warning(self, "提示", "至少需要配置一个区域。")
            return

        # 校验区域字段完整性
        for name, cfg in regions.items():
            missing = [k for k in ("region", "bucket", "endpoint") if not cfg[k]]
            if missing:
                QMessageBox.warning(
                    self, "提示",
                    f"区域「{name}」缺少字段：{', '.join(missing)}",
                )
                return

        settings = {
            "credentials": {
                "access_key": self._ak_edit.text().strip(),
                "secret_key": self._sk_edit.text().strip(),
                "security_token": self._token_edit.text().strip(),
            },
            "path_prefix": {"root_prefix": root, "module_prefix": module},
            "regions": regions,
        }
        try:
            config_manager.save_settings(settings)
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"配置保存失败：{e}")
            return

        QMessageBox.information(self, "已保存", "设置已保存，将在下次操作时生效。")
        self.accept()
