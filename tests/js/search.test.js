const test = require('node:test');
const assert = require('node:assert/strict');

const { withDom, loadScript } = require('./helpers');

function loadSearch() {
  try {
    return loadScript('search.js');
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND' && error.message.includes('/public/js/search.js')) {
      assert.fail('public/js/search.js must exist and expose the search helpers');
    }
    throw error;
  }
}

function loadSplitTerms() {
  const { splitTerms } = loadSearch();
  assert.equal(typeof splitTerms, 'function', 'public/js/search.js must export splitTerms');
  return splitTerms;
}

test('readSearchOptions returns the search defaults', () => {
  const dom = withDom();
  try {
    const { readSearchOptions } = loadSearch();

    // These defaults must agree exactly with PHP search_options() from step A1.
    assert.deepEqual(readSearchOptions(''), {
      ci: true,
      regex: false,
      list: false,
      trim: true,
      ambig: true,
    });
  } finally {
    dom.restore();
  }
});

test('readSearchOptions enables requested options without changing defaults', () => {
  const dom = withDom();
  try {
    const { readSearchOptions } = loadSearch();

    assert.deepEqual(readSearchOptions('?lemma=DRJEWO&regex=1&list=1'), {
      ci: true,
      regex: true,
      list: true,
      trim: true,
      ambig: true,
    });
  } finally {
    dom.restore();
  }
});

test('readSearchOptions turns options off with zero values', () => {
  const dom = withDom();
  try {
    const { readSearchOptions } = loadSearch();

    assert.deepEqual(readSearchOptions('?ci=0&ambig=0&trim=0'), {
      ci: false,
      regex: false,
      list: false,
      trim: false,
      ambig: false,
    });
  } finally {
    dom.restore();
  }
});

test('readSearchOptions supports exact while preferring explicit ambig', () => {
  const dom = withDom();
  try {
    const { readSearchOptions } = loadSearch();

    assert.equal(readSearchOptions('?exact=1').ambig, false);
    assert.equal(readSearchOptions('?exact=1&ambig=1').ambig, true);
  } finally {
    dom.restore();
  }
});

test('searchQueryString emits every provided flag in stable order', () => {
  const dom = withDom();
  try {
    const { searchQueryString } = loadSearch();

    assert.equal(
      searchQueryString('lemma', 'DRJEWO', { ci: true, ambig: true, trim: true }),
      'lemma=DRJEWO&ci=1&ambig=1&trim=1',
    );
  } finally {
    dom.restore();
  }
});

test('searchQueryString emits false flags explicitly', () => {
  const dom = withDom();
  try {
    const { searchQueryString } = loadSearch();

    assert.equal(
      searchQueryString('lemma', 'DRJEWO', {
        ci: false,
        regex: false,
        list: false,
        trim: false,
        ambig: false,
      }),
      'lemma=DRJEWO&ci=0&regex=0&list=0&trim=0&ambig=0',
    );
  } finally {
    dom.restore();
  }
});

test('searchQueryString escapes literal and regex terms without changing them', () => {
  const dom = withDom();
  try {
    const { searchQueryString } = loadSearch();
    const literalQuery = searchQueryString('lemma', 'a&b=c', {
      ci: true,
      regex: false,
      list: false,
      trim: true,
      ambig: true,
    });
    const regexQuery = searchQueryString('lemma', 'TE(J|N)', {
      ci: true,
      regex: true,
      list: false,
      trim: true,
      ambig: true,
    });

    assert.equal(literalQuery, 'lemma=a%26b%3Dc&ci=1&regex=0&list=0&trim=1&ambig=1');
    assert.equal(regexQuery, 'lemma=TE(J%7CN)&ci=1&regex=1&list=0&trim=1&ambig=1');
    assert.equal(new URLSearchParams(literalQuery).get('lemma'), 'a&b=c');
    assert.equal(new URLSearchParams(regexQuery).get('lemma'), 'TE(J|N)');
  } finally {
    dom.restore();
  }
});

// PHP twin: tests/php/SearchFilterTest.php. Keep these splitTerms cases in sync.
test('splitTerms preserves the whole string when list is off', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms('/^drjewo,tej$/;alternatiwa', { list: false, trim: true }), [
      '/^drjewo,tej$/;alternatiwa',
    ]);
  } finally {
    dom.restore();
  }
});

test('splitTerms splits semicolon and comma separators when list is on', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms('drjewo;tej', { list: true, trim: true }), ['drjewo', 'tej']);
    assert.deepEqual(splitTerms('drjewo,tej', { list: true, trim: true }), ['drjewo', 'tej']);
  } finally {
    dom.restore();
  }
});

test('splitTerms trims surrounding whitespace from each term', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms('drjewo, tej', { list: true, trim: true }), ['drjewo', 'tej']);
  } finally {
    dom.restore();
  }
});

test('splitTerms preserves internal spaces when trimming', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms(' NJEBYŚ LI ', { list: true, trim: true }), ['NJEBYŚ LI']);
  } finally {
    dom.restore();
  }
});

test('splitTerms preserves surrounding whitespace when trim is off', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms('drjewo, tej', { list: true, trim: false }), ['drjewo', ' tej']);
  } finally {
    dom.restore();
  }
});

test('splitTerms drops empty terms', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms('a;;b;', { list: true, trim: true }), ['a', 'b']);
    assert.deepEqual(splitTerms(' \t\n ', { list: true, trim: true }), []);
  } finally {
    dom.restore();
  }
});

test('splitTerms trims non-breaking spaces', () => {
  const dom = withDom();
  try {
    const splitTerms = loadSplitTerms();

    assert.deepEqual(splitTerms('\u00a0drjewo\u00a0', { list: true, trim: true }), ['drjewo']);
  } finally {
    dom.restore();
  }
});
