import importlib
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class RepositoryStructureTests(unittest.TestCase):
    def test_services_are_top_level_workspace_members(self) -> None:
        self.assertTrue((REPO_ROOT / "auth-service" / "pyproject.toml").is_file())
        self.assertTrue((REPO_ROOT / "user-service" / "pyproject.toml").is_file())
        self.assertFalse((REPO_ROOT / "services" / "auth-service").exists())
        self.assertFalse((REPO_ROOT / "services" / "user-service").exists())

    def test_app_directories_are_not_nested_under_package_name(self) -> None:
        for package_dir, package_name in [
            ("core-common", "core_common"),
            ("msg-common", "msg_common"),
            ("auth-service", "auth_service"),
            ("user-service", "user_service"),
        ]:
            with self.subTest(package_dir=package_dir):
                self.assertTrue((REPO_ROOT / package_dir / "app").is_dir())
                self.assertFalse((REPO_ROOT / package_dir / "app" / package_name).exists())

    def test_public_imports_are_preserved(self) -> None:
        for module_name in [
            "core_common.auth",
            "core_common.http",
            "core_common.models",
            "msg_common.bus",
            "msg_common.envelope",
            "auth_service.security",
            "user_service.service",
        ]:
            with self.subTest(module_name=module_name):
                self.assertIsNotNone(importlib.import_module(module_name))


if __name__ == "__main__":
    unittest.main()
