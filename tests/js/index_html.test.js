const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { PUBLIC_DIR, loadPage } = require('./helpers');

test('index.html references only local script files that exist', () => {
  const document = loadPage('index.html');

  const sources = [...document.querySelectorAll('script[src]')].map((el) => el.getAttribute('src'));

  assert.ok(sources.length > 0);
  for (const src of sources.filter((s) => !/^https?:\/\//.test(s))) {
    assert.ok(fs.existsSync(path.join(PUBLIC_DIR, src)), 'missing script: ' + src);
  }
});

test('index.html loads def_language.js before my_language.js so overrides win', () => {
  const document = loadPage('index.html');

  const sources = [...document.querySelectorAll('script[src]')].map((el) => el.getAttribute('src'));

  assert.ok(sources.indexOf('js/def_language.js') < sources.indexOf('js/my_language.js'));
});
