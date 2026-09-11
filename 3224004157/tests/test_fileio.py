"""Real temporary files and controlled OS errors verify file safety."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checker.errors import InvalidPathError, ResultWriteError, TextReadError
from checker.fileio import compare_files


class FileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.original = self.root / "原文 with spaces.txt"
        self.candidate = self.root / "对照.txt"
        self.output = self.root / "answer.txt"
        self.original.write_text("abc", encoding="utf-8")
        self.candidate.write_text("abd", encoding="utf-8")

    def compare(self):
        return compare_files(self.original, self.candidate, self.output)

    def test_answer_precision_and_only_requested_output(self):
        before = set(self.root.iterdir())
        self.assertAlmostEqual(self.compare(), 0.55)
        self.assertEqual(self.output.read_bytes(), b"0.55\n")
        self.assertEqual(set(self.root.iterdir()) - before, {self.output})

    def test_bom_is_accepted(self):
        self.original.write_text("相同文本", encoding="utf-8-sig")
        self.candidate.write_text("相同文本", encoding="utf-8")
        self.assertEqual(self.compare(), 1.0)

    def test_empty_files_write_zero(self):
        self.original.write_bytes(b"")
        self.candidate.write_bytes(b"")
        self.assertEqual(self.compare(), 0.0)
        self.assertEqual(self.output.read_bytes(), b"0.00\n")

    def test_existing_answer_is_replaced(self):
        self.output.write_text("old answer", encoding="utf-8")
        self.compare()
        self.assertEqual(self.output.read_text(), "0.55\n")

    def test_same_file_can_be_both_inputs(self):
        self.assertEqual(compare_files(self.original, self.original, self.output), 1.0)

    def test_relative_path_rejected(self):
        with self.assertRaises(InvalidPathError):
            compare_files(Path("relative.txt"), self.candidate, self.output)

    def test_missing_original(self):
        self.original.unlink()
        with self.assertRaises(TextReadError):
            self.compare()
        self.assertFalse(self.output.exists())

    def test_missing_candidate(self):
        self.candidate.unlink()
        with self.assertRaises(TextReadError):
            self.compare()

    def test_directory_is_not_input(self):
        with self.assertRaises(TextReadError):
            compare_files(self.root, self.candidate, self.output)

    def test_invalid_utf8_does_not_replace_previous_answer(self):
        self.candidate.write_bytes(b"\xff\xfe\x00\x00")
        self.output.write_text("previous", encoding="utf-8")
        with self.assertRaises(TextReadError):
            self.compare()
        self.assertEqual(self.output.read_text(), "previous")

    def test_answer_cannot_overwrite_original(self):
        with self.assertRaises(InvalidPathError):
            compare_files(self.original, self.candidate, self.original)
        self.assertEqual(self.original.read_text(), "abc")

    def test_answer_cannot_overwrite_candidate(self):
        with self.assertRaises(InvalidPathError):
            compare_files(self.original, self.candidate, self.candidate)
        self.assertEqual(self.candidate.read_text(), "abd")

    def test_symlink_output_cannot_overwrite_input(self):
        self.output.symlink_to(self.original)
        with self.assertRaises(InvalidPathError):
            self.compare()
        self.assertEqual(self.original.read_text(), "abc")

    def test_hardlink_output_cannot_overwrite_input(self):
        import os

        os.link(self.original, self.output)
        with self.assertRaises(InvalidPathError):
            self.compare()
        self.assertEqual(self.original.read_text(), "abc")

    def test_output_parent_must_exist(self):
        with self.assertRaises(ResultWriteError):
            compare_files(self.original, self.candidate, self.root / "missing" / "out.txt")

    def test_output_cannot_be_directory(self):
        with self.assertRaises(ResultWriteError):
            compare_files(self.original, self.candidate, self.root)

    def test_path_resolution_error_is_explained(self):
        with patch.object(Path, "resolve", side_effect=OSError("path failure")):
            with self.assertRaises(InvalidPathError):
                self.compare()

    def test_read_permission_failure_is_explained(self):
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaises(TextReadError):
                self.compare()
        self.assertFalse(self.output.exists())

    def test_write_permission_failure_is_explained(self):
        with patch.object(Path, "write_text", side_effect=PermissionError("denied")):
            with self.assertRaises(ResultWriteError):
                self.compare()
