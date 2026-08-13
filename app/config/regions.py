# -*- coding: utf-8 -*-
"""
OBS 区域与桶名称映射配置。

每个区域包含：
    name     : 用户可见的中文/英文区域名称
    region   : 华为云区域代码（用于 SDK 认证与 endpoint 生成）
    bucket   : 该区域对应的 OBS 桶名称
    endpoint : OBS 访问 endpoint（不含 bucket 前缀）

以后增加区域，只需在 REGIONS 中追加一项，无需修改上传逻辑。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RegionConfig:
    """单个区域的 OBS 访问配置。"""
    name: str        # 显示名称，如 "华北-北京四"
    region: str      # 区域代码，如 "cn-north-4"
    bucket: str      # 桶名称，如 "documentation-samples"
    endpoint: str    # OBS endpoint，如 "obs.cn-north-4.myhuaweicloud.com"

    @property
    def server(self) -> str:
        """ObsClient 需要的完整 server 地址。"""
        return f"https://{self.endpoint}"

    @property
    def bucket_endpoint(self) -> str:
        """桶级访问域名：{bucket}.{endpoint}。"""
        return f"{self.bucket}.{self.endpoint}"


# ---------------------------------------------------------------------------
# 区域映射表
# endpoint 统一遵循华为云 OBS 官方规则：obs.{region}.myhuaweicloud.com
# ---------------------------------------------------------------------------
REGIONS: Dict[str, RegionConfig] = {
    "华北-北京四": RegionConfig(
        name="华北-北京四", region="cn-north-4",
        bucket="documentation-samples",
        endpoint="obs.cn-north-4.myhuaweicloud.com",
    ),
    "华南-广州": RegionConfig(
        name="华南-广州", region="cn-south-1",
        bucket="documentation-samples-2",
        endpoint="obs.cn-south-1.myhuaweicloud.com",
    ),
    "华东-上海": RegionConfig(
        name="华东-上海", region="cn-east-3",
        bucket="documentation-samples-3",
        endpoint="obs.cn-east-3.myhuaweicloud.com",
    ),
    "西南-贵阳": RegionConfig(
        name="西南-贵阳", region="cn-southwest-2",
        bucket="documentation-samples-9",
        endpoint="obs.cn-southwest-2.myhuaweicloud.com",
    ),
    "华北-乌兰察布一": RegionConfig(
        name="华北-乌兰察布一", region="cn-north-9",
        bucket="documentation-samples-17",
        endpoint="obs.cn-north-9.myhuaweicloud.com",
    ),
    "cn-east-4": RegionConfig(
        name="cn-east-4", region="cn-east-4",
        bucket="documentation-samples-16",
        endpoint="obs.cn-east-4.myhuaweicloud.com",
    ),
    "中国-香港": RegionConfig(
        name="中国-香港", region="ap-southeast-1",
        bucket="documentation-samples-5",
        endpoint="obs.ap-southeast-1.myhuaweicloud.com",
    ),
    "亚太-新加坡": RegionConfig(
        name="亚太-新加坡", region="ap-southeast-3",
        bucket="documentation-samples-4",
        endpoint="obs.ap-southeast-3.myhuaweicloud.com",
    ),
    "亚太-曼谷": RegionConfig(
        name="亚太-曼谷", region="ap-southeast-2",
        bucket="documentation-samples-6",
        endpoint="obs.ap-southeast-2.myhuaweicloud.com",
    ),
    "亚太-雅加达": RegionConfig(
        name="亚太-雅加达", region="ap-southeast-4",
        bucket="documentation-samples-18",
        endpoint="obs.ap-southeast-4.myhuaweicloud.com",
    ),
    "土耳其-伊斯坦布尔": RegionConfig(
        name="土耳其-伊斯坦布尔", region="tr-west-1",
        bucket="documentation-samples-8",
        endpoint="obs.tr-west-1.myhuaweicloud.com",
    ),
    "南非-约翰内斯堡": RegionConfig(
        name="南非-约翰内斯堡", region="af-south-1",
        bucket="documentation-samples-11",
        endpoint="obs.af-south-1.myhuaweicloud.com",
    ),
    "中东-利雅得": RegionConfig(
        name="中东-利雅得", region="me-east-1",
        bucket="documentation-samples-12",
        endpoint="obs.me-east-1.myhuaweicloud.com",
    ),
    "拉美-墨西哥城一": RegionConfig(
        name="拉美-墨西哥城一", region="na-mexico-1",
        bucket="documentation-samples-19",
        endpoint="obs.na-mexico-1.myhuaweicloud.com",
    ),
    "拉美-墨西哥城二": RegionConfig(
        name="拉美-墨西哥城二", region="na-mexico-2",
        bucket="documentation-samples-13",
        endpoint="obs.na-mexico-2.myhuaweicloud.com",
    ),
    "拉美-圣保罗一": RegionConfig(
        name="拉美-圣保罗一", region="sa-brazil-1",
        bucket="documentation-samples-14",
        endpoint="obs.sa-brazil-1.myhuaweicloud.com",
    ),
    "拉美-圣地亚哥": RegionConfig(
        name="拉美-圣地亚哥", region="la-south-2",
        bucket="documentation-samples-15",
        endpoint="obs.la-south-2.myhuaweicloud.com",
    ),
    "af-north-1": RegionConfig(
        name="af-north-1", region="af-north-1",
        bucket="documentation-samples-10",
        endpoint="obs.af-north-1.myhuaweicloud.com",
    ),
}


def get_region_config(region_name: str) -> Optional[RegionConfig]:
    """根据区域显示名称获取生效 RegionConfig，不存在返回 None。

    优先读取用户配置（config_manager），未配置时回退到默认 REGIONS。
    """
    from app.config.config_manager import config_manager
    return config_manager.get_region_config(region_name) or REGIONS.get(region_name)


def list_region_names() -> List[str]:
    """返回所有生效区域显示名称。"""
    from app.config.config_manager import config_manager
    names = config_manager.list_region_names()
    return names if names else list(REGIONS.keys())
