"""Command-line input and value-free text/JSON reports."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv_audit import __version__
from dotenv_audit.core import Report, audit


def _print_text(report: Report) -> None:
    for finding in report.findings:
        location = finding.source
        if finding.line is not None:
            location += f":{finding.line}"
        key = f" {finding.key}" if finding.key else ""
        print(f"{finding.severity.upper()} {location} [{finding.code}]{key}: {finding.message}")
    errors = sum(f.severity == "error" for f in report.findings)
    warnings = len(report.findings) - errors
    error_label = "error" if errors == 1 else "errors"
    warning_label = "warning" if warnings == 1 else "warnings"
    print(f"{'PASS' if report.ok else 'FAIL'}: {errors} {error_label}, {warnings} {warning_label}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dotenv-audit",
        description="Compare dotenv keys without printing configuration values.",
        epilog="Exit codes: 0 = no errors; 1 = audit findings; 2 = input or usage error.",
    )
    parser.add_argument(
        "--example",
        type=Path,
        default=Path(".env.example"),
        help="required-key template (default: .env.example)",
    )
    parser.add_argument(
        "--env", type=Path, default=Path(".env"), help="file to audit (default: .env)"
    )
    parser.add_argument("--strict", action="store_true", help="fail on unexpected keys")
    parser.add_argument(
        "--check-empty", action="store_true", help="fail when a required key has an empty value"
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text", help="report format (default: text)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    contents: dict[str, str] = {}
    for source, path in (("example", args.example), ("env", args.env)):
        try:
            contents[source] = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            # Exception text may contain source bytes or sensitive filenames.
            message = f"Unable to read {source} file ({type(error).__name__})."
            if args.format == "json":
                print(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "ok": False,
                            "error": {"code": "input-error", "source": source, "message": message},
                        }
                    )
                )
            else:
                print(f"ERROR [{source}] [input-error]: {message}", file=sys.stderr)
            return 2

    report = audit(
        contents["example"], contents["env"], strict=args.strict, check_empty=args.check_empty
    )
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        _print_text(report)
    return 0 if report.ok else 1
