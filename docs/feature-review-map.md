# Feature Review Map

Use this map to find the code and data behind each feature and to see which areas have been reviewed. This is a working record, not a guarantee that every path in a reviewed feature is correct.

## Review Status

- **Reviewed:** Wortform has been reviewed and has tests, although coverage is not exhaustive. Its dependencies may have a different status.
- **Not reviewed:** The feature has not been reviewed or tested as a whole. A route or syntax smoke check is not feature validation.
- **Shared:** Used by multiple features; review and test coverage varies by component. See the shared code section below.

## Menu To Feature

Visualization folders are under `public/vis/`, PHP files under `public/php/`, ETL scripts under `etl/`, and data paths under `public/data/`. The ETL data directory can be overridden with `DSB_DATADIR`; this does not automatically change PHP data paths. Data files are generated runtime outputs, not source files. The table lists the main feature-specific files and dependencies, not every shared helper or visualization subpage. A dash means no direct endpoint or producer of its own.

| Area | Menu link | Visualization folder(s) | PHP files | ETL script(s) | Data files | Review status |
| --- | --- | --- | --- | --- | --- | --- |
| Metadaten | Copyright | `metadatarestricted/` | `metadata.php`, `metadatarestricted.php`, `metadatarestrictedperyear.php` | `metadata.py` | `metadata.db` | Not reviewed |
| Metadaten | Autor | `metadataauthor/`, `metadatacoauthornetwork/` | `metadata.php`, `metadataauthor.php`, `metadataauthorperyear.php`, `coauthors.php` | `metadata.py`, `authors.py` | `metadata.db`, `authors.db` | Not reviewed |
| Metadaten | Dok.Hierarchie | `metadatadochierarchy/` | `metadataurnlist.php` | `metadata.py` | `metadata.db` | Not reviewed |
| Metadaten | Sprache | `metadatalang/` | `metadata.php`, `metadatalang.php`, `metadatalangperyear.php` | `metadata.py` | `metadata.db` | Not reviewed |
| Textkorpus | Dok.-Belege | `docreferences/` | `metadata.php`, `prefixlemmasearch.php`, `prefixnormsearch.php`, `urnbylemma.php`, `urnbynorm.php` | `metadata.py`, `lemmatisierowasch.py`, `normierowasch.py` | `metadata.db`, `lemmamapping.db`, `normmapping.db` | Not reviewed |
| Textkorpus | Typo-Erkennung | `typorecognition/` | `metadata.php`, `urnbyword.php` | `bagofwords.py`, `singleusewords.py`, `typorecognition.py` | `bagofwords/_all.txt`, `bagofwords/_singleusewords.txt`, `typorecognition/typowords*`, `typorecognition/typos*` | Not reviewed |
| Textkorpus | Statistiken | `stats/`, `statschar/`, `statslemma/`, `statsnorm/`, `statsword/` | `charcountdaterange.php`, `tokencountdaterange.php`, `typecountperlemma.php`, `typecountpernorm.php`, `wordbylength.php` | `stats.py`, `bagofwords.py` | `stats.txt`, `stats/*`, `bagofwords.db`, `bagofwordsperyear/*` | Not reviewed |
| Textkorpus | Abdeckung | `tokenrec/` | - | `bagofwords.py` | `bagofwords/_all.txt` | Not reviewed |
| Textkorpus | Wortgenese & Worttod | `bwtime/` | - | `bagofwords.py` | `bagofwords/_minmaxyearmin`, `bagofwords/_minmaxyearmax` | Not reviewed |
| Zeichen | Zeichen (no current submenu link) | `characters/` | `charcountdaterange.php`, `charcountperyear.php`, `urnbychar.php` | `characters.py` | `characters.db`, `characters/`, `charactersperyear/` | Not reviewed |
| Wortform | Timeline | `bwlemma/`, `bwnorm/`, `bwword/` | `prefixlemmasearch.php`, `prefixnormsearch.php`, `prefixsearch.php`, `lemmagroup.php`, `normgroup.php`, `lemmatoken*.php`, `normtoken*.php`, `lemmasumperyear.php`, `normsumperyear.php`, `tokencountperyear.php`, `urnbylemma.php`, `urnbynorm.php` | `bagofwords.py`, `lemmatisierowasch.py`, `normierowasch.py` | `bagofwords.db`, `lemmamapping.db`, `normmapping.db`, `metadata.db` | Reviewed |
| Wortform | Variation | `lemmavariation/`, `normvariation/` | `prefixlemmasearch.php`, `prefixnormsearch.php`, `lemmacountperyear.php`, `normcountperyear.php`, `tokencountperyear.php`, `token2lemma.php`, `token2norm.php` | `bagofwords.py`, `lemmatisierowasch.py`, `normierowasch.py` | `bagofwords.db`, `lemmamapping.db`, `normmapping.db` | Reviewed |
| Wortform | Evaluation | `lemmaeval/`, `normeval/` | `prefixlemmasearch.php`, `prefixnormsearch.php`, `lemmagroup.php`, `normgroup.php`, `lemmatoken.php`, `normtoken.php`, `lemmacountperyear.php`, `normcountperyear.php` | `lemmatisierowasch.py`, `lemmaeval.py`, `normierowasch.py`, `normeval.py` | `lemmamapping.db`, `normmapping.db`, `lemmamapping/`, `normmapping/` | Reviewed |
| Wortform | Steckbrief | `profile/` | `prefixlemmasearch.php`, `prefixnormsearch.php`, `prefixsearch.php`, `lemmaprofile.php`, `normprofile.php`, `wordprofile.php` | `bagofwords.py`, `lemmatisierowasch.py`, `normierowasch.py`, `ngram.py`, `collocation.py` | `bagofwords.db`, `lemmamapping.db`, `normmapping.db`, `collocation.db` | Reviewed; see dependencies below |
| Zusammenhang | Kollokation | `collocation/` | `collocation.php` | `ngram.py`, `collocation.py` | `ngram2.db`, `collocation.db` | Not reviewed |
| Zusammenhang | nGram | `ngram/` | `ngram.php`, `ngramexact.php`, `ngramperyear.php`, `ngramperyearexact.php`, `prefixngramsearch.php` | `ngram.py` | `ngram2.db`, `ngram3.db`, `ngram5.db`; matching `ngram*` directories | Not reviewed |
| SpoznajRec | Rozeznaś | `langdetect/` | `langDetectToken.php`, `langDetectnGram.php`, `ngram.php`, `ngramperyear.php`, `prefixngramsearch.php` | `ngram.py`, `spoznajrec.py` | `ngram3.db`, `langDetect3.db`, `langDetect3/` | Not reviewed |
| SpoznajRec | Gódaś Rec | `langrec/` | - | `ngram.py`, `spoznajrec.py` | `langDetect3/dsb_slim`, `langDetect3/deu_slim`, `langDetect3/mix1`, `langDetect3/mix2` | Not reviewed |
| SpoznajRec | Cuzy Rec | `langsep/` | - | `ngram.py`, `spoznajrec.py` | `langDetect3/deu` | Not reviewed |

