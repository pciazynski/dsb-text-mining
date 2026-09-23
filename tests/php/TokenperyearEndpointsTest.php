<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class TokenperyearEndpointsTest extends TestCase
{
  private DevServer $server;

  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
  }

  protected function setUp(): void
  {
    $this->server = DevServer::boot();

    foreach (['lemma', 'norm'] as $column) {
      $db = $this->server->dataDir() . '/' . $column . 'mapping.db';
      @unlink($db);
      $pdo = FixtureDb::open($db);
      $pdo->exec("CREATE TABLE token{$column}typesubtypedatefrequency (token TEXT, {$column} TEXT, type TEXT, subtype TEXT, date TEXT, frequency INTEGER)");
      $pdo->exec("CREATE TABLE {$column}frequency ({$column} TEXT, frequency INTEGER, sortkey TEXT)");
      $pdo->exec("CREATE TABLE {$column}nonambig ({$column} TEXT, frequency INTEGER, sortkey TEXT)");

      $rows = [
        ['drjewo', '|DRJEWO|', '1870', 3],
        ['drjewo', '|DRJEWO|', '1880', 2],
        ['drjewa', '|DRJEWO|', '1881', 7],
        ['drjewje', '|DRJEWO|DRJEWOWY|', '1880', 4],
        ['drjewo', '|drjewo|', '1870', 1],
        ['tej', '|TEJ|', '1880', 6],
        ['drjewo', '|DRĚŚ|DRJEWO|', '1870', 5],
      ];
      $insert = $pdo->prepare(
        "INSERT INTO token{$column}typesubtypedatefrequency VALUES (:token, :cell, 'type', 'subtype', :date, :frequency)",
      );
      foreach ($rows as [$token, $cell, $date, $frequency]) {
        $insert->execute(compact('token', 'cell', 'date', 'frequency'));
      }

      foreach (['frequency', 'nonambig'] as $suffix) {
        $insertCell = $pdo->prepare(
          "INSERT INTO {$column}{$suffix} VALUES (:cell, 1, :sortkey)",
        );
        $cells = $suffix === 'frequency'
          ? ['|DRJEWO|', '|DRJEWO|DRJEWOWY|', '|drjewo|', '|TEJ|', '|DRĚŚ|DRJEWO|']
          : ['|DRJEWO|', '|DRJEWOWY|', '|drjewo|', '|TEJ|', '|DRĚŚ|'];
        foreach ($cells as $cell) {
          $insertCell->execute(['cell' => $cell, 'sortkey' => dsb_sortkey(trim($cell, '|'))]);
        }
      }
    }
  }

  public static function endpoints(): array
  {
    return [
      'lemma' => ['lemmatokenperyear.php', 'lemma'],
      'norm' => ['normtokenperyear.php', 'norm'],
    ];
  }

  #[DataProvider('endpoints')]
  public function testRangeIncludesBothEndpointsButNotTheFollowingYear(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'DRJEWO', '&cs=1&ambig=0&sort&year=1870-1880');

    $this->assertResponse($response, [
      ['|DRJEWO|', 'drjewo', 5],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testSingleYearRestrictsResults(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'DRJEWO', '&cs=1&ambig=0&sort&year=1870');

    $this->assertResponse($response, [
      ['|DRJEWO|', 'drjewo', 3],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testMissingYearReturnsUnfilteredRows(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'DRJEWO', '&cs=1&ambig=0&sort');

    $this->assertResponse($response, [
      ['|DRJEWO|', 'drjewa', 7],
      ['|DRJEWO|', 'drjewo', 5],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testSqlShapedYearsReturnEmptyBodies(string $endpoint, string $column): void
  {
    foreach (['BETWEEN 1 AND 2 OR 1=1', '> 0 OR 1=1 --'] as $year) {
      $response = $this->request($endpoint, $column, 'DRJEWO', '&year=' . urlencode($year));

      $this->assertResponse($response, []);
    }
  }

  #[DataProvider('endpoints')]
  public function testDefaultSearchFindsCaseInsensitiveAmbiguousCells(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'drjewo', '&sort&year=1880');

    $this->assertResponse($response, [
      ['|DRJEWO|DRJEWOWY|', 'drjewje', 4],
      ['|DRJEWO|', 'drjewo', 2],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testCaseSensitiveAndNonambiguousFlagsExcludeOtherCells(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'drjewo', '&cs=1&ambig=0&sort&year=1870-1880');

    $this->assertResponse($response, [
      ['|drjewo|', 'drjewo', 1],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testAmbigDisabledKeepsBothCaseVariants(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'drjewo', '&ambig=0&sort&year=1870-1880');

    $this->assertResponse($response, [
      ['|DRJEWO|', 'drjewo', 5],
      ['|drjewo|', 'drjewo', 1],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testListAndTrimFlagsResolveBothTerms(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, ' DRJEWO, TEJ ', '&cs=1&list=1&trim=1&ambig=0&sort&year=1880');

    $this->assertResponse($response, [
      ['|TEJ|', 'tej', 6],
      ['|DRJEWO|', 'drjewo', 2],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testRegexFlagResolvesMatchingCells(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'DRJEW.*', '&cs=1&regex=1&ambig=0&sort&year=1880');

    $this->assertResponse($response, [
      ['|DRJEWO|', 'drjewo', 2],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testRegexLookingTermWithoutFlagReturnsNothing(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'DRJEW.*', '&cs=1&regex=0&year=1880');

    $this->assertResponse($response, []);
  }

  #[DataProvider('endpoints')]
  public function testAllFiveFlagsTogetherResolveAListOfRegexes(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, ' DRJEW.*; TEJ ', '&regex=1&list=1&trim=1&cs=1&ambig=0&sort&year=1880');

    $this->assertResponse($response, [
      ['|TEJ|', 'tej', 6],
      ['|DRJEWO|', 'drjewo', 2],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testLegacyExactFlagUsesNonambiguousCells(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'drjewo', '&exact=1&sort&year=1870-1880');

    $this->assertResponse($response, [
      ['|DRJEWO|', 'drjewo', 5],
      ['|drjewo|', 'drjewo', 1],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testClickedWholeCellReturnsItsYearlyTokens(string $endpoint, string $column): void
  {
    $response = $this->request(
      $endpoint,
      $column,
      'DRĚŚ|DRJEWO',
      '&cs=1&regex=0&list=0&trim=1&ambig=0&sort&year=1870-1880',
    );

    $this->assertResponse($response, [
      ['|DRĚŚ|DRJEWO|', 'drjewo', 5],
    ]);
  }

  #[DataProvider('endpoints')]
  public function testSqlInjectionInTermReturnsEmptyBody(string $endpoint, string $column): void
  {
    $response = $this->request($endpoint, $column, 'x" OR "1"="1', '&year=1870-1880');

    $this->assertResponse($response, []);
  }

  #[DataProvider('endpoints')]
  public function testMissingTermReturnsEmptyBody(string $endpoint, string $column): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?year=1870-1880');

    $this->assertResponse($response, []);
  }

  public function testToken2normPreservesExistingTokenResult(): void
  {
    $response = $this->server->get('/php/token2norm.php?token=drjewo');

    $this->assertResponse($response, [
      ['drjewo', '|DRJEWO|', 'type', 'subtype'],
      ['drjewo', '|drjewo|', 'type', 'subtype'],
      ['drjewo', '|DRĚŚ|DRJEWO|', 'type', 'subtype'],
    ]);
  }

  public function testToken2normSqlInjectionReturnsEmptyBody(): void
  {
    $response = $this->server->get('/php/token2norm.php?token=' . urlencode('x" OR "1"="1'));

    $this->assertResponse($response, []);
  }

  private function request(string $endpoint, string $column, string $term, string $flags): array
  {
    return $this->server->get('/php/' . $endpoint . '?' . $column . '=' . rawurlencode($term) . $flags);
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
}
