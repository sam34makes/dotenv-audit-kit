# Initial verification — 2026-11-17

Code commit: `b1092cb0bee6898ef439df0d1301255fc5dd718c`.

## Local checks

- macOS, Python 3.12.14: all 33 unittest tests pass.
- Ruff lint and format checks pass; mypy strict checks pass.
- Source distribution and wheel build successfully.
- A clean virtual environment installs the wheel and passes console-script,
  module, JSON-output, and exit-code smoke checks.
- With synthetic `.env` and `private.env` files present in the examples folder,
  the source archive includes only the three public fixtures. This also holds
  with an older setuptools source-file manifest present.
- A separate code review found three issues in parsing and packaging. Each was
  reproduced and fixed before publication, with regression checks.

## Hosted checks

[Initial CI run](https://github.com/sam34makes/dotenv-audit-kit/actions/runs/44116449514)
passed the Linux test jobs on Python 3.10 through 3.15, the Windows Python 3.12
test job, and the quality job (lint, format, type check, package build, and clean
wheel installation).

The hosted macOS Python 3.12 job was still queued for a runner when this record
was written. Its result is available at the run link above. The local macOS
checks passed; they are separate from the pending hosted result.

This is initial alpha verification, not a certification of compatibility with
all dotenv implementations. See the README for the supported syntax.
