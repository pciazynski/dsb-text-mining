## First: the Option A caveats you asked about

**What it does.** Instead of pushing the user's term into the 2M-row detail table, every request resolves in two cheap steps:

1. **Resolve** — match the term(s) against `lemmanonambig` (one row per distinct lemma part, has an indexed `sortkey`). `ci` → `WHERE sortkey = ?` (index seek). `cs` → `WHERE lemma = ?` (index seek). `regex=1` → `WHERE lemma REGEXP ?` over *this small table only*.
2. **Expand** — if `ambig=1`, find the whole cells containing those parts: `SELECT lemma FROM lemmafrequency WHERE lemma LIKE ?` with `%|PART|%`. If `ambig=0`, just `WHERE lemma = ?`.
3. **Query** — the detail table gets `WHERE lemma IN (?,?,…)`, exact equality, hits `lemmaindex`.

**The real trade-offs:**

| # | Caveat | Severity / mitigation |
|---|---|---|
| 1 | Two extra small queries per request | Negligible — same PDO connection, both index-backed |
| 2 | **`IN()` parameter limit.** SQLite caps host params at 999 (<3.32) / 32766 (≥3.32). A broad regex (`.*`) could resolve to 100k cells | Cap resolution at N=500 cells + `X-Dsb-Result-Truncated: 1` header. The frontend already has `resultsetmax` / `lang_error_resultset_too_large`. If you ever need unbounded, escalate to a TEMP table + JOIN |
| 3 | **`ambig=1` still needs one unindexable `LIKE '%|PART|%'`** | But over `lemmafrequency` (distinct lemma cells) instead of the 2M-row detail table — still a large win, not O(1). Gets a `# CEILING:` comment |
| 4 | **Coupling**: results now depend on `lemmafrequency`/`lemmanonambig` agreeing with the detail table | Both are built in the same `_fill()` pass in `mapping_etl.py` from the same counter, so they do agree. Pinned by a regression test asserting resolve+IN returns the same rows as the old `LIKE`. |
| 5 | **Regex semantics shift**: today the pattern is wrapped as `.*\|X\|.*` and run against the whole cell `\|A\|B\|`. Now it runs against a bare part | For every realistic pattern (`TE(J\|N)`) the result is identical, and it's what users actually mean. A cross-pipe pattern like `TEN\|TO` stops working — the ambig checkbox now covers that intent |
| 6 | One new shared `require_once` in ~14 endpoints | Offset by deleting the per-endpoint `str_replace`/regex-building — net less code |

Net effect on performance: **faster than today** in every mode, because today's regex path full-scans 2M rows (`LIMIT 2100000`) and today's fuzzy path uses an unindexable `LIKE '%|X|%'` on the same table.

---

## Plan: Unified search box for bwlemma/bwnorm/bwword/lemmavariation/normvariation

One text field + five checkboxes (`ci`, `regex`, `list`, `trim`, `ambig`), deep-linkable, backed by two new shared files — `public/php/searchfilter.php` and `public/js/search.js` — that replace the ad-hoc, string-concatenated SQL in ~14 endpoints and the triplicated inline JS in 5 pages. Built bottom-up: pure functions first, then the resolver, then endpoints, then UI, then mirrored to the other 4 vis.

**Note for every Red step:** if the file under test doesn't exist yet, the Red agent must create an **empty stub** (`<?php` only, or a JS file with just the test-hook footer) so the test fails on an *assertion*, not a fatal/require error — both instruction files require that.

---

### Phase A — shared pure logic (no behaviour change yet)

Steps A1–A3 are parallel with A4–A5.

#### A1 — PHP option parsing DONE
> **TDD Red.** Create `tests/php/SearchFilterTest.php` (namespace `DsbTests`, `final class`, tabs) as a pure unit test that `require_once`s `public/php/searchfilter.php` in `setUpBeforeClass()`. Test a new function `search_options(array $get): array` that maps raw `$_GET` to a normalised options array with keys `ci`, `regex`, `list`, `trim`, `ambig`.
> Behaviour to pin:
> - Empty input array returns the defaults `['ci'=>true,'regex'=>false,'list'=>false,'trim'=>true,'ambig'=>true]`.
> - `'0'`, `''`, `'false'` turn a flag off; `'1'`, `'true'`, and a bare valueless param (`?ci`) turn it on.
> - Legacy alias: `exact=1` means `ambig=false`; `exact=0` means `ambig=true`; an explicit `ambig` param wins over `exact` when both are present.
> - Unknown/garbage values fall back to the default rather than throwing.
> Use `assertSame` on the whole array. One behaviour per test.

