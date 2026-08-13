# -*- coding: utf-8 -*-
"""文件工具单元测试。"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.utils.file_utils import (
    parse_filename, generate_object_key, is_primary_extension, is_supported_extension,
)


class TestFileUtils(unittest.TestCase):

    def setUp(self):
        self.tmp = os.path.join(os.path.dirname(__file__), "deploying-dify.tf")
        with open(self.tmp, "w", encoding="utf-8") as f:
            f.write("# test")
        self.yaml = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(self.yaml, "w", encoding="utf-8") as f:
            f.write("k: v")

    def tearDown(self):
        for p in (self.tmp, self.yaml):
            if os.path.exists(p):
                os.remove(p)

    def test_parse_filename(self):
        name, filename, ext = parse_filename(self.tmp)
        self.assertEqual(name, "deploying-dify")
        self.assertEqual(filename, "deploying-dify.tf")
        self.assertEqual(ext, ".tf")

    def test_primary_extension(self):
        self.assertTrue(is_primary_extension(self.tmp))
        self.assertFalse(is_primary_extension(self.yaml))

    def test_supported_extension(self):
        self.assertTrue(is_supported_extension(self.tmp))
        self.assertTrue(is_supported_extension(self.yaml))

    def test_object_key_dify(self):
        key = generate_object_key(self.tmp)
        self.assertEqual(
            key,
            "solution-as-code-publicbucket/solution-as-code-moudle/"
            "deploying-dify/deploying-dify.tf",
        )

    def test_object_key_custom_dir(self):
        """自定义目录覆盖默认 solution-name。"""
        key = generate_object_key(self.tmp, custom_dir="my-app")
        self.assertEqual(
            key,
            "solution-as-code-publicbucket/solution-as-code-moudle/"
            "my-app/deploying-dify.tf",
        )

    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            parse_filename("/no/such/file.tf")


if __name__ == "__main__":
    unittest.main()
