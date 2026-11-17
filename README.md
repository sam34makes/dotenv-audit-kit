# dotenv-audit-kit

Catch missing, duplicate, and unexpected `.env` keys before your app starts.

A small Python CLI with **zero runtime dependencies**, deterministic text/JSON
reports, and diagnostics that omit configuration values. Runs locally or in CI.

## Try it

Requires Python 3.10 or newer. This project is not published on PyPI yet.
Install from this repository in a virtual environment:

```sh
git clone https://github.com/sam34makes/dotenv-audit-kit.git
cd dotenv-audit-kit
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .

dotenv-audit --example examples/.env.example --env examples/complete.env
```

```text
PASS: 0 errors, 0 warnings.
```

See a deliberate failure:

```sh
dotenv-audit --example examples/.env.example --env examples/drift.env --check-empty
```

```text
ERROR env:3 [duplicate-key] APP_HOST: Key is already defined on line 2.
ERROR env [missing-key] APP_PORT: Required key is missing.
WARNING env:5 [unexpected-key] LEGACY_FLAG: Key is not declared in the example file.
ERROR env:4 [empty-value] API_TOKEN: Required key has an empty value.
FAIL: 3 errors, 1 warning.
```

## Use it in your project

Keep the required keys in a committed `.env.example`. Keep real values in a
git-ignored `.env`, then run:

```sh
dotenv-audit
dotenv-audit --strict --check-empty
dotenv-audit --example config/template.env --env config/local.env --format json
python -m dotenv_audit --help
```

| Option | Behavior |
| --- | --- |
| `--example PATH` | Required-key template; defaults to `.env.example` |
| `--env PATH` | File being checked; defaults to `.env` |
| `--strict` | Treat unexpected keys as errors instead of warnings |
| `--check-empty` | Fail when a required key has an empty value |
| `--format text\|json` | Report format; defaults to text |
| `--version` | Print the installed version |

Missing keys, duplicate definitions in **either file**, and malformed lines are
always errors. An empty or comment-only template is an error. Values in the
template describe the keys; they are not compared with the target values.

Exit codes: **0** no errors (warnings allowed), **1** audit findings, **2** input
or command usage error. In text mode, input errors go to stderr; audit reports
go to stdout. In JSON mode, audit reports and input errors go to stdout.
Argparse usage errors and help/version output retain their normal text format.

## JSON for CI

```json
{
  "schema_version": 1,
  "ok": false,
  "summary": {"errors": 1, "warnings": 0},
  "findings": [
    {
      "code": "missing-key",
      "severity": "error",
      "source": "env",
      "message": "Required key is missing.",
      "key": "API_TOKEN",
      "line": null
    }
  ]
}
```

An unreadable file produces `{"schema_version": 1, "ok": false, "error": {...}}`
with error fields `code`, `source`, and `message`, and exits with 2.
The [CI workflow](.github/workflows/ci.yml) runs a successful audit, a deliberate
failure, unit tests, type checks, lint, and a package build.

## Supported syntax

- ASCII identifier keys: letters or `_` first, then letters, digits, or `_`.
- `KEY=value`, optional whitespace around `=`, and optional `export KEY=value`.
- Blank lines, full-line `#` comments, UTF-8 BOM, and CRLF line endings.
- Single-line single/double quoted values, including escaped quotes.
- An unquoted `#` starts a comment at the beginning of a value or after
  whitespace. `KEY=abc#fragment` retains a nonempty value.
- An empty assignment, `''`, or `""` is empty. Quoted whitespace is nonempty.

This is a deliberately limited dotenv dialect, not a shell interpreter.
Multiline quoted values are unsupported. A syntax error stops parsing the
remainder of that file, so later value content cannot become reported keys.
If either file has a syntax error, comparisons are skipped until it is fixed;
missing and unexpected keys cannot be determined reliably from partial input.
Variable interpolation and shell expressions are treated as literal text;
they are never expanded or executed. Values are not type-checked, compared,
or checked for whether a credential works.

## Privacy

The CLI makes no network calls, changes no files, and never includes values or
raw source lines in reports. Files are read into memory for parsing; returned
objects retain only key names, line numbers, and emptiness metadata. Key names
can still reveal application details. This is not a secret scanner.

## Develop and contribute

```sh
python -m pip install -e '.[dev]'
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
mypy
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [ROADMAP.md](ROADMAP.md), and
[SECURITY.md](SECURITY.md). Small bug reports with fake input files are welcome.

Version **0.1.0** is an initial alpha. The project is independently maintained
by [sam34makes](https://github.com/sam34makes).

## License

[MIT](LICENSE).
