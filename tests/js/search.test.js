const { withDom, loadScript, loadPage } = require('./helpers');

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

function loadBuildVisUrls() {
  const { buildVisUrls } = loadSearch();
  expect(typeof buildVisUrls).toBe('function');
  return buildVisUrls;
}

function loadPhpUrlFromLocation() {
  const { phpUrlFromLocation } = loadSearch();
  expect(typeof phpUrlFromLocation).toBe('function');
  return phpUrlFromLocation;
}

const BWLEMMA_SEARCH_HTML = `
  <input id="prefixsearchCheckBox" type="checkbox">
  <input id="searchinput" type="text">
  <input id="ciCheckBox" checked type="checkbox">
  <input id="regexCheckBox" type="checkbox">
  <input id="listCheckBox" type="checkbox">
  <input id="trimCheckBox" checked type="checkbox">
  <input id="ambigCheckBox" checked type="checkbox">
`;

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

describe('searchOptionsFromForm', () => {
  it('reads the current checkbox state', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { searchOptionsFromForm } = loadSearch();
      dom.document.getElementById('ciCheckBox').checked = false;
      dom.document.getElementById('regexCheckBox').checked = true;

      expect(searchOptionsFromForm(dom.document)).toEqual({
        ci: false,
        regex: true,
        list: false,
        trim: true,
        ambig: true,
      });
    } finally {
      dom.restore();
    }
  });

  it('falls back to the default for a control the page does not have', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { searchOptionsFromForm } = loadSearch();
      dom.document.getElementById('ambigCheckBox').remove();

      expect(searchOptionsFromForm(dom.document).ambig).toBe(true);
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

  it('round-trips every combination of search options', () => {
    const dom = withDom();
    try {
      const { readSearchOptions, searchQueryString } = loadSearch();
      const flags = ['ci', 'regex', 'list', 'trim', 'ambig'];

      for (let mask = 0; mask < 2 ** flags.length; mask += 1) {
        const options = Object.fromEntries(
          flags.map((flag, index) => [flag, Boolean(mask & (1 << index))]),
        );

        expect(readSearchOptions(searchQueryString('lemma', 'TE(J|N)', options))).toEqual(options);
      }
    } finally {
      dom.restore();
    }
  });
});

describe('restoreSearchFromLocation', () => {
  function expectRestoredSearch(url, assertState) {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML, url });
    try {
      const { restoreSearchFromLocation } = loadSearch();
      expect(typeof restoreSearchFromLocation).toBe('function');
      restoreSearchFromLocation(dom.document, dom.window.location.search);
      assertState(dom.document);
    } finally {
      dom.restore();
    }
  }

  it('restores a regex list search and disables alphabetical sorting', () => {
    expectRestoredSearch(
      'https://example.test/vis/bwlemma/?lemma=DRJEWO&regex=1&list=1',
      (document) => {
        expect(document.querySelector('#searchinput').value).toBe('DRJEWO');
        expect(document.querySelector('#regexCheckBox').checked).toBe(true);
        expect(document.querySelector('#listCheckBox').checked).toBe(true);
        expect(document.querySelector('#ciCheckBox').checked).toBe(true);
        expect(document.querySelector('#trimCheckBox').checked).toBe(true);
        expect(document.querySelector('#ambigCheckBox').checked).toBe(true);
        expect(document.querySelector('#prefixsearchCheckBox').disabled).toBe(true);
      },
    );
  });

  it('restores an encoded regex term verbatim', () => {
    const term = 'TE(J|N)';
    expectRestoredSearch(
      'https://example.test/vis/bwlemma/?lemma=' + encodeURIComponent(term) + '&regex=1',
      (document) => {
        expect(document.querySelector('#searchinput').value).toBe(term);
      },
    );
  });

  it('preserves a legacy comma term without enabling list mode', () => {
    expectRestoredSearch('https://example.test/vis/bwlemma/?lemma=A,TEKE', (document) => {
      expect(document.querySelector('#searchinput').value).toBe('A,TEKE');
      expect(document.querySelector('#listCheckBox').checked).toBe(false);
    });
  });

  it('translates a legacy exact search to unambiguous mode', () => {
    expectRestoredSearch('https://example.test/vis/bwlemma/?lemma=X&exact=1', (document) => {
      expect(document.querySelector('#searchinput').value).toBe('X');
      expect(document.querySelector('#ambigCheckBox').checked).toBe(false);
    });
  });

  it('leaves the empty form at its defaults when lemma is absent', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML, url: 'https://example.test/vis/bwlemma/' });
    try {
      let eventCount = 0;
      dom.document.body.addEventListener('input', () => (eventCount += 1));
      dom.document.body.addEventListener('change', () => (eventCount += 1));
      const { restoreSearchFromLocation } = loadSearch();

      expect(typeof restoreSearchFromLocation).toBe('function');
      restoreSearchFromLocation(dom.document, dom.window.location.search);

      expect(dom.document.querySelector('#searchinput').value).toBe('');
      expect(dom.document.querySelector('#ciCheckBox').checked).toBe(true);
      expect(dom.document.querySelector('#regexCheckBox').checked).toBe(false);
      expect(dom.document.querySelector('#listCheckBox').checked).toBe(false);
      expect(dom.document.querySelector('#trimCheckBox').checked).toBe(true);
      expect(dom.document.querySelector('#ambigCheckBox').checked).toBe(true);
      expect(dom.document.querySelector('#prefixsearchCheckBox').disabled).toBe(false);
      expect(eventCount).toBe(0);
    } finally {
      dom.restore();
    }
  });

  it('puts markup in the input value without injecting HTML', () => {
    const term = '<img src=x onerror=alert(1)>';
    expectRestoredSearch(
      'https://example.test/vis/bwlemma/?lemma=' + encodeURIComponent(term),
      (document) => {
        expect(document.querySelector('#searchinput').value).toBe(term);
        expect(document.querySelector('img')).toBeNull();
        expect(document.body.innerHTML).not.toContain('onerror');
      },
    );
  });
});

