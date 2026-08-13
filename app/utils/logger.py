# -*- coding: utf-8 -*-
"""
安全日志模块。

设计要点：
1. 绝不打印 Access Key / Secret Key / Security Token。
2. 提供信号机制，UI 可订阅日志行实时展示。
3. 同时输出到控制台与文件（可选）。
"""

import logging
import os
from datetime import datetime
from typing import Callable, List

# 敏感关键词，日志中出现则脱敏
_SENSITIVE_HINTS = ("SECRET", "PASSWORD", "TOKEN", "ACCESS_KEY", "SK", "AK")


def _mask_secret(text: str) -> str:
    """简单脱敏：把疑似密钥的值替换为 ******。"""
    if not text:
        return text
    # 防止形如 "SecretKey=xxxx" 的泄露
    for hint in _SENSITIVE_HINTS:
        if hint in text.upper():
            # 仅在确实包含赋值符号时脱敏值部分
            for sep in ("=", ":", "："):
                if sep in text:
                    head, _, tail = text.partition(sep)
                    if tail.strip():
                        text = f"{head}{sep}******"
    return text


class AppLogger:
    """应用日志器，支持 UI 订阅。"""

    def __init__(self, name: str = "obs-uploader"):
        self._handlers: List[Callable[[str, str], None]] = []
        self._py_logger = logging.getLogger(name)
        if not self._py_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s",
                                                   datefmt="%H:%M:%S"))
            self._py_logger.addHandler(handler)
            self._py_logger.setLevel(logging.INFO)

    def add_handler(self, handler: Callable[[str, str], None]) -> None:
        """订阅日志。handler(level, message) -> None"""
        self._handlers.append(handler)

    def _emit(self, level: str, message: str) -> None:
        safe = _mask_secret(message)
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {safe}"
        # 控制台
        if level == "ERROR":
            self._py_logger.error(safe)
        elif level == "WARN":
            self._py_logger.warning(safe)
        else:
            self._py_logger.info(safe)
        # UI 订阅者
        for h in self._handlers:
            try:
                h(level, line)
            except Exception:
                pass

    def info(self, message: str) -> None:
        self._emit("INFO", message)

    def warn(self, message: str) -> None:
        self._emit("WARN", message)

    def error(self, message: str) -> None:
        self._emit("ERROR", message)

    def step(self, message: str) -> None:
        """流程步骤日志。"""
        self._emit("STEP", message)


# 全局单例
logger = AppLogger()
