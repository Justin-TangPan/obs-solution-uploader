# -*- coding: utf-8 -*-
"""
文件名解析与 Object Key 生成工具。
"""

import os
from typing import Tuple

from app.config.settings import object_key_prefix, SUPPORTED_EXTENSIONS, PRIMARY_EXTENSION


def parse_filename(file_path: str) -> Tuple[str, str, str]:
    """
    解析文件路径。

    :param file_path: 本地文件完整路径
    :return: (solution_name, filename, ext)
        solution_name : 去掉扩展名后的文件名，如 "deploying-cognee"
        filename      : 带扩展名的文件名，如 "deploying-cognee.tf"
        ext           : 小写扩展名（含点），如 ".tf"
    :raises FileNotFoundError: 文件不存在
    """
    if not file_path or not os.path.isfile(file_path):
        raise FileNotFoundError("选择的文件不存在或无法读取。")

    filename = os.path.basename(file_path)
    name_part, ext = os.path.splitext(filename)
    return name_part, filename, ext.lower()


def generate_solution_name(file_path: str) -> str:
    """根据文件名生成 solution-name（去掉扩展名）。"""
    name_part, _, _ = parse_filename(file_path)
    return name_part


def generate_object_key(file_path: str, custom_dir: str = None) -> str:
    """
    生成 OBS Object Key。

    规则：{root_prefix}/{module_prefix}/{custom_dir}/{filename}
    前缀来自用户配置（默认 solution-as-code-publicbucket/solution-as-code-moudle）。
    custom_dir 默认为 solution-name（文件名去掉扩展名）。

    例：
        deploying-cognee.tf, custom_dir=None
        -> solution-as-code-publicbucket/solution-as-code-moudle/deploying-cognee/deploying-cognee.tf

        deploying-cognee.tf, custom_dir="my-app"
        -> solution-as-code-publicbucket/solution-as-code-moudle/my-app/deploying-cognee.tf
    """
    from app.config.config_manager import config_manager
    solution_name, filename, _ = parse_filename(file_path)
    prefix = config_manager.object_key_prefix()
    directory = (custom_dir or solution_name).strip()
    if not directory:
        directory = solution_name
    return f"{prefix}/{directory}/{filename}"


def is_supported_extension(file_path: str) -> bool:
    """判断文件扩展名是否在支持列表内。"""
    _, _, ext = parse_filename(file_path)
    return ext in SUPPORTED_EXTENSIONS


def is_primary_extension(file_path: str) -> bool:
    """判断是否为主推扩展名（.tf）。"""
    _, _, ext = parse_filename(file_path)
    return ext == PRIMARY_EXTENSION


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）。"""
    return os.path.getsize(file_path)