describe('buildVisUrls', () => {
  it('builds all lemma visualization URLs with defaults', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', 'DRJEWO', {}, 0)).toEqual({
        timeline:
          'timeline.html?data=lemmasumperyear.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort&focus=0',
        group:
          'lemmalist.html?data=lemmagroup.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=lemmatoken.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort',
      });
    } finally {
      dom.restore();
    }
  });

  it('uses lemma counts for focus 3', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', 'DRJEWO', {}, 3).timeline).toBe(
        'timeline.html?data=lemmacountperyear.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort&focus=3',
      );
    } finally {
      dom.restore();
    }
  });

  it('uses the summed-list timeline page when list is enabled', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', 'DRJEWO', { list: true }, 0)).toEqual({
        timeline:
          'timelinesumlist.html?data=lemmasumperyear.php&lemma=DRJEWO&ci=1&regex=0&list=1&trim=1&ambig=1&sort&focus=0',
        group:
          'lemmalist.html?data=lemmagroup.php&lemma=DRJEWO&ci=1&regex=0&list=1&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=lemmatoken.php&lemma=DRJEWO&ci=1&regex=0&list=1&trim=1&ambig=1&sort',
      });
    } finally {
      dom.restore();
    }
  });

  it('keeps the standard endpoints when regex is enabled', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', 'TE(J|N)', { regex: true }, 0)).toEqual({
        timeline:
          'timeline.html?data=lemmasumperyear.php&lemma=TE(J%7CN)&ci=1&regex=1&list=0&trim=1&ambig=1&sort&focus=0',
        group:
          'lemmalist.html?data=lemmagroup.php&lemma=TE(J%7CN)&ci=1&regex=1&list=0&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=lemmatoken.php&lemma=TE(J%7CN)&ci=1&regex=1&list=0&trim=1&ambig=1&sort',
      });
    } finally {
      dom.restore();
    }
  });

  it.each(['A&B', 'A=B', 'A#B', 'TE(J|N)'])('percent-encodes and round-trips %s', (term) => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      Object.values(buildVisUrls('lemma', term, {}, 0)).forEach((url) => {
        expect(url).toContain('lemma=' + encodeURIComponent(term));
        expect(new URL(url, 'https://example.test').searchParams.get('lemma')).toBe(term);
      });
    } finally {
      dom.restore();
    }
  });

  it.each(['', ' \t\n '])('returns null for an empty term', (term) => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', term, {}, 0)).toBeNull();
    } finally {
      dom.restore();
    }
  });
});

