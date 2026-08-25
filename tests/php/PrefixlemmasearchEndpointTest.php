<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class PrefixlemmasearchEndpointTest extends TestCase
{
  private const NONAMBIGUOUS_ROWS = [
    ['|DRJEWO|', 10],
    ['|WÓDA|', 9],
    ['|PŁAŚ|', 8],
    ['|DRĚŚ|', 7],
    ['|DRĚNOW|', 6],
    ['|DRJEWOWY|', 5],
    ['|DRJAŽNIŚ|', 4],
    ['|TEJ|', 4],
    ['|DRĚMAŚ|', 3],
    ['|DRJEWKO|', 2],
    ['|NJEBYŚ LI|', 1],
    // Synthetic casing of the real WÓDA lemma, isolated to the ci=0 edge case.
    ['|wóda|', 2],
  ];

  private const AMBIGUOUS_ROWS = [
    ['|PŁAŚ|PŁAŚEŚ|PŁAŚIŚ|', 3],
  ];
  private const LIMIT_FIXTURE_PREFIX = 'LIMIT FIXTURE ';

  private DevServer $server;

  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
  }

  protected function setUp(): void
  {
    $this->server = DevServer::boot();

    $db = $this->server->dataDir() . '/lemmamapping.db';
    @unlink($db);
    $pdo = FixtureDb::open($db);
    $this->createFixture($pdo);
  }

  public function testMissingSortbyUsesFrequencyOrdering(): void
  {
    $default = $this->server->get('/php/prefixlemmasearch.php?lemma=drj&limit=30');
    $frequency = $this->server->get(
      '/php/prefixlemmasearch.php?lemma=drj&limit=30&sortby=frequency',
    );
    $expected = ['DRJEWO', 'DRJEWOWY', 'DRJAŽNIŚ', 'DRJEWKO'];

    $this->assertSuggestions($expected, $frequency);
    $this->assertSuggestions($expected, $default);
    $this->assertSame($frequency['body'], $default['body']);
  }

  public function testDefaultSearchIsCaseInsensitiveAndReturnsPlainText(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=drj&limit=30');

    $this->assertSame(200, $response['status']);
    $this->assertSuggestions(['DRJEWO', 'DRJEWOWY', 'DRJAŽNIŚ', 'DRJEWKO'], $response);
    $this->assertTrue($this->hasContentType($response['headers'], 'text/plain'));
  }

  public function testAlphabetSortUsesLowerSorbianAlphabetOrder(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=drj&sortby=alphabet');

    $this->assertSuggestions(
      ['DRJAŽNIŚ', 'DRJEWKO', 'DRJEWO', 'DRJEWOWY'],
      $response,
    );
  }

  public function testCaseSensitiveSearchReturnsOnlyMatchingCase(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=w%C3%B3&ci=0');

    $this->assertSuggestions(['wóda'], $response);
  }

  public function testCaseInsensitiveSearchIncludesLowercaseEdgeCase(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=w%C3%B3&ci=1');

    $this->assertSuggestions(['WÓDA', 'wóda'], $response);
  }

  public function testSorbianPrefixIsMatchedCaseInsensitivelyBySortkey(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=dr%C4%9B%C5%9B&ci=1');

    $this->assertSuggestions(['DRĚŚ'], $response);
  }

  public function testAmbigParameterNeverReturnsAmbiguousCells(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=p%C5%82a&ambig=1');

    $this->assertSuggestions(['PŁAŚ'], $response);
  }

  public function testUnknownSortbyFallsBackToFrequencyOrdering(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=drj&sortby=unknown');

    $this->assertSuggestions(['DRJEWO', 'DRJEWOWY', 'DRJAŽNIŚ', 'DRJEWKO'], $response);
  }

  public function testInjectedSortbyFallsBackToFrequencyAndLeavesTableIntact(): void
  {
    $payload = urlencode('frequency; DROP TABLE lemmanonambig --');
    $expected = ['DRJEWO', 'DRJEWOWY', 'DRJAŽNIŚ', 'DRJEWKO'];

    $injected = $this->server->get(
      '/php/prefixlemmasearch.php?lemma=drj&sortby=' . $payload,
    );
    $second = $this->server->get('/php/prefixlemmasearch.php?lemma=drj');

    $this->assertSuggestions($expected, $injected);
    $this->assertSuggestions($expected, $second);
  }

  public function testLimitTwoReturnsTopTwoSuggestions(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=drj&limit=2');

    $this->assertSuggestions(['DRJEWO', 'DRJEWOWY'], $response);
  }

  public function testExcessiveLimitIsCappedAtOneHundred(): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/lemmamapping.db');
    $expected = [];
    for ($index = 0; $index < 101; $index++) {
      $lemma = self::LIMIT_FIXTURE_PREFIX . sprintf('%03d', $index);
      $this->insertRow($pdo, 'lemmanonambig', '|' . $lemma . '|', 1000 - $index);
      if ($index < 100) {
        $expected[] = $lemma;
      }
    }

    $response = $this->server->get(
      '/php/prefixlemmasearch.php?lemma=limit%20fixture&limit=5000',
    );

    $this->assertSuggestions($expected, $response);
  }

  public function testMissingAndNonnumericLimitUseDefaultOfOneHundred(): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/lemmamapping.db');
    $expected = [];
    for ($index = 0; $index < 101; $index++) {
      $lemma = self::LIMIT_FIXTURE_PREFIX . sprintf('%03d', $index);
      $this->insertRow($pdo, 'lemmanonambig', '|' . $lemma . '|', 1000 - $index);
      if ($index < 100) {
        $expected[] = $lemma;
      }
    }

    $missing = $this->server->get('/php/prefixlemmasearch.php?lemma=limit%20fixture');
    $nonnumeric = $this->server->get(
      '/php/prefixlemmasearch.php?lemma=limit%20fixture&limit=invalid',
    );

    $this->assertSuggestions($expected, $missing);
    $this->assertSuggestions($expected, $nonnumeric);
  }

  public function testCutoffGroupsByCharactersAfterAMultibytePrefix(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=dr%C4%9B&cutoff=1');

    $this->assertSuggestions(['DRĚŚ'], $response);
  }

  public function testNoMatchesReturnsEmptyBodyWithoutNewline(): void
  {
    $response = $this->server->get('/php/prefixlemmasearch.php?lemma=xyz');

    $this->assertSame(200, $response['status']);
    $this->assertSuggestions([], $response);
  }

  public function testMissingAndEmptyLemmaReturnEmptyBody(): void
  {
    $missing = $this->server->get('/php/prefixlemmasearch.php');
    $empty = $this->server->get('/php/prefixlemmasearch.php?lemma=');

    $this->assertSame(200, $missing['status']);
    $this->assertSuggestions([], $missing);
    $this->assertSame(200, $empty['status']);
    $this->assertSuggestions([], $empty);
  }

  public function testPrefixQueriesUseCaseAppropriateIndexesForBothSortOrders(): void
  {
    $pdo = new \PDO('sqlite::memory:');
    $pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
    $this->createFixture($pdo);

    foreach (['alphabet' => 'sortkey ASC', 'frequency' => 'frequency DESC'] as $sortby => $order) {
      $plans = [
        'ci=1, sortby=' . $sortby => [
          $this->explainPrefixQuery($pdo, 'sortkey', dsb_sortkey('drj'), $order),
          'lemmanonambigsortkey',
        ],
        'ci=0, sortby=' . $sortby => [
          $this->explainPrefixQuery($pdo, 'lemma', '|drj', $order),
          'lemmanonambiglemma',
        ],
      ];

      foreach ($plans as $scenario => [$plan, $index]) {
        $message = $scenario . PHP_EOL . $plan;
        $this->assertStringContainsString('SEARCH', $plan, $message);
        $this->assertStringContainsString('USING INDEX ' . $index, $plan, $message);
        $this->assertStringNotContainsString('SCAN lemmanonambig', $plan, $message);
      }
    }
  }

  private function createFixture(\PDO $pdo): void
  {
    $pdo->exec('CREATE TABLE lemmanonambig (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE lemmafrequency (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE INDEX lemmanonambiglemma ON lemmanonambig(lemma)');
    $pdo->exec('CREATE INDEX lemmanonambigsortkey ON lemmanonambig(sortkey)');

    foreach (self::NONAMBIGUOUS_ROWS as [$lemma, $frequency]) {
      $this->insertRow($pdo, 'lemmanonambig', $lemma, $frequency);
      $this->insertRow($pdo, 'lemmafrequency', $lemma, $frequency);
    }
    foreach (self::AMBIGUOUS_ROWS as [$lemma, $frequency]) {
      $this->insertRow($pdo, 'lemmafrequency', $lemma, $frequency);
    }
  }

  private function insertRow(\PDO $pdo, string $table, string $lemma, int $frequency): void
  {
    $statement = $pdo->prepare(
      "INSERT INTO {$table} (lemma, frequency, sortkey) VALUES (:lemma, :frequency, :sortkey)",
    );
    $statement->execute([
      'lemma' => $lemma,
      'frequency' => $frequency,
      'sortkey' => dsb_sortkey(trim($lemma, '|')),
    ]);
  }

  private function assertSuggestions(array $expected, array $response): void
  {
    $this->assertSame($expected, $this->suggestions($response['body']));
    $expectedBody = $expected === [] ? '' : implode(PHP_EOL, $expected) . PHP_EOL;
    $this->assertSame($expectedBody, $response['body']);
  }

  private function suggestions(string $body): array
  {
    return $body === '' ? [] : explode(PHP_EOL, rtrim($body, PHP_EOL));
  }

  private function explainPrefixQuery(
    \PDO $pdo,
    string $column,
    string $prefix,
    string $order,
  ): string {
    $statement = $pdo->prepare(
      "EXPLAIN QUERY PLAN SELECT lemma FROM lemmanonambig
			WHERE {$column} >= :lower AND {$column} < :upper
			ORDER BY {$order} LIMIT 100",
    );
    $statement->execute([
      'lower' => $prefix,
      'upper' => $prefix . "\xFF",
    ]);

    return implode(PHP_EOL, $statement->fetchAll(\PDO::FETCH_COLUMN, 3));
  }

  private function hasContentType(array $headers, string $contentType): bool
  {
    foreach ($headers as $header) {
      if (stripos($header, 'Content-Type: ' . $contentType) === 0) {
        return true;
      }
    }

    return false;
  }
}
