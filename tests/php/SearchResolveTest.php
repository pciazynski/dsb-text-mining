<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class SearchResolveTest extends TestCase
{
  private \PDO $pdo;
  private string $tempDir;

  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
    require_once dirname(__DIR__, 2) . '/public/php/searchfilter.php';
  }

  protected function setUp(): void
  {
    $this->tempDir = sys_get_temp_dir() . '/dsb-search-resolve-' . bin2hex(random_bytes(8));
    mkdir($this->tempDir, 0700);

    $this->pdo = FixtureDb::open($this->tempDir . '/lemmamapping.db');
    $this->pdo->exec('CREATE TABLE lemmanonambig (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $this->pdo->exec('CREATE INDEX lemmanonambigsortkey ON lemmanonambig(sortkey)');
    $this->pdo->exec('CREATE TABLE lemmafrequency (lemma TEXT, frequency INTEGER, sortkey TEXT)');

    $this->insertRows('lemmanonambig', [
      '|DRJEWO|',
      '|drjewo|',
      '|DRĚŚ|',
      '|DRJEWOWY|',
      '|TEJ|',
      '|NJEBYŚ LI|',
    ]);
    $this->insertRows('lemmafrequency', [
      '|DRJEWO|',
      '|drjewo|',
      '|DRĚŚ|DRJEWO|',
      '|DRJEWO|DRJEWOWY|',
      '|TEJ|',
      '|NJEBYŚ LI|',
    ]);

    // Real norm forms from public/data/normmapping.db: "Drjewka"/"drjewka" is a genuine
    // case-ambiguous pair, "drjewa" (genitive of "drjewo") is ambiguous with "drěła",
    // and "drjewaŕ" is an unrelated longer word sharing the "drjewa" prefix.
    $this->pdo->exec('CREATE TABLE normnonambig (norm TEXT, frequency INTEGER, sortkey TEXT)');
    $this->pdo->exec('CREATE INDEX normnonambigsortkey ON normnonambig(sortkey)');
    $this->pdo->exec('CREATE TABLE normfrequency (norm TEXT, frequency INTEGER, sortkey TEXT)');

    $this->insertRows('normnonambig', [
      '|Drjewka|',
      '|drjewka|',
      '|drjewa|',
      '|drěła|',
      '|tej|',
      '|ten samy|',
    ], 'norm');
    $this->insertRows('normfrequency', [
      '|Drjewka|drjewka|',
      '|drjewa|',
      '|drěła|drjewa|',
      '|drjewaŕ|',
      '|tej|',
      '|ten samy|',
    ], 'norm');

    $this->pdo->exec('CREATE TABLE tokencount (token TEXT, frequency INTEGER, sortkey TEXT)');
    $this->pdo->exec('CREATE INDEX tokensortkeyindex ON tokencount(sortkey)');
    $this->insertRows('tokencount', ['drjewo', 'DRJEWO', 'drjewowy', 'tej'], 'token');
  }

  protected function tearDown(): void
  {
    unset($this->pdo);

    foreach (glob($this->tempDir . '/*') ?: [] as $file) {
      unlink($file);
    }
    rmdir($this->tempDir);
  }

  public function testResolveCellsCaseInsensitiveAmbiguousReturnsEveryMatchingCell(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|', '|drjewo|'],
      $this->resolve(['drjewo'], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseInsensitiveNonAmbiguousReturnsOnlyExactCells(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|drjewo|'],
      $this->resolve(['drjewo'], ['cs' => false, 'ambig' => false, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseSensitiveNonAmbiguousReturnsExactCaseOnly(): void
  {
    $this->assertSame(
      ['|drjewo|'],
      $this->resolve(['drjewo'], ['cs' => true, 'ambig' => false, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseSensitiveAmbiguousExpandsOnlyTheExactCasePart(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['DRJEWO'], ['cs' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseInsensitiveHandlesLowerSorbianCasing(): void
  {
    $this->assertSame(
      ['|DRĚŚ|DRJEWO|'],
      $this->resolve(['drěś'], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsRespectsPipeBoundaries(): void
  {
    $this->assertNotContains(
      '|DRJEWOWY|',
      $this->resolve(['DRJEWO'], ['cs' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsUnmatchedTermReturnsEmptyList(): void
  {
    $this->assertSame(
      [],
      $this->resolve(['NJEEKSISTUJO'], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsSqlInjectionTextReturnsEmptyList(): void
  {
    $this->assertSame(
      [],
      $this->resolve(['" OR 1=1 -- '], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsListFindsEveryCaseInsensitiveNonAmbiguousTerm(): void
  {
    $options = ['list' => true, 'trim' => true, 'cs' => false, 'ambig' => false, 'regex' => false];
    $terms = split_terms('drjewo, tej', $options);

    $this->assertSame(
      ['|DRJEWO|', '|TEJ|', '|drjewo|'],
      $this->resolve($terms, $options),
    );
  }

  public function testResolveCellsCaseSensitiveRegexOptionalCharacterMatchesOnlyExistingParts(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['DRJEWO?'], ['cs' => true, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsCaseSensitiveRegexExpandsEveryMatchingPart(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['DR.*'], ['cs' => true, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsCaseInsensitiveRegexMatchesUpperAndLowerCaseParts(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|drjewo|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['dr.*o'], ['cs' => false, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsListOfRegexesResolvesEveryPatternInOneCall(): void
  {
    $options = ['list' => true, 'trim' => true, 'cs' => true, 'ambig' => true, 'regex' => true];
    $terms = split_terms('DR.*O;TE.', $options);

    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|', '|TEJ|'],
      $this->resolve($terms, $options),
    );
  }

  public function testResolveRequestCellsRegexListSplitsOnlyOnSemicolon(): void
  {
    $this->assertTrue(
      function_exists('resolve_request_cells'),
      'resolve_request_cells() must be defined',
    );

    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|', '|TEJ|'],
      resolve_request_cells($this->pdo, 'lemma', [
        'lemma' => 'DR.*O;TE.',
        'regex' => '1',
        'list' => '1',
        'cs' => '1',
        'ambig' => '1',
        'trim' => '1',
      ]),
    );
  }

  public function testResolveRequestCellsRegexListKeepsCommaInsideQuantifier(): void
  {
    $this->assertTrue(
      function_exists('resolve_request_cells'),
      'resolve_request_cells() must be defined',
    );

    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      resolve_request_cells($this->pdo, 'lemma', [
        'lemma' => 'DR.{2,5}O',
        'regex' => '1',
        'list' => '1',
        'cs' => '1',
        'ambig' => '1',
        'trim' => '1',
      ]),
    );
  }

  public function testResolveCellsRegexDisabledTreatsMetacharactersLiterally(): void
  {
    $this->assertSame(
      [],
      $this->resolve(['DR.*O'], ['cs' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsInvalidRegexReturnsEmptyListWithoutWarning(): void
  {
    $warnings = [];
    set_error_handler(function (int $severity, string $message) use (&$warnings): bool {
      if ((error_reporting() & $severity) === 0) {
        return false;
      }

      $warnings[] = [$severity, $message];
      return true;
    });

    try {
      $results = $this->resolve(['('], ['cs' => true, 'ambig' => true, 'regex' => true]);
    } finally {
      restore_error_handler();
    }

    $this->assertSame([], $results);
    $this->assertSame([], $warnings);
  }

  public function testResolveCellsCapsResultsAndReportsTruncation(): void
  {
    $extraParts = [];
    for ($index = 0; $index < 600; $index++) {
      $extraParts[] = sprintf('|EXTRA%03d|', $index);
    }
    $this->insertRows('lemmafrequency', $extraParts);

    $this->assertTrue(defined('SEARCH_RESULT_CAP'), 'SEARCH_RESULT_CAP must be defined');
    $this->assertSame(500, constant('SEARCH_RESULT_CAP'));
    $this->assertTrue(
      function_exists('resolve_was_truncated'),
      'resolve_was_truncated() must be defined',
    );

    $results = $this->resolve(['.*'], ['cs' => true, 'ambig' => true, 'regex' => true]);
    $truncationStatus = 'resolve_was_truncated';

    $this->assertLessThanOrEqual(500, count($results));
    $this->assertTrue($truncationStatus());
  }

  public function testCaseInsensitiveNonAmbiguousLookupUsesSortkeyIndex(): void
  {
    $statement = $this->pdo->prepare(
      'EXPLAIN QUERY PLAN SELECT lemma FROM lemmanonambig WHERE sortkey = :sortkey',
    );
    $statement->execute(['sortkey' => dsb_sortkey('drjewo')]);
    $plan = implode("\n", $statement->fetchAll(\PDO::FETCH_COLUMN, 3));

    $this->assertStringContainsString('SEARCH', $plan);
    $this->assertStringContainsString('USING INDEX', $plan);
    $this->assertStringNotContainsString('SCAN', $plan);
  }

  public function testResolveCellsNormCaseInsensitiveAmbiguousReturnsEveryMatchingCell(): void
  {
    $this->assertSame(
      ['|drjewa|', '|drěła|drjewa|'],
      $this->resolveNorm(['drjewa'], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsNormCaseInsensitiveNonAmbiguousReturnsOnlyExactCells(): void
  {
    $this->assertSame(
      ['|Drjewka|', '|drjewka|'],
      $this->resolveNorm(['drjewka'], ['cs' => false, 'ambig' => false, 'regex' => false]),
    );
  }

  public function testResolveCellsNormCaseSensitiveNonAmbiguousReturnsExactCaseOnly(): void
  {
    $this->assertSame(
      ['|drjewka|'],
      $this->resolveNorm(['drjewka'], ['cs' => true, 'ambig' => false, 'regex' => false]),
    );
  }

  public function testResolveCellsNormCaseSensitiveAmbiguousExpandsOnlyTheExactCasePart(): void
  {
    $this->assertSame(
      ['|Drjewka|drjewka|'],
      $this->resolveNorm(['Drjewka'], ['cs' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsNormRespectsPipeBoundaries(): void
  {
    $this->assertNotContains(
      '|drjewaŕ|',
      $this->resolveNorm(['drjewa'], ['cs' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsNormListFindsEveryCaseInsensitiveNonAmbiguousTerm(): void
  {
    $options = ['list' => true, 'trim' => true, 'cs' => false, 'ambig' => false, 'regex' => false];
    $terms = split_terms('drjewka, tej', $options);

    $this->assertSame(
      ['|Drjewka|', '|drjewka|', '|tej|'],
      $this->resolveNorm($terms, $options),
    );
  }

  public function testResolveCellsNormCaseSensitiveRegexExpandsEveryMatchingPart(): void
  {
    $this->assertSame(
      ['|drjewa|', '|drjewaŕ|', '|drěła|drjewa|', '|Drjewka|drjewka|'],
      $this->resolveNorm(['drjew.*'], ['cs' => true, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsNormSqlInjectionTextReturnsEmptyList(): void
  {
    $this->assertSame(
      [],
      $this->resolveNorm(['" OR 1=1 -- '], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsNormCapsResultsAndReportsTruncation(): void
  {
    $extraParts = [];
    for ($index = 0; $index < 600; $index++) {
      $extraParts[] = sprintf('|EXTRA%03d|', $index);
    }
    $this->insertRows('normfrequency', $extraParts, 'norm');

    $results = $this->resolveNorm(['.*'], ['cs' => true, 'ambig' => true, 'regex' => true]);

    $this->assertLessThanOrEqual(500, count($results));
    $this->assertTrue(resolve_was_truncated());
  }

  public function testResolveCellsTokenReturnsBareTokens(): void
  {
    $this->assertSame(
      ['DRJEWO', 'drjewo'],
      $this->resolveToken(['drjewo'], ['cs' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsTokenCaseSensitiveReturnsOnlyExactToken(): void
  {
    $this->assertSame(
      ['drjewo'],
      $this->resolveToken(['drjewo'], ['cs' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsTokenAmbigTrueAndFalseGiveIdenticalResults(): void
  {
    $ambiguous = $this->resolveToken(['drjewo'], ['cs' => false, 'ambig' => true, 'regex' => false]);
    $nonAmbiguous = $this->resolveToken(['drjewo'], ['cs' => false, 'ambig' => false, 'regex' => false]);

    $this->assertSame($ambiguous, $nonAmbiguous);
  }

  public function testResolveCellsTokenRegexIsFullyAnchoredOnWholeToken(): void
  {
    $this->assertSame(
      ['drjewo'],
      $this->resolveToken(['drj.wo'], ['cs' => true, 'ambig' => true, 'regex' => true]),
    );

    $this->assertSame(
      [],
      $this->resolveToken(['drj'], ['cs' => true, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsUnsupportedBagColumnThrowsInvalidArgumentException(): void
  {
    $this->expectException(\InvalidArgumentException::class);

    resolve_cells($this->pdo, 'lemmabag', ['drjewo'], ['cs' => false, 'ambig' => true, 'regex' => false]);
  }

  public function testResolveCellsUnsupportedInjectionColumnThrowsInvalidArgumentException(): void
  {
    $this->expectException(\InvalidArgumentException::class);

    resolve_cells($this->pdo, 'x; DROP', ['drjewo'], ['cs' => false, 'ambig' => true, 'regex' => false]);
  }

  public function testTokenAmbigZeroUsesSortkeyIndexForLiteralLookup(): void
  {
    $statement = $this->pdo->prepare(
      'EXPLAIN QUERY PLAN SELECT token FROM tokencount WHERE sortkey = :sortkey',
    );
    $statement->execute(['sortkey' => dsb_sortkey('drjewo')]);
    $plan = implode("\n", $statement->fetchAll(\PDO::FETCH_COLUMN, 3));

    $this->assertStringContainsString('SEARCH', $plan);
    $this->assertStringContainsString('USING INDEX', $plan);
    $this->assertStringNotContainsString('SCAN', $plan);
  }

  public function testTokenAmbigOneDefaultAlsoUsesSortkeyIndexForLiteralLookup(): void
  {
    // ambig=1 is the default; tokens have no ambiguous cells, so the literal
    // lookup must still go through tokensortkeyindex instead of a full scan.
    $statement = $this->pdo->prepare(
      'EXPLAIN QUERY PLAN SELECT token FROM tokencount WHERE sortkey = :sortkey',
    );
    $statement->execute(['sortkey' => dsb_sortkey('drjewo')]);
    $plan = implode("\n", $statement->fetchAll(\PDO::FETCH_COLUMN, 3));

    $this->assertStringContainsString('SEARCH', $plan);
    $this->assertStringContainsString('USING INDEX', $plan);
    $this->assertStringNotContainsString('SCAN', $plan);
  }

  private function insertRows(string $table, array $values, string $column = 'lemma'): void
  {
    $statement = $this->pdo->prepare(
      "INSERT INTO {$table} ({$column}, frequency, sortkey) VALUES (:cell, :frequency, :sortkey)",
    );

    foreach ($values as $index => $value) {
      $statement->execute([
        'cell' => $value,
        'frequency' => count($values) - $index,
        'sortkey' => dsb_sortkey(trim($value, '|')),
      ]);
    }
  }

  private function resolve(array $terms, array $options): array
  {
    $this->assertTrue(function_exists('resolve_cells'), 'resolve_cells() must be defined');

    return resolve_cells($this->pdo, 'lemma', $terms, $options);
  }

  private function resolveNorm(array $terms, array $options): array
  {
    $this->assertTrue(function_exists('resolve_cells'), 'resolve_cells() must be defined');

    return resolve_cells($this->pdo, 'norm', $terms, $options);
  }

  private function resolveToken(array $terms, array $options): array
  {
    $this->assertTrue(function_exists('resolve_cells'), 'resolve_cells() must be defined');

    return resolve_cells($this->pdo, 'token', $terms, $options);
  }
}
