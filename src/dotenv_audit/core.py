"""Pure parsing and comparison. Source values never enter result objects."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Literal

Severity = Literal["error", "warning"]
_ASSIGNMENT = re.compile(r"(?:export[ \t]+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*=(.*)")


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    source: str
    message: str
    key: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class Entry:
    line: int
    empty: bool


@dataclass
class Document:
    entries: dict[str, Entry] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(f.severity == "error" for f in self.findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "ok": self.ok,
            "summary": {
                severity + "s": sum(f.severity == severity for f in self.findings)
                for severity in ("error", "warning")
            },
            "findings": [asdict(f) for f in self.findings],
        }


def _value_is_empty(raw: str) -> bool:
    """Validate one physical line and return emptiness, discarding its value."""
    value = raw.strip()
    if not value.startswith(("'", '"')):
        return not re.split(r"(?:^|\s)#", raw, maxsplit=1)[0].strip()

    quote = value[0]
    escaped = False
    for index in range(1, len(value)):
        char = value[index]
        if char == quote and not escaped:
            tail = value[index + 1 :].lstrip()
            if tail and not tail.startswith("#"):
                raise ValueError("Unexpected text after closing quote.")
            return index == 1
        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False
    raise ValueError("Expected a closing quote on the same line; parsing stopped.")


def parse(text: str, source: str) -> Document:
    """Parse a single-line dotenv dialect into key metadata and safe findings.

    `source` is a caller-supplied label, usually `example` or `env`.
    Neither source values nor raw source lines are retained in the document.
    """
    document = Document()
    for line_number, raw in enumerate(text.removeprefix("\ufeff").split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _ASSIGNMENT.fullmatch(line)
        if match is None:
            document.findings.append(
                Finding(
                    "invalid-line",
                    "error",
                    source,
                    "Expected KEY=value with an ASCII identifier key.",
                    line=line_number,
                )
            )
            break
        key, value = match.groups()
        try:
            empty = _value_is_empty(value)
        except ValueError as error:
            document.findings.append(
                Finding(
                    "invalid-value",
                    "error",
                    source,
                    str(error),
                    key,
                    line_number,
                )
            )
            break
        if key in document.entries:
            first = document.entries[key].line
            document.findings.append(
                Finding(
                    "duplicate-key",
                    "error",
                    source,
                    f"Key is already defined on line {first}.",
                    key,
                    line_number,
                )
            )
        else:
            document.entries[key] = Entry(line_number, empty)
    return document


def audit(
    example: str,
    env: str,
    *,
    strict: bool = False,
    check_empty: bool = False,
) -> Report:
    """Compare key sets; never compare, expand, execute, or return values."""
    expected = parse(example, "example")
    actual = parse(env, "env")
    report = Report(expected.findings + actual.findings)
    if any(f.code in {"invalid-line", "invalid-value"} for f in report.findings):
        # Neither absence nor unexpectedness is reliable after a syntax error.
        return report
    if not expected.entries:
        report.findings.append(
            Finding(
                "empty-example",
                "error",
                "example",
                "Example file must define at least one key.",
            )
        )
    for key in sorted(expected.entries.keys() - actual.entries.keys()):
        report.findings.append(
            Finding(
                "missing-key",
                "error",
                "env",
                "Required key is missing.",
                key,
            )
        )
    for key in sorted(actual.entries.keys() - expected.entries.keys()):
        report.findings.append(
            Finding(
                "unexpected-key",
                "error" if strict else "warning",
                "env",
                "Key is not declared in the example file.",
                key,
                actual.entries[key].line,
            )
        )
    if check_empty:
        for key in sorted(expected.entries.keys() & actual.entries.keys()):
            if actual.entries[key].empty:
                report.findings.append(
                    Finding(
                        "empty-value",
                        "error",
                        "env",
                        "Required key has an empty value.",
                        key,
                        actual.entries[key].line,
                    )
                )
    return report