#### A2 — PHP term splitting DONE
> **TDD Red.** Add tests to `tests/php/SearchFilterTest.php` for a new pure function `split_terms(string $raw, array $opts): array` in `public/php/searchfilter.php`.
> Behaviour to pin:
> - `list=false`: returns exactly one element, the whole string, regardless of `;` or `,` in it (so a regex containing `,` survives).
> - `list=true`: splits on `;` **and** on `,` (legacy support), so `"drjewo;tej"` and `"drjewo,tej"` both give `['drjewo','tej']`.
> - `trim=true`: leading/trailing whitespace is stripped from each term, so `"drjewo, tej"` gives exactly `['drjewo','tej']` — this is the reported bug. Internal spaces are preserved, so `" NJEBYŚ LI "` gives `['NJEBYŚ LI']` (single space kept between the two words).
> - `trim=false`: `"drjewo, tej"` gives `['drjewo',' tej']`.
> - Empty terms are dropped: `"a;;b;"` gives `['a','b']`; an all-whitespace input gives `[]`.
> - Unicode whitespace (NBSP U+00A0) is trimmed too when `trim=true`.

#### A3 — PHP safe regex compilation DONE
> **TDD Red.** Add tests to `tests/php/SearchFilterTest.php` for a new pure function `compile_term_pattern(string $term, array $opts): ?string` in `public/php/searchfilter.php`, which turns a user term into a PCRE pattern string ready for `preg_match`, or `null` if the term is not a usable pattern.
> Behaviour to pin:
> - `regex=true, ci=false`: `"TE(J|N)"` compiles to a pattern that matches `TEJ` and `TEN` and does **not** match `tej` or `XTEJ` (fully anchored).
> - `regex=true, ci=true`: the same pattern also matches `tej` and `Tej` — including Sorbian casing, so a pattern for `ŚĚŠ` matches `śěš`.
> - **Delimiter injection is neutralised**: a term of `a/i` or `a#x` or `a}` must not change the modifiers or blow up — it either compiles to something that matches those literal strings or returns `null`; it must never emit a PHP warning (phpunit.xml has `failOnWarning="true"`, so a warning is already a failure).
> - An invalid pattern such as `"("` or `"a{2,1}"` returns `null` and emits no warning.
> - `regex=false`: the function is not used for matching at all — assert it returns `null` (literal terms take the equality path, never `preg_match`). This is the "no regex in the backend when regex is off" guarantee.
> Assert matching by calling `preg_match(compile_term_pattern(...), $subject)` directly in the test.

#### A4 — JS option parsing + query-string building DONE
> **TDD Red.** Create `tests/js/search.test.js` (CommonJS, `node:test`, `node:assert/strict`, using `withDom` and `loadScript` from `helpers.js`, always `restore()` in a `finally`). It tests a new file `public/js/search.js` which must expose, via the guarded `module.exports` test-hook footer, `readSearchOptions` and `searchQueryString`.
> Behaviour to pin for `readSearchOptions(searchString)`:
> - `''` returns the defaults `{ci:true, regex:false, list:false, trim:true, ambig:true}` (`assert.deepEqual` on the whole object).
> - `'?lemma=DRJEWO&regex=1&list=1'` returns `regex:true, list:true` with the other defaults intact.
> - `'?ci=0&ambig=0&trim=0'` turns those three off.
> - Legacy `'?exact=1'` maps to `ambig:false`; explicit `ambig` wins over `exact`.
> - **These must agree exactly with the PHP `search_options()` defaults from step A1** — add a comment in the test saying so.
> Behaviour to pin for `searchQueryString(fieldName, term, opts)`:
> - Returns a query fragment such as `lemma=DRJEWO&ci=1&ambig=1&trim=1` — flags always emitted explicitly as `0`/`1` (never omitted), so a deep link is unambiguous.
> - The term is `encodeURIComponent`-escaped: a term of `a&b=c` and a regex term of `TE(J|N)` must round-trip through `new URLSearchParams` back to the original string.
> - Key order is stable (assert the exact full string).

#### A5 — JS term splitting (mirror of A2) DONE
> **TDD Red.** Add tests to `tests/js/search.test.js` for `splitTerms(raw, opts)` exported from `public/js/search.js`.
> Pin exactly the same cases as PHP step A2 — `list` off = single term; `list` on splits on `;` and `,`; `trim` on turns `"drjewo, tej"` into `['drjewo','tej']` but keeps `'NJEBYŚ LI'` intact with its inner space; `trim` off keeps `' tej'`; empty terms dropped; NBSP handled.
> Use `assert.deepEqual` on the full arrays. Add a comment naming `tests/php/SearchFilterTest.php` as the PHP twin that must stay in sync.

