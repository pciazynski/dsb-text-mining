<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class PrefixnormsearchEndpointTest extends TestCase
{
  private const NONAMBIGUOUS_ROWS = [
    ['|Chóśebuzu|', 16208],
    ['|Chóśebuza|', 4741],
    ['|chóśebuske|', 1910],
    ['|Chylu|', 1837],
    ['|chwaliś|', 1798],
    ['|Chóta|', 123],
    ['|chyta|', 132],
  ];

  private const AMBIGUOUS_ROWS = [
    ['|Chóta|chyta|', 120],
  ];

  private const CUTOFF_ROWS = [
    ['|Chóśebuzu|', 16208],
    ['|Chóśebuza|', 4741],
    ['|Chóśebuzom|', 22],
  ];

  private const BYTE_CUTOFF_ROWS = [
    ['|chóśebuskeg|', 712],
    ['|chóśebuski|', 681],
    ['|chóśebuskem|', 394],
  ];

  private DevServer $server;

  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
  }

  protected function setUp(): void
  {
    $this->server = DevServer::boot();

    $db = $this->server->dataDir() . '/normmapping.db';
    @unlink($db);
    $pdo = FixtureDb::open($db);
    $this->createFixture($pdo);
  }

  public function testMissingSortbyUsesFrequencyOrdering(): void
  {
    $default = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3&limit=30');
    $frequency = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&limit=30&sortby=frequency',
    );
    $expected = ['Chóśebuzu', 'Chóśebuza', 'chóśebuske', 'Chóta'];

    $this->assertSuggestions($expected, $frequency);
    $this->assertSuggestions($expected, $default);
    $this->assertSame($frequency['body'], $default['body']);
  }

  public function testDefaultSearchIsCaseInsensitiveAndReturnsPlainText(): void
  {
    $response = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3');

    $this->assertSame(200, $response['status']);
    $this->assertSuggestions(['Chóśebuzu', 'Chóśebuza', 'chóśebuske', 'Chóta'], $response);
    $this->assertTrue($this->hasContentType($response['headers'], 'text/plain'));
  }

  public function testAlphabetSortUsesLowerSorbianAlphabetOrder(): void
  {
    $response = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&sortby=alphabet',
    );

    $this->assertSuggestions(['chóśebuske', 'Chóśebuza', 'Chóśebuzu', 'Chóta'], $response);
  }

  public function testCaseSensitiveSearchReturnsOnlyMatchingCase(): void
  {
    $response = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3&cs=1');

    $this->assertSuggestions(['chóśebuske'], $response);
  }

  public function testCaseInsensitiveSearchIncludesUppercaseInitial(): void
  {
    $response = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3&cs=0');

    $this->assertSuggestions(['Chóśebuzu', 'Chóśebuza', 'chóśebuske', 'Chóta'], $response);
  }

  public function testSorbianPrefixIsMatchedCaseInsensitively(): void
  {
    $response = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3%C5%9B');

    $this->assertSuggestions(['Chóśebuzu', 'Chóśebuza', 'chóśebuske'], $response);
  }

  public function testAmbigParameterDoesNotSwitchAwayFromNormnonambig(): void
  {
    $withoutAmbig = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3');
    $withAmbig = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3&ambig=1');

    $expected = ['Chóśebuzu', 'Chóśebuza', 'chóśebuske', 'Chóta'];
    $this->assertSuggestions($expected, $withoutAmbig);
    $this->assertSuggestions($expected, $withAmbig);
    $this->assertSame($withoutAmbig['body'], $withAmbig['body']);
  }

  public function testUnknownSortbyFallsBackToFrequencyOrdering(): void
  {
    $response = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&sortby=unknown',
    );

    $this->assertSuggestions(['Chóśebuzu', 'Chóśebuza', 'chóśebuske', 'Chóta'], $response);
  }

  public function testInjectedSortbyFallsBackToFrequencyAndLeavesTableIntact(): void
  {
    $payload = urlencode('frequency; DROP TABLE normnonambig --');
    $expected = ['Chóśebuzu', 'Chóśebuza', 'chóśebuske', 'Chóta'];

    $injected = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&sortby=' . $payload,
    );
    $second = $this->server->get('/php/prefixnormsearch.php?norm=ch%C3%B3');

    $this->assertSuggestions($expected, $injected);
    $this->assertSuggestions($expected, $second);
  }

  public function testLimitIsAppliedAsAnInteger(): void
  {
    $response = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&sortby=frequency&limit=2',
    );

    $this->assertSuggestions(['Chóśebuzu', 'Chóśebuza'], $response);
  }

  public function testCutoffReturnsAtMostOneSuggestionPerCharacterPrefixGroup(): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/normmapping.db');
    $this->replaceChóFixture($pdo, self::CUTOFF_ROWS);

    $response = $this->server->get(
      '/php/prefixnormsearch.php?norm=Ch%C3%B3&cs=1&cutoff=2&limit=20',
    );

    $this->assertSame(200, $response['status']);
    $suggestions = $this->suggestions($response['body']);
    $this->assertSame(1, count($suggestions));
    $this->assertContains($suggestions[0], ['Chóśebuzu', 'Chóśebuza', 'Chóśebuzom']);
  }

  public function testCutoffGroupsByCharactersAfterAMultibytePrefix(): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/normmapping.db');
    $this->replaceChóFixture($pdo, self::CUTOFF_ROWS);

    $response = $this->server->get(
      '/php/prefixnormsearch.php?norm=Ch%C3%B3%C5%9Bebu&cs=1&cutoff=2&limit=20',
    );

    $this->assertSame(200, $response['status']);
    $suggestions = $this->suggestions($response['body']);
    $this->assertSame(3, count($suggestions));
    foreach ($suggestions as $suggestion) {
      $this->assertContains($suggestion, ['Chóśebuzu', 'Chóśebuza', 'Chóśebuzom']);
    }
  }

  public function testCutoffCountsCharactersInsteadOfUtf8Bytes(): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/normmapping.db');
    $this->replaceChóFixture($pdo, self::BYTE_CUTOFF_ROWS);

    $response = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3%C5%9Bebu&cs=1&cutoff=2&limit=20',
    );

    $this->assertSame(200, $response['status']);
    $suggestions = $this->suggestions($response['body']);
    $this->assertSame(1, count($suggestions));
    $this->assertContains($suggestions[0], ['chóśebuskeg', 'chóśebuski', 'chóśebuskem']);
  }

  public function testNonnumericCutoffIsIgnoredWithoutServerError(): void
  {
    $baseline = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&sortby=frequency',
    );
    $invalid = $this->server->get(
      '/php/prefixnormsearch.php?norm=ch%C3%B3&sortby=frequency&cutoff=invalid',
    );

    $this->assertSame(200, $invalid['status']);
    $this->assertSame($baseline['body'], $invalid['body']);
  }

  public function testNoMatchesReturnsEmptyBodyWithoutNewline(): void
  {
    $response = $this->server->get('/php/prefixnormsearch.php?norm=xyz');

    $this->assertSame(200, $response['status']);
    $this->assertSuggestions([], $response);
  }

  public function testMissingAndEmptyNormReturnEmptyBody(): void
  {
    $missing = $this->server->get('/php/prefixnormsearch.php');
    $empty = $this->server->get('/php/prefixnormsearch.php?norm=');

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
        'cs=0, sortby=' . $sortby => [
          $this->explainPrefixQuery($pdo, 'sortkey', dsb_sortkey('chó'), $order),
          'normnonambigsortkey',
        ],
        'cs=1, sortby=' . $sortby => [
          $this->explainPrefixQuery($pdo, 'norm', '|chó', $order),
          'normnonambignorm',
        ],
      ];

      foreach ($plans as $scenario => [$plan, $index]) {
        $message = $scenario . PHP_EOL . $plan;
        $this->assertStringContainsString('SEARCH', $plan, $message);
        $this->assertStringContainsString('USING INDEX ' . $index, $plan, $message);
        $this->assertStringNotContainsString('SCAN normnonambig', $plan, $message);
      }
    }
  }

  private function createFixture(\PDO $pdo): void
  {
    $pdo->exec('CREATE TABLE normnonambig (norm TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE normfrequency (norm TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE INDEX normnonambignorm ON normnonambig(norm)');
    $pdo->exec('CREATE INDEX normnonambigsortkey ON normnonambig(sortkey)');

    foreach (self::NONAMBIGUOUS_ROWS as [$norm, $frequency]) {
      $this->insertRow($pdo, 'normnonambig', $norm, $frequency);
      $this->insertRow($pdo, 'normfrequency', $norm, $frequency);
    }
    foreach (self::AMBIGUOUS_ROWS as [$norm, $frequency]) {
      $this->insertRow($pdo, 'normfrequency', $norm, $frequency);
    }
  }

  private function insertRow(\PDO $pdo, string $table, string $norm, int $frequency): void
  {
    $statement = $pdo->prepare(
      "INSERT INTO {$table} (norm, frequency, sortkey) VALUES (:norm, :frequency, :sortkey)",
    );
    $statement->execute([
      'norm' => $norm,
      'frequency' => $frequency,
      'sortkey' => dsb_sortkey(trim($norm, '|')),
    ]);
  }

  private function replaceChóFixture(\PDO $pdo, array $rows): void
  {
    foreach (['normnonambig', 'normfrequency'] as $table) {
      $pdo->exec("DELETE FROM {$table} WHERE norm LIKE '|Chó%'");
    }

    foreach ($rows as [$norm, $frequency]) {
      $this->insertRow($pdo, 'normnonambig', $norm, $frequency);
      $this->insertRow($pdo, 'normfrequency', $norm, $frequency);
    }
  }

  private function assertSuggestions(array $expected, array $response): void
  {
    $this->assertSame(200, $response['status']);
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
      "EXPLAIN QUERY PLAN SELECT norm FROM normnonambig
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
