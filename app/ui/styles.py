# -*- coding: utf-8 -*-
"""
全局 QSS 样式表 —— 现代浅色主题。
"""

GLOBAL_QSS = """
/* ===================== 基础 ===================== */
QWidget {
    font-size: 13px;
    font-family: "Segoe UI", "Microsoft YaHei UI", "PingFang SC", sans-serif;
    color: #1f2937;
}
QMainWindow, QDialog {
    background-color: #f4f5f7;
}

/* ===================== 卡片（QGroupBox） ===================== */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    margin-top: 16px;
    padding: 12px 14px 12px 14px;
    font-weight: 600;
    color: #374151;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background-color: #ffffff;
    border-radius: 4px;
    font-size: 13px;
    color: #2563eb;
}

/* ===================== 标签 ===================== */
QLabel {
    background: transparent;
}
QLabel#AppTitle {
    font-size: 22px;
    font-weight: 700;
    color: #111827;
    padding: 0;
}
QLabel#AppSubtitle {
    font-size: 12px;
    color: #9ca3af;
    padding: 0;
}
QLabel#SectionLabel {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
}

/* ===================== 输入框 ===================== */
QLineEdit {
    padding: 7px 10px;
    border: 1px solid #d1d5db;
    border-radius: 7px;
    background-color: #ffffff;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 1.5px solid #2563eb;
    background-color: #ffffff;
}
QLineEdit:disabled {
    background-color: #f3f4f6;
    color: #9ca3af;
}

/* ===================== 下拉框 ===================== */
QComboBox {
    padding: 7px 10px;
    border: 1px solid #d1d5db;
    border-radius: 7px;
    background-color: #ffffff;
    min-height: 18px;
}
QComboBox:hover {
    border-color: #9ca3af;
}
QComboBox:focus {
    border: 1.5px solid #2563eb;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6b7280;
    width: 0;
    height: 0;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    border: 1px solid #d1d5db;
    border-radius: 6px;
    background-color: #ffffff;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* ===================== 按钮 ===================== */
QPushButton {
    padding: 7px 16px;
    border: 1px solid #d1d5db;
    border-radius: 7px;
    background-color: #ffffff;
    color: #374151;
}
QPushButton:hover {
    border-color: #9ca3af;
    background-color: #f9fafb;
}
QPushButton:pressed {
    background-color: #f3f4f6;
}
QPushButton:disabled {
    color: #cbd5e1;
    border-color: #e5e7eb;
    background-color: #f9fafb;
}

/* 主按钮 */
QPushButton#PrimaryBtn {
    background-color: #2563eb;
    border: none;
    color: #ffffff;
    font-weight: 600;
    font-size: 14px;
    padding: 11px 24px;
    border-radius: 8px;
}
QPushButton#PrimaryBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#PrimaryBtn:pressed {
    background-color: #1e40af;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #93c5fd;
    color: #ffffff;
}

/* 次按钮（小图标按钮） */
QPushButton#GhostBtn {
    background-color: transparent;
    border: 1px solid #e5e7eb;
    color: #6b7280;
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 12px;
}
QPushButton#GhostBtn:hover {
    background-color: #f3f4f6;
    color: #374151;
    border-color: #d1d5db;
}

/* 设置按钮 */
QPushButton#SettingsBtn {
    background-color: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 13px;
    color: #374151;
}
QPushButton#SettingsBtn:hover {
    background-color: #eff6ff;
    border-color: #93c5fd;
    color: #2563eb;
}

/* ===================== 文件拖拽区 ===================== */
QFrame#FileDropArea {
    border: 2px dashed #cbd5e1;
    border-radius: 10px;
    background-color: #f9fafb;
}
QFrame#FileDropArea:hover {
    border-color: #2563eb;
    background-color: #eff6ff;
}

/* ===================== 信息卡片 ===================== */
QFrame#InfoBox {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}

/* ===================== 路径预览 ===================== */
QLabel#PathPreview {
    color: #6b7280;
    padding: 6px 10px;
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    font-size: 12px;
}

/* ===================== 列表 ===================== */
QListWidget {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: #ffffff;
    padding: 3px;
    outline: none;
}
QListWidget::item {
    padding: 5px 8px;
    border-radius: 5px;
}
QListWidget::item:hover {
    background-color: #f3f4f6;
}
QListWidget::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}

/* ===================== 文本编辑 / 日志 ===================== */
QTextEdit {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: #ffffff;
    padding: 6px;
    font-family: "Consolas", "Cascadia Code", "Microsoft YaHei UI", monospace;
    font-size: 12px;
}
QTextEdit#StepsText {
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
}

/* ===================== 进度条 ===================== */
QProgressBar {
    border: none;
    border-radius: 7px;
    background-color: #e5e7eb;
    text-align: center;
    height: 14px;
    font-size: 11px;
    color: #374151;
}
QProgressBar::chunk {
    border-radius: 7px;
    background-color: #2563eb;
}

/* ===================== 滚动条 ===================== */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 9px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 9px;
    margin: 0;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===================== 分隔器 ===================== */
QSplitter::handle {
    background-color: #e5e7eb;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #2563eb;
}

/* ===================== 表格（设置对话框） ===================== */
QTableWidget {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background-color: #ffffff;
    gridline-color: #f3f4f6;
    outline: none;
}
QTableWidget::item {
    padding: 5px;
}
QTableWidget::item:selected {
    background-color: #dbeafe;
    color: #1e40af;
}
QHeaderView::section {
    background-color: #f9fafb;
    border: none;
    border-right: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    padding: 6px 8px;
    font-weight: 600;
    color: #6b7280;
}

/* ===================== 消息框 ===================== */
QMessageBox {
    background-color: #ffffff;
}

/* ===================== 工具提示 ===================== */
QToolTip {
    background-color: #1f2937;
    color: #f9fafb;
    border: none;
    border-radius: 6px;
    padding: 5px 8px;
    font-size: 12px;
}
"""