---

### Phase B — the PHP resolver *(depends on A1–A3)*

#### B1 — resolve literal terms DONE
> **TDD Red.** Create `tests/php/SearchResolveTest.php`. It `require_once`s `public/php/searchfilter.php` and, in `setUp()`, builds a **temporary SQLite file** (in a temp dir it creates and deletes itself — do not touch `data`) with tables `lemmanonambig(lemma, frequency, sortkey)` and `lemmafrequency(lemma, frequency, sortkey)`.
> Fixture rows (sortkey computed with the real `dsb_sortkey()` from `dsb_collation.php`, on the value with outer pipes stripped, exactly as `mapping_etl.py` does):
> - `lemmanonambig`: `|DRJEWO|`, `|drjewo|`, `|DRĚŚ|`, `|DRJEWOWY|`, `|TEJ|`, `|NJEBYŚ LI|`
> - `lemmafrequency`: `|DRJEWO|`, `|drjewo|`, `|DRĚŚ|DRJEWO|`, `|DRJEWO|DRJEWOWY|`, `|TEJ|`, `|NJEBYŚ LI|`
>
> Test a new function `resolve_cells(PDO $pdo, string $field, array $terms, array $opts): array` returning the sorted list of concrete pipe-wrapped cell values to query the detail tables with.
> Behaviour to pin (`regex=false` throughout):
> - `ci=true, ambig=true`, term `drjewo` → `['|DRJEWO|','|DRJEWO|DRJEWOWY|','|DRĚŚ|DRJEWO|','|drjewo|']` (sorted). This is the case-insensitive + ambiguous default.
> - `ci=true, ambig=false`, term `drjewo` → `['|DRJEWO|','|drjewo|']` only — no ambiguous cells.
> - `ci=false, ambig=false`, term `drjewo` → `['|drjewo|']` only.
> - `ci=false, ambig=true`, term `DRJEWO` → the three cells containing the uppercase part, **not** `|drjewo|`.
> - Sorbian casing works: `ci=true`, term `drěś` → `['|DRĚŚ|DRJEWO|']`.
> - `DRJEWOWY` must **not** be returned for term `DRJEWO` (no prefix/substring bleed — the `|` boundaries are respected).
> - A term matching nothing returns `[]`.
> - A term of `" OR 1=1 -- ` returns `[]` and does not throw (parameterisation).
> Also assert with `EXPLAIN QUERY PLAN` that the `ci=true, ambig=false` lookup **uses the sortkey index** (`SEARCH` … `USING INDEX`, not `SCAN`) — this is the performance guarantee for the default mode.

#### B2 — resolve lists and regexes, plus the cap DONE
> **TDD Red.** Add tests to `tests/php/SearchResolveTest.php` using the same fixture.
> Behaviour to pin:
> - **List**, `list=true, trim=true, ci=true, ambig=false`, raw input `"drjewo, tej"` (split via `split_terms` from A2) → `['|DRJEWO|','|TEJ|','|drjewo|']`. The reported bug — `TEJ` must be found.
> - **Regex**, `regex=true, ci=false, ambig=true`, term `DRJEWO?` → the cells for `DRJEWO`, and `DRJEW` is not in the fixture so nothing extra; term `DR.*` matches `DRJEWO`, `DRĚŚ`, `DRJEWOWY` parts and expands to all their cells.
> - **Regex + ci**: `regex=true, ci=true`, term `dr.*o` matches both `|DRJEWO|` and `|drjewo|` parts.
> - **List of regexes**: `regex=true, list=true`, raw `"DR.*O;TE."` resolves both patterns in one call.
> - **`regex=false` never uses regex**: assert that a term containing regex metacharacters, e.g. `DR.*O`, returns `[]` (it is treated as a literal string, and no literal lemma `DR.*O` exists).
> - **Invalid regex**: `regex=true`, term `(` returns `[]` and produces no PHP warning.
> - **Cap**: seed 600 extra parts, resolve with `regex=true` and term `.*`; assert at most 500 cells come back (a `SEARCH_RESULT_CAP` constant in `searchfilter.php`) and that a companion function `resolve_was_truncated()` (or a by-ref/second return element — your call, pin one shape) reports truncation.

