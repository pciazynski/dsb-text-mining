## First: the Option A caveats you asked about

**What it does.** Instead of pushing the user's term into the 2M-row detail table, every request resolves in two cheap steps:

1. **Resolve** — match the term(s) against `lemmanonambig` (one row per distinct lemma part, has an indexed `sortkey`). `cs=0` → `WHERE sortkey = ?` (index seek). `cs=1` → `WHERE lemma = ?` (index seek). `regex=1` → `WHERE lemma REGEXP ?` over *this small table only*.
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

One text field + five checkboxes (`cs`, `regex`, `list`, `trim`, `ambig`), deep-linkable, backed by two new shared files — `public/php/searchfilter.php` and `public/js/search.js` — that replace the ad-hoc, string-concatenated SQL in ~14 endpoints and the triplicated inline JS in 5 pages. Built bottom-up: pure functions first, then the resolver, then endpoints, then UI, then mirrored to the other 4 vis.

**Note for every Red step:** if the file under test doesn't exist yet, the Red agent must create an **empty stub** (`<?php` only, or a JS file with just the test-hook footer) so the test fails on an *assertion*, not a fatal/require error — both instruction files require that.

---

### Phase A — shared pure logic (no behaviour change yet)

Steps A1–A3 are parallel with A4–A5.

#### A1 — PHP option parsing DONE
> **TDD Red.** Create `tests/php/SearchFilterTest.php` (namespace `DsbTests`, `final class`, tabs) as a pure unit test that `require_once`s `public/php/searchfilter.php` in `setUpBeforeClass()`. Test a new function `search_options(array $get): array` that maps raw `$_GET` to a normalised options array with keys `cs`, `regex`, `list`, `trim`, `ambig`.
> Behaviour to pin:
> - Empty input array returns the defaults `['cs'=>false,'regex'=>false,'list'=>false,'trim'=>true,'ambig'=>true]`.
> - `'0'`, `''`, `'false'` turn a flag off; `'1'` and `'true'` turn it on.
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
> - `regex=true, cs=true`: `"TE(J|N)"` compiles to a pattern that matches `TEJ` and `TEN` and does **not** match `tej` or `XTEJ` (fully anchored).
> - `regex=true, cs=false`: the same pattern also matches `tej` and `Tej` — including Sorbian casing, so a pattern for `ŚĚŠ` matches `śěš`.
> - **Delimiter injection is neutralised**: a term of `a/i` or `a#x` or `a}` must not change the modifiers or blow up — it either compiles to something that matches those literal strings or returns `null`; it must never emit a PHP warning (phpunit.xml has `failOnWarning="true"`, so a warning is already a failure).
> - An invalid pattern such as `"("` or `"a{2,1}"` returns `null` and emits no warning.
> - `regex=false`: the function is not used for matching at all — assert it returns `null` (literal terms take the equality path, never `preg_match`). This is the "no regex in the backend when regex is off" guarantee.
> Assert matching by calling `preg_match(compile_term_pattern(...), $subject)` directly in the test.

#### A4 — JS option parsing + query-string building DONE
> **TDD Red.** Create `tests/js/search.test.js` (CommonJS, `node:test`, `node:assert/strict`, using `withDom` and `loadScript` from `helpers.js`, always `restore()` in a `finally`). It tests a new file `public/js/search.js` which must expose, via the guarded `module.exports` test-hook footer, `readSearchOptions` and `searchQueryString`.
> Behaviour to pin for `readSearchOptions(searchString)`:
> - `''` returns the defaults `{cs:false, regex:false, list:false, trim:true, ambig:true}` (`assert.deepEqual` on the whole object).
> - `'?lemma=DRJEWO&regex=1&list=1'` returns `regex:true, list:true` with the other defaults intact.
> - `'?cs=1&ambig=0&trim=0'` enables case sensitivity and turns the other two options off.
> - Legacy `'?exact=1'` maps to `ambig:false`; explicit `ambig` wins over `exact`.
> - **These must agree exactly with the PHP `search_options()` defaults from step A1** — add a comment in the test saying so.
> Behaviour to pin for `searchQueryString(fieldName, term, opts)`:
> - Returns a query fragment such as `lemma=DRJEWO&cs=0&ambig=1&trim=1` — flags always emitted explicitly as `0`/`1` (never omitted), so a deep link is unambiguous.
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
> - `cs=false, ambig=true`, term `drjewo` → `['|DRJEWO|','|DRJEWO|DRJEWOWY|','|DRĚŚ|DRJEWO|','|drjewo|']` (sorted). This is the case-insensitive + ambiguous default.
> - `cs=false, ambig=false`, term `drjewo` → `['|DRJEWO|','|drjewo|']` only — no ambiguous cells.
> - `cs=true, ambig=false`, term `drjewo` → `['|drjewo|']` only.
> - `cs=true, ambig=true`, term `DRJEWO` → the three cells containing the uppercase part, **not** `|drjewo|`.
> - Sorbian casing works: `cs=false`, term `drěś` → `['|DRĚŚ|DRJEWO|']`.
> - `DRJEWOWY` must **not** be returned for term `DRJEWO` (no prefix/substring bleed — the `|` boundaries are respected).
> - A term matching nothing returns `[]`.
> - A term of `" OR 1=1 -- ` returns `[]` and does not throw (parameterisation).
> Also assert with `EXPLAIN QUERY PLAN` that the `cs=false, ambig=false` lookup **uses the sortkey index** (`SEARCH` … `USING INDEX`, not `SCAN`) — this is the performance guarantee for the default mode.

#### B2 — resolve lists and regexes, plus the cap DONE
> **TDD Red.** Add tests to `tests/php/SearchResolveTest.php` using the same fixture.
> Behaviour to pin:
> - **List**, `list=true, trim=true, cs=false, ambig=false`, raw input `"drjewo, tej"` (split via `split_terms` from A2) → `['|DRJEWO|','|TEJ|','|drjewo|']`. The reported bug — `TEJ` must be found.
> - **Regex**, `regex=true, cs=true, ambig=true`, term `DRJEWO?` → the cells for `DRJEWO`, and `DRJEW` is not in the fixture so nothing extra; term `DR.*` matches `DRJEWO`, `DRĚŚ`, `DRJEWOWY` parts and expands to all their cells.
> - **Regex + case folding**: `regex=true, cs=false`, term `dr.*o` matches both `|DRJEWO|` and `|drjewo|` parts.
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
> - `?lemma=drjewo&cs=1` returns only the lowercase cell.
> - Legacy `?lemma=DRJEWO&exact=1` behaves identically to `&ambig=0`.
> - `?lemma=drjewo,tej&list=1&trim=1` returns rows for both, `TEJ` included (the reported bug).
> - `?lemma=DR.*O&regex=1` returns the regex matches; the same URL **without** `&regex=1` returns an empty body.
> - Missing `lemma` param → empty body, status 200.
> - **SQL injection**: `?lemma=` + urlencoded `woda" OR "1"="1` returns an **empty body**. Write this as a normal assertion for the correct behaviour, *not* wrapped in `KnownBug` — this step is where it gets fixed.
> - `Content-Type: text/plain` is present.
> Also assert `?lemma=drjewo&regex=1&list=1&trim=1&cs=1&ambig=0` (all five flags) returns a coherent body — the flag matrix must not blow up.

