# Lower Sorbian corpus data exposed by services at `tsi.daty.info`

This document describes the Lower Sorbian corpus exposed by remote TSI services used by this project as observed on 2026-08-01. The corpus data might change in the future.

## Lower Sorbian corpus / corpora background information
 - Lower Sorbian corpus is maintained by Sorbian Institute and availlable for users on https://dolnoserbski.de/korpus/
 - That corpus has 4 main subcorpuses as described here: https://dolnoserbski.de/korpus/zredla/
 - This project here (DTS - dsb-text-mining) does not use dolnoserbski.de. It can access raw corpus data and some statistics via TSI/CTS remote service, which is explained in `docs/upstream-tsi-cts-service.md`
 - Explanation and specification of the raw corpus data can be found here: https://dolnoserbski.de/korpus/format/
 - This file provide some hints and info about the data in this corpus, it should help, but it is not extensive.

## Linguistic layers

The words in corpus data has 3 representations:

| Layer           | Source                                                     | Best suited to                                           | Important limitation                                                        |
| --------------- | ---------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------------------------------- |
| Surface form    | Text inside `<w>` | Historical spelling, graphemics, OCR/transcription study, improving the corpus itself, finding rare words | Might be written in very old spellings, might have typos or other problems, are often inflected forms |
| Normalized form | `<w norm="...">`                                           | Helps searching and reading in modern Lower Sorbian spelling | Optional in corpus data; may contain alternatives separated by vertical bars               |
| Lemma           | `<w lemma="...">`                                          | Lexical and morphological aggregation, to analyse words without paying attention to spelling or declinated/conjugated forms                    | Optional; may be ambiguous (separated by vertical bars) and is not a full morphological analysis       |

Surface forms preserve historical variation but inflate type counts through
orthographic variants. Normalized forms support comparison with modern Lower
Sorbian but erase part of that variation. Lemmas aggregate lexical candidates
but do not encode a complete morphological analysis. In ideal world those representations should be equivalent, but sometimes some equivalents are missing. E.g. for some words the norm and lemma form is completely missing.


## Corpus snapshot and biases

The live inventory currently contains 9,083 edition rows spanning 1574-2023:

- 6,346 rows are labelled `dsb`, 2,684 `deu`, and 53 use other labels;
- 4,276 rows (47%) are marked restricted;
- 106 rows have no year;
- 7,313 rows (81%) belong to four newspaper series: _Nowy Casnik_,
  _Bramborski Zassnik_, _Bramborski sserski Zassnik_, and _Bramborske Nowiny_;
- only 50 dated rows precede 1825, while every 25-year period from 1850 onward
  contains hundreds or thousands of rows.
- those numbers can be very different if other corpus, improved corpus or subcorpus is being fed and used by TSI remote service

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
   layers. E.g. wortforms "Pſchiżo" and "pśiźo" can both have norm annotation as "pśiźo", and lemma as "PŚIŚ". Many other wortfroms like e.g. "Pſchidu" or "pśiźoš" will be annonated with lemma "PŚIŚ". But for some words this annotations might be missing.
5. **The inventory year is the analytical date.** The numeric suffix after the
   dot in an edition URN, for example `.20260310110000`, is a version/import
   timestamp, not the publication year. Dates can still be missing or disagree
   with titles.


### Corpus data problems to pay attention to

TEI-like fragments, can look like this:

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
