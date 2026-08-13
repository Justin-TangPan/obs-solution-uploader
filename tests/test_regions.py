# -*- coding: utf-8 -*-
"""区域配置与 Object Key / URL 生成单元测试。"""

import os
import sys
import unittest

# 确保可导入 app 包
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config.regions import REGIONS, get_region_config, list_region_names
from app.services.url_service import generate_public_url
from app.utils.file_utils import generate_object_key, generate_solution_name


class TestRegions(unittest.TestCase):

    def test_region_count(self):
        self.assertEqual(len(REGIONS), 18)

    def test_beijing_four(self):
        rc = get_region_config("华北-北京四")
        self.assertIsNotNone(rc)
        self.assertEqual(rc.bucket, "documentation-samples")
        self.assertEqual(rc.region, "cn-north-4")
        self.assertEqual(rc.endpoint, "obs.cn-north-4.myhuaweicloud.com")

    def test_guangzhou(self):
        rc = get_region_config("华南-广州")
        self.assertEqual(rc.bucket, "documentation-samples-2")
        self.assertEqual(rc.region, "cn-south-1")

    def test_shanghai(self):
        rc = get_region_config("华东-上海")
        self.assertEqual(rc.bucket, "documentation-samples-3")

    def test_all_endpoints_match_pattern(self):
        for name, rc in REGIONS.items():
            self.assertTrue(rc.endpoint.startswith("obs."))
            self.assertTrue(rc.endpoint.endswith(".myhuaweicloud.com"))
            self.assertIn(rc.region, rc.endpoint)

    def test_unknown_region(self):
        self.assertIsNone(get_region_config("不存在的区域"))


class TestObjectKey(unittest.TestCase):

    def setUp(self):
        # 创建临时 .tf 文件用于测试
        self.tmp = os.path.join(os.path.dirname(__file__), "deploying-cognee.tf")
        with open(self.tmp, "w", encoding="utf-8") as f:
            f.write("# test")

    def tearDown(self):
        if os.path.exists(self.tmp):
            os.remove(self.tmp)

    def test_solution_name(self):
        self.assertEqual(generate_solution_name(self.tmp), "deploying-cognee")

    def test_object_key(self):
        key = generate_object_key(self.tmp)
        self.assertEqual(
            key,
            "solution-as-code-publicbucket/solution-as-code-moudle/"
            "deploying-cognee/deploying-cognee.tf",
        )


class TestPublicUrl(unittest.TestCase):

    def test_beijing_url(self):
        rc = get_region_config("华北-北京四")
        key = ("solution-as-code-publicbucket/solution-as-code-moudle/"
               "deploying-cognee/deploying-cognee.tf")
        url = generate_public_url(rc, key)
        self.assertEqual(
            url,
            "https://documentation-samples.obs.cn-north-4.myhuaweicloud.com/"
            "solution-as-code-publicbucket/solution-as-code-moudle/"
            "deploying-cognee/deploying-cognee.tf",
        )

    def test_url_encoding(self):
        rc = get_region_config("华北-北京四")
        key = "solution-as-code-publicbucket/solution-as-code-moudle/中文目录/文件.tf"
        url = generate_public_url(rc, key)
        # 中文应被编码，/ 不被编码
        self.assertIn("%E4%B8%AD%E6%96%87", url)
        self.assertIn("/", url)


if __name__ == "__main__":
    unittest.main()
