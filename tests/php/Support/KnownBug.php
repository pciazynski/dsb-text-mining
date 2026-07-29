<?php

declare(strict_types=1);

namespace DsbTests\Support;

use PHPUnit\Framework\ExpectationFailedException;

/**
 * Strict expected-failure support for known, unfixed bugs.
 *
 * PHPUnit has no xfail, and markTestIncomplete()/markTestSkipped() rot silently:
 * they stay green forever, including after the bug is fixed. This reproduces
 * pytest's xfail(strict=True) instead.
 */
trait KnownBug
{
  /**
   * Run assertions describing the CORRECT behavior of a known-broken code path.
   *
   * Passes while the bug reproduces; fails loudly once it no longer does, forcing
   * the marker to be removed. Only assertion failures count as "still broken" —
   * a typo or fatal error still fails the test.
   */
  protected function assertStillBroken(string $reason, callable $assertions): void
  {
    try {
      $assertions();
    } catch (ExpectationFailedException) {
      $this->addToAssertionCount(1);

      return;
    }

    $this->fail(
      'XPASS: "' . $reason . '" no longer reproduces. '
        . 'Drop assertStillBroken() and keep the assertions as a plain test.',
    );
  }
}
