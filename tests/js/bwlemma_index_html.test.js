const fs = require('node:fs');
const path = require('node:path');

const { PUBLIC_DIR, loadPage } = require('./helpers');

describe('vis/bwlemma/index.html', () => {
  it('has one search text input and removes the legacy search inputs', () => {
    const document = loadPage('vis/bwlemma/index.html');

    const textInputs = [...document.querySelectorAll('input[type="text"]')];

    expect(textInputs.map((input) => input.id)).toEqual(['searchinput']);
    expect(document.querySelector('#lemma')).toBeNull();
    expect(document.querySelector('#regexsearch')).toBeNull();
    expect(document.querySelector('#lemmalist')).toBeNull();
  });

  it('provides all search option checkboxes with the intended defaults', () => {
    const document = loadPage('vis/bwlemma/index.html');

    const expectedDefaults = {
      ciCheckBox: true,
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

  it('keeps alphabetical sorting off by default', () => {
    const document = loadPage('vis/bwlemma/index.html');

    const checkbox = document.querySelector('#prefixsearchCheckBox');

    expect(checkbox?.getAttribute('type')).toBe('checkbox');
    expect(checkbox.hasAttribute('checked')).toBe(false);
  });

  it('loads the existing search script after its dependencies', () => {
    const document = loadPage('vis/bwlemma/index.html');
    const sources = [...document.querySelectorAll('script[src]')].map((script) =>
      script.getAttribute('src'),
    );
    const searchSource = sources.find((source) => source.endsWith('js/search.js'));

    expect(searchSource).toBeDefined();
    expect(fs.existsSync(path.resolve(PUBLIC_DIR, 'vis/bwlemma', searchSource))).toBe(true);
    expect(sources.indexOf(searchSource)).toBeGreaterThan(
      sources.findIndex((source) => source.endsWith('js/datahandler.js')),
    );
    expect(sources.indexOf(searchSource)).toBeGreaterThan(
      sources.findIndex((source) => source.endsWith('js/def_language.js')),
    );
  });

  it('defines globals for every search option label', () => {
    const languageSource = fs.readFileSync(path.join(PUBLIC_DIR, 'js/def_language.js'), 'utf8');
    const globals = [
      'lang_search_casesensitive',
      'lang_search_regex',
      'lang_search_list',
      'lang_search_trim',
      'lang_search_ambig',
    ];

    for (const globalName of globals) {
      expect(languageSource).toMatch(new RegExp(`\\bvar\\s+${globalName}\\s*=`));
    }
  });
});
