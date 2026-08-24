<?php

declare(strict_types=1);

namespace DsbTests;

use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class SearchFilterTest extends TestCase
{
  public static function setUpBeforeClass(): void
  {
    $file = dirname(__DIR__, 2) . '/public/php/searchfilter.php';

    if (is_file($file)) {
      require_once $file;
    }
  }

  public function testSearchOptionsEmptyInputReturnsDefaults(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => true],
      $this->searchOptions([]),
    );
  }

  public function testSearchOptionsFalseValuesTurnFlagsOff(): void
  {
    $this->assertSame(
      ['ci' => false, 'regex' => false, 'list' => false, 'trim' => false, 'ambig' => false],
      $this->searchOptions(['ci' => '0', 'regex' => '', 'list' => 'false', 'trim' => '0', 'ambig' => 'false']),
    );
  }

  public function testSearchOptionsBareValueTurnsFlagOff(): void
  {
    $this->assertSame(
      ['ci' => false, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => true],
      $this->searchOptions(['ci' => '']),
    );
  }

  public function testSearchOptionsTrueValuesTurnFlagsOn(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => true, 'list' => true, 'trim' => true, 'ambig' => true],
      $this->searchOptions(['ci' => '1', 'regex' => 'true', 'list' => '1', 'trim' => 'true', 'ambig' => '1']),
    );
  }

  public function testSearchOptionsExactOneTurnsAmbigOff(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => false],
      $this->searchOptions(['exact' => '1']),
    );
  }

  public function testSearchOptionsExactZeroTurnsAmbigOn(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => true],
      $this->searchOptions(['exact' => '0']),
    );
  }

  public function testSearchOptionsExplicitAmbigOnWinsOverExact(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => true],
      $this->searchOptions(['ambig' => '1', 'exact' => '1']),
    );
  }

  public function testSearchOptionsExplicitAmbigOffWinsOverExact(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => false],
      $this->searchOptions(['ambig' => '0', 'exact' => '0']),
    );
  }

  public function testSearchOptionsGarbageValuesFallBackToDefaults(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => true],
      $this->searchOptions([
        'ci' => 'garbage',
        'regex' => 'garbage',
        'list' => 'garbage',
        'trim' => 'garbage',
        'ambig' => 'garbage',
      ]),
    );
  }

  public function testSearchOptionsUnknownParametersAreIgnored(): void
  {
    $this->assertSame(
      ['ci' => true, 'regex' => false, 'list' => false, 'trim' => true, 'ambig' => true],
      $this->searchOptions(['unknown' => '1']),
    );
  }

  public function testSplitTermsListOffPreservesTheWholeString(): void
  {
    $this->assertSame(
      ['/^drjewo,tej$/;alternatiwa'],
      $this->splitTerms('/^drjewo,tej$/;alternatiwa', ['list' => false, 'trim' => true]),
    );
  }

  public function testSplitTermsListOnSplitsSemicolonAndLegacyCommaSeparators(): void
  {
    $this->assertSame(
      ['drjewo', 'tej'],
      $this->splitTerms('drjewo;tej', ['list' => true, 'trim' => true]),
    );
    $this->assertSame(
      ['drjewo', 'tej'],
      $this->splitTerms('drjewo,tej', ['list' => true, 'trim' => true]),
    );
  }

  public function testSplitTermsTrimOnStripsSurroundingWhitespaceFromEachTerm(): void
  {
    $this->assertSame(
      ['drjewo', 'tej'],
      $this->splitTerms('drjewo, tej', ['list' => true, 'trim' => true]),
    );
  }

  public function testSplitTermsTrimOnPreservesInternalSpaces(): void
  {
    $this->assertSame(
      ['NJEBYŚ LI'],
      $this->splitTerms(' NJEBYŚ LI ', ['list' => true, 'trim' => true]),
    );
  }

  public function testSplitTermsTrimOffPreservesSurroundingWhitespace(): void
  {
    $this->assertSame(
      ['drjewo', ' tej'],
      $this->splitTerms('drjewo, tej', ['list' => true, 'trim' => false]),
    );
  }

  public function testSplitTermsDropsEmptyTerms(): void
  {
    $this->assertSame(
      ['a', 'b'],
      $this->splitTerms('a;;b;', ['list' => true, 'trim' => true]),
    );
  }

  public function testSplitTermsAllWhitespaceReturnsNoTerms(): void
  {
    $this->assertSame(
      [],
      $this->splitTerms(" \t\n ", ['list' => true, 'trim' => true]),
    );
  }

  public function testSplitTermsTrimOnStripsUnicodeNonBreakingSpaces(): void
  {
    $this->assertSame(
      ['drjewo'],
      $this->splitTerms("\u{00A0}drjewo\u{00A0}", ['list' => true, 'trim' => true]),
    );
  }

  public function testCompileTermPatternCaseSensitiveRegexIsFullyAnchored(): void
  {
    $this->assertCompileTermPatternExists();

    $options = ['regex' => true, 'ci' => false];

    $this->assertSame(1, preg_match(compile_term_pattern('TE(J|N)', $options), 'TEJ'));
    $this->assertSame(1, preg_match(compile_term_pattern('TE(J|N)', $options), 'TEN'));
    $this->assertSame(0, preg_match(compile_term_pattern('TE(J|N)', $options), 'tej'));
    $this->assertSame(0, preg_match(compile_term_pattern('TE(J|N)', $options), 'XTEJ'));
  }

  public function testCompileTermPatternCaseInsensitiveRegexUsesUnicodeCasing(): void
  {
    $this->assertCompileTermPatternExists();

    $options = ['regex' => true, 'ci' => true];

    $this->assertSame(1, preg_match(compile_term_pattern('TE(J|N)', $options), 'tej'));
    $this->assertSame(1, preg_match(compile_term_pattern('TE(J|N)', $options), 'Tej'));
    $this->assertSame(1, preg_match(compile_term_pattern('ŚĚŠ', $options), 'śěš'));
  }

  public function testCompileTermPatternNeutralizesDelimiterInjection(): void
  {
    $this->assertCompileTermPatternExists();

    $options = ['regex' => true, 'ci' => false];

    foreach (['a/i', 'a#x', 'a}'] as $term) {
      $pattern = compile_term_pattern($term, $options);

      if ($pattern !== null) {
        $this->assertSame(1, preg_match($pattern, $term));
      } else {
        $this->assertNull($pattern);
      }
    }
  }

  public function testCompileTermPatternInvalidRegexReturnsNull(): void
  {
    $this->assertCompileTermPatternExists();

    $options = ['regex' => true, 'ci' => false];

    $this->assertNull(compile_term_pattern('(', $options));
    $this->assertNull(compile_term_pattern('a{2,1}', $options));
  }

  public function testCompileTermPatternRegexOffReturnsNull(): void
  {
    $this->assertCompileTermPatternExists();

    $this->assertNull(compile_term_pattern('TE(J|N)', ['regex' => false, 'ci' => true]));
  }

  public function testInClauseThreeCellsReturnsPlaceholdersAndOrderedParams(): void
  {
    $this->assertSame(
      ['sql' => 'lemma IN (?,?,?)', 'params' => ['woda', '|bom|boma|', 'źěło']],
      $this->inClause('lemma', ['woda', '|bom|boma|', 'źěło']),
    );
  }

  public function testInClauseEmptyCellsReturnsNeverTrueClause(): void
  {
    $this->assertSame(
      ['sql' => '1=0', 'params' => []],
      $this->inClause('lemma', []),
    );
  }

  public function testInClauseAcceptsWhitelistedColumns(): void
  {
    foreach (['lemma', 'norm', 'token', 'lemmabag', 'normbag'] as $column) {
      $this->assertSame(
        ['sql' => "$column IN (?)", 'params' => ['woda']],
        $this->inClause($column, ['woda']),
      );
    }
  }

  public function testInClauseRejectsColumnOutsideWhitelist(): void
  {
    $this->assertTrue(function_exists('in_clause'), 'in_clause() must be defined');
    $this->expectException(\InvalidArgumentException::class);

    in_clause('lemma) OR 1=1 --', ['woda']);
  }

  private function searchOptions(array $get): array
  {
    $this->assertTrue(function_exists('search_options'), 'search_options() must be defined');

    return search_options($get);
  }

  private function splitTerms(string $raw, array $opts): array
  {
    $this->assertTrue(function_exists('split_terms'), 'split_terms() must be defined');

    return split_terms($raw, $opts);
  }

  private function assertCompileTermPatternExists(): void
  {
    $this->assertTrue(function_exists('compile_term_pattern'), 'compile_term_pattern() must be defined');
  }

  private function inClause(string $column, array $cells): array
  {
    $this->assertTrue(function_exists('in_clause'), 'in_clause() must be defined');

    return in_clause($column, $cells);
  }
}