#### C2 — `lemmasumperyear.php` and `lemmacountperyear.php` DONE
> **TDD Red.** Create `tests/php/LemmaperyearEndpointsTest.php` covering both endpoints against the same seeded fixture (add a `date` dimension with two years).
> Pin for each endpoint: the default case-insensitive + ambiguous body; `ambig=0`; `cs=1`; `list=1` with `"drjewo, tej"`; `regex=1`; legacy `exact=1`; missing param; and the injection payload returning an empty body.
> Specifically pin the current comma bug as **fixed**: `?lemma=drjewo,tej&list=1` must return rows for both terms. (Today `str_replace` mangles the second term into a malformed `LIKE`.)

#### C3 — `lemmatoken.php` DONE
> **TDD Red.** Extend the existing `LemmatokenEndpointTest.php` (keep its current tests passing) with the new flag matrix: `cs`, `ambig`, `list` (with `; ` and `, `), `regex`, legacy `exact`, and the injection payload returning an empty body.
> If `tests/php/LemmatokenRegressionsTest.php` contains a `KnownBug` marker for the `lemma` SQL concatenation, **remove that marker** and convert it to a plain assertion here — Green will make it pass and the marker would otherwise XPASS-fail.
> Also pin: `&inclusive` (used by lemmavariation) still behaves as before when the new flags are absent.

#### C4 — `urnbylemma.php` year whitelist + `metadata.php` binding DONE
> **TDD Red.** Create `tests/php/DoclistEndpointsRegressionsTest.php` covering the two endpoints behind bwlemma's document list.
> Behaviour to pin on `/php/urnbylemma.php`:
> - The new flag matrix (`cs`/`ambig`/`list`/`regex`) on the `lemmabag` column, using the resolver's cells and `lemmabag LIKE` per cell.
> - **`year` is no longer raw SQL**: today `&year=` is concatenated verbatim (`' AND date ' . $_GET['year']`). Pin that `?year=1870-1880` and `?year=1870` work as a range/exact filter and that `?year=` + urlencoded `> 0 OR 1=1 --` returns an empty body / is rejected.
> Behaviour to pin on `/php/metadata.php`:
> - `?author=`, `?year=`, `?lang=`, `?restricted=` filter correctly, and each of them with a `" OR 1=1 --` payload returns an empty body (all four are string-concatenated today).

#### C5 — `prefixlemmasearch.php` (autocomplete) DONE
> **TDD Red.** Create `tests/php/PrefixlemmasearchEndpointTest.php`, seeding `lemmanonambig` and `lemmafrequency`.
> Behaviour to pin:
> - `?lemma=drj&limit=30` (default, `cs=0`) returns `DRJEWO`, `DRJEWOWY`, `drjewo` — case-insensitive prefix, pipes stripped, newline-separated. **Today this is broken** because the input is uppercased and matched with a case-sensitive `LIKE` against mixed-case data.
> - `?lemma=drj&cs=1` returns only `drjewo`.
> - Sorbian prefix: `?lemma=drě&cs=0` returns `DRĚŚ`.
> - Suggestions always come from `lemmanonambig` — an ambiguous cell like `DRĚŚ|DRJEWO` is **never** suggested, regardless of any `ambig` param.
> - `sortby` is whitelisted: `alphabet` and `frequency` work; `?sortby=` + `frequency; DROP TABLE lemmanonambig --` returns a normal body and leaves the table intact (assert by issuing a second successful request). Today `sortby` is concatenated straight into `ORDER BY`.
> - `limit` and `cutoff` are cast to int; a non-numeric `limit` falls back to the default.
> - Empty/missing `lemma` → empty body.
> - **Performance**: with `EXPLAIN QUERY PLAN` (via a direct PDO on the fixture, in a separate unit-style test), assert `cs=0` prefix search uses `lemmanonambigsortkey` and `cs=1` uses `lemmanonambiglemma` — a `SEARCH`, never a `SCAN`. This must hold for **both** `sortby=alphabet` and `sortby=frequency`, since frequency is now the default.

---

### Phase D — bwlemma frontend *(depends on A4–A5; D3 depends on D2)*

#### D1 — control enable/disable logic DONE
> **TDD Red.** Add tests to `tests/js/search.test.js` for a function `searchControlState(opts)` exported from `public/js/search.js`. It is a **pure** function returning `{autocomplete: boolean, alphabetSort: boolean}` describing which controls should be enabled.
> Behaviour to pin:
> - Defaults (`regex:false, list:false`) → both `true`.
> - `regex:true` → both `false`.
> - `list:true` → both `false`.
> - `regex:true, list:true` → both `false`.
> - `cs`, `trim`, `ambig` have no effect on the result.
> Then add a second test for `applySearchControlState(document, opts)` — a thin DOM function, tested inside `withDom({html: '<input id="prefixsearchCheckBox" type="checkbox"><input id="searchinput">'})` — asserting it sets `disabled` on `#prefixsearchCheckBox` and detaches/reattaches the autocomplete on `#searchinput` accordingly. Assert the resulting `disabled` property values, not call sequences.

#### D2 — bwlemma markup DONE
> **TDD Red.** Create `tests/js/bwlemma_index_html.test.js` using `loadPage('vis/bwlemma/index.html')` (static parse, no script execution) and `PUBLIC_DIR`.
> Behaviour to pin:
> - There is exactly **one** search text input, with id `searchinput`. The old `#lemma`, `#regexsearch` and `#lemmalist` inputs no longer exist.
> - Five checkboxes exist with ids `csCheckBox`, `regexCheckBox`, `listCheckBox`, `trimCheckBox`, `ambigCheckBox`.
> - The `checked` attribute is present on `csCheckBox`, `trimCheckBox`, `ambigCheckBox` and **absent** on `regexCheckBox`, `listCheckBox`.
> - `#prefixsearchCheckBox` still exists and its `checked` attribute is now **absent** (alphabetical sorting defaults OFF).
> - `js/search.js` is referenced by a `<script src>` that exists under `PUBLIC_DIR`, and it loads **after** `js/datahandler.js` and after `js/def_language.js`.
> - Every new label reads from a `lang_*` global: assert `def_language.js` defines `lang_search_casesensitive`, `lang_search_regex`, `lang_search_list`, `lang_search_trim`, `lang_search_ambig` (grep the file text for the `var` declarations).

