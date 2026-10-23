# Contributing to JSRouteMap

Open an issue with a synthetic reproducer and the expected/actual result. Never attach real credentials, customer HARs, or production logs.

Use Python 3.10+ and the standard library for runtime code. Run `python -m unittest discover -s tests -v` before submitting changes. Include a regression test for parsing, privacy or detection changes. Detection changes must document false positives and evidence limits.

No external requests or telemetry belong in the default workflow. Keep output deterministic for identical inputs. Discuss new dependencies first.