#### B3 — parameterised `IN` clause builder DONE
> **TDD Red.** Add tests to `tests/php/SearchFilterTest.php` for a pure function `in_clause(string $column, array $cells): array` in `public/php/searchfilter.php`, returning `['sql' => ..., 'params' => [...]]`.
> Behaviour to pin:
> - Three cells produce SQL of exactly `lemma IN (?,?,?)` and `params` equal to the three cells in order.
> - An empty cell list produces a **never-true** clause (e.g. `1=0`) with empty params — so an endpoint with no matches returns nothing instead of returning everything. Assert the exact string.
> - The column name is validated against a whitelist (`lemma`, `norm`, `token`, `lemmabag`, `normbag`); anything else throws `InvalidArgumentException`. This closes the identifier-injection hole.

---

### Phase C — bwlemma PHP endpoints *(depends on B)*

Each of C1–C5 is independent of the others and can run in parallel. All are HTTP smoke tests via `DevServer` (`DevServer.php`), seeded per-test into `$server->dataDir()`.

#### C1 — `lemmagroup.php` DONE
> **TDD Red.** Create `tests/php/LemmagroupEndpointTest.php`. Boot `DevServer`, seed `lemmamapping.db` in `dataDir()` with `tokenlemmatypesubtypedatefrequency`, `lemmafrequency` and `lemmanonambig` using the same small fixture as `tests/php/SearchResolveTest.php` (a handful of rows so exact bodies are assertable).
> Behaviour to pin on `/php/lemmagroup.php`:
> - Default request `?lemma=drjewo&sort` returns the exact tab-separated body for the case-insensitive, ambiguous-inclusive match — all cells containing `DRJEWO`, ordered by `sumfreq DESC`, newline-terminated.
> - `?lemma=drjewo&ambig=0` returns only the unambiguous cells.
> - `?lemma=drjewo&ci=0` returns only the lowercase cell.
> - Legacy `?lemma=DRJEWO&exact=1` behaves identically to `&ambig=0`.
> - `?lemma=drjewo,tej&list=1&trim=1` returns rows for both, `TEJ` included (the reported bug).
> - `?lemma=DR.*O&regex=1` returns the regex matches; the same URL **without** `&regex=1` returns an empty body.
> - Missing `lemma` param → empty body, status 200.
> - **SQL injection**: `?lemma=` + urlencoded `woda" OR "1"="1` returns an **empty body**. Write this as a normal assertion for the correct behaviour, *not* wrapped in `KnownBug` — this step is where it gets fixed.
> - `Content-Type: text/plain` is present.
> Also assert `?lemma=drjewo&regex=1&list=1&trim=1&ci=0&ambig=0` (all five flags) returns a coherent body — the flag matrix must not blow up.

#### C2 — `lemmasumperyear.php` and `lemmacountperyear.php`
> **TDD Red.** Create `tests/php/LemmaperyearEndpointsTest.php` covering both endpoints against the same seeded fixture (add a `date` dimension with two years).
> Pin for each endpoint: the default ci+ambig body; `ambig=0`; `ci=0`; `list=1` with `"drjewo, tej"`; `regex=1`; legacy `exact=1`; missing param; and the injection payload returning an empty body.
> Specifically pin the current comma bug as **fixed**: `?lemma=drjewo,tej&list=1` must return rows for both terms. (Today `str_replace` mangles the second term into a malformed `LIKE`.)

#### C3 — `lemmatoken.php`
> **TDD Red.** Extend the existing `LemmatokenEndpointTest.php` (keep its current tests passing) with the new flag matrix: `ci`, `ambig`, `list` (with `; ` and `, `), `regex`, legacy `exact`, and the injection payload returning an empty body.
> If `tests/php/LemmatokenRegressionsTest.php` contains a `KnownBug` marker for the `lemma` SQL concatenation, **remove that marker** and convert it to a plain assertion here — Green will make it pass and the marker would otherwise XPASS-fail.
> Also pin: `&inclusive` (used by lemmavariation) still behaves as before when the new flags are absent.

#### C4 — `urnbylemma.php` year whitelist + `metadata.php` binding
> **TDD Red.** Create `tests/php/DoclistEndpointsRegressionsTest.php` covering the two endpoints behind bwlemma's document list.
> Behaviour to pin on `/php/urnbylemma.php`:
> - The new flag matrix (`ci`/`ambig`/`list`/`regex`) on the `lemmabag` column, using the resolver's cells and `lemmabag LIKE` per cell.
> - **`year` is no longer raw SQL**: today `&year=` is concatenated verbatim (`' AND date ' . $_GET['year']`). Pin that `?year=1870-1880` and `?year=1870` work as a range/exact filter and that `?year=` + urlencoded `> 0 OR 1=1 --` returns an empty body / is rejected.
> Behaviour to pin on `/php/metadata.php`:
> - `?author=`, `?year=`, `?lang=`, `?restricted=` filter correctly, and each of them with a `" OR 1=1 --` payload returns an empty body (all four are string-concatenated today).

