# Local security toolkit

Five independent Python tools by **Khedr Tayshoori**. Local analysis, standard-library runtime, Python 3.10+, MIT.

| Project | Purpose | Demo input | Guide |
| --- | --- | --- | --- |
| SessionScope | Compare session evidence before and after logout | HAR | [English](sessionscope/README.md) · [العربية](sessionscope/README.ar.md) |
| FlowDiff | Compare HTTP and JSON structures | Two HARs | [English](flowdiff/README.md) · [العربية](flowdiff/README.ar.md) |
| JSRouteMap | Extract static route candidates with source locations | JavaScript | [English](jsroutemap/README.md) · [العربية](jsroutemap/README.ar.md) |
| LogSentinel | Correlate SSH and failed web-path patterns | SSH/Nginx logs | [English](logsentinel/README.md) · [العربية](logsentinel/README.ar.md) |
| BountyEvidence | Validate and format vulnerability reports | Finding JSON | [English](bountyevidence/README.md) · [العربية](bountyevidence/README.ar.md) |

## Start on Termux

```bash
pkg install python git
git clone https://github.com/khdertaysh1/khdertaysh1.git
cd khdertaysh1/projects/sessionscope
python -m sessionscope examples/before.har examples/after.har -o reports/logout.html
```

Every project can be copied to its own repository without importing another project. Each includes a CLI, bilingual documentation, synthetic examples, MIT license, unit tests and its own workflow for standalone use. The parent repository has an active workflow across all five projects.

## Verification — 2026-10-23

- **63 unit tests passed** on Python 3.12.14 / Linux.
- All five wheels built and installed in an isolated virtual environment with access to existing build tools.
- All five installed commands executed their synthetic demos from outside the source tree.
- Self-contained HTML and JSON demos generated locally; example reports live in each project's `docs/` directory.
- Python 3.10, 3.12 and 3.13 are configured in GitHub Actions; remote check results are separate from local verification.
- Android/Termux is a design target, not a device-tested compatibility claim.

## Scope

These are focused **0.1.0** releases. They provide observations for manual security analysis, not automated proof of vulnerabilities. No command scans live targets, replays sessions, executes JavaScript, submits reports or sends telemetry. Real captures may contain private information; never commit them. Generated reports are not guaranteed anonymous.
