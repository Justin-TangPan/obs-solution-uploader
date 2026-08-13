# -*- coding: utf-8 -*-
"""配置管理器单元测试：默认值、自定义保存/加载、区域覆盖、路径前缀。"""

import json
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.config.config_manager import ConfigManager
from app.config.regions import REGIONS as DEFAULT_REGIONS


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.tmp_dir, "user_settings.json")
        self.cm = ConfigManager()
        self.cm.init(self.config_path)

    def tearDown(self):
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.tmp_dir)

    def test_defaults_when_no_file(self):
        """无配置文件时返回默认值。"""
        self.assertEqual(len(self.cm.get_regions()), 18)
        root, module = self.cm.get_path_prefix()
        self.assertEqual(root, "solution-as-code-publicbucket")
        self.assertEqual(module, "solution-as-code-moudle")
        self.assertIsNone(self.cm.get_credentials())

    def test_beijing_default(self):
        rc = self.cm.get_region_config("华北-北京四")
        self.assertEqual(rc.bucket, "documentation-samples")
        self.assertEqual(rc.region, "cn-north-4")

    # ------------------------------------------------------------------
    def test_save_and_reload_credentials(self):
        self.cm.set_credentials("AK_TEST", "SK_TEST")
        self.cm.save()
        self.assertTrue(os.path.exists(self.config_path))

        cm2 = ConfigManager()
        cm2.init(self.config_path)
        creds = cm2.get_credentials()
        self.assertIsNotNone(creds)
        self.assertEqual(creds.access_key, "AK_TEST")
        self.assertEqual(creds.secret_key, "SK_TEST")

    def test_save_and_reload_path_prefix(self):
        self.cm.set_path_prefix("custom-root", "custom-module")
        self.cm.save()

        cm2 = ConfigManager()
        cm2.init(self.config_path)
        root, module = cm2.get_path_prefix()
        self.assertEqual(root, "custom-root")
        self.assertEqual(module, "custom-module")
        self.assertEqual(cm2.object_key_prefix(), "custom-root/custom-module")

    def test_custom_region_override(self):
        """自定义区域覆盖默认，新增区域生效。"""
        regions = {
            "华北-北京四": {
                "bucket": "my-custom-bucket",
                "region": "cn-north-4",
                "endpoint": "obs.cn-north-4.myhuaweicloud.com",
            },
            "自定义区域": {
                "bucket": "documentation-samples-99",
                "region": "cn-north-99",
                "endpoint": "obs.cn-north-99.myhuaweicloud.com",
            },
        }
        self.cm.set_regions(regions)
        self.cm.save()

        cm2 = ConfigManager()
        cm2.init(self.config_path)
        rc = cm2.get_region_config("华北-北京四")
        self.assertEqual(rc.bucket, "my-custom-bucket")
        custom = cm2.get_region_config("自定义区域")
        self.assertIsNotNone(custom)
        self.assertEqual(custom.region, "cn-north-99")
        # 默认的广州被替换后不再存在
        self.assertIsNone(cm2.get_region_config("华南-广州"))

    def test_reset_regions_to_default(self):
        self.cm.set_regions({"X": {"bucket": "b", "region": "r", "endpoint": "e"}})
        self.cm.reset_regions_to_default()
        self.assertEqual(len(self.cm.get_regions()), 18)
        self.assertIsNotNone(self.cm.get_region_config("华北-北京四"))

    def test_apply_and_save_settings(self):
        settings = {
            "credentials": {"access_key": "A", "secret_key": "B", "security_token": ""},
            "path_prefix": {"root_prefix": "r", "module_prefix": "m"},
            "regions": {"区域A": {"bucket": "b", "region": "rg", "endpoint": "ep"}},
        }
        self.cm.save_settings(settings)
        self.assertTrue(os.path.exists(self.config_path))
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["credentials"]["access_key"], "A")
        self.assertEqual(data["path_prefix"]["root_prefix"], "r")
        self.assertIn("区域A", data["regions"])

    def test_partial_config_merges_with_defaults(self):
        """只写部分字段，缺失字段回退默认。"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({"path_prefix": {"root_prefix": "only-root"}}, f)
        cm2 = ConfigManager()
        cm2.init(self.config_path)
        root, module = cm2.get_path_prefix()
        self.assertEqual(root, "only-root")
        self.assertEqual(module, "solution-as-code-moudle")  # 默认
        self.assertEqual(len(cm2.get_regions()), 18)  # 默认区域


if __name__ == "__main__":
    unittest.main()
