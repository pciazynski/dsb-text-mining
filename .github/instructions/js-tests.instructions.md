---
description: 'Use these guidelines when generating or updating JavaScript and HTML tests.'
applyTo: 'tests/js/**'
---

# JavaScript / HTML tests (dsb-text-mining)

## Setup & layout

- Run: `npm test`; single file: `npx jest tests/js/config.test.js`. Runner is Jest with explicit jsdom instances from `tests/js/helpers.js`; do not add Vitest, Testing Library, Sinon, or another test framework.
- Tests are CommonJS `tests/js/<subject>.test.js` (no `"type"` in package.json).
- The frontend has no build step and no modules: `public/js/*.js` declare globals loaded via `<script src>`. Never add `import`/`export` there.
- Reuse `tests/js/helpers.js` before writing new helpers:
  - `withDom({ html, url })` — fresh jsdom globals (`window`/`document`/`location`/`XMLHttpRequest`/`fetch`); returns `{ window, document, restore }`. **Always `restore()` in a `finally`** or globals leak across tests.
  - `loadScript('config.js')` — loads a `public/js/` file fresh (clears require cache), returns its test-hook exports. Call it inside `withDom` (files touch `document` at load time).
  - `loadPage('index.html')` — parses a `public/` HTML page without executing scripts; returns the `document`.
  - `PUBLIC_DIR` — absolute path to `public/` for asset-existence checks.

## Exposing production code to tests

Append a guarded footer at the very bottom of the `public/js/` file — nothing else changes; browsers are unaffected (`module` is undefined there):

```js
// Test hook only. Browsers load this file via <script src>, where `module` is undefined.
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getColor, stringToColour };
}
```

- One footer per file; export only what tests need. Never restructure, wrap in an IIFE, or modularize a file to make it testable.
- Don't export symbols declared inside conditional blocks (e.g. the `if (typeof Plotly !== 'undefined')` section of config.js) — they're `undefined` at test load.

## Conventions

- Group tests by subject with `describe('functionName', ...)`; write behavior-only `it(...)` descriptions so the combined Jest name reads naturally, e.g. `describe('splitTerms', ...)` plus `it('drops empty terms', ...)`.
- Use Jest's global `expect`; do not import `node:assert`. Prefer `toBe` for primitives, `toEqual` for objects/arrays, `toMatch` for patterns, and specific numeric matchers such as `toBeGreaterThan`.
- One observable behavior per test; Arrange-Act-Assert with blank lines; happy path first, then edge cases.
- Tests are order-independent (own DOM, reloaded scripts) and must fail via assertion, never a load/`require` error. Run new tests before finishing.
- Assert exact results where cheap (full strings and `toEqual` on arrays/objects), not just `includes` or partial truthiness.

## HTML tests

- jsdom-only; no browser, no Playwright, no screenshots. `loadPage` does not execute scripts — test what a static parse proves: local `script[src]`/`link[href]`/`img[src]` targets exist under `PUBLIC_DIR`; required script order (e.g. `def_language.js` before `my_language.js`); structure/ids that `gui.js` queries.
- For inline-script or DOM-building behavior, call the function from its `public/js/` file inside `withDom` instead of running the page.

## Test doubles

- Test behavior (inputs → return values, DOM produced, URL built), never call sequences.
- Fake ONLY at boundaries: network (`globalThis.fetch`/`XMLHttpRequest`), time (`Date`), `location` (pass `url` to `withDom`). Never mock repo code. No real network requests — not to `phpurl`, not to `ctsurl`; stub and assert the URL built.

## Known, unfixed bugs

- Jest's `it.todo` and `it.skip` do not fail when a bug is fixed, so never use them for known bugs.
- Use `knownBug(name, bugDescription, fn)` from `tests/js/helpers.js` (pytest-style strict xfail): write Jest expectations for the CORRECT behavior; it passes while the expectation fails and fails loudly (XPASS) once fixed. Only Jest matcher failures are swallowed, so typos, missing files, and runtime errors still fail.
- Files: `tests/js/<subject>.regressions.test.js`.
