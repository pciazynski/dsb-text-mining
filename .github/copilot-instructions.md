# General coding rules ("lazy senior dev" — lazy means efficient, not careless)

First understand the problem: read the task and the code it touches, trace the real flow end to end. Only then pick the cheapest option that holds:

1. Does this need to be built at all? (YAGNI) — if not, say so and stop.
2. Does a helper/util/pattern already exist in this codebase? Reuse it.
3. Does the Python/PHP/JS stdlib, a native platform feature, or an already-installed dependency do this? Use it.
4. Only then: write the minimum code that works.

## Rules

- No abstractions that weren't explicitly requested.
- No new dependencies if avoidable. No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins — but only in the right place. A small change in the wrong place is a second bug.
- Bug fix = root cause, not symptom. Grep every caller of the function you touch; fix the shared function once instead of patching one call site.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- When two stdlib approaches are the same size, pick the edge-case-correct one.
- Mark deliberate simplifications with a greppable comment: `# CEILING: <known limit>; upgrade: <path>` (e.g. O(n²) scan, global lock, naive heuristic).

## Never be lazy about

- Understanding the problem before editing.
- Input validation at trust boundaries (HTTP params, file contents, DB queries).
- Error handling that prevents data loss. Security. Accessibility.
- Anything explicitly requested.
- Leaving a check behind: non-trivial new logic gets ONE small test (see the test instructions in `.github/instructions/` for the language's conventions). Trivial one-liners need no test.

## This project

- Python ETL scripts in `etl/`, PHP API in `public/php/`, JS frontend in `public/js/`, tests in `tests/` (one folder per language: `tests/python/`, `tests/js/`, `tests/php/`).
- Data paths come from `settings.datadir` (env override `DSB_DATADIR`); never hardcode paths.

## Reference docs (read only when relevant)

- `PRODUCT.md` — purpose, users, product principles, Non-Goals, domain glossary (lemma / norm form / word form, CTS, TSI). Read before adding or removing any user-facing feature, endpoint, or visualisation, and whenever judging "does this need to be built at all?".
- `docs/tsi-cts-explanation.md` — upstream TSI/CTS endpoint contracts, tokenization quirks, restricted-content and error behavior. Read before touching `etl/pythoncts.py`, `etl/bagofwords.py`, or anything hitting `tsi.daty.info`.
- `docs/data-lower-sorbian-corpus.md` — corpus layers (surface/norm/lemma), `|` ambiguity, coverage gaps, corpus bias. Read before changing lemma/norm ETL or the lemma/norm PHP endpoints.
