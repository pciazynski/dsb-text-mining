# Product

## Purpose

dsb-text-mining is am experimental product developed for and by Serbski Institut (Sorbian Institute) to provide linguists tools to retrieve usefull aggregated data (statistics, text minings etc) from Lower Sorbian corpus (both historical and modern corpus). Specifically to analyse how the language evolves, how it changes, how we can make better dictionaries, how we can improve corpus itself and how we can help new learners to discover and learn more authentic Lower Sorbian.

## Users

- Primary: linguists, dictionary writers, workers of Sorbian Institute
- Secondary: anyone interested in understanding Lower Sorbian deeper or learning it better

## Core Workflows

1. A researcher searches for a specific word (providing a standard lemma form) and wants to see how this word was used over the time.
2. A Sorbian Institute worker search for typos and ambiguities in the corpus they provided before.
3. Lower Sorbian hobbyist or student wants to find which words are most frequent and wants to extract a usefull list to learn Lower Sorbian effectively.
4. Fluent Lower Sorbian speaker translates a text into Lower Sorbian and wants to find more authentic words based on real historical data, rather than directly from dictionary.
5. An IT guy from Sorbian Institute wants to extract and implement one small feature into another webapp, e.g. "Steckbrief" info into digital Lower Sorbian dictionary or nicely looking visualisation of how the usage of some word evovlved over the time into the dictionary.
6. A researcher wants to see whether Drjowk or Drjewk form is more frequent and when.
7. A researcher is analysing how the spelling changed over time.
8. A researcher is anyalysing how one word replaced another over time, without paying attention to spelling or grammatical forms.

## Product Principles

- Statistics and data provided by this system needs to be verifiable and reproducible. They need to be scientific-paper ready.
- Frontend is mostly experimental sandbox - it does not need to be beautiful, those functionalities will be extracted and integrated into other websites in the further future.
- If frontend provides some visualisation it should be easy to understand, easy to analyse and useful for linguists, not just fancy looking.
- Processing pipeline must be well tested and must produce reproducible, traceble data artifacts.
- Optimized for working with often ambiguious, historical, rather small Lower Sorbian corpus, with many possible spellings, possible problems with lemmatization and other problems of very small endangered languages, where historical data is often more valuable than modern day data.

## Behavioral Invariants

- Providing the specific corpus data it should analyse everything correctly. The user needs to be sure what is the outcome and why.
- It can never happen that user takes some visualisation from this system like for example in which years the word "wordowaś" was used and how many times into scientific paper, and later we discover that this is completely wrong because of a stupid processing error.
- It must handle UTF-8 characters correctly, works with all possible spelling of Lower Sorbian, it should correctly consume TSI remote endpoint (but do not overly trusting it). 

## Non-Goals

- This product does not provide searching and exploring corpora texts directly, we have another product for that.
- If some visualisation is technically possible it does not automatically mean that it's useful. It should not be overly complicated.
- It does not to be optimized for huge large language corporas or for huge million users traffic. But it should still work fast enough for Lower Sorbian corpus and up to 100 users at the same time.

## Domain Language

- **Lemma:** The most base, standard, dictionary-like form of the Lower Sorbian word in the modern spelling. So the form which is not conjugated or declinated. Might be missing in the corpus data or might be amiguious because of the diffculties of lemmatizing lower sorbian words
- **Norm version:** Some word normalized into the modern lower sorbian spelling, but might be derived form or conjugated ot declinated.

## Current Constraints

- Lower Sorbian corpus has many mistakes, especially with OCR, lemmatization and so on. We need to account for that. There will be newer, slowly corrected versions of corpora.
- Many automatisations known from large langauges or NLP or from AI tools cannot be easily applied to Lower Sorbian, because Lower Sorbian is a very small language with highly complex grammar, many dialects, no big standards etc.
- The team working on this project is very small, the users are also not many. That requires good prioritization.

## Open Product Questions

- What components/statistics/visualisations of this system are genuinely useful and which can be removed entirely?
- How this project will evolve, will the frontend stay or will it be soon extracted and moved to other web apps, here focusing rather on processing the data?
