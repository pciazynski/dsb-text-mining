---
description: 'Use these guidelines when generating or updating PHP tests.'
applyTo: 'tests/php/**'
---

# PHP tests (dsb-text-mining)

## Setup & layout

- Run: `composer test` (fresh checkout: `composer install` first). Single test: `vendor/bin/phpunit --filter testReturnsEmptyBody`.
- PHPUnit 11, configured by phpunit.xml. Root composer.json exists **only** for the test harness — the app has no Composer deps or autoloader. No runtime packages; no namespaces/`use` in `public/php/`.
- Tests: `tests/php/<Subject>Test.php`, namespace `DsbTests`, `final class ... extends TestCase`, tabs for indentation.
- Helpers in `tests/php/Support/` — reuse before writing new ones:
  - `DevServer::boot()` — built-in PHP server, once per run, against an isolated **copy** of `public/php/` in a temp dir.
    - `->get('/php/lemmatoken.php?lemma=woda')` → `['status' => int, 'body' => string, 'headers' => string[]]`.
    - `->dataDir()` — the throwaway dir endpoints see as `../data/`; seed fixture SQLite files there with plain `PDO`.
  - `KnownBug` trait — `assertStillBroken()`, see below.

## Two kinds of test

1. **Unit tests** for includable pure functions (dsb_collation.php): `require_once` in `setUpBeforeClass()`, call directly. Prefer this whenever reachable without HTTP.
2. **HTTP smoke tests** via `DevServer` for the `$_GET` endpoint scripts (top-level procedural, print to stdout). Never `include` an endpoint with hand-set `$_GET` + `ob_start()`: it skips headers/routing and a second `include` silently no-ops.

## Endpoint smoke tests

- Never point a test at the real `public/data/` — `DevServer` isolates; keep it that way. Seed the smallest SQLite fixture (2-4 rows) in `setUp()`.
- Assert the **exact** body (`assertSame("|woda|\twoda\t5\n...", ...)`; tab-separated, newline-terminated plain text), the status code, and `Content-Type` when set.
- Per endpoint cover: happy path, missing/empty required param, and `exact=0` vs `exact=1` where it applies.
- Some endpoints concatenate `$_GET` into SQL. Use benign fixture tokens; pin the injection bug with the known-bug marker, never assert it as correct.

## Conventions

- One behavior per test; names `test<Unit><Scenario><Expected>`; Arrange-Act-Assert with blank lines; happy path first, then edge cases.
- Tests are order-independent: seed your own fixture DB in `setUp()` (`DevServer` is shared, its data dir is not).
- Tests must fail via assertion, never a fatal/include error. Run new tests before finishing.
- `assertSame` over `assertEquals`; assert exact full bodies and row counts, not membership.

## Test doubles

- Test behavior (query string in → status/headers/body out), never call sequences.
- Fake ONLY at boundaries: HTTP (`DevServer`) and filesystem/DB (temp dir + real SQLite). Never a mocked PDO, no mocking library, never mock repo code, no real network.

## Known, unfixed bugs

- PHPUnit has no xfail; `markTestIncomplete()`/`markTestSkipped()` rot silently — never use for bugs. Use the `KnownBug` trait, wrapping assertions for the CORRECT behavior:

```php
use DsbTests\Support\KnownBug;

$this->assertStillBroken('lemma parameter is concatenated into SQL', function (): void {
    $response = $this->server->get('/php/lemmatoken.php?lemma=' . urlencode('woda" OR "1"="1'));
    $this->assertSame('', $response['body']);
});
```

- Passes while the bug reproduces, fails loudly (XPASS) once fixed — remove the marker then. Only assertion failures are swallowed.
- Files: `tests/php/<Subject>RegressionsTest.php`.
