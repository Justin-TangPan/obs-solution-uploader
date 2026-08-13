# -*- coding: utf-8 -*-
"""
公网 URL 生成服务。

规则：https://{bucket}.{endpoint}/{url-encoded-object-key}
"""

from urllib.parse import quote

from app.config.regions import RegionConfig


def generate_public_url(region: RegionConfig, object_key: str) -> str:
    """
    生成对象的公网访问 URL。

    :param region:  区域配置
    :param object_key: 对象 Key（可能含中文/特殊字符）
    :return: 完整 https URL
    """
    # Object Key 中的 / 不应被编码，仅编码每一段内的特殊字符
    safe_chars = "/"
    encoded_key = quote(object_key, safe=safe_chars)
    return f"https://{region.bucket_endpoint}/{encoded_key}"