describe('phpUrlFromLocation', () => {
  it('keeps search flags and sort while dropping visualization-only parameters', () => {
    const dom = withDom();
    try {
      const phpUrlFromLocation = loadPhpUrlFromLocation();
      const search =
        '?data=lemmasumperyear.php&lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort&focus=0';

      expect(phpUrlFromLocation('data', 'lemma', search)).toBe(
        'lemmasumperyear.php?lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort',
      );
    } finally {
      dom.restore();
    }
  });

  it('drops jitter and scale parameters', () => {
    const dom = withDom();
    try {
      const phpUrlFromLocation = loadPhpUrlFromLocation();
      const search = '?data=lemmasumperyear.php&lemma=DRJEWO&jitter=2&scale=3&sort';

      expect(phpUrlFromLocation('data', 'lemma', search)).toBe(
        'lemmasumperyear.php?lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort',
      );
    } finally {
      dom.restore();
    }
  });

  it('translates legacy exact searches to an unambiguous search', () => {
    const dom = withDom();
    try {
      const phpUrlFromLocation = loadPhpUrlFromLocation();

      expect(
        phpUrlFromLocation('data', 'lemma', '?data=lemmasumperyear.php&lemma=DRJEWO&exact=1&sort'),
      ).toBe('lemmasumperyear.php?lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=0&sort');
    } finally {
      dom.restore();
    }
  });

  it('uses the A4 defaults when search flags are missing', () => {
    const dom = withDom();
    try {
      const phpUrlFromLocation = loadPhpUrlFromLocation();

      expect(
        phpUrlFromLocation('data', 'lemma', '?data=lemmasumperyear.php&lemma=DRJEWO&sort'),
      ).toBe('lemmasumperyear.php?lemma=DRJEWO&ci=1&regex=0&list=0&trim=1&ambig=1&sort');
    } finally {
      dom.restore();
    }
  });

  it.each(['../../evil.php', 'http://x/'])('rejects unsafe data filename %s', (data) => {
    const dom = withDom();
    try {
      const phpUrlFromLocation = loadPhpUrlFromLocation();
      const search = '?data=' + encodeURIComponent(data) + '&lemma=DRJEWO&sort';

      expect(phpUrlFromLocation('data', 'lemma', search)).toBeNull();
    } finally {
      dom.restore();
    }
  });
});

describe('bwlemma iframe pages', () => {
  const pages = [
    'timeline.html',
    'timelinesum.html',
    'timelinesumlist.html',
    'percenttimeline.html',
    'percenttimelinesumlist.html',
    'lemmalist.html',
    'tokenlist.html',
    'traviz.html',
    'doclist.html',
  ];

  it.each(pages)('%s loads js/search.js', (page) => {
    const document = loadPage('vis/bwlemma/' + page);
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );

    expect(sources).toContain('../../js/search.js');
  });

  it.each(pages)('%s forwards search flags to its PHP request', (page) => {
    const document = loadPage('vis/bwlemma/' + page);
    const inlineSource = [...document.querySelectorAll('script:not([src])')]
      .map((script) => script.textContent)
      .join('\n');

    expect(inlineSource).toMatch(
      /\bdataset\s*=\s*phpUrlFromLocation\(\s*['"]data['"]\s*,\s*['"]lemma['"]\s*,\s*(?:window\.)?location\.search\s*\)/,
    );
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

describe('searchControlState', () => {
  it('enables controls only for non-regex single-term searches', () => {
    const dom = withDom();
    try {
      const { searchControlState } = loadSearch();

      expect(typeof searchControlState).toBe('function');
      expect(searchControlState({ regex: false, list: false })).toEqual({
        autocomplete: true,
        alphabetSort: true,
      });
      expect(searchControlState({ regex: true, list: false })).toEqual({
        autocomplete: false,
        alphabetSort: false,
      });
      expect(searchControlState({ regex: false, list: true })).toEqual({
        autocomplete: false,
        alphabetSort: false,
      });
      expect(searchControlState({ regex: true, list: true })).toEqual({
        autocomplete: false,
        alphabetSort: false,
      });
      expect(
        searchControlState({
          regex: false,
          list: false,
          ci: false,
          trim: false,
          ambig: false,
        }),
      ).toEqual({ autocomplete: true, alphabetSort: true });
    } finally {
      dom.restore();
    }
  });

  it('disables and re-enables alphabet sorting and autocomplete', () => {
    const dom = withDom({
      html: '<input id="prefixsearchCheckBox" type="checkbox"><input id="searchinput">',
    });
    try {
      const { applySearchControlState } = loadSearch();
      const alphabetSort = dom.document.getElementById('prefixsearchCheckBox');
      const searchInput = dom.document.getElementById('searchinput');

      expect(typeof applySearchControlState).toBe('function');
      applySearchControlState(dom.document, { regex: true, list: false });
      expect(alphabetSort.disabled).toBe(true);
      expect(searchInput.disabled).toBe(true);

      applySearchControlState(dom.document, { regex: false, list: false });
      expect(alphabetSort.disabled).toBe(false);
      expect(searchInput.disabled).toBe(false);

      applySearchControlState(dom.document, { regex: false, list: true });
      expect(alphabetSort.disabled).toBe(true);
      expect(searchInput.disabled).toBe(true);
    } finally {
      dom.restore();
    }
  });
});
