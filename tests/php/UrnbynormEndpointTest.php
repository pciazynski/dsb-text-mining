<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class UrnbynormEndpointTest extends TestCase
{
  private DevServer $server;

  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
  }

  protected function setUp(): void
  {
    $this->server = DevServer::boot();
    $path = $this->server->dataDir() . '/normmapping.db';
    @unlink($path);
    $pdo = FixtureDb::open($path);
    $pdo->exec('CREATE TABLE urndatenormbag (urn TEXT, date TEXT, normbag TEXT)');
    $pdo->exec('CREATE TABLE normfrequency (norm TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE normnonambig (norm TEXT, frequency INTEGER, sortkey TEXT)');

    foreach (
      [
        'normfrequency' => ['|buda|', '|Buda|', '|Bóda|buda|Buda|', '|weto|', '|njejo li|'],
        'normnonambig' => ['|buda|', '|Buda|', '|Bóda|', '|weto|', '|njejo li|'],
      ] as $table => $cells
    ) {
      $statement = $pdo->prepare("INSERT INTO {$table} VALUES (?, ?, ?)");
      foreach ($cells as $cell) {
        $statement->execute([$cell, 1, dsb_sortkey(trim($cell, '|'))]);
      }
    }

    $statement = $pdo->prepare('INSERT INTO urndatenormbag VALUES (?, ?, ?)');
    foreach (
      [
        ['urn:doc:1870', '1870', '|weto||buda|'],
        ['urn:doc:1875', '1875', '|weto||Bóda|buda|Buda|'],
        ['urn:doc:1880', '1880', '|Buda|'],
        ['urn:doc:1890', '1890', '|buda|'],
        ['urn:doc:1900', '1900', '|weto|'],
        ['urn:doc:1910', '1910', '|njejo li|'],
      ] as $row
    ) {
      $statement->execute($row);
    }
  }

  public function testDefaultReturnsCaseInsensitiveAmbiguousDocuments(): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=buda&sort');

    $this->assertTextResponse($response, ['1870', '1875', '1880', '1890']);
  }

  public function testCaseInsensitiveSearchDoesNotMatchLongSDocuments(): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/normmapping.db');
    foreach (['normfrequency', 'normnonambig'] as $table) {
      $statement = $pdo->prepare("INSERT INTO {$table} VALUES (?, ?, ?)");
      foreach (['|str.|', '|ſtr.|'] as $cell) {
        $statement->execute([$cell, 1, dsb_sortkey(trim($cell, '|'))]);
      }
    }
    $statement = $pdo->prepare('INSERT INTO urndatenormbag VALUES (?, ?, ?)');
    $statement->execute(['urn:doc:1920', '1920', '|ſtr.|']);
    $statement->execute(['urn:doc:1930', '1930', '|str.|']);

    $response = $this->server->get('/php/urnbynorm.php?norm=str.');

    $this->assertTextResponse($response, ['1930']);
  }

  public function testAmbigDisabledReturnsOnlyUnambiguousCells(): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=buda&ambig=0&sort');

    $this->assertTextResponse($response, ['1870', '1880', '1890']);
  }

  public function testCaseSensitiveReturnsOnlyMatchingCase(): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=buda&cs=1&sort');

    $this->assertTextResponse($response, ['1870', '1875', '1890']);
  }

  public function testBwnormExactCellRequestReturnsMatchingDocuments(): void
  {
    $response = $this->server->get(
      '/php/urnbynorm.php?norm=buda&cs=1&regex=0&list=0&trim=1&ambig=0&year=1870-1880',
    );

    $this->assertTextResponse($response, ['1870']);
  }

  public function testWholeCellRequestDoesNotMatchIndividualParts(): void
  {
    $response = $this->server->get(
      '/php/urnbynorm.php?norm=' . urlencode('Bóda|buda|Buda')
        . '&cs=1&regex=0&list=0&trim=1&ambig=0&sort',
    );

    $this->assertTextResponse($response, ['1875']);
  }

  public function testListReturnsDocumentsForBothSemicolonSeparatedTerms(): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=buda%3Bweto&list=1&sort');

    $this->assertTextResponse($response, ['1870', '1875', '1880', '1890', '1900']);
  }

  public function testListPreservesSpacesInsideNormForm(): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=njejo%20li&list=1&cs=1&sort');

    $this->assertTextResponse($response, ['1910']);
  }

  public static function regexCases(): array
  {
    return [
      'prefix alone is not a whole match' => ['bu', []],
      'explicit wildcard matches case insensitively' => ['bu.*', ['1870', '1875', '1880', '1890']],
      'delimiter injection' => ['a/i', []],
      'invalid pattern' => ['(', []],
    ];
  }

  #[DataProvider('regexCases')]
  public function testRegexIsAnchoredAndInvalidPatternsReturnEmptyBody(string $term, array $years): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=' . urlencode($term) . '&regex=1&sort');

    $this->assertTextResponse($response, $years);
  }

  public static function yearCases(): array
  {
    return [
      'inclusive range' => ['1870-1880', ['1870', '1875', '1880']],
      'range with spaces' => [' 1870 - 1880 ', ['1870', '1875', '1880']],
      'single year' => ['1870', ['1870']],
      'missing is unfiltered' => [null, ['1870', '1875', '1880', '1890']],
      'empty is unfiltered' => ['', ['1870', '1875', '1880', '1890']],
      'whitespace is unfiltered' => ['   ', ['1870', '1875', '1880', '1890']],
      'SQL injection' => ['> 0 OR 1=1 --', []],
      'raw SQL range' => ['BETWEEN 1 AND 2', []],
      'missing upper bound' => ['1870-', []],
      'missing lower bound' => ['-1880', []],
      'extra bound' => ['1870-1880-1890', []],
      'garbage' => ['abcd', []],
    ];
  }

  #[DataProvider('yearCases')]
  public function testYearFilterReturnsOnlyRequestedDocuments(?string $year, array $years): void
  {
    $query = '/php/urnbynorm.php?norm=buda&sort';
    if ($year !== null) {
      $query .= '&year=' . urlencode($year);
    }

    $response = $this->server->get($query);

    $this->assertTextResponse($response, $years);
  }

  public function testNormSqlInjectionReturnsEmptyBody(): void
  {
    $response = $this->server->get('/php/urnbynorm.php?norm=' . urlencode('" OR 1=1 --'));

    $this->assertTextResponse($response, []);
  }

  public static function emptyRequests(): array
  {
    return [
      'missing norm' => [''],
      'empty norm' => ['?norm='],
    ];
  }

  #[DataProvider('emptyRequests')]
  public function testMissingOrEmptyNormReturnsEmptyBody(string $query): void
  {
    $response = $this->server->get('/php/urnbynorm.php' . $query);

    $this->assertTextResponse($response, []);
  }

  private function assertTextResponse(array $response, array $years): void
  {
    $rows = array_map(
      static fn(string $year): string => implode(chr(9), ['urn:doc:' . $year, $year]),
      $years,
    );
    $expectedBody = $rows === [] ? '' : implode(PHP_EOL, $rows) . PHP_EOL;

    $this->assertSame(200, $response['status']);
    $this->assertSame($expectedBody, $response['body']);
    $this->assertMatchesRegularExpression(
      '/^Content-Type:\s*text\/plain/im',
      implode(PHP_EOL, $response['headers']),
    );
  }
}
