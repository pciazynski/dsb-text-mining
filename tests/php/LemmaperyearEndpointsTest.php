<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class LemmaperyearEndpointsTest extends TestCase
{
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
    $pdo->exec('CREATE TABLE tokenlemmatypesubtypedatefrequency (token TEXT, lemma TEXT, type TEXT, subtype TEXT, date TEXT, frequency INTEGER)');
    $pdo->exec('CREATE TABLE lemmafrequency (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE lemmanonambig (lemma TEXT, frequency INTEGER, sortkey TEXT)');

    $rows = [
      ['dṙewo', '|DRJEWO|', '1880', 6],
      ['drjewo', '|DRJEWO|', '1880', 2],
      ['drjewa', '|DRJEWO|', '1881', 5],
      ['drjewje', '|DRJEWO|DRJEWOWY|', '1880', 2],
      ['tej', '|TEJ|', '1881', 1],
      ['drjewo', '|drjewo|', '1880', 4],
      ['wóda', '|WÓDA|', '1881', 7],
    ];
    $statement = $pdo->prepare(
      'INSERT INTO tokenlemmatypesubtypedatefrequency VALUES (:token, :lemma, "", "", :date, :frequency)',
    );
    foreach ($rows as [$token, $lemma, $date, $frequency]) {
      $statement->execute(compact('token', 'lemma', 'date', 'frequency'));
    }

    $this->insertLemmaRows($pdo, 'lemmafrequency', [
      '|DRJEWO|' => 13,
      '|DRJEWO|DRJEWOWY|' => 2,
      '|TEJ|' => 1,
      '|drjewo|' => 4,
      '|WÓDA|' => 7,
    ]);
    $this->insertLemmaRows($pdo, 'lemmanonambig', [
      '|DRJEWO|' => 13,
      '|DRJEWOWY|' => 2,
      '|TEJ|' => 1,
      '|drjewo|' => 4,
      '|WÓDA|' => 7,
    ]);
  }

  public static function endpoints(): array
  {
    return [
      'count per year' => ['lemmacountperyear.php', false],
      'sum per year' => ['lemmasumperyear.php', true],
    ];
  }

  #[DataProvider('endpoints')]
  public function testDefaultReturnsCaseInsensitiveAmbiguousRows(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=drjewo');

    $this->assertResponse($response, $summed ? [
      ['|DRJEWO|', '1880', 8],
      ['|DRJEWO|', '1881', 5],
      ['|DRJEWO|DRJEWOWY|', '1880', 2],
      ['|drjewo|', '1880', 4],
    ] : [
      ['|DRJEWO|', '1880', 6, 'dṙewo'],
      ['|DRJEWO|', '1880', 2, 'drjewo'],
      ['|DRJEWO|', '1881', 5, 'drjewa'],
      ['|DRJEWO|DRJEWOWY|', '1880', 2, 'drjewje'],
      ['|drjewo|', '1880', 4, 'drjewo'],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testAmbigDisabledReturnsOnlyUnambiguousCells(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=drjewo&ambig=0');

    $this->assertResponse($response, $summed ? [
      ['|DRJEWO|', '1880', 8],
      ['|DRJEWO|', '1881', 5],
      ['|drjewo|', '1880', 4],
    ] : [
      ['|DRJEWO|', '1880', 6, 'dṙewo'],
      ['|DRJEWO|', '1880', 2, 'drjewo'],
      ['|DRJEWO|', '1881', 5, 'drjewa'],
      ['|drjewo|', '1880', 4, 'drjewo'],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testCaseInsensitiveDisabledReturnsOnlyExactCase(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=drjewo&ci=0');

    $this->assertResponse($response, [
      $summed
        ? ['|drjewo|', '1880', 4]
        : ['|drjewo|', '1880', 4, 'drjewo'],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testListReturnsRowsForEveryTrimmedTerm(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=drjewo%2C%20tej&list=1');

    $this->assertResponse($response, $this->listRows($summed));
  }

  #[DataProvider('endpoints')]
  public function testListWithoutSpaceReturnsRowsForBothTerms(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=drjewo,tej&list=1');

    $this->assertResponse($response, $this->listRows($summed));
  }

  #[DataProvider('endpoints')]
  public function testRegexReturnsMatchingRows(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=dr.*o&regex=1');

    $this->assertResponse($response, $summed ? [
      ['|DRJEWO|', '1880', 8],
      ['|DRJEWO|', '1881', 5],
      ['|DRJEWO|DRJEWOWY|', '1880', 2],
      ['|drjewo|', '1880', 4],
    ] : [
      ['|DRJEWO|', '1880', 6, 'dṙewo'],
      ['|DRJEWO|', '1880', 2, 'drjewo'],
      ['|DRJEWO|', '1881', 5, 'drjewa'],
      ['|DRJEWO|DRJEWOWY|', '1880', 2, 'drjewje'],
      ['|drjewo|', '1880', 4, 'drjewo'],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testLegacyExactFlagMatchesOnlyUnambiguousCells(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?lemma=drjewo&exact=1');

    $this->assertResponse($response, $summed ? [
      ['|DRJEWO|', '1880', 8],
      ['|DRJEWO|', '1881', 5],
      ['|drjewo|', '1880', 4],
    ] : [
      ['|DRJEWO|', '1880', 6, 'dṙewo'],
      ['|DRJEWO|', '1880', 2, 'drjewo'],
      ['|DRJEWO|', '1881', 5, 'drjewa'],
      ['|drjewo|', '1880', 4, 'drjewo'],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testMissingLemmaReturnsEmptyBody(string $endpoint, bool $summed): void
  {
    $response = $this->server->get('/php/' . $endpoint);

    $this->assertResponse($response, []);
  }

  #[DataProvider('endpoints')]
  public function testSqlInjectionTextReturnsEmptyBody(string $endpoint, bool $summed): void
  {
    $payload = urlencode('woda" OR "1"="1');

    $response = $this->server->get('/php/' . $endpoint . '?lemma=' . $payload);

    $this->assertResponse($response, []);
  }

  private function assertResponse(array $response, array $rows): void
  {
    $this->assertSame(200, $response['status']);
    $this->assertSame($this->body($rows), $response['body']);
    $this->assertMatchesRegularExpression(
      '/^Content-Type:\s*text\/plain/im',
      implode(PHP_EOL, $response['headers']),
    );
  }

  private function body(array $rows): string
  {
    if ($rows === []) {
      return '';
    }

    return implode(PHP_EOL, array_map(
      static fn(array $row): string => implode(chr(9), $row),
      $rows,
    )) . PHP_EOL;
  }

  private function listRows(bool $summed): array
  {
    return $summed ? [
      ['|DRJEWO|', '1880', 8],
      ['|DRJEWO|', '1881', 5],
      ['|DRJEWO|DRJEWOWY|', '1880', 2],
      ['|TEJ|', '1881', 1],
      ['|drjewo|', '1880', 4],
    ] : [
      ['|DRJEWO|', '1880', 6, 'dṙewo'],
      ['|DRJEWO|', '1880', 2, 'drjewo'],
      ['|DRJEWO|', '1881', 5, 'drjewa'],
      ['|DRJEWO|DRJEWOWY|', '1880', 2, 'drjewje'],
      ['|TEJ|', '1881', 1, 'tej'],
      ['|drjewo|', '1880', 4, 'drjewo'],
    ];
  }

  private function insertLemmaRows(\PDO $pdo, string $table, array $rows): void
  {
    $statement = $pdo->prepare(
      "INSERT INTO {$table} (lemma, frequency, sortkey) VALUES (:lemma, :frequency, :sortkey)",
    );
    foreach ($rows as $lemma => $frequency) {
      $statement->execute([
        'lemma' => $lemma,
        'frequency' => $frequency,
        'sortkey' => dsb_sortkey(trim($lemma, '|')),
      ]);
    }
  }
}
