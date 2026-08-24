<?php

declare(strict_types=1);

namespace DsbTests;

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

    $this->pdo = new \PDO('sqlite:' . $this->tempDir . '/lemmamapping.db');
    $this->pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
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
      $this->resolve(['drjewo'], ['ci' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseInsensitiveNonAmbiguousReturnsOnlyExactCells(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|drjewo|'],
      $this->resolve(['drjewo'], ['ci' => true, 'ambig' => false, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseSensitiveNonAmbiguousReturnsExactCaseOnly(): void
  {
    $this->assertSame(
      ['|drjewo|'],
      $this->resolve(['drjewo'], ['ci' => false, 'ambig' => false, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseSensitiveAmbiguousExpandsOnlyTheExactCasePart(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['DRJEWO'], ['ci' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsCaseInsensitiveHandlesLowerSorbianCasing(): void
  {
    $this->assertSame(
      ['|DRĚŚ|DRJEWO|'],
      $this->resolve(['drěś'], ['ci' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsRespectsPipeBoundaries(): void
  {
    $this->assertNotContains(
      '|DRJEWOWY|',
      $this->resolve(['DRJEWO'], ['ci' => false, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsUnmatchedTermReturnsEmptyList(): void
  {
    $this->assertSame(
      [],
      $this->resolve(['NJEEKSISTUJO'], ['ci' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsSqlInjectionTextReturnsEmptyList(): void
  {
    $this->assertSame(
      [],
      $this->resolve(['" OR 1=1 -- '], ['ci' => true, 'ambig' => true, 'regex' => false]),
    );
  }

  public function testResolveCellsListFindsEveryCaseInsensitiveNonAmbiguousTerm(): void
  {
    $options = ['list' => true, 'trim' => true, 'ci' => true, 'ambig' => false, 'regex' => false];
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
      $this->resolve(['DRJEWO?'], ['ci' => false, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsCaseSensitiveRegexExpandsEveryMatchingPart(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['DR.*'], ['ci' => false, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsCaseInsensitiveRegexMatchesUpperAndLowerCaseParts(): void
  {
    $this->assertSame(
      ['|DRJEWO|', '|drjewo|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|'],
      $this->resolve(['dr.*o'], ['ci' => true, 'ambig' => true, 'regex' => true]),
    );
  }

  public function testResolveCellsListOfRegexesResolvesEveryPatternInOneCall(): void
  {
    $options = ['list' => true, 'trim' => true, 'ci' => false, 'ambig' => true, 'regex' => true];
    $terms = split_terms('DR.*O;TE.', $options);

    $this->assertSame(
      ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|DRĚŚ|DRJEWO|', '|TEJ|'],
      $this->resolve($terms, $options),
    );
  }

  public function testResolveCellsRegexDisabledTreatsMetacharactersLiterally(): void
  {
    $this->assertSame(
      [],
      $this->resolve(['DR.*O'], ['ci' => false, 'ambig' => true, 'regex' => false]),
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
      $results = $this->resolve(['('], ['ci' => false, 'ambig' => true, 'regex' => true]);
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

    $results = $this->resolve(['.*'], ['ci' => false, 'ambig' => true, 'regex' => true]);
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

  private function insertRows(string $table, array $values): void
  {
    $statement = $this->pdo->prepare(
      "INSERT INTO {$table} (lemma, frequency, sortkey) VALUES (:lemma, :frequency, :sortkey)",
    );

    foreach ($values as $index => $value) {
      $statement->execute([
        'lemma' => $value,
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
}