## Shared Code And Dependencies

- `public/js/gui.js` builds the menu; `config.js`, `datahandler.js`, `def_language.js`, `my_language.js`, `autocomplete.js`, and `search.js` support multiple views. Menu entries for areas outside Wortform have not been reviewed as features.
- `etl/setup.py` schedules the pipeline. `settings.py`, `config_def.py`, `pythoncts.py`, `dsb_collation.py`, `mapping_etl.py`, `mappingeval.py`, and `docu.py` provide configuration, corpus access, collation, mapping, evaluation, or reporting used across jobs. `etl/config.py` is generated by setup. Coverage varies; see the untested jobs under known issues.
- Shared PHP includes `metadata.php`, `dsb_collation.php`, `searchfilter.php`, and the prefix search and document-reference endpoints. Several features also share the bag-of-words and lemma/norm mapping data.
- Wortform uses `metadata.db` for document information and `collocation.db` for word profiles; their production paths are not reviewed as features. Wortform also links to the unreviewed `collocation/` and `docreferences/` views. Conversely, Dok.-Belege uses Wortform search and document-reference endpoints.
- Tests are organized under `tests/js/`, `tests/php/`, and `tests/python/`. They include Wortform, search, mapping, bag-of-words, and pipeline regression coverage; the presence of a test does not imply full feature coverage.
- `etl/psedcytas.py` uses `etl/learn/dnw-audio-urls.txt`. SpoznajRec also uses language data under `etl/learn/`. `scripts/install-libs.sh` downloads frontend vendor libraries; vendor output is not tracked.
- Klay (`klayjs` and `cytoscape-klay`) is still required by `collocation/globalwordnetklay.html` and `metadatadochierarchy/treenetwork.html`; both views are reachable from their feature pages.
- Evaluation uses `lemmaeval/piechart.html` and `normeval/piechart.html` for mapping uniqueness, not token lengths. Their obsolete token-length click handlers were already broken in the original repository and have been removed; no additional PHP endpoint is needed.
- Dok.Hierarchie uses the shared `public/digilabstyles.css`. Its extra `mydigilabstyles.css` link was removed because that file is absent from both this fork and the reference repository.

## Files Removed From The Original Work

This repository is a fork of the original work linked in the README. The following files are absent because they were obsolete, unused, or not usable in the current fork; the reasons differ by group:

- Wortform regex endpoints: `lemmaregex2token.php`, `lemmaregexgroup.php`, `lemmaregexsearch.php`, `lemmatokenregex.php`, `normregex2token.php`, `normregexgroup.php`, `normregexsearch.php`, `regexsearch.php`. The current search filter replaces them.
- PHP endpoints with no known callers: `authors.php`, `authorcount.php`, `authorcountperyear.php`, `collocationperyear.php`, `lemmabylength.php`, `lemmabytype.php`, `lemmacountpertoken.php`, `lemmadaterange.php`, `lemmatypes.php`, `normbylength.php`, `tokenfrequencybylength.php`. The original evaluation charts referenced `tokenbylength.php`, which is absent even from the reference repository; their obsolete handlers have been removed rather than restoring an unrelated endpoint.
- ETL scripts: `_charmix.py` has no consumer for its output; `_zelenjerec.py` was disabled in the original setup; `_mjenjoweda.py` required the missing `learn/ortsliste.txt` and did not run.
- Obsolete view files: `lemmastats.html`, `lemmatree.html`, `normtree.html`, and `*_klay.html` variants. `statsword/tokeninfo.html` was also removed because no application page referenced it. The actively used `collocation/globalwordnetklay.html` and `metadatadochierarchy/treenetwork.html` remain.
- Old tooling and unused data: `versionize.py`, `update.bat`, `version.txt`, `deu_intermediateresults.txt`, and `deu_mixed-typical_2011_1M-wordsorig.txt`. Historical reports in the original `etl/doc/` are not runtime inputs and were not copied as a separate legacy documentation tree.

## Known Issues

- Several unreviewed PHP endpoints build SQL from raw `$_GET` values, creating SQL injection risk. `langDetect*.php` also builds its database filename from the `n` query parameter.
- `metadata.py`, `authors.py`, `characters.py`, `singleusewords.py`, `ngram.py`, `collocation.py`, `spoznajrec.py`, `stats.py`, and `typorecognition.py` have no dedicated tests.
