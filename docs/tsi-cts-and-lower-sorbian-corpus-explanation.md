# Lower Sorbian corpus services at `tsi.daty.info`

This document describes the remote TSI services used by
this project, including
their Lower Sorbian corpus data and current production behavior as observed on
2026-08-01. The data and configuration can change. The custom `plain/` and `tm/`
endpoints are not standard CTS operations.

## Linguistic layers

The service exposes three non-equivalent representations:

| Layer           | Source                                                     | Best suited to                                           | Important limitation                                                        |
| --------------- | ---------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------- |
| Surface form    | Text inside `<w>`; `tm/bagofwords.php` and `tm/ngrams.php` | Historical spelling, graphemics, OCR/transcription study | Orthographic, case, punctuation and artifact variants remain separate types |
| Normalized form | `<w norm="...">`                                           | Comparing historical forms with modern Lower Sorbian     | Optional; may contain alternatives separated by vertical bars               |
| Lemma           | `<w lemma="...">`                                          | Lexical and morphological aggregation                    | Optional; may be ambiguous and is not a full morphological analysis         |

Surface forms preserve historical variation but inflate type counts through
orthographic variants. Normalized forms support comparison with modern Lower
Sorbian but erase part of that variation. Lemmas aggregate lexical candidates
but do not encode a complete morphological analysis.

## Corpus snapshot and biases

The live inventory currently contains 9,083 edition rows spanning 1574-2023:

- 6,346 rows are labelled `dsb`, 2,684 `deu`, and 53 use other labels;
- 4,276 rows (47%) are marked restricted;
- 106 rows have no year;
- 7,313 rows (81%) belong to four newspaper series: _Nowy Casnik_,
  _Bramborski Zassnik_, _Bramborski sserski Zassnik_, and _Bramborske Nowiny_;
- only 50 dated rows precede 1825, while every 25-year period from 1850 onward
  contains hundreds or thousands of rows.

Important corpus properties:

1. **The corpus is not balanced.** Raw counts mostly measure newspaper volume,
   publication frequency, document length and digitization coverage. Edition
   counts are not equivalent to independent speakers or texts.
2. **`lang` is an edition-level hint, not token-level language identification.**
   Newspaper issues contain Lower Sorbian and German together. A sampled 2017
   `dsb` issue has German `die` among its frequent surface forms, while a sampled
   2018 `deu` issue has frequent Lower Sorbian `jo`, `se`, `su`, `až`, and `we`.
   The 1882 issue used below is labelled `deu` although its opening is Lower
   Sorbian. Filtering only on `lang=dsb` loses relevant text and does not remove
   all German text.
3. **Language labels are not fully standardized.** Besides `dsb`, `deu` and
   `hsb`, the inventory contains labels such as `de`, `dez`, `slě` and isolated
   labels for other languages.
4. **Historical spelling is real data, not modern Lower Sorbian.** Forms such as
   `Pſchiżo`, `ße`, `ſtwortk`, and combining-mark spellings such as `ßeb́e`
   occur. Surface and normalized frequencies therefore describe different
   linguistic layers.
5. **The inventory year is the analytical date.** The numeric suffix after the
   dot in an edition URN, for example `.20260310110000`, is a version/import
   timestamp, not the publication year. Dates can still be missing or disagree
   with titles.

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

`lemma`, `norm`, `type`, and `subtype` are optional. In one sampled 1882 issue,
3,098 of 3,157 `<w>` elements had `lemma` and `norm`; the 59 unannotated elements
included German advertisement text such as `<w>Wendiſche</w>` and
`<w>Predigtbuch</w>`. Another sampled historical work had complete coverage.
Coverage therefore varies by document and often by language or text segment.

`|` separates alternatives rather than multiple occurrences. Ambiguity can be
substantial:

```xml
<w lemma="PŁAŚ|PŁAŚEŚ|PŁAŚIŚ" norm="płaśi">płaſchi</w>
<w lemma="WE|WĚŹEŚ|WÓ" norm="we|wě|wó">we</w>
```

One surface `<w>` can also map to a multiword analysis. Spaces inside an
attribute are data, not element boundaries:

```xml
<w lemma="NJEBYŚ LI" norm="njejo li">Ńejoli</w>
```

Historical elision can leave apostrophes in normalized forms, for example
`<w lemma="WÓN" norm="jog'">Jog'</w>` and alternatives such as
`norm="twojog'|twójog'"`. This differs from bag-of-words tokenization, where the
production `replacearr` removes the straight apostrophe. Normalized alternatives
can additionally differ only by spelling or case, for example
`Bóda|buda|Buda`. Missing, ambiguous, multiword, apostrophe-bearing, and
case-varying values are all present in the live corpus. `deletexml` and `nl` are
presence-only output flags.

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
