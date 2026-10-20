// Shared helpers for the browser-frontend tests. Keep this file dependency-light:
// jsdom is the only devDependency the suite is allowed to rely on.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { JSDOM } = require('jsdom');

const PUBLIC_DIR = path.join(__dirname, '..', '..', 'public');

// Globals a public/js file may touch at load time. Saved and restored per test.
const DOM_GLOBALS = ['window', 'document', 'location', 'navigator', 'XMLHttpRequest', 'fetch'];

/**
 * Install a fresh jsdom window as globals so that global-scope scripts can be loaded.
 * Always call `restore()` (e.g. in a `finally` or `t.after`) — globals leak otherwise.
 */
function withDom({
  html = '<!doctype html><body></body>',
  url = 'http://localhost/vis/test/',
} = {}) {
  const dom = new JSDOM(html, { url });
  const saved = {};

  for (const name of DOM_GLOBALS) {
    saved[name] = globalThis[name];
    globalThis[name] = name === 'window' ? dom.window : dom.window[name];
  }

  return {
    window: dom.window,
    document: dom.window.document,
    restore() {
      for (const name of DOM_GLOBALS) {
        if (saved[name] === undefined) {
          delete globalThis[name];
        } else {
          globalThis[name] = saved[name];
        }
      }
      dom.window.close();
    },
  };
}

/** Load a file from public/js/ fresh (no module cache), returning its test-hook exports. */
function loadScript(name) {
  const file = path.join(PUBLIC_DIR, 'js', name);
  delete require.cache[require.resolve(file)];
  return require(file);
}

/** Parse a public/ HTML page WITHOUT executing its scripts. Returns the jsdom document. */
function loadPage(relPath) {
  const file = path.join(PUBLIC_DIR, relPath);
  const dom = new JSDOM(fs.readFileSync(file, 'utf8'), { url: 'http://localhost/' + relPath });
  return dom.window.document;
}

/**
 * Strict expected-failure test for a known, unfixed bug (node:test has no xfail;
 * its built-in `todo` silently tolerates a pass and therefore rots like `skip`).
 *
 * `fn` asserts the CORRECT behavior. The test passes while the bug is present and
 * fails loudly the moment the bug is fixed, forcing the marker to be removed.
 */
function knownBug(name, reason, fn) {
  test(name + ' [BUG: ' + reason + ']', async () => {
    let stillBroken = false;
    try {
      await fn();
    } catch (err) {
      // Only a failed assertion counts as "still broken"; typos and load errors must surface.
      if (err instanceof assert.AssertionError) {
        stillBroken = true;
      } else {
        throw err;
      }
    }

    assert.ok(
      stillBroken,
      'XPASS: "' +
        reason +
        '" no longer reproduces. Drop knownBug() and keep this as a plain test().',
    );
  });
}

module.exports = { PUBLIC_DIR, withDom, loadScript, loadPage, knownBug };
