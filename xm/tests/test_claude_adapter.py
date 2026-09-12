import re
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_claude_adapter():
    with (ROOT / "adapters" / "claude.toml").open("rb") as handle:
        return tomllib.load(handle)


class ClaudeAdapterTests(unittest.TestCase):
    def test_print_mode_never_waits_for_an_unattended_permission_prompt(self):
        entry = load_claude_adapter()["entry"]
        pairs = list(zip(entry, entry[1:]))

        self.assertIn(("--permission-prompts", "none"), pairs)

    def test_login_prompts_are_classified_as_adapter_errors(self):
        patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in load_claude_adapter()["success"]["forbid"]
        ]

        for message in (
            "Not logged in · Please run /login",
            "Authentication required. Please log in.",
            "Your account is on hold and can't sign in to Claude Code.",
        ):
            with self.subTest(message=message):
                self.assertTrue(any(pattern.search(message) for pattern in patterns))

    def test_runner_delivers_the_noninteractive_permission_policy(self):
        adapter = load_claude_adapter()
        with tempfile.TemporaryDirectory(prefix="xm-claude-regression-") as temp:
            root = Path(temp)
            fake = root / "fake_claude.py"
            fake.write_text(
                """\
import sys
import time

args = sys.argv[1:]
try:
    permission_target = args[args.index("--permission-prompts") + 1]
except (ValueError, IndexError):
    permission_target = "host"

sys.stdin.read()
if permission_target == "host":
    time.sleep(5)
else:
    print("FAKE_CLAUDE_OK")
""",
                encoding="utf-8",
            )
            adapters = root / "adapters"
            adapters.mkdir()
            entry = [str(fake), *adapter["entry"]]
            (adapters / "claude.toml").write_text(
                "\n".join(
                    [
                        'name = "claude"',
                        f"bin = {json.dumps(sys.executable)}",
                        f"entry = {json.dumps(entry)}",
                        'prompt_via = "stdin"',
                        'answer_from = "stdout"',
                        'model_flag = "--model"',
                        'timeout_flag = ""',
                        'timeout_format = ""',
                        '[success]',
                        'exit_ok = [0]',
                        'forbid = []',
                        'min_chars = 1',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "bin" / "xm"),
                    "--adapters",
                    str(adapters),
                    "run",
                    "-a",
                    "claude",
                    "-t",
                    "1",
                    "permission regression probe",
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(completed.stdout)
            self.assertEqual(manifest["results"][0]["status"], "ok")
            self.assertEqual(manifest["results"][0]["answer_chars"], 14)


if __name__ == "__main__":
    unittest.main()
