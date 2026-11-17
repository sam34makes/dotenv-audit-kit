# Contributing

Start with a reproducible bug or one small improvement from the roadmap.
For changes to the supported dotenv syntax or CLI flags, open an issue first
so the behavior can be agreed before implementation.

1. Fork and clone the repository. Use Python 3.10 or newer and a virtual environment.
2. Run `python -m pip install -e '.[dev]'`.
3. Add a focused test, make the change, then run the checks in the README.
4. Open a pull request explaining the problem, the new behavior, and the checks run.

Tests use the standard library's unittest runner. Keep runtime dependencies at
zero and preserve exit codes and JSON schema compatibility. No code path should
execute dotenv content, log source values, or send files over the network.

Use invented values in issues, tests, and screenshots. Never submit a real `.env`
file or live credential. Be respectful, give others time to respond, and keep
feedback focused on the code. AI-assisted contributions are welcome when their
author understands the change and has verified its behavior.
