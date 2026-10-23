![BountyEvidence](docs/banner.svg)

# BountyEvidence

**Build consistent, privacy-conscious vulnerability reports.**

Python 3.10+ · Standard-library runtime · Offline by design · MIT · v0.1.0

[العربية](README.ar.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

## Why this exists

A focused, inspectable tool for a repeatable security workflow. Reports retain evidence and uncertainty, so an analyst can reproduce the observation without trusting an automatic vulnerability verdict.

## Capabilities

- Create a structured synthetic finding with `init`.
- Validate required narrative, reproduction steps, evidence references, limitations and remediation.
- Render portable Markdown, JSON and self-contained escaped HTML.
- Redact common labeled credentials, bearer tokens, JWTs and URL query strings as a best effort.
- Reference evidence files without opening, uploading or embedding them.

## Quick start

From this project's directory, no installation or external runtime dependencies are needed:

```bash
python -m bountyevidence build examples/finding.json -o reports/finding.md
```

Open the HTML report in a browser, or use a `.json` output path for structured data. Markdown is also supported.

Another example:

```bash
python -m bountyevidence build examples/finding.json -o reports/finding.html
```

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
bountyevidence --help
```

Packaging uses setuptools; installing may fetch build tools. The analysis command itself has no network functionality. The source form `python -m bountyevidence` works without pip from this directory.

### Android / Termux

```bash
pkg install python git
git clone https://github.com/khdertaysh1/khdertaysh1.git
cd khdertaysh1/projects/bountyevidence
python -m bountyevidence build examples/finding.json -o reports/finding.md
```

Termux installation requires a network connection. Runtime analysis is local. Android compatibility follows from the standard-library implementation; device testing has not been performed.

## Read the demo

The example is a fabricated logout finding for a documentation-only host. It illustrates the difference between actual observations, proposed impact and remaining verification. The tool does not invent impact, score CVSS, submit reports or attach original captures.

[View the synthetic JSON result](docs/demo.json) · [Download the self-contained HTML demo](docs/demo.html)

## Inputs and outputs

Use `python -m bountyevidence --help` for the full command interface. Inputs are local files; paths containing spaces should be quoted. Reports are deterministic for identical inputs and options. Exit code **0** means analysis completed, not that the input is secure. Exit code **2** means invalid arguments or an input/output error. Reports can replace an existing output file, but cannot overwrite a specified input.

The `examples/` directory contains only synthetic, documentation-only data. Canary strings named `CANARY_*` test omission of common secret-bearing values. No real target credentials are included.

Create your own starting file with `python -m bountyevidence init finding.json`. The command refuses to overwrite an existing file. Build usage: `python -m bountyevidence build finding.json -o reports/finding.md`.

## Evidence limits and privacy

- Redaction is best effort. Unlabeled secrets, emails, URL credentials, path segments, account IDs and addresses may remain.
- Do not treat the output as anonymized. Read every generated report before sharing it.
- Evidence references are plain text: files are not loaded or verified.
- Unknown fields are rejected so accidentally pasted raw captures are not silently copied.
- Markdown content is quoted and escaped; HTML reports use no external assets or JavaScript.

Reports are **not guaranteed anonymous**. Paths, property names, source filenames and IP addresses may reveal context. Review output before publishing. Keep real HARs and logs outside public repositories.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q bountyevidence
```

The repository workflow tests Python 3.10, 3.12 and 3.13. Current local verification is recorded in the toolkit catalog; a configured workflow does not by itself mean remote checks passed.

## License

MIT © 2026 Khedr Tayshoori. See [LICENSE](LICENSE).
