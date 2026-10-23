![JSRouteMap](docs/banner.svg)

# JSRouteMap

**Inventory static API route candidates in local JavaScript.**

Python 3.10+ · Standard-library runtime · Offline by design · MIT · v0.1.0

[العربية](README.ar.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

## Why this exists

A focused, inspectable tool for a repeatable security workflow. Reports retain evidence and uncertainty, so an analyst can reproduce the observation without trusting an automatic vulnerability verdict.

## Capabilities

- Recursively inventory local `.js`, `.mjs` and `.cjs` files.
- Identify literal route candidates and nearby fetch, axios method and XHR open context.
- Track source filename and line number for review.
- Replace template expressions with `{dynamic}` without evaluating JavaScript.
- Strip URL userinfo, query values and fragments; never contact extracted endpoints.

## Quick start

From this project's directory, no installation or external runtime dependencies are needed:

```bash
python -m jsroutemap examples/app.js -o reports/routes.html
```

Open the HTML report in a browser, or use a `.json` output path for structured data. Omit `-o` to print JSON to stdout.

Another example:

```bash
python -m jsroutemap examples -o reports/routes.json
```

## Install

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
jsroutemap --help
```

Packaging uses setuptools; installing may fetch build tools. The analysis command itself has no network functionality. The source form `python -m jsroutemap` works without pip from this directory.

### Android / Termux

```bash
pkg install python git
git clone https://github.com/khdertaysh1/khdertaysh1.git
cd khdertaysh1/projects/jsroutemap
python -m jsroutemap examples/app.js -o reports/routes.html
```

Termux installation requires a network connection. Runtime analysis is local. Android compatibility follows from the standard-library implementation; device testing has not been performed.

## Read the demo

The demo finds route candidates such as `/api/preferences` with method POST and `/api/{dynamic}/settings` with an unknown method. `fetch` is deliberately UNKNOWN because a later options object can override its method. Candidate counts are not vulnerability counts.

[View the synthetic JSON result](docs/demo.json) · [Download the self-contained HTML demo](docs/demo.html)

## Inputs and outputs

Use `python -m jsroutemap --help` for the full command interface. Inputs are local files; paths containing spaces should be quoted. Reports are deterministic for identical inputs and options. Exit code **0** means analysis completed, not that the input is secure. Exit code **2** means invalid arguments or an input/output error. Reports can replace an existing output file, but cannot overwrite a specified input.

The `examples/` directory contains only synthetic, documentation-only data. Canary strings named `CANARY_*` test omission of common secret-bearing values. No real target credentials are included.



## Evidence limits and privacy

- This is a lexical heuristic, not an AST parser. Comments, regex literals and embedded code can create false positives.
- Concatenation, escaped quotes and computed properties may be missed or partially extracted.
- Only root-relative and absolute HTTP(S) strings are considered; protocol-relative and plain relative paths are skipped.
- A 50 MiB combined input cap and symlink refusal limit accidental traversal; large bundles should be split.
- Output must be outside any scanned input directory. Keep source directories scoped to avoid traversing unrelated files.

Reports are **not guaranteed anonymous**. Paths, property names, source filenames and IP addresses may reveal context. Review output before publishing. Keep real HARs and logs outside public repositories.

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q jsroutemap
```

The repository workflow tests Python 3.10, 3.12 and 3.13. Current local verification is recorded in the toolkit catalog; a configured workflow does not by itself mean remote checks passed.

## License

MIT © 2026 Khedr Tayshoori. See [LICENSE](LICENSE).
