"""Test actual process calls as well as CLI argument/error handling."""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import main

ENTRY = Path(__file__).resolve().parents[1] / "main.py"


class CommandLineTests(unittest.TestCase):
    def test_help(self):
        for flag in ("--help", "-h"):
            with self.subTest(flag=flag), contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main([flag]), 0)
                self.assertIn("绝对路径", stdout.getvalue())

    def test_wrong_argument_counts(self):
        for arguments in ([], ["one"], ["one", "two"], ["a", "b", "c", "d"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(arguments), 2)

    def test_default_sys_argv(self):
        with patch.object(sys, "argv", ["main.py", "--help"]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)

    def test_expected_error_has_no_traceback(self):
        with contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(main(["a", "b", "c"]), 1)
        self.assertIn("绝对路径", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_function_and_real_process_with_absolute_unicode_space_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            original = root / "原文 text.txt"
            candidate = root / "修改 text.txt"
            output = root / "答案 text.txt"
            original.write_text("abc", encoding="utf-8")
            candidate.write_text("abd", encoding="utf-8")
            arguments = [str(original), str(candidate), str(output)]
            self.assertEqual(main(arguments), 0)
            completed = subprocess.run(
                [sys.executable, "-B", str(ENTRY), *arguments],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=folder,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(completed.stderr, "")
            self.assertEqual(output.read_bytes(), b"0.55\n")

    def test_real_process_missing_arguments(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(ENTRY)], capture_output=True, text=True, timeout=5
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("用法", completed.stderr)
