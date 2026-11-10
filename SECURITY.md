# Security Policy

## Supported versions

Only the `main` branch is supported. There are no releases yet.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting: open the repository's Security tab and choose "Report a vulnerability". Please do not open a public issue for a security problem.

This is a one-person project. Expect an acknowledgement within about a week and a fix or a decision as soon as practical afterwards. Reports are disclosed publicly once a fix is available, with credit if you want it.

## What counts

The tooling downloads and verifies files by hash, extracts archives, and reads YAML and TOML configuration. Reports of interest include:

- Hash verification that can be bypassed.
- Archive extraction that writes outside its target directory.
- Unsafe parsing of untrusted YAML, TOML or manifest input.
- Release or install steps that overwrite files outside their intended directories.
- Secrets or personal data committed to the repository.

Problems in Project Zomboid, KnoxMap or PZ Mapping Tools belong with their own maintainers.