#### C5 — `prefixlemmasearch.php` (autocomplete)
> **TDD Red.** Create `tests/php/PrefixlemmasearchEndpointTest.php`, seeding `lemmanonambig` and `lemmafrequency`.
> Behaviour to pin:
> - `?lemma=drj&limit=30` (default, `ci=1`) returns `DRJEWO`, `DRJEWOWY`, `drjewo` — case-insensitive prefix, pipes stripped, newline-separated. **Today this is broken** because the input is uppercased and matched with a case-sensitive `LIKE` against mixed-case data.
> - `?lemma=drj&ci=0` returns only `drjewo`.
> - Sorbian prefix: `?lemma=drě&ci=1` returns `DRĚŚ`.
> - Suggestions always come from `lemmanonambig` — an ambiguous cell like `DRĚŚ|DRJEWO` is **never** suggested, regardless of any `ambig` param.
> - `sortby` is whitelisted: `alphabet` and `frequency` work; `?sortby=` + `frequency; DROP TABLE lemmanonambig --` returns a normal body and leaves the table intact (assert by issuing a second successful request). Today `sortby` is concatenated straight into `ORDER BY`.
> - `limit` and `cutoff` are cast to int; a non-numeric `limit` falls back to the default.
> - Empty/missing `lemma` → empty body.
> - **Performance**: with `EXPLAIN QUERY PLAN` (via a direct PDO on the fixture, in a separate unit-style test), assert `ci=1` prefix search uses `lemmanonambigsortkey` and `ci=0` uses `lemmanonambiglemma` — a `SEARCH`, never a `SCAN`. This must hold for **both** `sortby=alphabet` and `sortby=frequency`, since frequency is now the default.

---

### Phase D — bwlemma frontend *(depends on A4–A5; D3 depends on D2)*

#### D1 — control enable/disable logic
> **TDD Red.** Add tests to `tests/js/search.test.js` for a function `searchControlState(opts)` exported from `public/js/search.js`. It is a **pure** function returning `{autocomplete: boolean, alphabetSort: boolean}` describing which controls should be enabled.
> Behaviour to pin:
> - Defaults (`regex:false, list:false`) → both `true`.
> - `regex:true` → both `false`.
> - `list:true` → both `false`.
> - `regex:true, list:true` → both `false`.
> - `ci`, `trim`, `ambig` have no effect on the result.
> Then add a second test for `applySearchControlState(document, opts)` — a thin DOM function, tested inside `withDom({html: '<input id="prefixsearchCheckBox" type="checkbox"><input id="searchinput">'})` — asserting it sets `disabled` on `#prefixsearchCheckBox` and detaches/reattaches the autocomplete on `#searchinput` accordingly. Assert the resulting `disabled` property values, not call sequences.

#### D2 — bwlemma markup
> **TDD Red.** Create `tests/js/bwlemma_index_html.test.js` using `loadPage('vis/bwlemma/index.html')` (static parse, no script execution) and `PUBLIC_DIR`.
> Behaviour to pin:
> - There is exactly **one** search text input, with id `searchinput`. The old `#lemma`, `#regexsearch` and `#lemmalist` inputs no longer exist.
> - Five checkboxes exist with ids `ciCheckBox`, `regexCheckBox`, `listCheckBox`, `trimCheckBox`, `ambigCheckBox`.
> - The `checked` attribute is present on `ciCheckBox`, `trimCheckBox`, `ambigCheckBox` and **absent** on `regexCheckBox`, `listCheckBox`.
> - `#prefixsearchCheckBox` still exists and its `checked` attribute is now **absent** (alphabetical sorting defaults OFF).
> - `js/search.js` is referenced by a `<script src>` that exists under `PUBLIC_DIR`, and it loads **after** `js/datahandler.js` and after `js/def_language.js`.
> - Every new label reads from a `lang_*` global: assert `def_language.js` defines `lang_search_casesensitive`, `lang_search_regex`, `lang_search_list`, `lang_search_trim`, `lang_search_ambig` (grep the file text for the `var` declarations).

