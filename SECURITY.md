# Security

Only the latest released version is supported. The initial version is 0.1.0.

If you find a way for a normal audit report to disclose a value or execute input,
please report it with synthetic data. Use GitHub's private vulnerability report
option if it is available on the repository's Security tab. If no private channel
is available, open an issue requesting a private contact channel without sharing
exploit details or sensitive files.

Do not post real secrets. If a credential has already been exposed, rotate it
with its provider; deleting a report does not revoke a credential.

The CLI reads local files into memory. It does not modify them, load them into
the environment, interpolate variables, execute expressions, or make network
requests. Reports include key names and line numbers, so review them before
publishing. The parser supports a documented subset of dotenv syntax and is not
a general-purpose secret scanner or a complete configuration validator.
