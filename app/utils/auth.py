# -*- coding: utf-8 -*-
"""
认证信息加载。

优先级：
1. 环境变量 HUAWEICLOUD_ACCESS_KEY / HUAWEICLOUD_SECRET_KEY
2. config.yaml（若存在）
3. UI 运行时输入（通过参数传入）

绝不把凭证写入源码或日志。
"""

import os
from dataclasses import dataclass
from typing import Optional

import yaml

from app.config.settings import ENV_ACCESS_KEY, ENV_SECRET_KEY, ENV_SECURITY_TOKEN, CONFIG_FILE


@dataclass
class Credentials:
    access_key: str
    secret_key: str
    security_token: Optional[str] = None

    def is_valid(self) -> bool:
        return bool(self.access_key) and bool(self.secret_key)


def load_from_env() -> Optional[Credentials]:
    """从环境变量加载凭证。"""
    ak = os.environ.get(ENV_ACCESS_KEY, "").strip()
    sk = os.environ.get(ENV_SECRET_KEY, "").strip()
    token = os.environ.get(ENV_SECURITY_TOKEN, "").strip() or None
    if ak and sk:
        return Credentials(ak, sk, token)
    return None


def load_from_config(config_path: Optional[str] = None) -> Optional[Credentials]:
    """从 config.yaml 加载凭证。"""
    path = config_path or CONFIG_FILE
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return None
    ak = str(data.get("access_key", "")).strip()
    sk = str(data.get("secret_key", "")).strip()
    token = str(data.get("security_token", "")).strip() or None
    if ak and sk:
        return Credentials(ak, sk, token)
    return None


def load_credentials(config_path: Optional[str] = None,
                     override: Optional[Credentials] = None,
                     user_settings_cred: Optional[Credentials] = None) -> Optional[Credentials]:
    """
    按优先级加载凭证。

    优先级：override（UI 运行时输入）> user_settings_cred（设置面板保存）
            > 环境变量 > config.yaml
    """
    if override and override.is_valid():
        return override
    if user_settings_cred and user_settings_cred.is_valid():
        return user_settings_cred
    env_cred = load_from_env()
    if env_cred:
        return env_cred
    file_cred = load_from_config(config_path)
    if file_cred:
        return file_cred
    return None
