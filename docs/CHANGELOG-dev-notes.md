# Dev Notes (2026-08-23)
- implement A1 to A5 of searchBoxSimplficiationPlan.md


# Dev Notes (2026-08-04)

## Lemma and norm ETL

- Moved duplicated lemma/norm logic into `etl/mapping_etl.py`; the original modules remain thin, compatible entry points.
- Fixed document limits and restricted/empty documents incorrectly affecting which documents were processed.
- Fixed `type`/`subtype` leakage, empty targets, empty non-ambiguous rows, and unsafe database replacement. Rebuilds now use a temporary database and preserve the previous database on failure.
- Added a shared per-run passage cache, so lemma and norm processing fetch each document once. Restricted or failed responses are not cached, and `setup.py` clears stale cache data.
- Added `_status.txt` manifests with `ok`, `empty`, `restricted`, `invalid`, or `unavailable` per attempted document; one failed request no longer stops the batch.

## Evaluation and tests

- Consolidated lemma/norm evaluation in `etl/mappingeval.py`. Uniqueness output now includes both mapping-record and occurrence-weighted metrics and rejects malformed rows with row context.
- Corrected sorting-redundancy counts for duplicate identical groups.
- Added focused Python coverage for mapping, database rebuilds, evaluation, and passage caching. Added strict known-bug JS tests for evaluation labels and category names; those UI issues remain unresolved.
- Clarified corpus/upstream-service documentation and simplified README test commands.

# Dev Notes (2026-07-29)

## Multi-language test infrastructure (uncommitted, on dev-only-wortform)

- Python tests moved `tests/` → `tests/python/` (pytest `testpaths` updated); JS and PHP suites added alongside.
- **JS**: `node:test` + jsdom (only devDep), new `package.json`; `tests/js/` with `helpers.js` (`withDom`, `loadScript`, `loadPage`, `knownBug`) + first tests for config.js and index.html. Test-hook `module.exports` footer added to `public/js/config.js`.
- **PHP**: PHPUnit 11 via root `composer.json` (test harness only), `phpunit.xml`; `tests/php/` with `Support/DevServer.php` (isolated built-in server + throwaway data dir) and `Support/KnownBug.php` (`assertStillBroken`, strict-xfail equivalent) + first tests for dsb_collation and lemmatoken endpoint.
- CI: `tests.yml` split into three jobs (python / js on Node 18 / php 8.3 with pdo_sqlite); earlier commits: single Python version in CI, vscode settings.
- Agent setup: `.github/copilot-instructions.md` ("lazy senior dev" rules), per-language test instruction files, six agents (bug-hunter, characterization/regression testers, TDD red/green/refactor).
- `.gitignore`: `.phpunit.cache/`, `/vendor/`.
- All three suites green.

## Docs

- Condensed the three test instruction files in `.github/instructions/` (~35-40% fewer tokens): cut generic testing advice and repeated rationale, kept repo-specific facts (commands, helpers/fixtures, no-mock policy, strict-xfail patterns, code examples).
- Rewrote README "Running Tests": was Python-only, now covers all three suites (pytest / npm test / composer test) with a quick-reference table and a note on the known-bug XPASS convention.

# Dev Notes (2026-07-28)

- Added regression tests for bagofwords behavior and Python script coverage.
- Fixed existing regression tests and removed a small unused variable.

# Dev Notes (2026-07-14)

- TSI `bagofwords.php` is configured with `$multibyte = false` (see `config.php`) but why? it contributes to inconsistencies with lowercasing special characters
- in `bagofwords-endpoint-review.md` there's a review with potential problems - some of them are probably easily solvable with puting `$multibyte = true`, some of them are probably not problematic if we look at norm and lemma forms, but still would be good to talk about that with Fabian

# Dev Notes (2026-07-05)

- Project cleaned up
- external libs needs to be installed with scripts/install-libs.sh
- 2 new permamnent branches: archive/full-baseline and upstream-main
- in dev-only-wortform is the newest clean version with temporarily deleted other features than Wortform in order to focus

# Dev Notes (2026-06-24)

Purpose: keep deep rationale out of changelog/TODO while preserving decisions, risks, and evidence.

## 1) Regex behavior change (lemma + norm)

Implemented on six endpoints:

- lemmaregexsearch.php
- lemmaregexgroup.php
- lemmaregex2token.php
- normregexsearch.php
- normregexgroup.php
- normregex2token.php

Behavior:

- exact mode: `exact=1` or bare `exact` -> `\|term\|`
- ambiguous mode: `exact=0` or no exact flag -> `.*\|term\|.*`

User example preserved in changelog:

- Query term DRJEWO now matches both `|DRJEWO|` and ambiguous fields like `|DRĚŚ|DRJEWO|`.

## 2) SQL fix in norm regex token panel

Issue:

- Invalid SQL order (`LIMIT` before `GROUP BY`) produced no results.

