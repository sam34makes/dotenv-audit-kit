import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_invalid_key_cannot_expose_multiline_content_in_either_format(self):
        self.env_file.write_text('BAD.KEY="first\nVALUE_FRAGMENT=second\n"', encoding="utf-8")
        for output_format in ("text", "json"):
            result = self.run_cli("--format", output_format)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("VALUE_FRAGMENT", result.stdout + result.stderr)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.example = self.root / ".env.example"
        self.env_file = self.root / ".env"
        self.example.write_text("HOST=localhost\nTOKEN=\n", encoding="utf-8")
        self.env_file.write_text("HOST=prod\nTOKEN=very-secret-value\n", encoding="utf-8")

    def run_cli(self, *args):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        return subprocess.run(
            [sys.executable, "-m", "dotenv_audit", *args],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_defaults_pass_and_never_print_values(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)
        self.assertNotIn("very-secret-value", result.stdout + result.stderr)

    def test_missing_duplicate_and_empty_keys_fail(self):
        self.env_file.write_text("TOKEN=\nTOKEN=secret\n", encoding="utf-8")
        result = self.run_cli("--check-empty")
        self.assertEqual(result.returncode, 1)
        for code in ("duplicate-key", "missing-key", "empty-value"):
            self.assertIn(code, result.stdout)
        self.assertNotIn("secret", result.stdout + result.stderr)

    def test_json_schema_and_strict_mode(self):
        self.env_file.write_text("HOST=prod\nTOKEN=secret\nEXTRA=private", encoding="utf-8")
        result = self.run_cli("--format", "json", "--strict")
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(data["schema_version"], 1)
        self.assertFalse(data["ok"])
        self.assertEqual(data["summary"], {"errors": 1, "warnings": 0})
        self.assertEqual(data["findings"][0]["key"], "EXTRA")
        self.assertNotIn("private", result.stdout + result.stderr)
        self.assertFalse(result.stderr)

    def test_warnings_do_not_fail(self):
        self.env_file.write_text("HOST=x\nTOKEN=x\nEXTRA=x", encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARNING", result.stdout)

    def test_missing_input_returns_two_with_json_error(self):
        self.env_file.unlink()
        result = self.run_cli("--format", "json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["error"]["code"], "input-error")
        self.assertFalse(result.stderr)

    def test_invalid_utf8_does_not_leak_bytes(self):
        self.env_file.write_bytes(b"TOKEN=very-secret-value\xff")
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("very-secret-value", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_input_directory_is_handled(self):
        result = self.run_cli("--env", str(self.root))
        self.assertEqual(result.returncode, 2)
        self.assertIn("input-error", result.stderr)

    def test_explicit_paths_and_bom_crlf(self):
        other = self.root / "sample.env"
        other.write_bytes(b"\xef\xbb\xbfHOST=x\r\nTOKEN=y\r\n")
        result = self.run_cli("--env", str(other), "--example", str(self.example))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_assignment_is_value_free_in_both_formats(self):
        self.env_file.write_text('HOST=x\nTOKEN="very-secret-value\n', encoding="utf-8")
        for output_format in ("text", "json"):
            result = self.run_cli("--format", output_format)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("very-secret-value", result.stdout + result.stderr)

    def test_input_is_never_executed(self):
        marker = self.root / "must-not-exist"
        self.env_file.write_text(f"HOST=$(touch {marker})\nTOKEN=${{HOME}}", encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0)
        self.assertFalse(marker.exists())

    def test_empty_template_fails(self):
        self.example.write_text("", encoding="utf-8")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("empty-example", result.stdout)

    def test_help_version_and_usage(self):
        self.assertEqual(self.run_cli("--help").returncode, 0)
        self.assertIn("0.1.0", self.run_cli("--version").stdout)
        self.assertEqual(self.run_cli("--format", "unsupported").returncode, 2)


if __name__ == "__main__":
    unittest.main()
