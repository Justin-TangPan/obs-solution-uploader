# -*- coding: utf-8 -*-
"""
应用入口。

运行方式：
    python -m app.main
或：
    python app/main.py
"""

import os
import sys


def main() -> None:
    # 确保项目根目录在 sys.path 中（支持直接 python app/main.py 运行）
    if __package__ is None or __package__ == "":
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

    from PySide6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow
    from app.config.config_manager import config_manager

    # 初始化用户配置（凭证 / 路径前缀 / 区域映射）
    config_path = os.path.join(os.getcwd(), "user_settings.json")
    config_manager.init(config_path)

    app = QApplication(sys.argv)
    app.setApplicationName("OBS Solution Uploader")

    # 全局样式
    app.setStyleSheet("""
        QWidget { font-size: 13px; }
        QGroupBox { font-weight: bold; margin-top: 10px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
        QPushButton { padding: 6px 14px; }
        #FileDropArea {
            border: 2px dashed #bbb;
            border-radius: 6px;
            background: #fafafa;
        }
        #FileDropArea:hover { border-color: #1565c0; background: #f0f7ff; }
        QLineEdit, QComboBox { padding: 4px 6px; }
    """)

    yaml_config_path = os.path.join(os.getcwd(), "config.yaml")
    window = MainWindow(config_path=yaml_config_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
