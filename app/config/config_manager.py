# -*- coding: utf-8 -*-
"""
用户配置管理器。

将凭证、目标路径前缀、区域映射表持久化到 user_settings.json，
未配置项回退到代码内默认值（即当前商定的值）。

配置文件位置：
- 打包后：exe 同目录下的 user_settings.json
- 开发时：项目根目录下的 user_settings.json

配置文件不进 Git（已加入 .gitignore）。
"""

import json
import os
import sys
from typing import Dict, List, Optional, Tuple

from app.config.regions import REGIONS as DEFAULT_REGIONS, RegionConfig
from app.config.settings import (
    ROOT_PREFIX as DEFAULT_ROOT_PREFIX,
    MODULE_PREFIX as DEFAULT_MODULE_PREFIX,
)
from app.utils.auth import Credentials


# ---------------------------------------------------------------------------
# 默认配置（从现有静态配置派生，确保「默认就是当前商定的值」）
# ---------------------------------------------------------------------------
def _default_credentials() -> dict:
    return {"access_key": "", "secret_key": "", "security_token": ""}


def _default_path_prefix() -> dict:
    return {"root_prefix": DEFAULT_ROOT_PREFIX, "module_prefix": DEFAULT_MODULE_PREFIX}


def _default_regions() -> dict:
    return {
        name: {
            "bucket": rc.bucket,
            "region": rc.region,
            "endpoint": rc.endpoint,
        }
        for name, rc in DEFAULT_REGIONS.items()
    }


def _default_settings() -> dict:
    return {
        "credentials": _default_credentials(),
        "path_prefix": _default_path_prefix(),
        "regions": _default_regions(),
    }


# ---------------------------------------------------------------------------
# 配置管理器
# ---------------------------------------------------------------------------
class ConfigManager:
    """单例配置管理器。未 init 时全部返回默认值。"""

    def __init__(self):
        self._path: Optional[str] = None
        self._data: dict = _default_settings()

    # ------------------------------------------------------------------
    # 初始化 / 加载 / 保存
    # ------------------------------------------------------------------
    def init(self, config_path: Optional[str] = None) -> None:
        """设置配置文件路径并加载。"""
        self._path = config_path or self._default_path()
        self._data = self._load()

    @staticmethod
    def _default_path() -> str:
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.getcwd()
        return os.path.join(base, "user_settings.json")

    def _load(self) -> dict:
        if not self._path or not os.path.isfile(self._path):
            return _default_settings()
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return _default_settings()
        # 与默认结构合并，保证缺失键有默认值
        merged = _default_settings()
        merged["credentials"].update(data.get("credentials", {}))
        merged["path_prefix"].update(data.get("path_prefix", {}))
        regions = data.get("regions")
        if isinstance(regions, dict) and regions:
            merged["regions"] = regions
        return merged

    def save(self) -> None:
        """把当前内存配置写入文件。"""
        if not self._path:
            self._path = self._default_path()
        try:
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @property
    def config_path(self) -> str:
        return self._path or self._default_path()

    # ------------------------------------------------------------------
    # 凭证
    # ------------------------------------------------------------------
    def get_credentials(self) -> Optional[Credentials]:
        c = self._data.get("credentials", {})
        ak = str(c.get("access_key", "")).strip()
        sk = str(c.get("secret_key", "")).strip()
        token = str(c.get("security_token", "")).strip() or None
        if ak and sk:
            return Credentials(ak, sk, token)
        return None

    def set_credentials(self, access_key: str, secret_key: str,
                        security_token: str = "") -> None:
        self._data.setdefault("credentials", {})
        self._data["credentials"]["access_key"] = access_key or ""
        self._data["credentials"]["secret_key"] = secret_key or ""
        self._data["credentials"]["security_token"] = security_token or ""

    # ------------------------------------------------------------------
    # 目标路径前缀
    # ------------------------------------------------------------------
    def get_path_prefix(self) -> Tuple[str, str]:
        p = self._data.get("path_prefix", {})
        root = str(p.get("root_prefix", DEFAULT_ROOT_PREFIX)).strip() or DEFAULT_ROOT_PREFIX
        module = str(p.get("module_prefix", DEFAULT_MODULE_PREFIX)).strip() or DEFAULT_MODULE_PREFIX
        return root, module

    def set_path_prefix(self, root_prefix: str, module_prefix: str) -> None:
        self._data.setdefault("path_prefix", {})
        self._data["path_prefix"]["root_prefix"] = root_prefix or DEFAULT_ROOT_PREFIX
        self._data["path_prefix"]["module_prefix"] = module_prefix or DEFAULT_MODULE_PREFIX

    def object_key_prefix(self) -> str:
        root, module = self.get_path_prefix()
        return f"{root}/{module}"

    # ------------------------------------------------------------------
    # 区域映射
    # ------------------------------------------------------------------
    def get_regions(self) -> Dict[str, RegionConfig]:
        result: Dict[str, RegionConfig] = {}
        regions = self._data.get("regions", {})
        for name, cfg in regions.items():
            try:
                result[name] = RegionConfig(
                    name=name,
                    region=str(cfg.get("region", "")).strip(),
                    bucket=str(cfg.get("bucket", "")).strip(),
                    endpoint=str(cfg.get("endpoint", "")).strip(),
                )
            except Exception:
                continue
        if not result:
            return dict(DEFAULT_REGIONS)
        return result

    def get_region_config(self, name: str) -> Optional[RegionConfig]:
        return self.get_regions().get(name)

    def list_region_names(self) -> List[str]:
        return list(self.get_regions().keys())

    def set_regions(self, regions: Dict[str, dict]) -> None:
        """regions: {name: {bucket, region, endpoint}}"""
        self._data["regions"] = regions

    def reset_regions_to_default(self) -> None:
        self._data["regions"] = _default_regions()

    # ------------------------------------------------------------------
    # 整体读写（供设置对话框使用）
    # ------------------------------------------------------------------
    def get_all_settings(self) -> dict:
        """返回当前生效配置的深拷贝（供 UI 编辑）。"""
        return json.loads(json.dumps(self._data, ensure_ascii=False))

    def apply_settings(self, settings: dict) -> None:
        """用 UI 编辑结果覆盖内存配置（不立即落盘）。"""
        creds = settings.get("credentials", {})
        self.set_credentials(
            creds.get("access_key", ""),
            creds.get("secret_key", ""),
            creds.get("security_token", ""),
        )
        prefix = settings.get("path_prefix", {})
        self.set_path_prefix(
            prefix.get("root_prefix", DEFAULT_ROOT_PREFIX),
            prefix.get("module_prefix", DEFAULT_MODULE_PREFIX),
        )
        regions = settings.get("regions", {})
        if isinstance(regions, dict):
            self.set_regions(regions)

    def save_settings(self, settings: dict) -> None:
        """应用并持久化。"""
        self.apply_settings(settings)
        self.save()


# 全局单例
config_manager = ConfigManager()
