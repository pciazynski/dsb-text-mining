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

    expect(document.querySelector('#csCheckBox').getAttribute('onchange')).toBe(
      'switchPrefixsearch()',
    );
  });

  it.each(['regexCheckBox', 'listCheckBox'])(
    'updates prefix-search availability when %s changes',
    (id) => {
      const document = loadPage('vis/bwlemma/index.html');
      const onchange = document.querySelector(`#${id}`).getAttribute('onchange');

      expect(onchange).toBe('switchSearchOptions()');
    },
  );

  it('groups alphabetical sorting with its text so both can be greyed out', () => {
    const document = loadPage('vis/bwlemma/index.html');

    const checkbox = document.querySelector('#prefixsearchCheckBox');

    expect(checkbox?.getAttribute('type')).toBe('checkbox');
    expect(checkbox.hasAttribute('checked')).toBe(false);
    expect(checkbox.closest('label')).not.toBeNull();
  });

  it('initializes autocomplete case-insensitively when case sensitivity is unchecked', () => {
    const document = loadPage('vis/bwlemma/index.html');
    const initialization = [...document.querySelectorAll('script:not([src])')]
      .map((script) => script.textContent)
      .find((source) => source.includes("autocomplete(\n            'searchinput'"));

    expect(document.querySelector('#csCheckBox').checked).toBe(false);
    expect(initialization).toContain('&cs=0&lemma=');
  });

  it('passes the current mode state when refreshing autocomplete', () => {
    const document = loadPage('vis/bwlemma/index.html');
    const inlineSource = [...document.querySelectorAll('script:not([src])')]
      .map((script) => script.textContent)
      .join('\n');
    const switchPrefixsearch = inlineSource.match(
      /var switchPrefixsearch = function \(\) \{[\s\S]*?\n    \};/,
    )?.[0];

    expect(switchPrefixsearch).toMatch(
      /autocomplete\([\s\S]*?searchControlState\(searchOptionsFromForm\(document\)\)\.autocomplete[\s\S]*?\)/,
    );
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
