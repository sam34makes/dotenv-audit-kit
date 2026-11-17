# dotenv-audit-kit Implementation Plan

**Goal:** Deliver a tested, installable configuration comparison CLI and public repository.
**Architecture:** A pure parser/auditor returns typed findings; argparse handles file input and presentation.
**Tech Stack:** Python 3.10+, setuptools, unittest; Ruff and mypy for development.
**Spec:** ../specs/2026-11-17-dotenv-audit-design.md

## Constraints and review focus

No runtime dependencies. Never execute input or print values. Test malformed
quotes, duplicate keys in both files, Unicode/BOM/CRLF, unreadable input, and
empty/comment-only values. Support Python 3.10 through 3.15 in CI.

## Task 1: Parser and audit

- [x] Add `tests/test_core.py` covering literal values, line numbers, safe errors,
  missing/extra/empty keys, strict mode, and duplicates.
- [x] Run tests and observe a missing module failure.
- [x] Implement `parse(text: str, source: str) -> Document` and
  `audit(example: str, env: str, *, strict: bool = False,
  check_empty: bool = False) -> Report` in `src/dotenv_audit/core.py`.
- [x] Run parser/audit tests and confirm all pass.

## Task 2: CLI and packaging

- [x] Add subprocess tests for text/JSON, exit codes, input failures, secret
  redaction, `--help`, and `--version`; observe failures before implementation.
- [x] Implement `cli.main(argv: list[str] | None = None) -> int`, the module
  entry point, and `pyproject.toml` console script `dotenv-audit`.
- [x] Install in a project virtual environment and run the full suite.

## Task 3: Open-source delivery

- [x] Add README, license, examples, contributor/security guidance, issue
  templates, changelog, roadmap, and read-only-permission CI.
- [x] Run Ruff, mypy, tests, sdist/wheel build, and isolated wheel smoke test.
- [x] Upload the reviewed, tested files to a new public repo.
- [x] Verify remote contents and inspect hosted CI results. See `docs/verification.md` for the pending hosted macOS job.