#### D3 — bwlemma URL building *(depends on D2)*
> **TDD Red.** Add tests to `tests/js/search.test.js` for `buildVisUrls(kind, term, opts, focus)` exported from `public/js/search.js` — a **pure** function returning the object of iframe `src` URLs for a vis (`{timeline, group, tokens}`), so the inline `updateTimeline`/`updateTimelineRegex`/`updateTimelineList` triple in bwlemma collapses into one code path.
> Behaviour to pin for `kind: 'lemma'`:
> - Defaults, term `DRJEWO`, `focus: 0` → `timeline` is `timeline.html?data=lemmasumperyear.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort&focus=0` (assert the exact strings for all three URLs).
> - `focus: 3` switches `data=` to `lemmacountperyear.php`.
> - `list:true` switches the timeline page to `timelinesumlist.html`; everything else keeps the same flags.
> - `regex:true` does **not** change which endpoint is called — the same `lemmasumperyear.php`/`lemmagroup.php`/`lemmatoken.php` handle it via `&regex=1`. (This is what lets Phase F delete the six separate `*regex*.php` endpoints.)
> - A term with `&`, `=`, `#` or `TE(J|N)` is percent-encoded and round-trips.
> - An empty/whitespace-only term returns `null` (caller does nothing).

#### D4 — sub-page flag forwarding
> **TDD Red.** Add tests to `tests/js/search.test.js` for `phpUrlFromLocation(dataParam, fieldName, search)` exported from `public/js/search.js` — the function the bwlemma iframe sub-pages will use instead of hand-concatenating `dataset + '?lemma=' + lemma + '&sort'`.
> Behaviour to pin:
> - Given `search` of `'?data=lemmasumperyear.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort&focus=0'`, it returns exactly `lemmasumperyear.php?lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort` — i.e. all five flags survive the hop into the iframe, and vis-only params (`focus`, `jitter`, `scale`) are dropped.
> - Legacy `exact=1` in the incoming search is translated to `ambig=0` on the way out.
> - Missing flags fall back to the A4 defaults.
> - The `data` param is validated: a value of `../../evil.php` or `http://x/` returns `null` (only a bare `[a-z0-9_]+\.php` filename is accepted). This closes an open redirect / arbitrary-fetch hole that exists today.
> Then add a `loadPage` structural test asserting each of `vis/bwlemma/timeline.html`, `timelinesum.html`, `timelinesumlist.html`, `percenttimeline.html`, `percenttimelinesumlist.html`, `lemmalist.html`, `tokenlist.html`, `traviz.html`, `doclist.html` includes `js/search.js` via `<script src>`.
> Finally pin that `timelinesumlist.html`'s per-series split uses `splitTerms` semantics: add a `search.js` test that `splitTerms('drjewo, tej', {list:true, trim:true})` gives the two series names `['drjewo','tej']` — no leading space in the second legend entry.

#### D5 — deep-linking round trip
> **TDD Red.** Add tests to `tests/js/search.test.js` for `restoreSearchFromLocation(document, search)` exported from `public/js/search.js`, tested inside `withDom` with the bwlemma search markup and a `url`.
> Behaviour to pin:
> - `?lemma=DRJEWO&regex=1&list=1` sets `#searchinput.value` to `DRJEWO`, checks `#regexCheckBox` and `#listCheckBox`, leaves `#ciCheckBox`/`#trimCheckBox`/`#ambigCheckBox` checked, and disables `#prefixsearchCheckBox` (per D1).
> - `?lemma=` + urlencoded `TE(J|N)` with `&regex=1` restores the term verbatim.
> - Legacy `?lemma=A,TEKE` with no `list` param restores the raw term with `list` unchecked (old bookmark, unchanged meaning).
> - Legacy `?lemma=X&exact=1` restores with `#ambigCheckBox` **unchecked**.
> - No `lemma` param → input empty, all defaults, nothing triggered.
> - **XSS**: `?lemma=` + urlencoded `<img src=x onerror=alert(1)>` ends up as the input's `.value` only; assert `document.querySelector('img')` is `null` and that `document.body.innerHTML` does not contain `onerror`. (The current pages pass `getQueryVariable` results into `document.write`/`document.title` — this pins the safe path.)
> - Round trip: `readSearchOptions(searchQueryString('lemma', term, opts))` returns `opts` unchanged for every combination of the five flags (loop over all 32 combinations).

---

### Phase E — mirror to the other 4 vis *(depends on C + D; E1–E4 mutually parallel)*

