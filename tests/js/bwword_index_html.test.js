const fs = require('node:fs');
const path = require('node:path');

const { PUBLIC_DIR, loadPage } = require('./helpers');

function inlineSourceOf(document) {
  return [...document.querySelectorAll('script:not([src])')]
    .map((script) => script.textContent)
    .join('\n');
}

describe('vis/bwword/index.html', () => {
  it('uses one search input and removes legacy inputs and ambiguity controls', () => {
    const document = loadPage('vis/bwword/index.html');
    const textInputs = [...document.querySelectorAll('input[type="text"]')];

    expect(textInputs.map((input) => input.id)).toEqual(['searchinput']);
    expect(document.querySelector('#wordinput')).toBeNull();
    expect(document.querySelector('#regexsearch')).toBeNull();
    expect(document.querySelector('#wordlist')).toBeNull();
    expect(document.querySelector('#ambigCheckBox')).toBeNull();
    expect(document.querySelector('#ambigSearchButton')).toBeNull();
  });

  it('restores token searches from both token and legacy word links', () => {
    const document = loadPage('vis/bwword/index.html');

    expect(inlineSourceOf(document)).toMatch(
      /restoreSearchFromLocation\(\s*document\s*,\s*window\.location\.search\s*,\s*['"]token['"]\s*\)/,
    );
  });

  it('loads js/search.js for deep-link restoration', () => {
    const document = loadPage('vis/bwword/index.html');
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );
    const searchSource = sources.find((source) => source.endsWith('js/search.js'));

    expect(searchSource).toBeDefined();
    expect(fs.existsSync(path.resolve(PUBLIC_DIR, 'vis/bwword', searchSource))).toBe(true);
    expect(sources.indexOf(searchSource)).toBeGreaterThan(
      sources.findIndex((source) => source.endsWith('js/datahandler.js')),
    );
  });

  it('sets both visualization frames from the shared token URL builder', () => {
    const document = loadPage('vis/bwword/index.html');
    const updateTimeline = inlineSourceOf(document).match(
      /var updateTimeline = function \(\) \{[\s\S]*?\n    \};/,
    )?.[0];

    expect(updateTimeline).toMatch(/buildVisUrls\(\s*['"]token['"]\s*,/);
    expect(updateTimeline).toMatch(/getElementById\(['"]timeline['"]\)\.src\s*=\s*\w+\.timeline/);
    expect(updateTimeline).toMatch(/getElementById\(['"]wordinfo['"]\)\.src\s*=\s*\w+\.wordinfo/);
  });
});

describe('legacy token links', () => {
  it.each([
    'vis/bwword/wordinfo.html',
    'vis/lemmavariation/datalist.html',
    'vis/normvariation/datalist.html',
  ])('%s continues to use the word query alias', (page) => {
    const document = loadPage(page);

    expect(inlineSourceOf(document)).toContain('?word=');
  });
});

describe('vis/normvariation/datalist.html', () => {
  it('builds bwword links without a stray quote in the word query', () => {
    const document = loadPage('vis/normvariation/datalist.html');
    const source = inlineSourceOf(document);

    expect(source).toContain("?word=' +");
    expect(source).not.toContain('?word="\'');
  });
});
