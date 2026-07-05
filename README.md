# dsb-text-mining

**dsb-text-mining** (**Niedersorbisches Text Mining**) is a browser-based
digilab for exploring Lower Sorbian corpus text data from a Text Service Infrastructure
CTS/Text API endpoint. This repo contains the data-processing scripts written in Python,
PHP query endpoints, and static visualization pages.

## Pipeline Overview

The project is a three-tier system: a Python ETL pipeline produces local
datasets, PHP endpoints expose them over HTTP, and a static frontend renders
visualizations in the browser.

```
CTS Text API  →  Python ETL (etl/*.py)  →  public/data/ (TSV + SQLite)  →  PHP (public/php/*.php)  →  Frontend (public/index.html, public/vis/, public/js/, public/lib/)
   remote          build-time                generated                read-time              run-time
```

1. **Extract.** `etl/setup.py` writes `etl/config.py` from `etl/config_def.py`
   with the chosen CTS namespace and document count, then runs selected ETL
   scripts in sequence. `etl/pythoncts.py` resolves the namespace through
   `https://urncts.eu` and fetches text and metadata from the CTS endpoint.
2. **Transform.** Each ETL script collects its slice of the corpus
   (authors, characters, lemmas, n-grams, collocations, etc.), parses it, and
   writes intermediate tab-separated files into `public/data/<topic>/`.
3. **Load.** The same scripts then create per-topic SQLite databases in
   `public/data/` (for example `public/data/authors.db`,
   `public/data/lemmamapping.db`, `public/data/ngram3.db`) and add indexes for
   fast lookups.
4. **Serve.** The endpoints in `public/php/` open those SQLite files via PDO and
   return plain-text TSV responses driven by query parameters.
5. **Render.** `public/index.html` and the modules in `public/vis/` use shared
   helpers from `public/js/` (notably `datahandler.js`) to fetch PHP responses
   or raw `.txt` files and render Cytoscape, Plotly, and Traviz visualizations
   from `public/lib/`.

The pipeline is build-once / serve-many: the Python stage is run on the server
to (re)generate `public/data/`, and the PHP and frontend stages then operate purely
against those generated artifacts.

## Installation

The project has two independent stages: a one-time **build** that generates
`data/`, and a **serve** stage that exposes the digilab over HTTP. The serve
stage can be run either with the PHP built-in server (for local development) or
behind a real web server (for deployment).

### Prerequisites

- Python 3
- PHP 8.x with PDO SQLite (e.g. `sudo apt install -y php8.3-sqlite3`)

### 1. Build the data (required for both modes)

Clone the repository and run the setup script with the CTS namespace you want
to build. The optional second argument limits the number of documents
processed, which is useful for a first test run.

```bash
git clone https://github.com/pciazynski/dsb-text-mining.git
cd dsb-text-mining
python3 etl/setup.py dsb
# or, for a smaller test build:
python3 etl/setup.py dsb 50
```

The default `dsb` namespace is resolved through `https://urncts.eu`. If
`urnlist.txt` exists, the scripts use it as the document list instead of asking
the endpoint for the full inventory.

The generated `public/data/` directory must remain alongside the PHP and frontend
files for the interface to work.

### 2a. Run locally (development)

From the project root, start the PHP built-in server using the bundled router
and open the digilab in the browser.

```bash
php -S 127.0.0.1:8000 -t public public/router.php
```

Then open `http://127.0.0.1:8000/`. `public/router.php` is only needed here — it
handles the directory-redirect behavior that the built-in server lacks.

### 2b. Deploy (production)

Place the project directory inside the document root of a PHP-capable web
server (Apache, nginx + PHP-FPM, etc.) and serve it as static content with PHP
handling for `.php` files. `router.php` is not used in this mode; a real web
server handles directory indexes and routing on its own.

## License And Attribution

This project is licensed under the Creative Commons Attribution-ShareAlike 4.0
International license (CC BY-SA 4.0).

- License text: https://creativecommons.org/licenses/by-sa/4.0/
- Local license file: `LICENSE.txt`

This repository is a modified fork of the following original work.

### Original Work

- Title: Niedersorbisches Text Mining
- Author: Tiepmar, J.
- Institution: Sorbisches Institut e.V.
- Year: 2026
- DOI: https://doi.org/10.5281/zenodo.20506485
- Source: https://bitbucket.org/dhdigilab/dsb-text-mining
- License: Creative Commons Attribution-ShareAlike 4.0 International
  (CC BY-SA 4.0)
- License URL: https://creativecommons.org/licenses/by-sa/4.0/

### Fork Maintainer

- Name: Piotr Ciążyński / Pětš Śěžyński
- Fork URL: https://github.com/pciazynski/dsb-text-mining
- Modified since: 2026-04-28 (but sometimes synced from the upstream)

### Modification Log

Keep this section updated for public releases or major changes.

- 2026-04-28: Pětš Śěžyński added explicit CC BY-SA attribution and
  ShareAlike compliance documentation for fork publication.

### Redistribution Reminder

Redistributions of this fork should preserve attribution to the original work,
indicate modifications, and remain under CC BY-SA 4.0.

If you publish a fork of this project, keep the CC BY-SA 4.0 license,
preserve attribution to the original work, and clearly indicate that your fork
contains modifications.

## Citation

Tiepmar, J. Niedersorbisches Text Mining. Sorbisches Institut e.V., 2026.
https://doi.org/10.5281/zenodo.20506485

## References

### Sorbian Institute

Institute for the Study of the Language, History and Culture of the Lusatian Sorbs/Wends and Comparative Minority Research.

https://www.serbski-institut.de/en/

### Lower Sorbian Langueage Resources

https://dolnoserbski.de/

### Text API

Tiepmar, J. 2025. Canonical Text Service Infrastructure.
https://urncts.eu, requested on 06 March 2026.

### Traviz

S. Jaenicke, A. Gssner, M. Buechler and G. Scheuermann (2014).
Visualizations for Text Re-use. In Proceedings of the 5th International
Conference on Information Visualization Theory and Applications, IVAPP 2014,
pages 59-70.

### Plotly

Plotly Technologies Inc. Collaborative data science. Montreal, QC, 2015.
https://plot.ly.

### Cytoscape

Shannon, P. et al., 2003. Cytoscape: a software environment for integrated
models of biomolecular interaction networks. Genome Research, 13(11),
pp. 2498-2504.

### logDice

Rychly, P., 2008. A Lexicographer-Friendly Association Score.

### Language Separation

Tiepmar, J. 2024. n-Gram based Language Separation for Minority Languages.
MiLES conference. Turin.
