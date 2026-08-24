const { withDom, loadScript } = require('./helpers');

function loadSearch() {
  try {
    return loadScript('search.js');
  } catch (error) {
    if (error.code === 'MODULE_NOT_FOUND' && error.message.includes('/public/js/search.js')) {
      throw new Error('public/js/search.js must exist and expose the search helpers');
    }
    throw error;
  }
}

function loadSplitTerms() {
  const { splitTerms } = loadSearch();
  expect(typeof splitTerms).toBe('function');
  return splitTerms;
}

describe('readSearchOptions', () => {
  it('returns the search defaults', () => {
    const dom = withDom();
    try {
      const { readSearchOptions } = loadSearch();

      // These defaults must agree exactly with PHP search_options() from step A1.
      expect(readSearchOptions('')).toEqual({
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

  it('enables requested options without changing defaults', () => {
    const dom = withDom();
    try {
      const { readSearchOptions } = loadSearch();

      expect(readSearchOptions('?lemma=DRJEWO&regex=1&list=1')).toEqual({
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

  it('turns options off with zero values', () => {
    const dom = withDom();
    try {
      const { readSearchOptions } = loadSearch();

      expect(readSearchOptions('?ci=0&ambig=0&trim=0')).toEqual({
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

  it('supports exact while preferring explicit ambig', () => {
    const dom = withDom();
    try {
      const { readSearchOptions } = loadSearch();

      expect(readSearchOptions('?exact=1').ambig).toBe(false);
      expect(readSearchOptions('?exact=1&ambig=1').ambig).toBe(true);
    } finally {
      dom.restore();
    }
  });
});

describe('searchQueryString', () => {
  it('emits every provided flag in stable order', () => {
    const dom = withDom();
    try {
      const { searchQueryString } = loadSearch();

      expect(searchQueryString('lemma', 'DRJEWO', { ci: true, ambig: true, trim: true })).toBe(
        'lemma=DRJEWO&ci=1&ambig=1&trim=1',
      );
    } finally {
      dom.restore();
    }
  });

  it('emits false flags explicitly', () => {
    const dom = withDom();
    try {
      const { searchQueryString } = loadSearch();

      expect(
        searchQueryString('lemma', 'DRJEWO', {
          ci: false,
          regex: false,
          list: false,
          trim: false,
          ambig: false,
        }),
      ).toBe('lemma=DRJEWO&ci=0&regex=0&list=0&trim=0&ambig=0');
    } finally {
      dom.restore();
    }
  });

  it('escapes literal and regex terms without changing them', () => {
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

      expect(literalQuery).toBe('lemma=a%26b%3Dc&ci=1&regex=0&list=0&trim=1&ambig=1');
      expect(regexQuery).toBe('lemma=TE(J%7CN)&ci=1&regex=1&list=0&trim=1&ambig=1');
      expect(new URLSearchParams(literalQuery).get('lemma')).toBe('a&b=c');
      expect(new URLSearchParams(regexQuery).get('lemma')).toBe('TE(J|N)');
    } finally {
      dom.restore();
    }
  });
});

// PHP twin: tests/php/SearchFilterTest.php. Keep these splitTerms cases in sync.
describe('splitTerms', () => {
  it('preserves the whole string when list is off', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('/^drjewo,tej$/;alternatiwa', { list: false, trim: true })).toEqual([
        '/^drjewo,tej$/;alternatiwa',
      ]);
    } finally {
      dom.restore();
    }
  });

  it('splits semicolon and comma separators when list is on', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('drjewo;tej', { list: true, trim: true })).toEqual(['drjewo', 'tej']);
      expect(splitTerms('drjewo,tej', { list: true, trim: true })).toEqual(['drjewo', 'tej']);
    } finally {
      dom.restore();
    }
  });

  it('trims surrounding whitespace from each term', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('drjewo, tej', { list: true, trim: true })).toEqual(['drjewo', 'tej']);
    } finally {
      dom.restore();
    }
  });

  it('preserves internal spaces when trimming', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms(' NJEBYŚ LI ', { list: true, trim: true })).toEqual(['NJEBYŚ LI']);
    } finally {
      dom.restore();
    }
  });

  it('preserves surrounding whitespace when trim is off', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('drjewo, tej', { list: true, trim: false })).toEqual(['drjewo', ' tej']);
    } finally {
      dom.restore();
    }
  });

  it('drops empty terms', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('a;;b;', { list: true, trim: true })).toEqual(['a', 'b']);
      expect(splitTerms(' \t\n ', { list: true, trim: true })).toEqual([]);
    } finally {
      dom.restore();
    }
  });

  it('trims non-breaking spaces', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('\u00a0drjewo\u00a0', { list: true, trim: true })).toEqual(['drjewo']);
    } finally {
      dom.restore();
    }
  });
});
