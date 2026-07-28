**Decisions**

- Test framework: plain `pytest` + `monkeypatch` + `tmp_path` only. No `unittest.mock` ceremony, no `responses`/`vcrpy`, no factory libraries.
- Tests live in a top-level `tests/` folder, not inside etl, using pytest's `pythonpath` ini option instead of packaging etl as a module — smallest possible change to the existing layout.
- **In scope**: pure logic (`dsb_sortkey`, `sanitycheck`, `process` aggregation), HTTP layer with mocked `urlopen`, SQLite builders against tmp databases.
- **Out of scope** (per your selection): end-to-end pipeline smoke test with a fake CTS server, and regression tests pinning the documented bugs (Unicode lowercasing, SQL-injection-by-concatenation in `db()`, duplicate `_minmaxyearmin/max.txt`). Those bugs stay unfixed here — the SQLite tests will use benign tokens so they don't accidentally assert the buggy behaviour as correct.
- No test ever touches the network; `urncts.eu` is only reached through monkeypatched seams.
- `lemmatisierowasch.py` / `normierowasch.py` get the import-safety refactor but no tests yet — their parsing logic is entangled with I/O and deserves a follow-up.

**Further Considerations**

1. `lemmaeval.py` and `normeval.py` are 100% top-level scripting with zero reusable functions. Option A: just wrap the body in `main()` now, test later. Option B: also extract the frequency/uniqueness computation into a pure function and test it. Option C: leave them untouched. Recommend **A** — keeps this change mechanical.
2. `_ERROR.txt` is written with a hardcoded relative path in `collect()`, so a stray file can appear in whatever cwd tests run from. Option A: route it through `settings.datadir` as part of step 3. Option B: leave it and just gitignore it (already is). Recommend **A**, it's one line.
3. The suite as scoped won't catch the `db()` SQL-injection issue. Option A: add a single `xfail`-marked test documenting it as a known bug. Option B: skip entirely per the agreed scope. Recommend **B** now, **A** when you tackle the fix.