#### E1 — bwnorm
> **TDD Red.** Mirror Phase C and Phase D for bwnorm. Create `tests/php/NormSearchEndpointsTest.php` covering `normgroup.php`, `normsumperyear.php`, `normcountperyear.php`, `normtoken.php`, `urnbynorm.php` and `prefixnormsearch.php` with the same flag matrix and the same injection assertions as C1–C5, using `normmapping.db` with `normfrequency`/`normnonambig`/`tokennormtypesubtypedatefrequency`.
> Create `tests/js/bwnorm_index_html.test.js` mirroring D2 (ids `searchinput`, five checkboxes, `prefixsearchCheckBox` unchecked, `js/search.js` loaded) and add `kind: 'norm'` cases to the `buildVisUrls` tests from D3, asserting the exact URLs with `norm=` and the `norm*` endpoints.
> Note `prefixnormsearch.php` does **not** currently uppercase its input (unlike the lemma one) — pin that both now behave identically under `ci=1`/`ci=0`.

#### E2 — bwword
> **TDD Red.** Mirror for bwword. Create `tests/php/WordSearchEndpointsTest.php` covering `tokencountperyear.php` and `prefixsearch.php` against `bagofwords.db` (`tokencount(token, frequency, sortkey)` + `tokendatecount`).
> Differences to pin explicitly:
> - There is **no ambiguity concept** for word forms: `?token=X&ambig=0` and `&ambig=1` return identical bodies, and the resolver goes `tokencount` → `token IN (...)` on `tokendatecount` with no pipes and no expansion step.
> - `ci=1` is index-backed via `tokensortkeyindex` (assert with `EXPLAIN QUERY PLAN`); today `prefixsearch.php` does a case-**sensitive** `LIKE` with no sortkey filter at all, so `?word=w&ci=1` finding `Woda` is a new behaviour to pin.
> - `?token=a,b&list=1&trim=1` returns both (today the comma OR-chain is concatenated).
> - Injection payloads on `token`, `word` and `sortby` return empty bodies.
> Create `tests/js/bwword_index_html.test.js` mirroring D2 but asserting `#ambigCheckBox` is **absent** from the bwword markup, and add `kind: 'word'` cases to `buildVisUrls`.

#### E3 — lemmavariation
> **TDD Red.** Mirror for lemmavariation, whose main endpoint is `lemmatoken.php` (already covered in C3) called with `&inclusive` and `&weight`.
> Create `tests/js/lemmavariation_index_html.test.js` mirroring D2, and add a `buildTreeUrls(kind, term, opts, weight)` function to `public/js/search.js` with tests pinning: the three tree iframes (`lemmatree_dagre.html`, `sunburst.html`, `traviz.html`) all get `data=lemmatoken.php` plus the five flags plus `&sort&inclusive`, `weight:true` appends `&weight`, `regex:true` does not switch to `lemmatokenregex.php`, and the `addToList` button now joins with `;` instead of `,` (test a pure `appendToList(existing, item)` helper).
> Also pin that `updateTreeFromRegex`/`updateTreeFromList` no longer exist as separate paths — one `buildTreeUrls` call covers all flag combinations.

#### E4 — normvariation
> **TDD Red.** Mirror E3 for normvariation: `tests/js/normvariation_index_html.test.js` plus `kind: 'norm'` cases for `buildTreeUrls` against `normtoken.php` and the `norm*` tree pages. Note normvariation's autocomplete currently passes `&cutoff=2` — pin that `cutoff` is still forwarded and still int-cast.

---

### Phase F — cleanup *(TDD **Refactor**, not Red; depends on E)*

#### F1 — delete the dead regex endpoints
> **TDD Refactor.** With `&regex=1` now handled by the main endpoints, delete `lemmaregexsearch.php`, `lemmaregexgroup.php`, `lemmaregex2token.php`, `lemmatokenregex.php`, `normregexsearch.php`, `normregexgroup.php`, `normregex2token.php` and `regexsearch.php`, plus the six copies of `_sqliteRegexp()` they contain (the one surviving copy lives in `searchfilter.php`).
> Grep `vis` and `tests` for every reference first; the full suite (`composer test` and `npm test`) must stay green with no test changes. If any reference survives, stop and report instead of deleting.

#### F2 — collapse duplicated inline JS
> **TDD Refactor.** With all five vis driven by `public/js/search.js`, remove the now-duplicated inline `updateTimeline*` / `updateTree*` / `switchPrefixsearch` / `addToList` bodies from the five `index.html` files, leaving thin one-line delegations. No test changes; `npm test` stays green.

