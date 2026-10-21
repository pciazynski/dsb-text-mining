const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const { PUBLIC_DIR, loadPage } = require('./helpers');

function inlineSourceOf(document) {
  return [...document.querySelectorAll('script:not([src])')]
    .map((script) => script.textContent)
    .join('\n');
}

describe('vis/bwnorm/index.html', () => {
  it('opens dolnoserbski.de through the shared URL builder', () => {
    const source = inlineSourceOf(loadPage('vis/bwnorm/index.html'));

    expect(source).toContain('dolnoserbskiUrl(');
    expect(source).not.toContain("slownik?wuraz=' +");
  });

  it('sends the current search options to the norm variation page', () => {
    const source = inlineSourceOf(loadPage('vis/bwnorm/index.html'));

    expect(source).toContain("variationUrl('norm'");
    expect(source).not.toContain("'../normvariation?norm=' +");
  });

  it('has one search text input and removes the legacy search inputs', () => {
    const document = loadPage('vis/bwnorm/index.html');

    const textInputs = [...document.querySelectorAll('input[type="text"]')];

    expect(textInputs.map((input) => input.id)).toEqual(['searchinput']);
    expect(document.querySelector('#norm')).toBeNull();
    expect(document.querySelector('#regexsearch')).toBeNull();
    expect(document.querySelector('#normlist')).toBeNull();
  });

  it('provides all search option checkboxes with the intended defaults', () => {
    const document = loadPage('vis/bwnorm/index.html');

    const expectedDefaults = {
      csCheckBox: false,
      regexCheckBox: false,
      listCheckBox: false,
      trimCheckBox: true,
      ambigCheckBox: true,
    };

    for (const [id, checked] of Object.entries(expectedDefaults)) {
      const checkbox = document.querySelector(`#${id}`);
      expect(checkbox?.getAttribute('type')).toBe('checkbox');
      expect(checkbox.hasAttribute('checked')).toBe(checked);
    }
  });

  it('wires every search option checkbox to the shared change handler', () => {
    const document = loadPage('vis/bwnorm/index.html');

    for (const id of [
      'csCheckBox',
      'regexCheckBox',
      'listCheckBox',
      'trimCheckBox',
      'ambigCheckBox',
    ]) {
      expect(document.querySelector(`#${id}`)?.getAttribute('onchange')).toBe(
        'switchSearchOptions()',
      );
    }
  });

  it('updates the ambig button label and the norm example as part of switchSearchOptions', () => {
    const document = loadPage('vis/bwnorm/index.html');
    const switchSearchOptions = inlineSourceOf(document).match(
      /var switchSearchOptions = function \(\) \{[\s\S]*?\n    \};/,
    )?.[0];

    expect(switchSearchOptions).toMatch(/applyAmbigButtonLabel\(document\)/);
    expect(switchSearchOptions).toMatch(/applySearchExample\(document,\s*'norm'\)/);
    expect(document.getElementById('ambigSearchButton')).not.toBeNull();
  });

  it('groups alphabetical sorting with its text so both can be greyed out', () => {
    const document = loadPage('vis/bwnorm/index.html');

    const checkbox = document.querySelector('#prefixsearchCheckBox');

    expect(checkbox?.getAttribute('type')).toBe('checkbox');
    expect(checkbox.hasAttribute('checked')).toBe(false);
    expect(checkbox.closest('label')).not.toBeNull();
  });

  it('has a placeholder for the example instead of hard-coded ones', () => {
    const document = loadPage('vis/bwnorm/index.html');

    const text = document.documentElement.textContent;

    expect(document.querySelector('#searchexample')).not.toBeNull();
    expect(text).not.toContain('Chóśebuz');
    expect(text).not.toContain('tej,ten');
  });

  it('initializes norm autocomplete case-insensitively when case sensitivity is unchecked', () => {
    const document = loadPage('vis/bwnorm/index.html');
    const initialization = [...document.querySelectorAll('script:not([src])')]
      .map((script) => script.textContent)
      .find((source) => /autocomplete\(\s*'searchinput'/.test(source));

    expect(document.querySelector('#csCheckBox')?.checked).toBe(false);
    expect(initialization).toContain('prefixnormsearch.php?');
    expect(initialization).toContain('&cs=0&norm=');
  });

  it('passes the current mode state when refreshing autocomplete', () => {
    const document = loadPage('vis/bwnorm/index.html');
    const switchPrefixsearch = inlineSourceOf(document).match(
      /var switchPrefixsearch = function \(\) \{[\s\S]*?\n    \};/,
    )?.[0];

    expect(switchPrefixsearch).toMatch(
      /autocomplete\([\s\S]*?searchControlState\(searchOptionsFromForm\(document\)\)\.autocomplete[\s\S]*?\)/,
    );
  });

  it('restores a deep-linked norm search', () => {
    const document = loadPage('vis/bwnorm/index.html');

    expect(inlineSourceOf(document)).toMatch(
      /restoreSearchFromLocation\(\s*document\s*,\s*window\.location\.search\s*,\s*'norm'\s*\)/,
    );
  });

  it('loads the existing search script after its dependencies', () => {
    const document = loadPage('vis/bwnorm/index.html');
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );
    const searchSource = sources.find((source) => source.endsWith('js/search.js'));

    expect(searchSource).toBeDefined();
    expect(fs.existsSync(path.resolve(PUBLIC_DIR, 'vis/bwnorm', searchSource))).toBe(true);
    expect(sources.indexOf(searchSource)).toBeGreaterThan(
      sources.findIndex((source) => source.endsWith('js/datahandler.js')),
    );
    expect(sources.indexOf(searchSource)).toBeGreaterThan(
      sources.findIndex((source) => source.endsWith('js/def_language.js')),
    );
  });
});

describe('bwnorm callNormtree', () => {
  function openBwnorm() {
    const html = fs.readFileSync(path.join(PUBLIC_DIR, 'vis/bwnorm/index.html'), 'utf8');
    const dom = new JSDOM(html, {
      runScripts: 'outside-only',
      url: 'https://example.test/vis/bwnorm/index.html',
    });
    for (const script of dom.window.document.querySelectorAll('script[src]')) {
      const file = path.join(PUBLIC_DIR, 'vis/bwnorm', script.getAttribute('src'));
      dom.window.eval(fs.readFileSync(file, 'utf8'));
    }
    const inlineScripts = dom.window.document.querySelectorAll('script:not([src])');
    dom.window.eval(inlineScripts[inlineScripts.length - 2].textContent);
    return dom;
  }

  it('opens normvariation for the term in the search input', () => {
    const dom = openBwnorm();
    try {
      const opened = [];
      dom.window.open = (url) => opened.push(url);
      const input = dom.window.document.getElementById('searchinput');
      expect(input).not.toBeNull();
      input.value = ' Chóśebuz ';

      dom.window.callNormtree();

      expect(opened).toHaveLength(1);
      const target = new URL(opened[0], dom.window.location.href);
      expect(target.pathname).toBe('/vis/normvariation');
      expect(target.searchParams.get('norm')).toBe('Chóśebuz');
    } finally {
      dom.window.close();
    }
  });
});
