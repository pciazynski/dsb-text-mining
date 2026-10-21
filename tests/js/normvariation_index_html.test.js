const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const { PUBLIC_DIR, loadPage, withDom, loadScript } = require('./helpers');

function inlineSourceOf(document) {
  return [...document.querySelectorAll('script:not([src])')]
    .map((script) => script.textContent)
    .join('\n');
}

describe('vis/normvariation/index.html', () => {
  it('opens dolnoserbski.de through the shared URL builder', () => {
    const source = inlineSourceOf(loadPage('vis/normvariation/index.html'));

    expect(source).toContain('dolnoserbskiUrl(');
    expect(source).not.toContain("slownik?wuraz=' +");
  });

  it('has one search text input and removes the legacy search inputs', () => {
    const document = loadPage('vis/normvariation/index.html');

    expect([...document.querySelectorAll('input[type="text"]')].map((input) => input.id)).toEqual([
      'searchinput',
    ]);
    for (const id of ['norm', 'normlist', 'normregex']) {
      expect(document.getElementById(id)).toBeNull();
    }
  });

  it('provides all search option checkboxes with the intended defaults', () => {
    const document = loadPage('vis/normvariation/index.html');
    const defaults = {
      csCheckBox: false,
      regexCheckBox: false,
      listCheckBox: false,
      trimCheckBox: true,
      ambigCheckBox: true,
    };

    for (const [id, checked] of Object.entries(defaults)) {
      const checkbox = document.getElementById(id);
      expect(checkbox?.getAttribute('type')).toBe('checkbox');
      expect(checkbox.hasAttribute('checked')).toBe(checked);
      expect(checkbox.getAttribute('onchange')).toBe('switchSearchOptions()');
    }
  });

  it('defaults alphabetical sorting off and keeps its label with the control', () => {
    const document = loadPage('vis/normvariation/index.html');
    const checkbox = document.getElementById('prefixsearchCheckBox');

    expect(checkbox?.getAttribute('type')).toBe('checkbox');
    expect(checkbox.hasAttribute('checked')).toBe(false);
    expect(checkbox.closest('label')).not.toBeNull();
  });

  it('provides a dynamic example placeholder', () => {
    const document = loadPage('vis/normvariation/index.html');

    expect(document.getElementById('searchexample')).not.toBeNull();
  });

  it('makes the druge and francojski example an explicit semicolon list', () => {
    const document = loadPage('vis/normvariation/index.html');
    const normLinks = [...document.querySelectorAll('a[href^="?norm="]')].map((link) =>
      link.getAttribute('href'),
    );

    expect(normLinks).toContain('?norm=druge;francojski&list=1');
    expect(normLinks).not.toContain('?norm=druge,francojski');
  });

  it('loads search.js after datahandler.js and def_language.js', () => {
    const document = loadPage('vis/normvariation/index.html');
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );
    const searchSource = sources.find((source) => source.endsWith('js/search.js'));

    expect(searchSource).toBeDefined();
    expect(fs.existsSync(path.resolve(PUBLIC_DIR, 'vis/normvariation', searchSource))).toBe(true);
    for (const dependency of ['js/datahandler.js', 'js/def_language.js']) {
      expect(sources.indexOf(searchSource)).toBeGreaterThan(
        sources.findIndex((source) => source.endsWith(dependency)),
      );
    }
  });

  it('restores norm searches through the shared helper without inferring lists from commas', () => {
    const source = inlineSourceOf(loadPage('vis/normvariation/index.html'));

    expect(source).toMatch(
      /restoreSearchFromLocation\(\s*document\s*,\s*window\.location\.search\s*,\s*['"]norm['"]\s*\)/,
    );
    expect(source).not.toMatch(/curnorm\.includes\(\s*['"],['"]\s*\)/);
  });

  it('restores a legacy comma link as one literal in the actual search form', () => {
    const page = loadPage('vis/normvariation/index.html');
    const dom = withDom({ html: page.documentElement.outerHTML });
    try {
      const { restoreSearchFromLocation } = loadScript('search.js');
      expect(dom.document.getElementById('searchinput')).not.toBeNull();

      restoreSearchFromLocation(dom.document, '?norm=druge,francojski', 'norm');

      expect(dom.document.getElementById('searchinput').value).toBe('druge,francojski');
      expect(dom.document.getElementById('listCheckBox').checked).toBe(false);
    } finally {
      dom.restore();
    }
  });

  it('uses one tree URL builder instead of separate list and regex search paths', () => {
    const source = inlineSourceOf(loadPage('vis/normvariation/index.html'));

    expect(source).toMatch(/buildTreeUrls\(\s*['"]norm['"]\s*,/);
    expect(source).not.toMatch(/\bupdateTreeFrom(?:List|Regex)\b/);
    expect(source).not.toContain('normtokenregex.php');
  });

  it('keeps the norm autocomplete cutoff and limit on the unified input', () => {
    const source = inlineSourceOf(loadPage('vis/normvariation/index.html'));

    expect(source).toMatch(
      /autocomplete\(\s*['"]searchinput['"]\s*,\s*['"]prefixnormsearch\.php\?&?cutoff=2&limit=20&norm=/,
    );
  });
});

describe('buildTreeUrls for normvariation', () => {
  it.each([false, true])('builds only tree and traviz URLs with weight=%s', (weight) => {
    const dom = withDom();
    try {
      const { buildTreeUrls } = loadScript('search.js');
      const suffix = '&sort&inclusive' + (weight ? '&weight' : '');

      expect(buildTreeUrls('norm', 'pśiźo', {}, weight)).toEqual({
        tree:
          'normtree_dagre.html?data=normtoken.php&norm=p%C5%9Bi%C5%BAo&cs=0&regex=0&list=0&trim=1&ambig=1' +
          suffix,
        traviz:
          'traviz.html?data=normtoken.php&norm=p%C5%9Bi%C5%BAo&cs=0&regex=0&list=0&trim=1&ambig=1' +
          suffix,
      });
    } finally {
      dom.restore();
    }
  });

  it.each([
    ['te(j|n)', false, 'te(j%7Cn)'],
    ['te(j|n);Chóśebuz', true, 'te(j%7Cn)%3BCh%C3%B3%C5%9Bebuz'],
  ])('uses the existing norm endpoint for regex %s', (term, list, encoded) => {
    const dom = withDom();
    try {
      const { buildTreeUrls } = loadScript('search.js');
      const options = { cs: true, regex: true, list, trim: false, ambig: false };
      const query =
        'norm=' + encoded + '&cs=1&regex=1&list=' + (list ? '1' : '0') + '&trim=0&ambig=0';

      expect(buildTreeUrls('norm', term, options, false)).toEqual({
        tree: 'normtree_dagre.html?data=normtoken.php&' + query + '&sort&inclusive',
        traviz: 'traviz.html?data=normtoken.php&' + query + '&sort&inclusive',
      });
    } finally {
      dom.restore();
    }
  });
});

describe('normvariation iframe pages', () => {
  const pages = ['normtree_dagre.html', 'traviz.html'];

  it.each(pages)('%s routes synchronous reads through readPHPChecked', (page) => {
    const source = inlineSourceOf(loadPage('vis/normvariation/' + page));

    expect(source).toMatch(/\breadPHPChecked\(/);
    expect(source).not.toMatch(/\breadPHP\(/);
  });

  it.each(pages)('%s loads search.js after datahandler.js', (page) => {
    const document = loadPage('vis/normvariation/' + page);
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );

    expect(sources).toContain('../../js/search.js');
    expect(sources.indexOf('../../js/search.js')).toBeGreaterThan(
      sources.indexOf('../../js/datahandler.js'),
    );
  });

  it.each(pages)('%s forwards norm search flags through the shared PHP URL helper', (page) => {
    const source = inlineSourceOf(loadPage('vis/normvariation/' + page));

    expect(source).toMatch(
      /phpUrlFromLocation\(\s*['"]data['"]\s*,\s*['"]norm['"]\s*,\s*(?:window\.)?location\.search\s*\)/,
    );
  });

  it('uses explicit search options instead of endpoint names or commas to decide the root', () => {
    const source = inlineSourceOf(loadPage('vis/normvariation/normtree_dagre.html'));

    expect(source).toMatch(/treeHasRoot\(\s*(?:window\.)?location\.search\s*\)/);
    expect(source).not.toMatch(/dataset\.includes\(\s*['"]regex\.php['"]\s*\)/);
    expect(source).not.toMatch(/norm\.includes\(\s*['"],['"]\s*\)/);
  });
});

describe('normvariation clicked nodes', () => {
  function openPage() {
    const html = fs.readFileSync(path.join(PUBLIC_DIR, 'vis/normvariation/index.html'), 'utf8');
    const dom = new JSDOM(html, {
      runScripts: 'outside-only',
      url: 'https://example.test/vis/normvariation/index.html',
    });
    for (const script of dom.window.document.querySelectorAll('script[src]')) {
      const file = path.join(PUBLIC_DIR, 'vis/normvariation', script.getAttribute('src'));
      dom.window.eval(fs.readFileSync(file, 'utf8'));
    }
    const scripts = dom.window.document.querySelectorAll('script:not([src])');
    dom.window.eval(scripts[scripts.length - 2].textContent);
    return dom;
  }

  it.each([
    ['|pśiźo|', 'p%C5%9Bi%C5%BAo'],
    ['|we|wě|wó|', 'we%7Cw%C4%9B%7Cw%C3%B3'],
  ])('opens the exact norm cell %s without its outer pipes', (item, encoded) => {
    const dom = openPage();
    try {
      dom.window.normclick(item);

      expect(dom.window.document.getElementById('timeline').getAttribute('src')).toBe(
        'normtimeline.html?data=normcountperyear.php&norm=' +
          encoded +
          '&cs=1&regex=0&list=0&trim=1&ambig=0&sort&focus=3',
      );
      expect(dom.window.document.getElementById('tokeninfo').getAttribute('src')).toBe(
        'error_token.html',
      );
    } finally {
      dom.window.close();
    }
  });

  it('opens the exact historical token timeline and its encoded token info', () => {
    const dom = openPage();
    try {
      dom.window.normclick('Pſchiżo');

      expect(dom.window.document.getElementById('timeline').getAttribute('src')).toBe(
        'tokentimeline.html?data=tokencountperyear.php&token=P%C5%BFchi%C5%BCo&cs=1&regex=0&list=0&trim=1&ambig=0&sort&focus=3',
      );
      expect(dom.window.document.getElementById('tokeninfo').getAttribute('src')).toBe(
        'datalist.html?data=token2norm.php&token=P%C5%BFchi%C5%BCo',
      );
    } finally {
      dom.window.close();
    }
  });
});
