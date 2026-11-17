# Roadmap

## Shipped in 0.1.0

- Local key comparison, duplicate detection, and safe parse errors.
- Optional strict and required-empty checks.
- Versioned JSON reports and stable exit codes.
- CLI, package build, examples, tests, and cross-platform CI.

## Candidates for the next release

- Add fixture-based compatibility tests against common dotenv conventions,
  documenting differences before extending the parser.
- Add an optional `--ignore-key` flag for intentional local-only variables.
  Ignored keys must not hide malformed lines or duplicate definitions.
- Provide a pre-commit hook definition with usage examples and tests.

## Before a PyPI release

- Collect feedback from real projects and review package naming availability.
- Confirm the supported syntax and JSON contract, prepare release notes, and
  verify installation from both wheel and source distribution.

Feedback determines priorities. This file is a set of proposed improvements,
not a promise of dates or adoption.
