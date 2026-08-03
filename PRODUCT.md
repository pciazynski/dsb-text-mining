# Product

## Purpose

dsb-text-mining (DTM) is an experimental product developed for and by Serbski Institut (Sorbian Institute) in order to provide linguists the tools to retrieve useful aggregated data (e.g. statistics, text minings, etc) from Lower Sorbian corpus (both historical and modern corpus). Specifically to analyse how the language evolves, how it changes, how we can make better dictionaries, how we can improve corpus itself and how we can help new learners to discover and learn more authentic Lower Sorbian.

DTM is one of three pillars of a planned "historical vocabulary information system" (the other two: historical dictionaries, stem-based lexicon).

## Users

- Primary: linguists, researchers, dictionary writers, workers of Sorbian Institute
- Secondary: anyone interested in understanding Lower Sorbian deeper or learning it better

## Core Workflows

1. A researcher searches for a specific word (providing a standard lemma form) and wants to see how this word was used over the years.
2. A Sorbian Institute worker search for typos and ambiguities in a corpus in order to improve it.
3. Lower Sorbian hobbyist or student wants to find which words are the most frequent and they want to extract a useful list to learn Lower Sorbian efficiently.
4. Fluent Lower Sorbian speaker translates a text into Lower Sorbian and wants to find more authentic words based on real historical data, rather than directly from dictionary.
5. An IT guy from Sorbian Institute wants to extract and implement one small feature into another webapp, e.g. "Steckbrief" card into digital Lower Sorbian dictionary (like dolnoserbski.de) or nicely looking visualisation of how the usage of some word evovlved over the time into the dictionary.
6. A researcher wants to see whether the form Drjowk or Drjewk is more frequent and in which years or which kind of texts.
7. A researcher is analysing how the spelling has changed over time.
8. A researcher is analysing how one word replaced another over time, this time without paying attention to spelling or grammatical forms.

## Product Principles

- Statistics and data provided by this system needs to be verifiable and reproducible. They need to be scientific-paper ready.
- Frontend is rather an experimental sandbox - it does not need to be pretty, those functionalities will be extracted and integrated into other websites later in the further future.
- If frontend provides some visualisation it should be easy to understand, easy to analyse and useful for linguists, not just fancy looking. Sometimes table or list can be better than visualisation.
- The processing pipeline (setup.py) must be well tested and must produce reproducible, traceble data artifacts. Output data need to be trustful.
- Optimized for working with often very ambiguious, historical and rather small Lower Sorbian corpus, with many possible spellings, possible lemmatization problems and other problems related to small endangered languages, where historical data is often more valuable than modern day data.

## Behavioral Invariants

- Providing the specific corpus data it should analyse everything correctly. The user needs to be sure what is the outcome and why.
- It can never happen that user takes some visualisation from this system (e.g.in which years the word "wordowaś" was used and how many times) into a scientific paper, and later he discovers that this is completely wrong because of a stupid processing error.
- It must handle UTF-8 characters correctly, works with all possible spellings of Lower Sorbian. It should correctly consume TSI remote endpoints (but do not overly trusting it - it needs to be prepared for possible problems of remote TSI/CTS endpoint). 

## Non-Goals

- This product does not provide features for searching and exploring corpora texts directly, we have another product for that. It can provide links to those services though.
- Even if some visualisation is technically possible it does not automatically mean that it's useful. It should not be overly complicated.
- It does not need to be optimized for huge large language corporas or for huge many million users traffic. But it should still work fast enough for Lower Sorbian corpus and up to 100 users at the same time.

## Domain Language

- **Lemma:** The most base, standard, dictionary-like form of the Lower Sorbian word in the modern spelling. This is the form which is not conjugated or declinated. Might be missing in the corpus data or might be amiguious because of the diffculties of lemmatizing Lower Sorbian words
- **Norm form:** A word normalized into the modern lower sorbian spelling, but without lemmatization - it might be a derived form, conjugated or declinated.
- **Wort form:** An exact occurence of the word in the corpus, might be in old spelling and might be not a base form.
- **DTM:** - dolnoserbski-text-mining (this project), previously called `dsbwortschatz`
- **CTS:** - Canonical Text Services which functions as a fine-grained "coordinate system" for text fragments of the Lower Sorbian text corpus and thus serves as the basis for analyses over the corpus data. CTS it's an upstream service whichc provides data to this product (DTM)
- **TSI:** - Text Service Infrastructure - a bit fuzzy term which sometimes means the whole pipeline (CTS + DTM), sometimes it means just CTS (for example CTS is served from tsi.daty.info)

## Current Constraints

- Lower Sorbian corpus has many mistakes, because of typos in transcription, challenges of lemmatization and so on. We need to account for that. Newer, slowly corrected versions of corpora will come in the future.
- Many automatisations known from large langauges or NLP or from AI tools cannot be easily applied to Lower Sorbian, because Lower Sorbian is a very small language with highly complex grammar, many dialects and no obvious big standard etc.
- The team working on this project is very small, the users group is also rather tiny. That requires a good prioritization.
- processing the whole data by the whole pipeline can take up to ~35 h for the full corpus (~1.5 days). This is why dynamic/interactive document subsets are considered infeasible; a mostly fixed corpus definition is assumed. Although stakeholders (researchers from SI) would love to have dynamic/interactive corpora subsets.

## Open Product Questions

- What components/statistics/visualisations of this system are genuinely useful? Which can be removed entirely?
- How this project will evolve, will the frontend part stay or will it be soon extracted and moved to other web apps? Maybe here we should focus rather on just processing the data? That's still not decided.
