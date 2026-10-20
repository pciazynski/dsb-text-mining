---
description: 'Use these guidelines when generating or updating Python tests.'
applyTo: 'tests/python/**'
---

# Python tests (dsb-text-mining)

## Setup & layout

- Run from repo root: `.venv/bin/python -m pytest`. First-time: `python3 -m venv .venv && .venv/bin/python -m pip install -e ".[test]"`.
- `pyproject.toml` sets `pythonpath = ["etl"]` — import bare: `import bagofwords`, not `from etl import ...`.
- Flat `tests/python/`, no `__init__.py`. Fixtures/factories in `tests/python/conftest.py` — reuse before writing new ones:
  - `datadir` — points `settings.datadir` at a tmp dir (via `DSB_DATADIR`), reloads dependent modules.
  - `reset_cts_globals` — REQUIRED for any test touching `pythoncts` state.
  - `write_peryear` — writes tiny per-year token/frequency files.
  - `no_sleep` — disables real sleeping in retry loops, records call args.
- `etl/` modules have module-level globals; use the fixtures above, don't invent new reload logic.

## Conventions

- One behavior per test; names `test_<unit>_<scenario>_<expected>`; Arrange-Act-Assert with blank lines; happy path first, then edge cases.
- Tests are order-independent (own tmp dir/DB/state) and must fail via assertion, never import/collection error. Run new tests before finishing.
- Assert exact results where cheap (row counts, full lists), not just membership.
- Tests should be readable and easy to understand for a human. So do not use `\t` or `\n` because they are not easy to read for humans.

## Test doubles

- Test behavior (inputs → return values, files, DB rows), never call sequences.
- Fake ONLY at boundaries: network (`monkeypatch` on `urlopen`), time (`no_sleep`), filesystem (`tmp_path`/`datadir`). Never mock repo code; use real SQLite in a tmp dir. No real network.

## Known, unfixed bugs

- Assert the CORRECT behavior + `@pytest.mark.xfail(strict=True, reason="BUG: <desc>")`. Never `skip` (rots silently); strict xfail turns XPASS when fixed, forcing marker removal.
- Files: `tests/python/test_*_regressions.py`.
