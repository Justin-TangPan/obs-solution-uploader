# -*- coding: utf-8 -*-
"""
应用全局设置：固定目录、支持的文件类型、认证相关常量。
"""

# OBS 对象 Key 固定根目录
ROOT_PREFIX = "solution-as-code-publicbucket"
MODULE_PREFIX = "solution-as-code-moudle"

# 第一版主推 .tf，同时允许以下扩展名（方便后续扩展）
SUPPORTED_EXTENSIONS = (".tf", ".yaml", ".yml", ".json", ".zip", ".md")
PRIMARY_EXTENSION = ".tf"

# 公共读 ACL 值（OBS / S3 标准值）
ACL_PUBLIC_READ = "public-read"
ACL_PRIVATE = "private"

# 认证相关环境变量名
ENV_ACCESS_KEY = "HUAWEICLOUD_ACCESS_KEY"
ENV_SECRET_KEY = "HUAWEICLOUD_SECRET_KEY"
ENV_SECURITY_TOKEN = "HUAWEICLOUD_SECURITY_TOKEN"  # 临时访问凭证（可选）

# 配置文件名
CONFIG_FILE = "config.yaml"


def object_key_prefix() -> str:
    """返回固定根目录前缀：solution-as-code-publicbucket/solution-as-code-moudle/"""
    return f"{ROOT_PREFIX}/{MODULE_PREFIX}"