Fix:

- Query now builds with `GROUP BY` before final `LIMIT`.

## 3) Security changes done

Done now:

- Regex patterns are passed as bound parameters in regex endpoints.
- Year range in lemma/norm regex2token is parsed to ints and bound.

Still open:

- Direct concatenation of `$_GET['year']` remains in:
  - urnbylemma.php
  - urnbynorm.php
  - urnbyword.php
  - lemmatokenperyear.php
  - normtokenperyear.php
  - tokencountdaterange.php
  - charcountdaterange.php

Recommended pattern:

- parse + validate year values
- use prepared statements with bound params

## 4) Inconsistencies to resolve

DB source mismatch:

- normregexsearch.php reads normmapping.db
- normregexgroup.php + normregex2token.php currently read lemmamapping.db

`exact` convention mismatch across endpoints:

- regex endpoints: `isset(exact) && exact !== '0'`
- sum/count-per-year endpoints: `isset(exact)`
- token-per-year endpoints: `exact == 1`

Need one project-wide rule and rollout.

## 5) Risk note: REGEXP callback

Current callback uses user-controlled regex in `preg_match()`.
Potential risk:

- expensive patterns (ReDoS)
- full scans when indexes are ineffective with regex

Potential mitigations:

- reject dangerous constructs or very long patterns
- enforce max pattern length
- add endpoint timeouts/limits where possible
- document expected regex complexity

## 6) Decisions needed

- Should ambiguous-regex behavior be extended beyond the six lemma/norm regex endpoints?
- Should all endpoints use explicit `exact=1` / `exact=0` semantics?
- Which DB is authoritative for norm regex group/token views?

# Developer Notes (2026-06-30)

## Scope

Only changes made on 2026-06-30.

Commits:

- 0bec510: fix DB path in norm regex endpoints.
- 1432aa3: fix Enter key handling in autocomplete.
- 13cf5dc: remove unused suffix endpoints.
- 62ae8d2: add precomputed sortkey-based Lower Sorbian ordering for prefix suggestions.

## What changed and why

### 1) Correct DB for norm regex endpoints

Files:

- php/normregex2token.php
- php/normregexgroup.php

Change:

- PDO path changed from ../data/lemmamapping.db to ../data/normmapping.db.

Reason:

- Norm regex endpoints must query norm mapping data, not lemma mapping data.

User effect:

- Norm regex token/group responses are now based on the correct dataset.

### 2) Autocomplete Enter behavior fix

File:

- js/autocomplete.js

Change:

- Keydown listener now runs in capture phase.
- On Enter with an active suggestion: preventDefault, stopImmediatePropagation,
  click highlighted item, return.

Reason:

- Ensure suggestion selection happens before page-level Enter handlers.

User effect:

- Pressing Enter after highlighting a suggestion reliably selects that suggestion.

### 3) Remove unused suffix endpoints

Files removed:

- php/suffixsearch.php
- php/suffixlemmasearch.php
- php/suffixnormsearch.php

Reason:

- Cleanup dead/unused code.

User effect:

- No expected UI impact (no in-repo references found).

### 4) Faster and correct Lower Sorbian prefix sorting

Files:

- dsb_collation.py (new)
- \_bagofwords.py
- \_lemmatisierowasch.py
- \_normierowasch.py
- php/prefixsearch.php
- php/prefixlemmasearch.php
- php/prefixnormsearch.php

Change:

- Added dsb_sortkey() helper in Python.
- Added sortkey TEXT columns and sortkey indexes in relevant SQLite tables.
- ETL scripts now precompute and store sortkeys.
- Prefix endpoints now use ORDER BY sortkey ASC for alphabet mode.
- Output assembly changed to array + implode style.

Reason:

- SQLite default lexical order does not match Lower Sorbian collation.
- Precomputed sortkeys allow correct order directly in SQL with index support.

User effect:

- Alphabetical suggestions follow Lower Sorbian order.
- Suggestion endpoints are faster for alphabet sorting due to indexed ordering.

## Validation done

- PHP syntax checks passed for modified prefix files.
- Python syntax checks passed for modified Python files.
- Manual PHP endpoint smoke calls for changed prefix endpoints returned data.

## Follow-up note

- Deployment/build must ensure databases are rebuilt so new sortkey columns and
  indexes exist before relying on sortkey ordering in prefix endpoints.

## Addendum (2026-06-30)

- `php/prefixlemmasearch.php` and `php/prefixnormsearch.php` now use a
  sortkey-prefix filter in alphabet mode (`sortkey LIKE '<prefixkey>%'`) in
  addition to text prefix matching; this keeps modern Niedersorbisch sorting
  responsive.
- `php/dsb_collation.php` provides the shared PHP `dsb_sortkey()` helper.
- Sorting labels are now provided via language keys (not inline text):
  modernes Niedersorbisch for lemma/norm and Unicode for wortformen.
