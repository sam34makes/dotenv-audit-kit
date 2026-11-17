import unittest

from dotenv_audit.core import audit, parse


class ParserTests(unittest.TestCase):
    def test_invalid_key_cannot_expose_multiline_value_content(self):
        document = parse('BAD.KEY="first\nVALUE_FRAGMENT=second\n"', "env")
        self.assertNotIn("VALUE_FRAGMENT", repr(document))
        self.assertEqual(len(document.findings), 1)

    def test_unicode_line_separators_inside_values_do_not_create_keys(self):
        document = parse('TOKEN="secret\u0085PRIVATE_VALUE=hidden"', "env")
        self.assertEqual(set(document.entries), {"TOKEN"})
        self.assertFalse(document.findings)

    def test_multiline_content_cannot_be_reported_as_key_names(self):
        document = parse('TOKEN="secret\nPRIVATE_VALUE=hidden\n"', "env")
        self.assertNotIn("PRIVATE_VALUE", repr(document))
        self.assertEqual(document.entries, {})

    def test_comments_export_whitespace_bom_and_crlf(self):
        document = parse('\ufeff# comment\r\n export PORT = 8000\r\nNAME="a # b"\r\n', "env")
        self.assertEqual(set(document.entries), {"PORT", "NAME"})
        self.assertEqual(document.entries["PORT"].line, 2)
        self.assertFalse(document.findings)

    def test_empty_values_and_inline_comments(self):
        for value, empty in [
            ("", True),
            ("  # comment", True),
            ('""', True),
            ("''", True),
            ('" "', False),
            ("abc # comment", False),
            ("abc#part", False),
            ('"value" # comment', False),
        ]:
            with self.subTest(value=value):
                document = parse(f"KEY={value}", "env")
                self.assertFalse(document.findings)
                self.assertEqual(document.entries["KEY"].empty, empty)

    def test_escaped_quotes_and_equals(self):
        document = parse("TOKEN=\"a\\\"b=c\"\nSINGLE='a\\'b'\nURL=a=b=c", "env")
        self.assertEqual(len(document.entries), 3)
        self.assertFalse(document.findings)

    def test_duplicate_keeps_first_line_and_reports_second(self):
        document = parse("A=1\nA=2\n", "example")
        self.assertEqual(document.entries["A"].line, 1)
        self.assertEqual(document.findings[0].code, "duplicate-key")
        self.assertEqual(document.findings[0].line, 2)
        self.assertIn("line 1", document.findings[0].message)

    def test_invalid_lines_never_echo_source(self):
        for text in ["TOP_SECRET", "BAD-KEY=TOP_SECRET", "1KEY=TOP_SECRET", "=TOP_SECRET"]:
            with self.subTest(text=text):
                document = parse(text, "env")
                self.assertEqual(document.findings[0].code, "invalid-line")
                self.assertNotIn("TOP_SECRET", repr(document))

    def test_unclosed_and_trailing_quoted_values_fail(self):
        for value in ['"secret', "'secret", '"secret"trailing', '"secret\\"']:
            with self.subTest(value=value):
                document = parse(f"KEY={value}", "env")
                self.assertEqual(document.findings[0].code, "invalid-value")
                self.assertNotIn("secret", repr(document))

    def test_multiline_values_are_rejected_without_retaining_content(self):
        document = parse('KEY="secret\nsecret"', "env")
        self.assertTrue(document.findings)
        self.assertNotIn("secret", repr(document))

    def test_expressions_are_literal_and_values_are_not_retained(self):
        document = parse("KEY=$(touch /tmp/dotenv-audit-must-not-run)\nVAR=${HOME}", "env")
        self.assertFalse(document.findings)
        self.assertNotIn("touch", repr(document))
        self.assertNotIn("HOME", repr(document))

    def test_identifier_keys_are_case_sensitive_and_ascii(self):
        document = parse("_KEY=1\nkey=2\nKEY=3\nCAFÉ=4", "env")
        self.assertEqual(set(document.entries), {"_KEY", "key", "KEY"})
        self.assertEqual(len(document.findings), 1)


class AuditTests(unittest.TestCase):
    def test_syntax_errors_suppress_comparisons_of_partial_documents(self):
        for example, env in [
            ("A=\nB=\nC=", 'A=1\nB="open\n"\nC=2'),
            ('A=\nB="open\n"\nC=', "A=1\nB=2\nC=3"),
            ('BAD.KEY="open\nSECRET=part\n"', "A=1"),
        ]:
            with self.subTest(example=example, env=env):
                report = audit(example, env, check_empty=True)
                self.assertFalse(report.ok)
                self.assertTrue(
                    all(f.code in {"invalid-line", "invalid-value"} for f in report.findings)
                )

    def test_matching_keys_allow_different_values(self):
        report = audit("HOST=localhost", "HOST=production")
        self.assertTrue(report.ok)
        self.assertEqual(report.findings, [])

    def test_missing_keys_are_sorted_errors(self):
        report = audit("Z=\nA=\n", "")
        self.assertEqual([f.key for f in report.findings], ["A", "Z"])
        self.assertTrue(all(f.code == "missing-key" for f in report.findings))
        self.assertFalse(report.ok)

    def test_extra_keys_warn_by_default_and_fail_in_strict_mode(self):
        report = audit("A=1", "A=1\nB=2")
        self.assertTrue(report.ok)
        self.assertEqual(report.findings[0].severity, "warning")
        strict = audit("A=1", "A=1\nB=2", strict=True)
        self.assertFalse(strict.ok)
        self.assertEqual(strict.findings[0].severity, "error")

    def test_empty_check_is_optional_and_only_checks_required_keys(self):
        self.assertTrue(audit("A=", "A=").ok)
        report = audit("A=", "A=\nEXTRA=", check_empty=True)
        self.assertEqual([f.code for f in report.findings], ["unexpected-key", "empty-value"])
        self.assertEqual(report.findings[-1].key, "A")
        self.assertFalse(report.ok)

    def test_duplicates_in_either_file_fail(self):
        for example, env in [("A=1\nA=2", "A=1"), ("A=1", "A=1\nA=2")]:
            with self.subTest(example=example, env=env):
                report = audit(example, env)
                self.assertFalse(report.ok)
                self.assertEqual(report.findings[0].code, "duplicate-key")

    def test_blank_template_is_a_configuration_error(self):
        report = audit("# no required keys", "A=1")
        self.assertFalse(report.ok)
        self.assertIn("empty-example", [f.code for f in report.findings])

    def test_serializable_report_has_version_and_no_values(self):
        data = audit("A=supersecret", "B=anothersecret").to_dict()
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["summary"], {"errors": 1, "warnings": 1})
        self.assertNotIn("supersecret", repr(data))
        self.assertNotIn("anothersecret", repr(data))


if __name__ == "__main__":
    unittest.main()
