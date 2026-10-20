<?php

declare(strict_types=1);

namespace DsbTests;

use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class DsbCollationTest extends TestCase
{
  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
  }

  public function testSortkeyOrdersLowerSorbianSpecificLettersAfterTheirBaseLetter(): void
  {
    $this->assertLessThan(dsb_sortkey('Č'), dsb_sortkey('C'));
    $this->assertLessThan(dsb_sortkey('Ć'), dsb_sortkey('Č'));
    $this->assertLessThan(dsb_sortkey('L'), dsb_sortkey('Ł'));
  }

  public function testSortkeyIsCaseInsensitive(): void
  {
    $this->assertSame(dsb_sortkey('woda'), dsb_sortkey('WODA'));
  }

  public function testSortkeyUsesTwoDigitGroupsSoPrefixesSortFirst(): void
  {
    $this->assertSame(8, strlen(dsb_sortkey('WODA')));
    $this->assertLessThan(dsb_sortkey('WODA'), dsb_sortkey('WOD'));
  }

  public function testSortkeyPushesUnknownCharactersToTheEnd(): void
  {
    $this->assertLessThan(dsb_sortkey('-'), dsb_sortkey('Ž'));
  }
}
