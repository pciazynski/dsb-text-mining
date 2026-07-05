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
