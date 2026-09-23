const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const { PUBLIC_DIR, withDom, loadScript, loadPage } = require('./helpers');

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

function loadListPlotUrlsFromLocation() {
  const { listPlotUrlsFromLocation } = loadSearch();
  expect(typeof listPlotUrlsFromLocation).toBe('function');
  return listPlotUrlsFromLocation;
}

function loadListPlotTraces() {
  const { listPlotTraces } = loadSearch();
  expect(typeof listPlotTraces).toBe('function');
  return listPlotTraces;
}

function runBwlemmaPlotPage(page, search, phpResponses, truncated = false) {
  const html = fs.readFileSync(path.join(PUBLIC_DIR, 'vis', 'bwlemma', page), 'utf8');
  const dom = new JSDOM(html, {
    runScripts: 'outside-only',
    url: 'https://example.test/vis/bwlemma/' + page + search,
  });
  const externalScripts = [...dom.window.document.querySelectorAll('script[src]')].map((script) =>
    script.getAttribute('src'),
  );
  const inlineScripts = [...dom.window.document.querySelectorAll('script:not([src])')].map(
    (script) => script.textContent,
  );
  const plotCalls = [];
  const treeCalls = [];

  dom.window.Plotly = {
    Icons: { camera: {} },
    downloadImage() {},
    newPlot(_target, data, layout, configuration) {
      plotCalls.push({ data, layout, configuration });
      return dom.window.document.getElementById('myDiv');
    },
  };
  dom.window.TRAViz = class {
    align() {}
    visualize() {
      treeCalls.push(true);
    }
  };

  dom.window.eval(fs.readFileSync(path.join(PUBLIC_DIR, 'js', 'datahandler.js'), 'utf8'));

  externalScripts
    .filter((source) => source.startsWith('../../js/') && source !== '../../js/datahandler.js')
    .forEach((source) => {
      const scriptPath = path.join(PUBLIC_DIR, 'js', path.basename(source));
      dom.window.eval(fs.readFileSync(scriptPath, 'utf8'));
    });

  dom.window.readPHP = (url) => {
    if (truncated) {
      dom.window.rawFile = { getResponseHeader: () => '1' };
      return '|DRJEWO|\t1880\t3\n';
    }
    expect(Object.prototype.hasOwnProperty.call(phpResponses, url)).toBe(true);
    return phpResponses[url];
  };

  inlineScripts.forEach((source) => dom.window.eval(source));

  return {
    close: () => dom.window.close(),
    document: dom.window.document,
    plotCalls,
    treeCalls,
  };
}

const BWLEMMA_SEARCH_HTML = `
  <input id="prefixsearchCheckBox" type="checkbox">
  <input id="searchinput" type="text">
  <input id="csCheckBox" type="checkbox">
  <input id="regexCheckBox" type="checkbox">
  <input id="listCheckBox" type="checkbox">
  <input id="trimCheckBox" checked type="checkbox">
  <input id="ambigCheckBox" checked type="checkbox">
  <span id="searchexample"></span>
`;

describe('showTruncationNotice', () => {
  it('prepends one text-only notice and does not duplicate it', () => {
    const dom = withDom({ html: '<body><div id="chart"></div></body>' });
    const previousMessage = globalThis.lang_error_resultset_too_large;
    globalThis.lang_error_resultset_too_large = '<strong>translated notice</strong>';
    try {
      const { showTruncationNotice } = loadSearch();
      expect(typeof showTruncationNotice).toBe('function');
      const xhr = { getResponseHeader: () => '1' };

      expect(showTruncationNotice(dom.document, xhr)).toBe(true);
      expect(showTruncationNotice(dom.document, xhr)).toBe(true);
      expect(dom.document.querySelectorAll('body > *')).toHaveLength(2);
      expect(dom.document.body.firstElementChild.textContent).toBe(
        globalThis.lang_error_resultset_too_large,
      );
      expect(dom.document.body.firstElementChild.querySelector('strong')).toBeNull();
      expect(dom.document.body.lastElementChild.id).toBe('chart');
    } finally {
      if (previousMessage === undefined) {
        delete globalThis.lang_error_resultset_too_large;
      } else {
        globalThis.lang_error_resultset_too_large = previousMessage;
      }
      dom.restore();
    }
  });

  it.each([null, '0'])('adds nothing when the header is %s', (header) => {
    const dom = withDom();
    try {
      const { showTruncationNotice } = loadSearch();
      expect(typeof showTruncationNotice).toBe('function');

      expect(showTruncationNotice(dom.document, { getResponseHeader: () => header })).toBe(false);
      expect(dom.document.querySelectorAll('body > *')).toHaveLength(0);
    } finally {
      dom.restore();
    }
  });
});

