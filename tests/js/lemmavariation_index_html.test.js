const fs = require('node:fs');
const path = require('node:path');

const { PUBLIC_DIR, loadPage, withDom, loadScript } = require('./helpers');

function inlineSourceOf(document) {
  return [...document.querySelectorAll('script:not([src])')]
    .map((script) => script.textContent)
    .join('\n');
}

describe('vis/lemmavariation/index.html', () => {
  it('opens dolnoserbski.de through the shared URL builder', () => {
    const source = inlineSourceOf(loadPage('vis/lemmavariation/index.html'));

    expect(source).toContain('dolnoserbskiUrl(');
    expect(source).not.toContain("slownik?wuraz=' +");
  });

  it('has one search text input and removes the legacy search inputs', () => {
    const document = loadPage('vis/lemmavariation/index.html');

    expect([...document.querySelectorAll('input[type="text"]')].map((input) => input.id)).toEqual([
      'searchinput',
    ]);
    for (const id of ['lemma', 'lemmalist', 'lemmaregex']) {
      expect(document.getElementById(id)).toBeNull();
    }
  });

  it('provides all search option checkboxes with the intended defaults', () => {
    const document = loadPage('vis/lemmavariation/index.html');
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
    const document = loadPage('vis/lemmavariation/index.html');
    const checkbox = document.getElementById('prefixsearchCheckBox');

    expect(checkbox?.getAttribute('type')).toBe('checkbox');
    expect(checkbox.hasAttribute('checked')).toBe(false);
    expect(checkbox.closest('label')).not.toBeNull();
  });

  it('provides a dynamic example placeholder', () => {
    const document = loadPage('vis/lemmavariation/index.html');

    expect(document.getElementById('searchexample')).not.toBeNull();
    expect(document.documentElement.textContent).not.toContain('MŁYŃSKI,KRABAT');
  });

  it('loads search.js after datahandler.js and def_language.js', () => {
    const document = loadPage('vis/lemmavariation/index.html');
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );
    const searchSource = sources.find((source) => source.endsWith('js/search.js'));

    expect(searchSource).toBeDefined();
    expect(fs.existsSync(path.resolve(PUBLIC_DIR, 'vis/lemmavariation', searchSource))).toBe(true);
    for (const dependency of ['js/datahandler.js', 'js/def_language.js']) {
      expect(sources.indexOf(searchSource)).toBeGreaterThan(
        sources.findIndex((source) => source.endsWith(dependency)),
      );
    }
  });

  it('restores lemma searches through the shared helper without inferring lists from commas', () => {
    const source = inlineSourceOf(loadPage('vis/lemmavariation/index.html'));

    expect(source).toMatch(
      /restoreSearchFromLocation\(\s*document\s*,\s*window\.location\.search\s*,\s*['"]lemma['"]\s*\)/,
    );
    expect(source).not.toMatch(/curlemma\.includes\(\s*['"],['"]\s*\)/);
  });

  it('restores a legacy comma link as one literal in the actual search form', () => {
    const page = loadPage('vis/lemmavariation/index.html');
    const dom = withDom({ html: page.documentElement.outerHTML });
    try {
      const { restoreSearchFromLocation } = loadScript('search.js');
      expect(dom.document.getElementById('searchinput')).not.toBeNull();

      restoreSearchFromLocation(dom.document, '?lemma=DRJEWO,BOM', 'lemma');

      expect(dom.document.getElementById('searchinput').value).toBe('DRJEWO,BOM');
      expect(dom.document.getElementById('listCheckBox').checked).toBe(false);
    } finally {
      dom.restore();
    }
  });

  it('uses one tree URL builder instead of separate list and regex search paths', () => {
    const source = inlineSourceOf(loadPage('vis/lemmavariation/index.html'));

    expect(source).toMatch(/buildTreeUrls\(\s*['"]lemma['"]\s*,/);
    expect(source).not.toMatch(/\bupdateTreeFrom(?:List|Regex)\b/);
    expect(source).not.toContain('lemmatokenregex.php');
  });
});