---

### Relevant files

**New**
- `public/php/searchfilter.php` — `search_options()`, `split_terms()`, `compile_term_pattern()`, `resolve_cells()`, `in_clause()`, the single surviving `_sqliteRegexp()`, `SEARCH_RESULT_CAP`
- `public/js/search.js` — `readSearchOptions()`, `searchQueryString()`, `splitTerms()`, `searchControlState()`, `applySearchControlState()`, `buildVisUrls()`, `buildTreeUrls()`, `phpUrlFromLocation()`, `restoreSearchFromLocation()`, `appendToList()` + test-hook footer

**Modified — PHP** (all lose their concatenated SQL): `lemmagroup.php`, `normgroup.php`, `lemmasumperyear.php`, `normsumperyear.php`, `lemmacountperyear.php`, `normcountperyear.php`, `lemmatoken.php`, `normtoken.php`, `lemmatokenperyear.php`, `normtokenperyear.php`, `urnbylemma.php`, `urnbynorm.php`, `tokencountperyear.php`, `token2norm.php`, `metadata.php`, `prefixlemmasearch.php`, `prefixnormsearch.php`, `prefixsearch.php`

**Modified — JS/HTML**: the 5 `public/vis/*/index.html` plus their iframe sub-pages; `def_language.js` (5 new `lang_*` labels); `my_language.js` (template entries)

**Reuse, don't reinvent**: `dsb_sortkey()` in `dsb_collation.php`; `DevServer.php`; `helpers.js` (`withDom`, `loadScript`, `loadPage`, `knownBug`); `getQueryVariable()` in `datahandler.js`; the existing `resultsetmax` / `lang_error_resultset_too_large` mechanism

---

### Verification

1. `composer test` and `npm test` green after every Green step.
2. After C5 and E2, the `EXPLAIN QUERY PLAN` assertions prove the default (ci, non-regex) path is a `SEARCH … USING INDEX`, never a `SCAN` — the no-degradation guarantee.
3. Manual on the running server at `127.0.0.1:8000/vis/bwlemma/`: `drjewo, tej` with list+trim on shows **both** series; `DRJEWO` with ambig off shows only `|DRJEWO|`; ticking regex greys out both the suggestions and the alphabet checkbox.
4. Deep link `?lemma=DRJEWO&regex=1&list=1&ci=0&ambig=0&trim=1&headerconf=111111` restores the exact form state and results.
5. Grep the modified endpoints for `. $_GET` — the only remaining occurrences should be int casts and whitelisted identifiers.
6. Spot-check timing on the real `lemmamapping.db` before/after for `DRJEWO` (ambig on) and for `DR.*O` (regex) — the regex case should improve by orders of magnitude.

---

### Decisions taken

- **Two-phase resolve (Option A)** with the caveat table above; cap N=500 cells + `X-Dsb-Result-Truncated: 1` header.
- **Defaults**: `ci` ON, `ambig` ON, `trim` ON (your correction), `regex` OFF, `list` OFF, alphabetical suggestion sorting OFF.
- **Delimiter**: `;` primary, `,` still accepted for legacy links; splitting only happens when `list=1`, so a regex may contain commas freely.
- **Legacy `exact`** accepted as an alias for `!ambig` everywhere; explicit `ambig` wins.
- **Autocomplete** always suggests non-ambiguous forms and follows the `ci` checkbox — both paths index-backed, so typing stays fast.
- **`regex=0` means no `preg_match` anywhere** — pinned by an explicit test in A3 and B2.
- **Excluded**: `lemmaprofile.php`/`normprofile.php`/`wordprofile.php` (single-item detail pages, not the search box), `psedcytassearch.php`, `token2lemma.php` (already parameterised), the ETL, and any change to the DB schema.

### Further considerations

1. **Truncation UX.** The cap is currently silent apart from a response header. Do you want a visible "too many matches, narrow your search" message (an extra step reusing `lang_error_resultset_too_large`), or is silent capping acceptable for now?
2. **`ci` and the autocomplete request rate.** Suggestions fire on every keystroke through a *synchronous* `XMLHttpRequest` (`readPHP`). That's pre-existing, but if typing feels sluggish after the change it's the cause, not the new SQL. Want a small debounce step added, or leave it out of scope?
3. **`prefixsearch.php` becoming case-insensitive by default** is a visible behaviour change for bwword users who currently rely on case-sensitive prefix matching. The `ci` checkbox gives it back — flagging it so it doesn't surprise your stakeholder.
