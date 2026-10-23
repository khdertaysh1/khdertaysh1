![LogSentinel](docs/banner.svg)

# LogSentinel

**Detect time-windowed SSH and web patterns in local logs.**

Python 3.10+ · Standard-library runtime · Offline by design · MIT · v0.1.0

[العربية](README.ar.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

## Why this exists

A focused, inspectable tool for a repeatable security workflow. Reports retain evidence and uncertainty, so an analyst can reproduce the observation without trusting an automatic vulnerability verdict.

## Capabilities

- Detect SSH password-failure bursts per source within a sliding time window.
- Correlate password/publickey successes after a failure threshold.
- Flag distinct failed Nginx paths per source, excluding successful navigation.
- Report UTC alert timestamps, counts and evidence line numbers without raw log lines.
- Reject out-of-order timestamps and cap active source/per-source event state.

## Quick start

From this project's directory, no installation or external runtime dependencies are needed:

```bash
python -m logsentinel examples/auth.log --format ssh -o reports/ssh.html
```

Open the HTML report in a browser, or use a `.json` output path for structured data. Omit `-o` to print JSON to stdout.

Another example:

```bash
python -m logsentinel examples/access.log --format nginx --paths 10 --window 300 -o reports/web.json
```

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
logsentinel --help
```

Packaging uses setuptools; installing may fetch build tools. The analysis command itself has no network functionality. The source form `python -m logsentinel` works without pip from this directory.

### Android / Termux

```bash
pkg install python git
git clone https://github.com/khdertaysh1/khdertaysh1.git
cd khdertaysh1/projects/logsentinel
python -m logsentinel examples/auth.log --format ssh -o reports/ssh.html
```

Termux installation requires a network connection. Runtime analysis is local. Android compatibility follows from the standard-library implementation; device testing has not been performed.

## Read the demo

The SSH demo emits `ssh_failure_burst` and `ssh_success_after_failures`. The web demo emits `web_failed_path_sweep` for ten distinct failed paths. Alerts have review severity: shared NAT, legitimate automation or a user correcting credentials can produce the same pattern.

[View the synthetic JSON result](docs/demo.json) · [Download the self-contained HTML demo](docs/demo.html)

## Inputs and outputs

Use `python -m logsentinel --help` for the full command interface. Inputs are local files; paths containing spaces should be quoted. Reports are deterministic for identical inputs and options. Exit code **0** means analysis completed, not that the input is secure. Exit code **2** means invalid arguments or an input/output error. Reports can replace an existing output file, but cannot overwrite a specified input.

The `examples/` directory contains only synthetic, documentation-only data. Canary strings named `CANARY_*` test omission of common secret-bearing values. No real target credentials are included.



## Evidence limits and privacy

- Log input must be chronological. Rotate/split files spanning a year boundary before analysis.
- SSH supports ISO timestamps with timezone, or RFC3164 timestamps with explicit `--year` (assumed UTC).
- Nginx supports the standard common/combined request prefix, not arbitrary custom or JSON log formats.
- SSH usernames and raw web paths are not exported; source IP addresses remain visible for investigation.
- All alerts are accumulated in memory; split very large datasets. State caps default to 10,000 active IPs and 100,000 events per IP.
- Unsupported lines are counted as skipped. Inspect skip counts before trusting coverage. Malformed matched events cause a readable error.

Reports are **not guaranteed anonymous**. Paths, property names, source filenames and IP addresses may reveal context. Review output before publishing. Keep real HARs and logs outside public repositories.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q logsentinel
```

The repository workflow tests Python 3.10, 3.12 and 3.13. Current local verification is recorded in the toolkit catalog; a configured workflow does not by itself mean remote checks passed.

## License

MIT © 2026 Khedr Tayshoori. See [LICENSE](LICENSE).