describe('readPHPChecked', () => {
  it('returns the body when the response was not truncated', () => {
    const dom = withDom();
    const previousReadPHP = globalThis.readPHP;
    const previousRawFile = globalThis.rawFile;
    try {
      const { readPHPChecked } = loadSearch();
      expect(typeof readPHPChecked).toBe('function');
      globalThis.readPHP = (url) => {
        expect(url).toBe('lemmasumperyear.php?lemma=DRJEWO');
        globalThis.rawFile = { getResponseHeader: () => null };
        return '|DRJEWO|\t1880\t3\n';
      };

      expect(readPHPChecked(dom.document, 'lemmasumperyear.php?lemma=DRJEWO')).toBe(
        '|DRJEWO|\t1880\t3\n',
      );
      expect(dom.document.querySelectorAll('body > *')).toHaveLength(0);
    } finally {
      if (previousReadPHP === undefined) delete globalThis.readPHP;
      else globalThis.readPHP = previousReadPHP;
      if (previousRawFile === undefined) delete globalThis.rawFile;
      else globalThis.rawFile = previousRawFile;
      dom.restore();
    }
  });

  it('returns null and shows a notice when the response was truncated', () => {
    const dom = withDom();
    const previousReadPHP = globalThis.readPHP;
    const previousRawFile = globalThis.rawFile;
    const previousMessage = globalThis.lang_error_resultset_too_large;
    const languageSource = fs.readFileSync(path.join(PUBLIC_DIR, 'js', 'def_language.js'), 'utf8');
    globalThis.lang_error_resultset_too_large = new Function(
      'document',
      languageSource + '\nreturn lang_error_resultset_too_large;',
    )(dom.document);
    try {
      const { readPHPChecked } = loadSearch();
      expect(typeof readPHPChecked).toBe('function');
      globalThis.readPHP = (url) => {
        expect(url).toBe('lemmasumperyear.php?lemma=DRJEWO');
        globalThis.rawFile = { getResponseHeader: () => '1' };
        return '|DRJEWO|\t1880\t3\n';
      };

      expect(readPHPChecked(dom.document, 'lemmasumperyear.php?lemma=DRJEWO')).toBeNull();
      expect(dom.document.querySelectorAll('body > *')).toHaveLength(1);
      expect(dom.document.body.firstElementChild.textContent).toBe(
        globalThis.lang_error_resultset_too_large,
      );
    } finally {
      if (previousReadPHP === undefined) delete globalThis.readPHP;
      else globalThis.readPHP = previousReadPHP;
      if (previousRawFile === undefined) delete globalThis.rawFile;
      else globalThis.rawFile = previousRawFile;
      if (previousMessage === undefined) delete globalThis.lang_error_resultset_too_large;
      else globalThis.lang_error_resultset_too_large = previousMessage;
      dom.restore();
    }
  });
});