#### D3 — bwlemma URL building *(depends on D2)* DONE
> **TDD Red.** Add tests to `tests/js/search.test.js` for `buildVisUrls(kind, term, opts, focus)` exported from `public/js/search.js` — a **pure** function returning the object of iframe `src` URLs for a vis (`{timeline, group, tokens}`), so the inline `updateTimeline`/`updateTimelineRegex`/`updateTimelineList` triple in bwlemma collapses into one code path.
> Behaviour to pin for `kind: 'lemma'`:
> - Defaults, term `DRJEWO`, `focus: 0` → `timeline` is `timeline.html?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0` (assert the exact strings for all three URLs).
> - `focus: 3` switches `data=` to `lemmacountperyear.php`.
> - `list:true` switches the timeline page to `timelinesumlist.html`; everything else keeps the same flags.
> - `regex:true` does **not** change which endpoint is called — the same `lemmasumperyear.php`/`lemmagroup.php`/`lemmatoken.php` handle it via `&regex=1`. (This is what lets Phase F delete the six separate `*regex*.php` endpoints.)
> - A term with `&`, `=`, `#` or `TE(J|N)` is percent-encoded and round-trips.
> - An empty/whitespace-only term returns `null` (caller does nothing).

#### D4 — sub-page flag forwarding DONE
> **TDD Red.** Add tests to `tests/js/search.test.js` for `phpUrlFromLocation(dataParam, fieldName, search)` exported from `public/js/search.js` — the function the bwlemma iframe sub-pages will use instead of hand-concatenating `dataset + '?lemma=' + lemma + '&sort'`.
> Behaviour to pin:
> - Given `search` of `'?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0'`, it returns exactly `lemmasumperyear.php?lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort` — i.e. all five flags survive the hop into the iframe, and vis-only params (`focus`, `jitter`, `scale`) are dropped.
> - Legacy `exact=1` in the incoming search is translated to `ambig=0` on the way out.
> - Missing flags fall back to the A4 defaults.
> - The `data` param is validated: a value of `../../evil.php` or `http://x/` returns `null` (only a bare `[a-z0-9_]+\.php` filename is accepted). This closes an open redirect / arbitrary-fetch hole that exists today.
> Then add a `loadPage` structural test asserting each of `vis/bwlemma/timeline.html`, `timelinesum.html`, `timelinesumlist.html`, `percenttimeline.html`, `percenttimelinesumlist.html`, `lemmalist.html`, `tokenlist.html`, `traviz.html`, `doclist.html` includes `js/search.js` via `<script src>`.
> Finally pin that `timelinesumlist.html`'s per-series split uses `splitTerms` semantics: add a `search.js` test that `splitTerms('drjewo, tej', {list:true, trim:true})` gives the two series names `['drjewo','tej']` — no leading space in the second legend entry.

#### D5 — deep-linking round trip DONE
> **TDD Red.** Add tests to `tests/js/search.test.js` for `restoreSearchFromLocation(document, search)` exported from `public/js/search.js`, tested inside `withDom` with the bwlemma search markup and a `url`.
> Behaviour to pin:
> - `?lemma=DRJEWO&regex=1&list=1` sets `#searchinput.value` to `DRJEWO`, checks `#regexCheckBox` and `#listCheckBox`, leaves `#csCheckBox` unchecked, leaves `#trimCheckBox`/`#ambigCheckBox` checked, and disables `#prefixsearchCheckBox` (per D1).
> - `?lemma=` + urlencoded `TE(J|N)` with `&regex=1` restores the term verbatim.
> - Legacy `?lemma=A,TEKE` with no `list` param restores the raw term with `list` unchecked (old bookmark, unchanged meaning).
> - Legacy `?lemma=X&exact=1` restores with `#ambigCheckBox` **unchecked**.
> - No `lemma` param → input empty, all defaults, nothing triggered.
> - **XSS**: `?lemma=` + urlencoded `<img src=x onerror=alert(1)>` ends up as the input's `.value` only; assert `document.querySelector('img')` is `null` and that `document.body.innerHTML` does not contain `onerror`. (The current pages pass `getQueryVariable` results into `document.write`/`document.title` — this pins the safe path.)
> - Round trip: `readSearchOptions(searchQueryString('lemma', term, opts))` returns `opts` unchanged for every combination of the five flags (loop over all 32 combinations).

---


### intermediate phase - fixing bugs:
- Groß-/Kleinschreibung beachten is working reversed (maybe would be better to change in the code ci to cs - case sensitive?) - DONE
- vorschlage checkbox should be blocked if unavaillable - DONE
- list makes the plot not showing ambig - DONE
- comma problem for regexp, is semicolon safer - DONE
- autocomplete is case sensitive after reload, and later is not, I think let's make it synced to the checkbox - DONE
- regexp without ambig does not work - DONE
- inkl. ambig dynamically write (plot, remove from the button) - DONE
- weird, less used switches to the right (case senstive, leerzeichen) - DONE
- examples write dynamically - DONE


### Phase E — mirror to the other 4 vis *(depends on C + D; E0 blocks E1–E4; E1–E4 mutually parallel after E0)*

Verified state as of 2026-09-23; each fact below is noted as "Important info" on the step(s) it is relevant to.

**Acceptance after all of E:** temporary incompatibility between E steps is acceptable. Once E1–E4 are complete, verify each vis's literal, list, regex, suggestion, clicked-node, year-filtered and deep-link workflows end to end. Keep the explicitly tested `exact=1` alias and injection protections; do not require every old unflagged URL to return an identical body.

