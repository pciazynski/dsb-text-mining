const fs = require('node:fs');
const path = require('node:path');

const { PUBLIC_DIR, loadPage } = require('./helpers');

describe('index.html', () => {
  it('references only local script files that exist', () => {
    const document = loadPage('index.html');

    const sources = [...document.querySelectorAll('script[src]')].map((el) =>
      el.getAttribute('src'),
    );

    expect(sources.length).toBeGreaterThan(0);
    for (const src of sources.filter((s) => !/^https?:\/\//.test(s))) {
      expect(fs.existsSync(path.join(PUBLIC_DIR, src))).toBe(true);
    }
  });

  it('loads def_language.js before my_language.js so overrides win', () => {
    const document = loadPage('index.html');

    const sources = [...document.querySelectorAll('script[src]')].map((el) =>
      el.getAttribute('src'),
    );

    expect(sources.indexOf('js/def_language.js')).toBeLessThan(
      sources.indexOf('js/my_language.js'),
    );
  });
});