describe('readSearchOptions', () => {
  it('returns the search defaults', () => {
    const dom = withDom();
    try {
      const { readSearchOptions } = loadSearch();

      // These defaults must agree exactly with PHP search_options() from step A1.
      expect(readSearchOptions('')).toEqual({
        cs: false,
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
        cs: false,
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

      expect(readSearchOptions('?cs=1&ambig=0&trim=0')).toEqual({
        cs: true,
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
      dom.document.getElementById('csCheckBox').checked = false;
      dom.document.getElementById('regexCheckBox').checked = true;

      expect(searchOptionsFromForm(dom.document)).toEqual({
        cs: false,
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

      expect(searchQueryString('lemma', 'DRJEWO', { cs: true, ambig: true, trim: true })).toBe(
        'lemma=DRJEWO&cs=1&ambig=1&trim=1',
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
          cs: false,
          regex: false,
          list: false,
          trim: false,
          ambig: false,
        }),
      ).toBe('lemma=DRJEWO&cs=0&regex=0&list=0&trim=0&ambig=0');
    } finally {
      dom.restore();
    }
  });

  it('escapes literal and regex terms without changing them', () => {
    const dom = withDom();
    try {
      const { searchQueryString } = loadSearch();
      const literalQuery = searchQueryString('lemma', 'a&b=c', {
        cs: true,
        regex: false,
        list: false,
        trim: true,
        ambig: true,
      });
      const regexQuery = searchQueryString('lemma', 'TE(J|N)', {
        cs: true,
        regex: true,
        list: false,
        trim: true,
        ambig: true,
      });

      expect(literalQuery).toBe('lemma=a%26b%3Dc&cs=1&regex=0&list=0&trim=1&ambig=1');
      expect(regexQuery).toBe('lemma=TE(J%7CN)&cs=1&regex=1&list=0&trim=1&ambig=1');
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
      const flags = ['cs', 'regex', 'list', 'trim', 'ambig'];

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
        expect(document.querySelector('#csCheckBox').checked).toBe(false);
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
      expect(dom.document.querySelector('#csCheckBox').checked).toBe(false);
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

  it('shows the example that matches the restored options', () => {
    expectRestoredSearch(
      'https://example.test/vis/bwlemma/?lemma=DRJEWO&regex=1&list=1&trim=1&cs=0',
      (document) => {
        expect(document.querySelector('#searchexample').textContent).toBe('te(j|n); bom');
      },
    );
  });

  it('shows the lowercase example for the untouched form when every option is off', () => {
    // The page restores on every load, so this is the example a first-time visitor sees.
    expectRestoredSearch('https://example.test/vis/bwlemma/', (document) => {
      expect(document.querySelector('#searchexample').textContent).toBe('drjewo');
    });
  });

  it('restores a norm list and displays its example', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { restoreSearchFromLocation } = loadSearch();

      restoreSearchFromLocation(dom.document, '?norm=A;B&list=1', 'norm');

      expect(dom.document.querySelector('#searchinput').value).toBe('A;B');
      expect(dom.document.querySelector('#listCheckBox').checked).toBe(true);
      expect(dom.document.querySelector('#searchexample').textContent).toBe('tej; ten');
    } finally {
      dom.restore();
    }
  });

  it('restores legacy word links for tokens without overriding an explicit token', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { restoreSearchFromLocation } = loadSearch();
      const input = dom.document.querySelector('#searchinput');

      restoreSearchFromLocation(dom.document, '?word=woni', 'token');
      expect(input.value).toBe('woni');
      expect(dom.document.querySelector('#searchexample').textContent).toBe('woni');

      restoreSearchFromLocation(dom.document, '?word=woni&token=druge', 'token');
      expect(input.value).toBe('druge');

      restoreSearchFromLocation(dom.document, '?word=woni', 'norm');
      expect(input.value).toBe('');
    } finally {
      dom.restore();
    }
  });
});

describe('buildVisUrls', () => {
  it('builds all lemma visualization URLs with defaults', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', 'DRJEWO', {}, 0)).toEqual({
        timeline:
          'timeline.html?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0',
        group:
          'lemmalist.html?data=lemmagroup.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=lemmatoken.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort',
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
        'timeline.html?data=lemmacountperyear.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=3',
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
          'timelinesumlist.html?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort&focus=0',
        group:
          'lemmalist.html?data=lemmagroup.php&lemma=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=lemmatoken.php&lemma=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
      });
    } finally {
      dom.restore();
    }
  });

  it('builds all norm visualization URLs with defaults', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('norm', 'DRJEWO', {}, 0)).toEqual({
        timeline:
          'timeline.html?data=normsumperyear.php&norm=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0',
        group:
          'normlist.html?data=normgroup.php&norm=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=normtoken.php&norm=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort',
      });
    } finally {
      dom.restore();
    }
  });

  it('uses norm counts at focus 3 and the summed-list page in list mode', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('norm', 'DRJEWO', {}, 3).timeline).toBe(
        'timeline.html?data=normcountperyear.php&norm=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=3',
      );
      expect(buildVisUrls('norm', 'DRJEWO', { list: true }, 0)).toEqual({
        timeline:
          'timelinesumlist.html?data=normsumperyear.php&norm=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort&focus=0',
        group:
          'normlist.html?data=normgroup.php&norm=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=normtoken.php&norm=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
      });
    } finally {
      dom.restore();
    }
  });

  it('builds only a timeline and word info for one concrete token', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('token', 'woni', {}, 0)).toEqual({
        timeline:
          'timeline.html?data=tokencountperyear.php&token=woni&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0',
        wordinfo: 'wordinfo.html?data=token2lemma.php&token=woni',
      });
      expect(buildVisUrls('token', 'woni', {}, 3)).toEqual({
        timeline:
          'timeline.html?data=tokencountperyear.php&token=woni&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=3',
        wordinfo: 'wordinfo.html?data=token2lemma.php&token=woni',
      });
    } finally {
      dom.restore();
    }
  });

  it.each([
    [
      'list',
      { list: true },
      'timeline.html?data=tokencountperyear.php&token=woni&cs=0&regex=0&list=1&trim=1&ambig=1&sort&focus=0',
    ],
    [
      'regex',
      { regex: true },
      'timeline.html?data=tokencountperyear.php&token=woni&cs=0&regex=1&list=0&trim=1&ambig=1&sort&focus=0',
    ],
  ])(
    'disables token word info for %s searches without changing the timeline page',
    (_mode, options, timeline) => {
      const dom = withDom();
      try {
        const buildVisUrls = loadBuildVisUrls();

        expect(buildVisUrls('token', 'woni', options, 0)).toEqual({
          timeline,
          wordinfo: 'error_token.html',
        });
      } finally {
        dom.restore();
      }
    },
  );

  it('keeps the standard endpoints when regex is enabled', () => {
    const dom = withDom();
    try {
      const buildVisUrls = loadBuildVisUrls();

      expect(buildVisUrls('lemma', 'TE(J|N)', { regex: true }, 0)).toEqual({
        timeline:
          'timeline.html?data=lemmasumperyear.php&lemma=TE(J%7CN)&cs=0&regex=1&list=0&trim=1&ambig=1&sort&focus=0',
        group:
          'lemmalist.html?data=lemmagroup.php&lemma=TE(J%7CN)&cs=0&regex=1&list=0&trim=1&ambig=1&sort',
        tokens:
          'tokenlist.html?data=lemmatoken.php&lemma=TE(J%7CN)&cs=0&regex=1&list=0&trim=1&ambig=1&sort',
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
        '?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort&focus=0';

      expect(phpUrlFromLocation('data', 'lemma', search)).toBe(
        'lemmasumperyear.php?lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort',
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
        'lemmasumperyear.php?lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort',
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
      ).toBe('lemmasumperyear.php?lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=0&sort');
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
      ).toBe('lemmasumperyear.php?lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=1&sort');
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

describe('listPlotUrlsFromLocation', () => {
  it('requests ambiguous forms for every trimmed lemma in list mode', () => {
    const dom = withDom();
    try {
      const listPlotUrlsFromLocation = loadListPlotUrlsFromLocation();
      const search =
        '?data=lemmasumperyear.php&lemma=drjewo%2C%20bom&cs=0&regex=0&list=1&trim=1&ambig=1&sort&focus=0';

      expect(listPlotUrlsFromLocation('data', 'lemma', search)).toEqual([
        'lemmasumperyear.php?lemma=drjewo&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
        'lemmasumperyear.php?lemma=bom&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
      ]);
    } finally {
      dom.restore();
    }
  });

  it('requests a separate norm series for each term in list mode', () => {
    const dom = withDom();
    try {
      const listPlotUrlsFromLocation = loadListPlotUrlsFromLocation();

      expect(
        listPlotUrlsFromLocation('data', 'norm', '?data=normsumperyear.php&norm=A;B&list=1'),
      ).toEqual([
        'normsumperyear.php?norm=A&cs=0&regex=0&list=1&trim=1&ambig=1',
        'normsumperyear.php?norm=B&cs=0&regex=0&list=1&trim=1&ambig=1',
      ]);
    } finally {
      dom.restore();
    }
  });

  it('splits a regex list only on semicolon so each pattern keeps its commas', () => {
    const dom = withDom();
    try {
      const listPlotUrlsFromLocation = loadListPlotUrlsFromLocation();
      const search =
        '?data=lemmasumperyear.php&lemma=' +
        encodeURIComponent('te(j|n);bom') +
        '&cs=0&regex=1&list=1&trim=1&ambig=1&sort&focus=0';

      expect(listPlotUrlsFromLocation('data', 'lemma', search)).toEqual([
        'lemmasumperyear.php?lemma=te(j%7Cn)&cs=0&regex=1&list=1&trim=1&ambig=1&sort',
        'lemmasumperyear.php?lemma=bom&cs=0&regex=1&list=1&trim=1&ambig=1&sort',
      ]);
    } finally {
      dom.restore();
    }
  });

  it('leaves a regex quantifier with an internal comma as a single URL', () => {
    const dom = withDom();
    try {
      const listPlotUrlsFromLocation = loadListPlotUrlsFromLocation();
      const search =
        '?data=lemmasumperyear.php&lemma=' +
        encodeURIComponent('a{2,5}') +
        '&cs=0&regex=1&list=1&trim=1&ambig=1&sort&focus=0';

      expect(listPlotUrlsFromLocation('data', 'lemma', search)).toEqual([
        'lemmasumperyear.php?lemma=a%7B2%2C5%7D&cs=0&regex=1&list=1&trim=1&ambig=1&sort',
      ]);
    } finally {
      dom.restore();
    }
  });
});

describe('listPlotTraces', () => {
  it('plots every ambiguous lemma cell returned for a list search', () => {
    const dom = withDom();
    try {
      const listPlotTraces = loadListPlotTraces();
      const rawData = [
        '|BOM|\t1880\t3',
        '|DRJEWO|\t1880\t8',
        '|DRĚŚ|DRJEWO|\t1881\t2',
        '|BOM|BOMOWY|\t1882\t4',
        '|DRJEWO|DRJEWOWY|\t1880\t2',
        '|DRJEWO|\t1881\t5',
        '',
      ].join('\n');

      const traces = listPlotTraces(rawData, '\t').map(({ name, x, y, mode }) => ({
        name,
        x,
        y,
        mode,
      }));

      expect(traces).toEqual([
        { name: '|BOM|', x: ['1880'], y: [3], mode: 'markers' },
        { name: '|DRJEWO|', x: ['1880', '1881'], y: [8, 5], mode: 'markers' },
        { name: '|DRĚŚ|DRJEWO|', x: ['1881'], y: [2], mode: 'markers' },
        { name: '|BOM|BOMOWY|', x: ['1882'], y: [4], mode: 'markers' },
        { name: '|DRJEWO|DRJEWOWY|', x: ['1880'], y: [2], mode: 'markers' },
      ]);
    } finally {
      dom.restore();
    }
  });
});

describe('token-per-year Traviz URLs', () => {
  function openPage(kind) {
    const html = fs.readFileSync(path.join(PUBLIC_DIR, 'vis', kind, 'index.html'), 'utf8');
    const dom = new JSDOM(html, {
      runScripts: 'outside-only',
      url: 'https://example.test/vis/' + kind + '/index.html',
    });

    for (const script of dom.window.document.querySelectorAll('script[src]')) {
      const file = path.join(PUBLIC_DIR, 'vis', kind, script.getAttribute('src'));
      dom.window.eval(fs.readFileSync(file, 'utf8'));
    }
    const inlineScripts = dom.window.document.querySelectorAll('script:not([src])');
    dom.window.eval(inlineScripts[inlineScripts.length - 2].textContent);

    for (const id of ['yearminslider', 'yearmaxslider']) {
      const slider = dom.window.document.getElementById(id);
      slider.min = '1800';
      slider.max = '1900';
    }
    return dom;
  }

  it.each([
    ['bwlemma', 'lemma', 'lemmatokenperyear.php'],
    ['bwnorm', 'norm', 'normtokenperyear.php'],
  ])('%s sends a year range when a term is selected', (kind, termKey, endpoint) => {
    const dom = openPage(kind);
    try {
      const from = dom.window.document.getElementById('yearminslider');
      const to = dom.window.document.getElementById('yearmaxslider');
      from.value = '1870';
      to.value = '1880';

      dom.window.itemClick('DRJEWO');

      const selected = new URL(dom.window.document.getElementById('traviz').src);
      expect(selected.searchParams.get('data')).toBe(endpoint);
      expect(selected.searchParams.get(termKey)).toBe('DRJEWO');
      expect(selected.searchParams.get('year')).toBe('1870-1880');
    } finally {
      dom.window.close();
    }
  });

  it.each([
    ['bwlemma', 'lemma', 'lemmatokenperyear.php'],
    ['bwnorm', 'norm', 'normtokenperyear.php'],
  ])('%s sends the new year range after a slider change', (kind, termKey, endpoint) => {
    const dom = openPage(kind);
    try {
      const from = dom.window.document.getElementById('yearminslider');
      const to = dom.window.document.getElementById('yearmaxslider');
      from.value = '1870';
      to.value = '1880';
      dom.window.itemClick('DRJEWO');

      from.value = '1871';
      to.value = '1879';
      dom.window.updateTravizYear();

      const updated = new URL(dom.window.document.getElementById('traviz').src);
      expect(updated.searchParams.get('data')).toBe(endpoint);
      expect(updated.searchParams.get(termKey)).toBe('DRJEWO');
      expect(updated.searchParams.get('year')).toBe('1871-1879');
    } finally {
      dom.window.close();
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

  const resolverPages = pages.filter((page) => page !== 'doclist.html');

  it.each(resolverPages)('%s routes every synchronous fetch through readPHPChecked', (page) => {
    const document = loadPage('vis/bwlemma/' + page);
    const inlineSource = [...document.querySelectorAll('script:not([src])')]
      .map((script) => script.textContent)
      .join('\n');

    expect(inlineSource).toMatch(/\breadPHPChecked\(/);
    expect(inlineSource).not.toMatch(/\breadPHP\(/);
  });

  it.each(resolverPages)('%s renders no data when its response was truncated', (page) => {
    let view;
    try {
      expect(() => {
        view = runBwlemmaPlotPage(
          page,
          '?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=1&trim=1&ambig=1&sort',
          {},
          true,
        );
      }).not.toThrow();
      expect(view.plotCalls).toHaveLength(0);
      expect(view.treeCalls).toHaveLength(0);
      expect(view.document.querySelectorAll('table')).toHaveLength(0);
      expect(view.document.getElementById('containerDiv')?.children.length || 0).toBe(0);
    } finally {
      view?.close();
    }
  });

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

  it.each(['timelinesumlist.html', 'percenttimelinesumlist.html'])(
    '%s builds each plotted series with the list search options',
    (page) => {
      const document = loadPage('vis/bwlemma/' + page);
      const inlineSource = [...document.querySelectorAll('script:not([src])')]
        .map((script) => script.textContent)
        .join('\n');

      expect(inlineSource).toMatch(
        /listPlotUrlsFromLocation\(\s*['"]data['"]\s*,\s*['"]lemma['"]\s*,\s*(?:window\.)?location\.search\s*\)/,
      );
    },
  );

  it('renders the summed list plot from traces grouped by returned lemma cell', () => {
    const document = loadPage('vis/bwlemma/timelinesumlist.html');
    const inlineSource = [...document.querySelectorAll('script:not([src])')]
      .map((script) => script.textContent)
      .join('\n');

    expect(inlineSource).toMatch(/\bdata\s*=\s*listPlotTraces\(\s*[^,]+\s*,\s*sep\s*\)/);
  });

  it.each([
    ['omits', 'off', '0', 'Lemma DRJEWO'],
    ['includes', 'on', '1', 'Lemma DRJEWO inkl. ambig'],
  ])(
    '%s inkl. ambig in the timeline title when ambig search is %s',
    (_verb, _state, ambig, title) => {
      const search =
        '?data=lemmasumperyear.php&lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=' +
        ambig +
        '&sort&focus=0';
      const page = runBwlemmaPlotPage('timeline.html', search, {
        ['lemmasumperyear.php?lemma=DRJEWO&cs=0&regex=0&list=0&trim=1&ambig=' + ambig + '&sort']:
          '|DRJEWO|\t1880\t3\n',
      });
      try {
        expect(page.plotCalls[0].layout.title.text).toBe(title);
        expect(page.plotCalls[0].layout.title.text.includes('inkl. ambig')).toBe(ambig === '1');
      } finally {
        page.close();
      }
    },
  );

  it.each([
    ['omits', 'off', '0'],
    ['includes', 'on', '1'],
  ])(
    '%s inkl. ambig in the list timeline title when ambig search is %s',
    (_verb, _state, ambig) => {
      const search =
        '?data=lemmasumperyear.php&lemma=drjewo&cs=0&regex=0&list=1&trim=1&ambig=' +
        ambig +
        '&sort&focus=0';
      const page = runBwlemmaPlotPage('timelinesumlist.html', search, {
        ['lemmasumperyear.php?lemma=drjewo&cs=0&regex=0&list=1&trim=1&ambig=' + ambig + '&sort']:
          '|DRJEWO|\t1880\t3\n',
      });
      try {
        const title = page.plotCalls[0].layout.title.text;

        expect(title.startsWith('Jahressumme Lemma')).toBe(true);
        expect(title).toContain('>drjewo</span>');
        expect(title.includes('inkl. ambig')).toBe(ambig === '1');
      } finally {
        page.close();
      }
    },
  );
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

  it('splits a regex list only on semicolon', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('te(j|n);bom', { list: true, regex: true, trim: true })).toEqual([
        'te(j|n)',
        'bom',
      ]);
    } finally {
      dom.restore();
    }
  });

  it('does not treat comma as a regex-list separator', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('te(j|n),bom', { list: true, regex: true, trim: true })).toEqual([
        'te(j|n),bom',
      ]);
    } finally {
      dom.restore();
    }
  });

  it('keeps a comma inside a regex quantifier as one term', () => {
    const dom = withDom();
    try {
      const splitTerms = loadSplitTerms();

      expect(splitTerms('a{2,5}', { list: true, regex: true, trim: true })).toEqual(['a{2,5}']);
    } finally {
      dom.restore();
    }
  });
});

describe('listTermsFromLocation', () => {
  it('splits terms using the requested field and defaults to lemma', () => {
    const dom = withDom();
    try {
      const { listTermsFromLocation } = loadSearch();

      expect(listTermsFromLocation('?norm=A;B&list=1', 'norm')).toEqual(['A', 'B']);
      expect(listTermsFromLocation('?lemma=DRJEWO;BOM&list=1')).toEqual(['DRJEWO', 'BOM']);
      expect(listTermsFromLocation('?word=woni&list=1', 'token')).toEqual([]);
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
          cs: true,
          trim: false,
          ambig: false,
        }),
      ).toEqual({ autocomplete: true, alphabetSort: true });
    } finally {
      dom.restore();
    }
  });

  it.each([
    ['regex', { regex: true, list: false }],
    ['list', { regex: false, list: true }],
  ])('keeps the search input enabled in %s mode', (_mode, options) => {
    const dom = withDom({
      html: '<input id="prefixsearchCheckBox" type="checkbox"><input id="searchinput">',
    });
    try {
      const { applySearchControlState } = loadSearch();
      const searchInput = dom.document.getElementById('searchinput');

      applySearchControlState(dom.document, options);

      expect(searchInput.disabled).toBe(false);
    } finally {
      dom.restore();
    }
  });

  it.each([
    ['regex', { regex: true, list: false }],
    ['list', { regex: false, list: true }],
  ])('disables and greys alphabet sorting in %s mode', (_mode, options) => {
    const stylesheet = fs.readFileSync(path.join(PUBLIC_DIR, 'digilabstyles.css'), 'utf8');
    const dom = withDom({
      html:
        '<style>' +
        stylesheet +
        '</style><label><input id="prefixsearchCheckBox" type="checkbox">Alphabetical</label>',
    });
    try {
      const { applySearchControlState } = loadSearch();
      const alphabetSort = dom.document.getElementById('prefixsearchCheckBox');
      const alphabetSortLabel = alphabetSort.closest('label');

      applySearchControlState(dom.document, options);

      expect(alphabetSort.disabled).toBe(true);
      expect(dom.window.getComputedStyle(alphabetSortLabel).color).toBe('rgb(128, 128, 128)');

      applySearchControlState(dom.document, { regex: false, list: false });
      expect(alphabetSort.disabled).toBe(false);
      expect(dom.window.getComputedStyle(alphabetSortLabel).color).toBe('rgb(0, 0, 0)');
    } finally {
      dom.restore();
    }
  });
});

describe('ambigButtonLabel', () => {
  it.each([
    ['plain search', false, 'lang_searchitem'],
    ['ambig-inclusive search', true, 'lang_ambigsearch'],
  ])('returns the %s label', (_description, ambig, labelName) => {
    const dom = withDom();
    try {
      const { ambigButtonLabel } = loadSearch();
      const labels = loadScript('def_language.js');

      expect(ambigButtonLabel(ambig)).toBe(labels[labelName]);
    } finally {
      dom.restore();
    }
  });
});

describe('applyAmbigButtonLabel', () => {
  const HTML =
    '<input id="ambigCheckBox" checked type="checkbox">' +
    '<button id="ambigSearchButton">Suche inkl Ambig</button>';

  it.each([
    ['ambig-inclusive', true, 'lang_ambigsearch'],
    ['plain', false, 'lang_searchitem'],
  ])('shows the %s label for the checkbox state', (_description, checked, labelName) => {
    const dom = withDom({ html: HTML });
    try {
      const { applyAmbigButtonLabel } = loadSearch();
      const labels = loadScript('def_language.js');
      dom.document.getElementById('ambigCheckBox').checked = checked;

      applyAmbigButtonLabel(dom.document);

      expect(dom.document.getElementById('ambigSearchButton').textContent).toBe(labels[labelName]);
    } finally {
      dom.restore();
    }
  });

  it('flips the button label when the checkbox is unchecked and re-checked by the user', () => {
    const dom = withDom({ html: HTML });
    try {
      const { applyAmbigButtonLabel } = loadSearch();
      const { lang_searchitem, lang_ambigsearch } = loadScript('def_language.js');
      const checkbox = dom.document.getElementById('ambigCheckBox');
      const button = dom.document.getElementById('ambigSearchButton');
      checkbox.addEventListener('change', () => applyAmbigButtonLabel(dom.document));
      applyAmbigButtonLabel(dom.document);
      expect(button.textContent).toBe(lang_ambigsearch);

      checkbox.checked = false;
      checkbox.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
      expect(button.textContent).toBe(lang_searchitem);

      checkbox.checked = true;
      checkbox.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
      expect(button.textContent).toBe(lang_ambigsearch);
    } finally {
      dom.restore();
    }
  });
});

describe('searchExample', () => {
  it.each([
    ['a plain term', { cs: false, regex: false, list: false, trim: false }, 'drjewo'],
    ['a regex', { cs: false, regex: true, list: false, trim: false }, 'te(j|n)'],
    ['a list', { cs: false, regex: false, list: true, trim: false }, 'drjewo;bom'],
    [
      'a list with a space after the semicolon',
      { cs: false, regex: false, list: true, trim: true },
      'drjewo; bom',
    ],
    [
      'a semicolon-separated regex list',
      { cs: false, regex: true, list: true, trim: false },
      'te(j|n);bom',
    ],
    [
      'a semicolon-separated regex list with a space after the semicolon',
      { cs: false, regex: true, list: true, trim: true },
      'te(j|n); bom',
    ],
  ])('shows %s', (_description, options, expected) => {
    const dom = withDom();
    try {
      const { searchExample } = loadSearch();
      expect(typeof searchExample).toBe('function');

      expect(searchExample({ ...options, ambig: true })).toBe(expected);
    } finally {
      dom.restore();
    }
  });

  it.each([
    ['a plain term', { cs: true, regex: false, list: false, trim: false }, 'DRJEWO'],
    ['a regex', { cs: true, regex: true, list: false, trim: false }, 'TE(J|N)'],
    ['a list', { cs: true, regex: false, list: true, trim: false }, 'DRJEWO;BOM'],
    [
      'a list with a space after the semicolon',
      { cs: true, regex: false, list: true, trim: true },
      'DRJEWO; BOM',
    ],
    [
      'a semicolon-separated regex list',
      { cs: true, regex: true, list: true, trim: false },
      'TE(J|N);BOM',
    ],
    [
      'a semicolon-separated regex list with a space after the semicolon',
      { cs: true, regex: true, list: true, trim: true },
      'TE(J|N); BOM',
    ],
  ])(
    'shows %s in upper case when the search is case sensitive',
    (_description, options, expected) => {
      const dom = withDom();
      try {
        const { searchExample } = loadSearch();

        expect(searchExample({ ...options, ambig: true })).toBe(expected);
      } finally {
        dom.restore();
      }
    },
  );

  it.each([
    ['norm', false, 'Chóśebuz', 'te(j|n)', 'tej; ten', 'te(j|n); Chóśebuz'],
    ['norm', true, 'Chóśebuz', 'te(j|n)', 'tej; ten', 'te(j|n); Chóśebuz'],
    ['token', false, 'woni', 'w(o|a)n(a|i)', 'druge; woni', 'w(o|a)n(a|i); druge'],
    ['token', true, 'woni', 'w(o|a)n(a|i)', 'druge; woni', 'w(o|a)n(a|i); druge'],
  ])(
    'shows %s examples when case sensitivity is %s',
    (kind, cs, literal, regex, list, regexList) => {
      const dom = withDom();
      try {
        const { searchExample } = loadSearch();

        expect(searchExample({ cs, regex: false, list: false }, kind)).toBe(literal);
        expect(searchExample({ cs, regex: true, list: false }, kind)).toBe(regex);
        expect(searchExample({ cs, regex: false, list: true }, kind)).toBe(list);
        expect(searchExample({ cs, regex: true, list: true }, kind)).toBe(regexList);
        expect(searchExample({ cs, regex: false, list: true, trim: false }, kind)).toBe(
          list.replace('; ', ';'),
        );
        expect(searchExample({ cs, regex: true, list: true, trim: false }, kind)).toBe(
          regexList.replace('; ', ';'),
        );
      } finally {
        dom.restore();
      }
    },
  );

  it('is unaffected by the ambiguity option', () => {
    const dom = withDom();
    try {
      const { searchExample } = loadSearch();
      const options = { cs: false, regex: true, list: true, trim: true };

      expect(searchExample({ ...options, ambig: false })).toBe(
        searchExample({ ...options, ambig: true }),
      );
    } finally {
      dom.restore();
    }
  });
});

describe('applySearchExample', () => {
  it('writes the example for the current checkbox state', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { applySearchExample } = loadSearch();
      expect(typeof applySearchExample).toBe('function');
      dom.document.getElementById('csCheckBox').checked = false;
      dom.document.getElementById('listCheckBox').checked = true;

      applySearchExample(dom.document);

      expect(dom.document.getElementById('searchexample').textContent).toBe('drjewo; bom');
    } finally {
      dom.restore();
    }
  });

  it('follows the user ticking and unticking the search options', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { applySearchExample } = loadSearch();
      const example = dom.document.getElementById('searchexample');
      const tick = (id, checked) => {
        const checkbox = dom.document.getElementById(id);
        checkbox.checked = checked;
        checkbox.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
      };
      ['csCheckBox', 'regexCheckBox', 'listCheckBox', 'trimCheckBox', 'ambigCheckBox'].forEach(
        (id) => {
          dom.document
            .getElementById(id)
            .addEventListener('change', () => applySearchExample(dom.document));
        },
      );

      tick('csCheckBox', false);
      expect(example.textContent).toBe('drjewo');

      tick('regexCheckBox', true);
      expect(example.textContent).toBe('te(j|n)');

      tick('listCheckBox', true);
      expect(example.textContent).toBe('te(j|n); bom');

      tick('trimCheckBox', false);
      expect(example.textContent).toBe('te(j|n);bom');

      tick('regexCheckBox', false);
      expect(example.textContent).toBe('drjewo;bom');

      tick('csCheckBox', true);
      expect(example.textContent).toBe('DRJEWO;BOM');

      tick('listCheckBox', false);
      expect(example.textContent).toBe('DRJEWO');
    } finally {
      dom.restore();
    }
  });

  it('updates the displayed example for the selected kind as options change', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { applySearchExample } = loadSearch();
      const example = dom.document.getElementById('searchexample');
      const list = dom.document.getElementById('listCheckBox');

      applySearchExample(dom.document, 'token');
      expect(example.textContent).toBe('woni');

      list.checked = true;
      applySearchExample(dom.document, 'token');
      expect(example.textContent).toBe('druge; woni');

      applySearchExample(dom.document, 'norm');
      expect(example.textContent).toBe('tej; ten');
    } finally {
      dom.restore();
    }
  });

  it('leaves the page alone when it has no example element', () => {
    const dom = withDom({ html: BWLEMMA_SEARCH_HTML });
    try {
      const { applySearchExample } = loadSearch();
      dom.document.getElementById('searchexample').remove();

      expect(() => applySearchExample(dom.document)).not.toThrow();
    } finally {
      dom.restore();
    }
  });
});
