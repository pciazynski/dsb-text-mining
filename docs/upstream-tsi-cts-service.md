# Lower Sorbian corpus services at `tsi.daty.info`

This document describes the remote TSI services used by
this project and current production behavior as observed on
2026-08-01. The data and configuration can change.

## Background information

- This repo (DTS/DTM) is the *last* stage of a longer chain it does not control.
- TSI/CTS services provides passages of corpus data and some statistical analysis like frequencies of words, which DTS can consume.
- This project of this repo here (DTS - dsb-text-mining) access remote TSI in order to fetch those data and in order to to further staistical analysis and load the data for later presentation.
- If configured diffferently this project here (DTS) can access different remote instance of TSI.
- TSI provides all the data, but it cannot be 100% trusted, at least for now.
- If really needed for resolving some deep issue or to understand TSI better, the code of TSI can be accessed here: https://github.com/pciazynski/text-service-infrastructure
- If you need info about the corpus itself look at `docs/data-lower-sorbian-corpus.md`

## How corpus data gets into TSI/CTS

Data flow chain: 
1. TEI dump of the corpus from the language department (manual, periodic dump).
2. external filter/partition script (`tsi_dsb_import.jar`)
3. external script `CTSImport.jar` which loads data into MariaDB tables from CTS service
4. `buildcache.py` script from CTS service. After this stage CTS is ready to serve data under tsi.daty.info (or other URL). 
5. It can be now consumed by this repo here (DTM) by starting `setup.py` which run the whole processing pipeline and is caching everything into text files and SQLite.

## Production tokenization

The current `tsi.daty.info` configuration has `multibyte=false`. Therefore
`lowercase` uses PHP `strtolower()`: ASCII case is folded, but Unicode uppercase
letters are not reliably folded. Real outputs include uppercase forms such as
`Ẃedro`, `Łukow`, and `Žěkowach`. Endpoint-level `lowercase` is therefore not
complete Unicode case folding.

The production `replacearr` replaces a broad set of characters with spaces,
including `. , ! ?`, brackets, underscores, straight apostrophes, and common
hyphen/dash/minus characters. It does not include every Unicode punctuation
character. The right curly apostrophe `’` survives both inside forms such as
`k’tim` and as a standalone token; one sampled 1882 issue contains `’\t1`.

Other properties that materially affect results:

- splitting is on literal ASCII space, not general Unicode whitespace;
- no NFC/NFKC normalization is applied, so precomposed and decomposed-looking
  forms can be distinct keys (for example combining acute accents in `ßeb́e`);
- XML is removed with `<[^>]+>`, not parsed, so nested markup can create false
  boundaries and entities are not handled as XML data;
- TEI `type="ignore"` is ignored by the text-mining endpoints: numbers,
  fragments and nonlexical material are counted like words;
- `sort` and `lowercase` are presence-only flags: `lowercase=false` still turns
  lowercasing on.

The result is a frequency list of transformed **surface strings**, not a list of
linguistically normalized words.

## Endpoint contract

The namespace resolver currently maps `dsb` to `https://tsi.daty.info/`.
Responses below are UTF-8 plain text without TSV headers. Work URNs end in `:`;
passage URNs append a citation, and ranges use `{start}-{end}`.

### Inventory

```http
GET {base}plain/editions.php
```

Each row has exactly six tab-separated fields:

```text
urn  title  year  author  restricted  lang
```

Example (shown with `\t`):

```text
urn:cts:dsb:bramborske_nowiny_1882_37.20220128:\tBramborſke Nowiny 35 (1882) 37\t1882\t\t0\tdeu
```

Useful filters are `urnfilter`, `author`, `title`, `lang`, `restricted=1`, and
`unrestricted=1`; `sortBy` accepts `author`, `year`, `author,year`, or
`author,title`. The current handler reads but does not apply `year`, `yearmin`,
`yearmax`, or `offset`. Cached unfiltered and sort-only responses can be stale;
the live `sortBy=year` response was not chronologically ordered.

### Passage and annotations

```http
GET {base}plain/passage.php?urn={urn}[&copyrighttoken=...]
```

Without `deletexml`, this returns TEI-like fragments, not one XML document:

```xml
<w xmlns="http://www.tei-c.org/ns/1.0" lemma="PŚIŚ" norm="pśiźo">Pſchiżo</w>
<w xmlns="http://www.tei-c.org/ns/1.0" lemma="NA" norm="na">na</w>
```

### Bag of words

```http
GET {base}tm/bagofwords.php?urn={urn}&sort&lowercase
```

Output is exactly `surface-form<TAB>integer-count`, for example:

```text
a	130
ße	66
na	65
```

Each nonempty response line has exactly two fields and the count is an integer.
Frequencies describe the surface-string transformation above, not lemma or
normalized-word frequencies.

### N-grams

```http
GET {base}tm/ngrams.php?urn={urn}&n={integer>=2}&sort&lowercase
```

Output is `space-separated n-gram<TAB>integer-count`:

```text
k tomu	4
a tak	4
až do	4
```

Production sentence boundaries are comma, period, `!`, `?`, and `―`; windows
never cross them. Thus a comma always ends an n-gram sequence, even when it is
not a linguistic sentence boundary. Numbers and metadata are included: observed
bigrams include `na 3`, `1 mk`, and `100 lět`. The PHP handler validates `n`
using loose comparison.

## Restricted content and failures

Production has restricted documents enabled and a nonempty copyright token.
Technical access behavior currently differs by endpoint:

1. `plain/passage.php` requires the configured token for restricted text.
2. `tm/bagofwords.php` returns aggregate counts for restricted URNs without a
   token check.
3. `tm/ngrams.php` allows a restricted whole-work URN ending in
   `:` without a valid token, although it checks restricted passage/range URNs.

These points describe endpoint behavior, not institutional authorization for
aggregate analysis. A hidden deployment can use a separate token and access
policy for full restricted data.

Errors are plain-text bodies, often with HTTP 200, for example `Error code 7:
Unauthorized Access`. Missing parameters may expose PHP warnings instead of a
stable error body.
