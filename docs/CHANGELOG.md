# Changelog

## 2026-08-04

- Made lemma and normalization data processing more reliable and auditable.
- Each corpus passage is now downloaded only once per run, and every attempted document's processing status is recorded.
- Improved evaluation data and added regression coverage for the corrected processing errors.

## 2026-07-28

- added tests for PHP and JS
- added more agents
- added a helper script extract_alphabet.py

## 2026-07-28

- Added tests for Python scripts
- bagofwords functionality covered
- Added regression tests for bagofwords and related Python scripts (lowercasing unicode charachters)
- Fixed failing regression tests and cleaned up a small review-related code change.

## 2026-07-05

- project structure was cleaned up
- temporarily removed all functionality other than Wortform in order to focus on improving and understanding this first

## 2026-06-30

### Wortformen sorting label clarified

On the **Wortformen** page, the alphabetical suggestion mode is now explicitly
labeled as **Unicode** sorting for user clarity.

### Search suggestions are now better and faster

Prefix suggestions now use proper Lower Sorbian ordering and are generated
faster in the database. Pressing Enter on a highlighted suggestion now also
selects that suggestion reliably.

### Norm regex search now uses the correct data source

Norm regex token/group endpoints now read from the norm database (not lemma
database), so Norm results are consistent.

### Unused suffix endpoints removed

Unused suffix search PHP endpoints were removed as cleanup. No UI change is
expected.

**Manual browser test (quick)**

- Open the search page with autocomplete (for example Wortformen/Lemma/Norm).
- Type a prefix like `z`, press Arrow Down to highlight a suggestion, then
  press Enter.
- Expected: the highlighted suggestion is inserted and used, and suggestions
  appear in Lower Sorbian alphabet order.

## 2026-06-24

### Regex search now also finds ambiguous spellings

On the **Lemma**, **Normierung** and **Wortformen** pages there is a **Regex**
search box. A regex search now also finds spellings that could belong to more
than one lemma/norm, not only spellings that map to your search term alone.

**Example**

- Open the **Lemma** page (`.../vis/bwlemma/`).
- In the **Regex** box, type `DRJEWO` and press _Eingabe_.
- Before: you only got forms that map exactly to `DRJEWO`.
- Now: you also get ambiguous forms such as `DRĚŚ|DRJEWO`, where `DRJEWO` is
  one of several possible readings.

This affects all three result panels: the **Timeline** chart, the lemma/norm
list, and the **Tokenliste** (the list of actual spellings with their
occurrence counts). The Timeline label only shows "inkl. ambig" when ambiguous
forms are actually included.

### Token list on the Normierung page now works

The **Tokenliste** panel for a regex search on the **Normierung** page stayed
empty before. It now shows the matching spellings and their counts.

### More secure searches

Search terms typed into the Regex box and the date filters are now passed to
the database safely, so special characters in a search can no longer interfere
with the query.

---

Developer details (rationale, open issues, follow-ups) live in
`dev-notes-2026-06-24.md` and `TODOs.md`.