#### E0a — resolver by column - DONE
> **Important info:** `resolve_cells()` in `searchfilter.php` currently hardcodes `lemmafrequency`/`lemmanonambig` — generalising it by column is this step. `in_clause()` whitelists `lemma, norm, token, lemmabag, normbag`; the resolver whitelist here is intentionally narrower (`lemma, norm, token`). Do not unify them.
> **TDD Red.** Extend `tests/php/SearchResolveTest.php`. Add a norm fixture (`normfrequency`, `normnonambig`, same rows as the lemma fixture, column `norm`) and pin that `resolve_cells($pdo, 'norm', ...)` gives the same results as the lemma cases (cs / ambig / list / regex / cap / injection) reading the norm tables. Existing lemma tests stay green unchanged.
> Add a token fixture (`tokencount(token, frequency, sortkey)`, bare values, **no pipes**) and pin: `resolve_cells($pdo, 'token', ...)` returns bare tokens; `ambig=0` and `ambig=1` give identical results; **both** values of `ambig` use `tokensortkeyindex` for a `cs=0` literal lookup (`EXPLAIN QUERY PLAN` → `SEARCH … USING INDEX`), including the default `ambig=1`; regex is fully anchored on the whole token.
> An unsupported column (e.g. `lemmabag`, `x; DROP`) throws `InvalidArgumentException`. This whitelist is **narrower** than `in_clause()`'s on purpose (`lemmabag`/`normbag` are bag columns, never resolved) — do not merge the two lists.
> Implementation hint: a whitelist map column → `[ambigTable, partTable]`: `lemma` → `lemmafrequency`/`lemmanonambig`, `norm` → `normfrequency`/`normnonambig`, `token` → `tokencount`/`tokencount`. Tokens have no ambiguous cells: route literal tokens through the indexed part lookup regardless of `ambig`, rather than the default full-table ambiguous scan.

#### E0f — whole-cell terms (clicked items) *(depends on E0a)* - DONE
> **Important info — bug reproduced in UI and with a fixture: clicking an ambiguous cell finds nothing.** `lemmalist.html` strips the outer pipes (`|DRĚŚ|DRJEWO|` → `DRĚŚ|DRJEWO`) and `itemClick()` sends it with `exactOptions` (`cs=1&ambig=0`). The resolver compares the term against single **parts** (`lemmanonambig` holds `|DRĚŚ|` and `|DRJEWO|` separately), so `resolve_request_cells()` returns `[]` for both `ambig=0` and `ambig=1`. Timeline, token list, traviz and doclist stay empty. The legacy `exact=1` meant two different things — "exclude ambiguous cells" *and* "this string is one whole cell" — and only the first survived. `|` is not a valid character inside a lemma/norm, so a term containing `|` is unambiguously a whole cell. normvariation `normclick()` and lemmavariation `lemmaclick()` have the same bug (see E3/E4).
> **Important info:** `lemmafrequency`/`normfrequency` have a `sortkey` index (`lemmafrequencysortkeyindex`, `normfrequencysortkeyindex`) and `dsb_sortkey('DRĚŚ|DRJEWO') === dsb_sortkey('drěś|drjewo')`, so a whole-cell lookup by sortkey is index-backed in both `cs` modes.
> **Why:** see the bug above. A clicked list entry arrives as `DRĚŚ|DRJEWO` and must resolve to exactly the cell `|DRĚŚ|DRJEWO|`.
> **TDD Red.** Extend `tests/php/SearchResolveTest.php` (lemma fixture; also run the same cases against the norm fixture from E0a). Rule: when `regex=false` and a term contains `|`, it is a **whole cell**; `ambig` is ignored for that term.
> Behaviour to pin:
> - `cs=true`, term `DRĚŚ|DRJEWO` → `['|DRĚŚ|DRJEWO|']`, for **both** `ambig=true` and `ambig=false` (assert both).
> - `cs=false`, term `drěś|drjewo` → `['|DRĚŚ|DRJEWO|']`.
> - `cs=true`, term `drěś|drjewo` → `[]` (case must match).
> - Term `DRJEWO|DRĚŚ` (parts in the other order) → `[]` — the cell is matched verbatim, not as a set.
> - Term `|DRJEWO|` (pipes not stripped by a caller) → `['|DRJEWO|']` — outer pipes are trimmed before matching, so a single-part cell still works.
> - Mixed list `list=true`, raw `drjewo;DRĚŚ|DRJEWO`, `cs=true, ambig=false` → `['|DRĚŚ|DRJEWO|','|drjewo|']` — whole-cell and part terms coexist in one request.
> - `regex=true`, term `DRĚŚ|DRJEWO` is **not** a whole cell: `|` stays regex alternation, so with `cs=true, ambig=false` the result contains the part cells `|DRĚŚ|` and `|DRJEWO|` (from `lemmanonambig`) and does **not** contain `|DRĚŚ|DRJEWO|`. Use `assertEqualsCanonicalizing`, not an ordered assertion.
> - `EXPLAIN QUERY PLAN` for the `cs=false` whole-cell lookup shows `SEARCH … USING INDEX` on `lemmafrequency` (`lemmafrequencysortkeyindex` in the fixture), never `SCAN`.
> Then pin the endpoint: in `tests/php/LemmagroupEndpointTest.php` and `LemmaperyearEndpointsTest.php`, the exact call bwlemma's `itemClick()` sends — `?lemma=DRĚŚ|DRJEWO&cs=1&regex=0&list=0&trim=1&ambig=0&sort` — returns that cell's rows (non-empty body). Tokens never contain `|`, so no token case.
> Implementation hint: `_resolve_nonambiguous_cells()` already does sortkey seek + optional `cs` filter against a table parameter. For a term containing `|` (after trimming outer pipes), call it against the **cell table** (`lemmafrequency`/`normfrequency`) instead of the part table; `trim($cell,'|') === $term` is then the whole-cell comparison. Split terms into "whole-cell" and "part" groups first, resolve each, concatenate.

