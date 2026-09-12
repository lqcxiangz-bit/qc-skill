import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class XmSkillContractTests(unittest.TestCase):
    def test_claude_auth_uses_existing_credentials_and_never_starts_login(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Claude 认证边界", skill)
        auth_section = skill.split("## Claude 认证边界", 1)[1].split("\n## ", 1)[0]
        self.assertIn("本机凭证", auth_section)
        self.assertIn("`claude auth login`", auth_section)
        self.assertIn("禁止自动执行", auth_section)
        self.assertIn("沙箱外", auth_section)


if __name__ == "__main__":
    unittest.main()
