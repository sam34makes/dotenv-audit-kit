# dotenv-audit-kit design

Build a small Python developer tool that helps teams catch configuration drift
before running an application. The user selected this project as their first
open-source repository. It is independent of Anthropic and makes no eligibility
or adoption claims.

## Approach

A command-line package is the selected approach. A hosted dashboard would add
accounts and deployment work; a framework plugin would narrow the audience.
Python 3.10+, the standard library, and zero runtime dependencies keep this tool
easy to install and maintain. Setuptools handles packaging.

## Contract

- `dotenv-audit --example PATH --env PATH` compares keys, defaulting to
  `.env.example` and `.env`.
- Missing keys, duplicate keys in either file, and malformed assignments fail.
- Extra keys are warnings, or errors with `--strict`.
- `--check-empty` fails on empty values for required keys.
- Text is the default; `--format json` emits a versioned machine-readable report.
- Exit codes: 0 for no errors, 1 for findings, 2 for invalid input or usage.
- Read files as UTF-8, tolerating an initial BOM and CRLF line endings.
- Accept comments, optional `export`, conventional identifier keys, and single
  line quoted or unquoted values. Reject multiline quoted values explicitly.
- Do not evaluate shell expressions, interpolate variables, modify files, make
  network calls, or include values or raw source lines in diagnostics.
- Keep values out of parsed result objects; retain only key names, line numbers,
  and whether a value is empty. Key names themselves may reveal application
  details, so reports are not anonymous.

## Delivery

MIT license, working examples, contribution and security instructions, issue
templates, a roadmap, CI across supported Python versions and operating systems,
and tests for the parser, comparisons, and installed CLI. Publish one useful
repository under sam34makes; further projects can follow after actual feedback.