#### E0b — truncation signal *(parallel with E0a)* - DONE
> **Important info:** `X-Dsb-Result-Truncated` is not emitted anywhere yet.
> **Why:** the resolver silently stops at `SEARCH_RESULT_CAP` (500) cells. A broad regex (`D.*`) or a long list then gives plots and sums that **undercount without telling the user** — wrong numbers in a research tool. The header lets the page say "Resultset too large. Please refine query." (`lang_error_resultset_too_large`, already defined).
> **TDD Red (PHP).** In `tests/php/LemmagroupEndpointTest.php` and `LemmaperyearEndpointsTest.php`: a request resolving more than the cap (seed >500 parts, `regex=1`, term `.*`) sends `X-Dsb-Result-Truncated: 1`; a normal request does **not** send the header. Emit it once, inside `resolve_request_cells()`, guarded by `headers_sent()`, so every endpoint using it gets it for free.
> **TDD Red (JS).** In `tests/js/search.test.js`, two functions exported from `search.js`:
> - `showTruncationNotice(doc, xhr)` — given a fake `{getResponseHeader: name => '1'}` it prepends to `doc.body` one element whose `textContent` is `lang_error_resultset_too_large` (never `innerHTML`) and returns `true`; given an xhr whose header is `null` or `'0'` it adds nothing and returns `false`; calling it twice adds only one notice (assert `doc.querySelectorAll(...)` length is 1).
> - `readPHPChecked(doc, url)` — calls the global `readPHP(url)` (stub it in the test with a `globalThis.readPHP` that sets `globalThis.rawFile = {getResponseHeader: ...}` and returns a body), then inspects the global `rawFile` (that's where `datahandler.js`'s synchronous `readPHP()` leaves its `XMLHttpRequest`). Returns the body when the header is absent; when the header is `'1'` it calls `showTruncationNotice` and returns `null`. Pin both branches.
> **Structural test** (`loadPage`, text-based, add to the D4 test): for each of bwlemma's `timeline.html`, `timelinesum.html`, `timelinesumlist.html`, `percenttimeline.html`, `percenttimelinesumlist.html`, `lemmalist.html`, `tokenlist.html`, `traviz.html`, the page source contains `readPHPChecked(` and does **not** contain `readPHP(` (regex `/\breadPHP\(/`) — i.e. every fetch goes through the checked wrapper. Each page treats a `null` return as "render nothing" (`timelinesumlist.html`: skip that series). E1–E4 add their sub-pages to the same list as they migrate (norm, word and variation sub-pages incl. percent, list and tree views). `doclist.html` uses `readPHP_async` and is excluded — its endpoint (`urnbylemma.php`) does not use the resolver.
> `# CEILING:` note for Green: `header()` inside `resolve_request_cells()` only works because every endpoint resolves before printing; guard with `headers_sent()` and leave the comment there.

#### E0c — `search.js` per-kind config *(parallel with E0a)* - DONE
> **Important info:** `search.js` hardcodes `lemma` in `buildVisUrls()` (endpoints + `lemmalist.html`), `listTermsFromLocation()`, `restoreSearchFromLocation()` and `searchExample()` — generalising these is this step. bwword is deep-linked with `?word=` ([bwword/index.html](public/vis/bwword/index.html#L395)) while its PHP takes `token`. `?word=` links are generated live by `bwword/wordinfo.html`, `lemmavariation/datalist.html` and `normvariation/datalist.html` (the last one has a stray `"` after `word=` — broken today, fixed in E2). Static examples in the current pages (real corpus entries): bwnorm `Chóśebuz` / `te(j|n)` / `tej,ten`; bwword `w(o|a)n(a|i)` / `druge,woni`; normvariation `druge,francojski`.
> **TDD Red.** In `tests/js/search.test.js`:
> - `buildVisUrls('norm', 'DRJEWO', defaults, 0)` → `timeline.html?data=normsumperyear.php&norm=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0`, `group: normlist.html?data=normgroup.php&…&sort`, `tokens: tokenlist.html?data=normtoken.php&…&sort`; `focus: 3` → `normcountperyear.php`; `list:true` → `timelinesumlist.html`. Assert exact strings.
> - `buildVisUrls('token', 'woni', defaults, 0)` returns exactly two keys: `timeline: 'timeline.html?data=tokencountperyear.php&token=woni&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0'` and `wordinfo: 'wordinfo.html?data=token2lemma.php&token=woni'`. With `list:true` or `regex:true`, `wordinfo` is `'error_token.html'` (word-info only makes sense for one concrete token); `timeline` keeps `timeline.html` (bwword has no `timelinesumlist.html`). `focus` is ignored for tokens except being forwarded. `linreg_chart.html` is a toggle on the same iframe in `bwword/index.html`, not a separate URL — leave it to the page. Assert exact strings.
> - All existing `buildVisUrls('lemma', …)` tests stay green unchanged.
> - `listTermsFromLocation(search, field)` and `restoreSearchFromLocation(doc, search, field)` read `field` (default `'lemma'`, so bwlemma callers don't change): `?norm=A;B&list=1` gives `['A','B']` for `'norm'`.
> - **Legacy alias for bwword:** `restoreSearchFromLocation(doc, '?word=woni', 'token')` fills `#searchinput` with `woni` (falls back to `word` when `token` is absent; `token` wins when both are present). Only for `field === 'token'`.
> - `listPlotUrlsFromLocation('data', 'norm', '?data=normsumperyear.php&norm=A;B&list=1')` returns two norm-series URLs, not `[]`: pass its `termKey` into `listTermsFromLocation()`. Existing lemma-series URLs stay unchanged; bwnorm's list plot uses the new URLs.
> - `searchExample(options, kind)` — pin the exact strings below (`kind` defaults to `'lemma'`). Lists always use `;` in examples (comma is still accepted as input when `regex` is off). `trim:false` drops the space after `;`. Lemmas are stored uppercase, so only the lemma examples change with `cs`; norm and token examples are **identical for `cs` on and off**.
>
>   | kind | literal | regex | list | regex+list |
>   |---|---|---|---|---|
>   | `lemma`, cs off | `drjewo` | `te(j\|n)` | `drjewo; bom` | `te(j\|n); bom` |
>   | `lemma`, cs on | `DRJEWO` | `TE(J\|N)` | `DRJEWO; BOM` | `TE(J\|N); BOM` |
>   | `norm` | `Chóśebuz` | `te(j\|n)` | `tej; ten` | `te(j\|n); Chóśebuz` |
>   | `token` | `woni` | `w(o\|a)n(a\|i)` | `druge; woni` | `w(o\|a)n(a\|i); druge` |
>
>   The existing lemma-list assertions (`drjewo, bom`) change to `drjewo; bom` — update them. Pass `kind` through `applySearchExample(doc, kind)` and its page callers (`switchSearchOptions()`, `restoreSearchFromLocation()`), so the displayed example actually changes.

#### E0d — `urnbylemma.php` hardening, reusable for `urnbynorm.php` *(depends on E0a, E0f)* - DONE
> **Important info:** `urnbylemma.php` does not use `searchfilter.php` today: its regex is `'/'.$term.'/'` (unanchored, delimiter injection) and lists split on whitespace/comma. The bwlemma UI only calls it with one exact cell + `cs=1&regex=0&list=0&ambig=0`, so this is only reachable by crafted URL.
> **TDD Red.** In `tests/php/DoclistEndpointsRegressionsTest.php`:
> - The exact call bwlemma sends (`?lemma=<cell>&cs=1&regex=0&list=0&trim=1&ambig=0&year=1870-1880`) returns the expected matching document rows — pin that final behavior, not byte-for-byte compatibility with the old implementation.
> - `?lemma=a/i&regex=1` and `?lemma=(&regex=1` return an empty body and no PHP warning.
> - `regex=1` is fully anchored like the resolver: `DR` does not match `DRJEWO`, `DR.*` does.
> - `list=1` splits via `split_terms()`: `NJEBYŚ LI` stays one term; `drjewo;tej` finds both.
> - Whole-cell term (E0f rule, same as the resolver): `?lemma=DRĚŚ|DRJEWO&cs=1&regex=0&ambig=0` matches documents whose `lemmabag` contains the cell `|DRĚŚ|DRJEWO|`, and **not** documents that only contain `|DRJEWO|`. Today the bag is exploded on `||` into cells and each cell on `|` into parts; compare the whole cell when the term contains `|`.
> Implementation: replace only the inline `preg_match` with `compile_term_pattern()` and the inline split with `split_terms()`; add the whole-cell branch; do not restructure the rest.
> Move the year parsing into `year_clause(?string $year): ?array` in `searchfilter.php`, pinned in `SearchFilterTest.php` with `assertSame` on the whole array. **Semantics: unparsable → `null` → the endpoint prints an empty body (a wrong filter must never show an unfiltered result — accuracy over friendliness). Missing or empty → no filter.**
>
>   | input | result |
>   |---|---|
>   | `null` (param absent) | `['sql' => '1=1', 'params' => []]` |
>   | `''`, `'   '` | `['sql' => '1=1', 'params' => []]` |
>   | `'1870'` | `['sql' => 'date = ?', 'params' => ['1870']]` |
>   | `'1870-1880'` | `['sql' => 'date BETWEEN ? AND ?', 'params' => ['1870', '1880']]` |
>   | `' 1870 - 1880 '` | same as `'1870-1880'` |
>   | `'> 0 OR 1=1 --'` | `null` |
>   | `'BETWEEN 1 AND 2'` | `null` |
>   | `'1870-'`, `'-1880'`, `'1870-1880-1890'`, `'abcd'` | `null` |
>
>   Endpoints do `$year = year_clause($_GET['year'] ?? null); if ($year === null) { exit; }` and append `' AND ' . $year['sql']`. It is reused by E0e and E1.

#### E0e — per-year token endpoints and `token2norm.php` *(depends on E0d's `year_clause`)* - DONE
> **Important info:** `lemmatokenperyear.php`/`normtokenperyear.php` concatenate `year=BETWEEN x AND y` into SQL today (injection via URL). `token2norm.php` concatenates `token`.
> **TDD Red.** Create `tests/php/TokenperyearEndpointsTest.php` for `lemmatokenperyear.php` (seeds `lemmamapping.db`) and `normtokenperyear.php` (seeds `normmapping.db` — two databases in one `dataDir()`):
> - `year=1870-1880` restricts to the range, `year=1870` to one year; `year=` + urlencoded `BETWEEN 1 AND 2 OR 1=1` and `> 0 OR 1=1 --` return an empty body. **Missing `year` now returns the unfiltered rows** (today the endpoint requires it — deliberate change per E0d's table).
> - Term matching goes through `resolve_request_cells()` (flag matrix + legacy `exact=1` + injection payload on the term, as C1), including the E0f whole-cell call bwlemma's `updateTravizYear()` sends: `?lemma=DRĚŚ|DRJEWO&cs=1&regex=0&list=0&trim=1&ambig=0&sort&year=1870-1880`.
> - Update `updateTravizYear()` in `bwlemma/index.html` to send `&year=<from>-<to>` and delete its `CEILING` comment; pin the new URL in `search.test.js` if it's built there, otherwise with a `loadPage` text check. `bwnorm/index.html` also sends `year=BETWEEN ...` in `updateTravizYear()` **and** `itemClick()`: E1 must update both to the validated range format. Until E1, the bwnorm traviz may temporarily stop working; verify it again at the end of E.
> Add to the same file: `token2norm.php?token=<existing>` returns the same body as before; `?token=` + urlencoded `x" OR "1"="1` returns an empty body.

#### E1 — bwnorm *(depends on E0; E1a–E1d mutually parallel)*

All PHP steps seed `normmapping.db` in `dataDir()` with the norm twin of the lemma fixture (`tokennormtypesubtypedatefrequency`, `normfrequency`, `normnonambig`, `normtokenfrequency`, `urndatenormbag`; column `norm`). Each prompt is literally "mirror test X with `lemma` → `norm`"; `normtokenperyear.php` is already covered by E0e.

##### E1a — `normgroup.php`, `normsumperyear.php`, `normcountperyear.php`, `normtoken.php`
> **TDD Red.** Create `tests/php/NormSearchEndpointsTest.php` mirroring `LemmagroupEndpointTest.php` (for `normgroup.php`), `LemmaperyearEndpointsTest.php` (for `normsumperyear.php`/`normcountperyear.php`) and the flag-matrix part of `LemmatokenEndpointTest.php` (for `normtoken.php`), with `lemma` → `norm` everywhere: default cs-insensitive + ambiguous body, `ambig=0`, `cs=1`, `list=1` with `drjewo; tej`, `regex=1`, legacy `exact=1`, missing param → empty body, injection payload → empty body, the E0f whole-cell call (`?norm=DRĚŚ|DRJEWO&cs=1&ambig=0`) → that cell's rows, `X-Dsb-Result-Truncated: 1` on an over-cap regex (E0b). Green: each endpoint gets the same `resolve_request_cells($pdo, 'norm', $_GET)` + `in_clause('norm', …)` shape as its lemma twin.

##### E1b — `urnbynorm.php`
> **TDD Red.** Create `tests/php/UrnbynormEndpointTest.php` mirroring the `urnbylemma.php` half of `DoclistEndpointsRegressionsTest.php` incl. E0d's additions: the exact call bwnorm sends (`?norm=<cell>&cs=1&regex=0&list=0&trim=1&ambig=0&year=1870-1880`), the E0f whole-cell case, the `year_clause` table (range, single year, missing → unfiltered, garbage → empty body), `regex=1` anchored, `list=1` via `split_terms()`, injection on `norm` and `year` → empty body. Green: copy `urnbylemma.php`'s post-E0d structure over `normbag`.

##### E1c — `prefixnormsearch.php`
> **Important info:** `*nonambig` is a misleading name: `mapping_etl.py` inserts **every distinct part** split from all cells, with frequencies including ambiguous occurrences — suggesting from it loses no lemma/norm. No page sends `&ambig` to a prefix endpoint (profile's `ambigprefixsearchCheckBox` is commented out; `switchAmbigPrefixsearch()` is dead code). `prefixnormsearch.php`'s `cutoff` means "one suggestion per prefix group" (`GROUP BY SUBSTRING(norm,1,strlen+cutoff)`), unlike `prefixlemmasearch.php`'s length cap; normvariation depends on it (`cutoff=2`).
> **TDD Red.** Create `tests/php/PrefixnormsearchEndpointTest.php` mirroring `PrefixlemmasearchEndpointTest.php` (`lemma` → `norm`, tables `normnonambig`/`normfrequency`, indexes `normnonambigsortkey`/`normnonambignorm`): case-insensitive prefix default, `cs=1`, Sorbian prefix, suggestions only from `normnonambig`, `&ambig` ignored (profile's checkbox is commented out), whitelisted `sortby`, int `limit`, `SEARCH` never `SCAN` for both sort orders.
> **Deliberate changes to state in the test:** (1) with no `sortby`, the order is now `frequency DESC` (today: unordered); (2) `cutoff` keeps its **grouping** meaning, not the lemma length cap — normvariation's autocomplete sends `cutoff=2&limit=20`: at most one suggestion per distinct prefix of length (typed length + `cutoff`) of the pipe-prefixed value. Fixture: `|Chóśebuz|`, `|Chóśebuski|`, `|Chóśebuzar|`, typed `Chó`, `cutoff=2` → prefixes of 6 chars of `|Chóśe…` → all three share `|Chóśe` → exactly one suggestion; typed `Chóśebu`, `cutoff=2` → three. Count **characters** (`SUBSTR` on the UTF-8 string in SQLite counts characters; do not pass a PHP `strlen`) — today `strlen('ě')` = 2 over-counts. Non-numeric `cutoff` is ignored (no 500). `GROUP BY` loses the `LIMIT` early stop — Green marks it `# CEILING:`.

##### E1d — bwnorm frontend
> **TDD Red (JS).** Create `tests/js/bwnorm_index_html.test.js` mirroring the **current** `bwlemma_index_html.test.js` (single `#searchinput`, five checkboxes with the same defaults, `#prefixsearchCheckBox` unchecked, `#searchexample`, `#ambigSearchButton`, `switchSearchOptions()` wiring, `js/search.js` after `datahandler.js` and `def_language.js`). Extend the D4 structural test and the E0b `readPHPChecked` text check to the bwnorm sub-pages (`timeline`, `timelinesum`, `timelinesumlist`, `percenttimeline`, `percenttimelinesumlist`, `normlist`, `tokenlist`, `traviz`; `doclist` loads `search.js` only): each fetches via `phpUrlFromLocation('data', 'norm', …)`. `timelinesumlist.html` uses the norm-series URLs from E0c; `traviz`/`doclist` get `searchQueryString('norm', exactitem, exactOptions)` + `&year=<from>-<to>` in both `updateTravizYear()` and `itemClick()` (replacing `year=BETWEEN …`), same as bwlemma. `callNormtree()` opens `../normvariation?norm=…`. Keep `normlist.html` passing the clicked cell with outer pipes stripped — E0f makes that work.

#### E2 — bwword *(depends on E0)*
> **TDD Red (PHP).** Create `tests/php/WordSearchEndpointsTest.php` for `tokencountperyear.php` and `prefixsearch.php` against `bagofwords.db` (`tokencount(token, frequency, sortkey)`, `tokendatecount`):
> - No ambiguity: `ambig=0` and `ambig=1` return identical bodies.
> - `tokencountperyear.php?token=woda&cs=0` returns rows for both `woda` and `Woda` (fixture has both spellings) — **new behaviour**, today the `LIKE` is case-sensitive. `cs=1` returns only `woda`. `EXPLAIN QUERY PLAN` on the fixture: the `cs=0` literal lookup uses `tokensortkeyindex`.
> - `?token=druge;woni&list=1&trim=1` returns both; `?token=druge,woni&list=1` also (comma legacy); `regex=1` with `w(o|a)n(a|i)` returns `woni`/`wona`-style fixture rows and nothing else (anchored).
> - `prefixsearch.php`: `?word=wo` (default `cs=0`) returns `woda`, `Woda`, `woni` in `frequency DESC` order; `?word=wo&cs=1` excludes `Woda`; `sortby=alphabet` now orders by dsb `sortkey` (**deliberate change** — today it is Unicode `token` order); `sortby` whitelisted (`frequency; DROP TABLE tokencount --` → normal body, table intact on a second request); `limit` int. `cutoff` today builds `SUBSTRING(word, …)` on a nonexistent column — no bwword caller sends it, so **ignore it** (numeric or garbage) and pin that both `?word=wo&cutoff=2` and `?word=wo&cutoff=x` return normal suggestions, not a 500.
> - Injection payloads on `token`, `word`, `sortby` → empty/normal bodies with tables intact.
> - Once E3/E4 are complete, clicked tokens in both variation views reach `tokencountperyear.php` and show the expected rows; byte-for-byte compatibility with old `?token=X&sort` responses is not required.
> - `token2lemma.php` is already parameterised — untouched.
> **TDD Red (JS).** Create `tests/js/bwword_index_html.test.js` mirroring E1d's markup test, but `#ambigCheckBox` and the ambig label on `#ambigSearchButton` are **absent**; `#searchinput` replaces `#wordinput`, `#regexsearch`, `#wordlist`. The bwword sub-pages (`timeline`, `percenttimeline`, `linreg_chart`) load `search.js`, use `phpUrlFromLocation('data', 'token', …)` and `readPHPChecked` (add to the E0b text check). `index.html` calls `restoreSearchFromLocation(document, window.location.search, 'token')` — the `?word=` alias from E0c keeps the live cross-links from `wordinfo.html`, `lemmavariation/datalist.html` and `normvariation/datalist.html` working; fix the stray `"` in `normvariation/datalist.html`'s `href=../bwword/?word="` while there (pin with a `loadPage` text check that the file contains `?word=' +` and not `?word="'`). `updateTimeline()` sets the two iframes from `buildVisUrls('token', …)` (E0c) — `wordinfo` gets `error_token.html` on list/regex searches; the `switchlinreg` button is disabled when `list` or `regex` is on (pin via `searchControlState` — add a `linreg` key that equals `autocomplete`).

#### E3 — lemmavariation *(depends on E0)*
> **Important info:** `lemmatree_dagre.html` decides the root node via `dataset.includes('regex.php')` and `lemma.includes(',')` today — this is what `treeHasRoot()` below replaces. `phpUrlFromLocation()` forwards only the five flags + `sort`; `inclusive`/`weight` are frontend-only (the backend ignores `inclusive`, pinned in C3). `lemmaclick()` has the same ambiguous-cell bug as bwlemma's `itemClick()` (see E0f) — fixed the same way.
> **TDD Red.** Create `tests/js/lemmavariation_index_html.test.js` mirroring E1's markup test (ids, defaults, `search.js` order). In `search.test.js` add `buildTreeUrls(kind, term, opts, weight)`:
> - `kind:'lemma'` returns `{tree, sunburst, traviz}` for `lemmatree_dagre.html`, `sunburst.html`, `traviz.html`, each `?data=lemmatoken.php&<flags>&sort&inclusive`; `weight:true` appends `&weight`. Assert exact strings.
> - `regex:true` keeps `data=lemmatoken.php` (never `lemmatokenregex.php`).
> - `appendToList(existing, item)`: `('', 'A')` → `'A'`, `('A', 'B')` → `'A;B'`, trims, does not add a duplicate.
> Tree sub-pages (`lemmatree_dagre.html`, `sunburst.html`, `traviz.html`) load `search.js`, fetch via `phpUrlFromLocation('data', 'lemma', …)` + `readPHPChecked` (add to the E0b text check) and re-append `&inclusive`/`&weight` themselves. The root-node decision uses a new pure `treeHasRoot(search)` exported from `search.js` — `true` when `inclusive` is present, `regex=1` or `list=1`; `false` for `'?data=lemmatoken.php&lemma=DRJEWO'` — pinned for all four cases, replacing `dataset.includes('regex.php')`/`lemma.includes(',')`.
> Clicked-node paths: `lemmaclick(cell)` sends `searchQueryString('lemma', cell, exactOptions)` (same `exactOptions` as bwlemma) to `lemmatimeline.html?data=lemmacountperyear.php&…&sort&focus=3` — the cell may be ambiguous (`DRĚŚ|DRJEWO`), which E0f makes work; `tokenclick(token)` sends `searchQueryString('token', token, exactOptions)` to `timeline.html?data=tokencountperyear.php&…&sort` and `datalist.html?data=token2lemma.php&token=…`. Pin these two URL shapes in `search.test.js` as `buildClickUrls(kind, item)` if you extract them, otherwise with a `loadPage` text check.
> `index.html` restores with `restoreSearchFromLocation(document, window.location.search, 'lemma')`; the old `curlemma.includes(',')` branch goes away (a legacy `?lemma=A,B` deep link restores as a single literal, per D5). `updateTree`/`updateTreeFromList`/`updateTreeFromRegex` collapse into one `buildTreeUrls` call.

#### E4 — normvariation *(depends on E0; parallel with E3)*
> **Important info:** `normtokenregex.php` (linked by normvariation) does not exist — its regex tree is broken today. `normtree_dagre.html` decides the root node via `dataset.includes('regex.php')` and `lemma.includes(',')` today, same as `lemmatree_dagre.html` (see E3). `normclick()` has the same ambiguous-cell bug as bwlemma's `itemClick()` (see E0f) — fixed the same way.
> **TDD Red.** Create `tests/js/normvariation_index_html.test.js` mirroring E3's markup test. `buildTreeUrls('norm', …)` returns only `{tree, traviz}` (`normtree_dagre.html`, `traviz.html` — there is **no sunburst**) with `data=normtoken.php`. `regex:true` produces a working URL — today it points at the non-existent `normtokenregex.php`.
> `normtree_dagre.html` and `traviz.html` get the same `phpUrlFromLocation` + `treeHasRoot` + `readPHPChecked` change as E3.
> Clicked-node path `normclick(item)`: items starting with `|` are norm cells → strip outer pipes and send `searchQueryString('norm', cell, exactOptions)` to `normtimeline.html?data=normcountperyear.php&…&sort&focus=3` (ambiguous cells work via E0f); other items are tokens → `tokentimeline.html?data=tokencountperyear.php&` + `searchQueryString('token', item, exactOptions)` + `&sort&focus=3` and `datalist.html?data=token2norm.php&token=…`. Pin both shapes as in E3.
> The autocomplete call keeps `prefixnormsearch.php?cutoff=2&limit=20&norm=` (its `cutoff` semantics are pinned in E1c). `token2norm.php` is covered by E0e. The hard-coded example link `?norm=druge,francojski` becomes `?norm=druge;francojski&list=1`.

---

### Phase F — cleanup *(TDD **Refactor**, not Red; depends on E)*

#### F1 — delete the dead regex endpoints
> **TDD Refactor.** With `&regex=1` handled by the main endpoints, delete all **8** files: `lemmaregexsearch.php`, `lemmaregexgroup.php`, `lemmaregex2token.php`, `lemmatokenregex.php`, `normregexsearch.php`, `normregexgroup.php`, `normregex2token.php`, `regexsearch.php` — together with their **8** copies of `_sqliteRegexp()`. None survives: `searchfilter.php` matches with `preg_match` in PHP and registers no SQLite function.
> First grep `public/vis`, `public/js` and `tests` for `regex[a-z0-9]*\.php` and `regex.php`. After E the only acceptable hits are none — in particular the `dataset.includes('regex.php')` checks in `lemmatree_dagre.html`/`normtree_dagre.html` must already be replaced by `treeHasRoot()` (E3/E4). If any reference survives, stop and report instead of deleting. `composer test` and `npm test` stay green with no test changes.

#### F2 — collapse duplicated inline JS
> **TDD Refactor, only where duplication remains after E.** Move genuinely identical URL building and list operations from `updateTimeline*` / `updateTree*` / `switchPrefixsearch` / `addToList` / `addLemmaToList` / `addNormToList` / `addWordToList` into existing `search.js` helpers, leaving thin delegations where that preserves behavior. Keep page-specific actions local: word-info and regression controls, autocomplete endpoint/cutoff settings, year-filtered traviz/doclist, and variation tree controls need not become one generic handler. **Out of scope:** `vis/lemmaeval`, `vis/normeval`, `vis/profile` keep their own autocomplete wiring and inputs — they are not part of the unified search box. Before removing a body, pin any untested interactions it owns (search, suggestion toggle, list/regex, clicked item, year range); then run `npm test` and the affected PHP tests. Do not add a new abstraction solely to make every wrapper one line.

### Phase G - manual verification and bug fixing
#### G1 - Manually check if everything works as expected
#### G2 - Fix bugs if necessary

