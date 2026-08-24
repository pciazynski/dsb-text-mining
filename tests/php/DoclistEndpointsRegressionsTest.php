<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class DoclistEndpointsRegressionsTest extends TestCase
{
  private DevServer $server;

  public static function setUpBeforeClass(): void
  {
    require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
  }

  protected function setUp(): void
  {
    $this->server = DevServer::boot();
    $this->seedLemmaMapping();
    $this->seedMetadata();
  }

  public function testUrnByLemmaDefaultReturnsCaseInsensitiveAmbiguousDocuments(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1870', '1870'],
      ['urn:doc:1875', '1875'],
      ['urn:doc:1880', '1880'],
    ]));
  }

  public function testUrnByLemmaAmbigDisabledReturnsOnlyUnambiguousCells(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo&ambig=0&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1870', '1870'],
      ['urn:doc:1880', '1880'],
    ]));
  }

  public function testUrnByLemmaCaseInsensitiveDisabledReturnsOnlyExactCase(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo&ci=0&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1880', '1880'],
    ]));
  }

  public function testUrnByLemmaListReturnsDocumentsForEveryTerm(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo%2C%20tej&list=1&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1870', '1870'],
      ['urn:doc:1875', '1875'],
      ['urn:doc:1880', '1880'],
      ['urn:doc:1890', '1890'],
    ]));
  }

  public function testUrnByLemmaRegexReturnsDocumentsForResolvedCells(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=DR.*&regex=1&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1870', '1870'],
      ['urn:doc:1875', '1875'],
      ['urn:doc:1880', '1880'],
      ['urn:doc:1900', '1900'],
    ]));
  }

  public function testUrnByLemmaYearRangeIsInclusive(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo&year=1870-1880&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1870', '1870'],
      ['urn:doc:1875', '1875'],
      ['urn:doc:1880', '1880'],
    ]));
  }

  public function testUrnByLemmaExactYearReturnsOnlyThatYear(): void
  {
    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo&year=1870&sort');

    $this->assertTextResponse($response, $this->urnBody([
      ['urn:doc:1870', '1870'],
    ]));
  }

  public function testUrnByLemmaRejectsSqlInYear(): void
  {
    $payload = urlencode('> 0 OR 1=1 --');

    $response = $this->server->get('/php/urnbylemma.php?lemma=drjewo&year=' . $payload);

    $this->assertTextResponse($response, '');
  }

  public static function metadataFilters(): array
  {
    return [
      'author' => ['author', 'Alena', 'urn:doc:1870'],
      'year' => ['year', '1875', 'urn:doc:1875'],
      'language' => ['lang', 'de', 'urn:doc:1880'],
      'restricted' => ['restricted', '1', 'urn:doc:1875'],
    ];
  }

  #[DataProvider('metadataFilters')]
  public function testMetadataFiltersByRequestedField(
    string $parameter,
    string $value,
    string $expectedUrn,
  ): void {
    $response = $this->server->get(
      '/php/metadata.php?' . $parameter . '=' . urlencode($value),
    );

    $this->assertTextResponse($response, $this->metadataBody($expectedUrn));
  }

  public static function metadataFilterNames(): array
  {
    return [
      'author' => ['author'],
      'year' => ['year'],
      'language' => ['lang'],
      'restricted' => ['restricted'],
    ];
  }

  #[DataProvider('metadataFilterNames')]
  public function testMetadataTreatsInjectionPayloadAsLiteralValue(string $parameter): void
  {
    $payload = urlencode('" OR 1=1 --');

    $response = $this->server->get('/php/metadata.php?' . $parameter . '=' . $payload);

    $this->assertTextResponse($response, '');
  }

  private function seedLemmaMapping(): void
  {
    $db = $this->server->dataDir() . '/lemmamapping.db';
    @unlink($db);
    $pdo = FixtureDb::open($db);
    $pdo->exec('CREATE TABLE urndatelemmabag (urn TEXT, date TEXT, lemmabag TEXT)');
    $pdo->exec('CREATE TABLE lemmafrequency (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE lemmanonambig (lemma TEXT, frequency INTEGER, sortkey TEXT)');

    $this->insertLemmaRows($pdo, 'lemmafrequency', [
      '|DRJEWO|',
      '|drjewo|',
      '|DRĚŚ|DRJEWO|',
      '|TEJ|',
      '|DRJEWOWY|',
    ]);
    $this->insertLemmaRows($pdo, 'lemmanonambig', [
      '|DRJEWO|',
      '|drjewo|',
      '|DRĚŚ|',
      '|TEJ|',
      '|DRJEWOWY|',
    ]);

    $statement = $pdo->prepare('INSERT INTO urndatelemmabag VALUES (?, ?, ?)');
    foreach (
      [
        ['urn:doc:1870', '1870', '|OTHER||DRJEWO||MORE|'],
        ['urn:doc:1875', '1875', '|OTHER||DRĚŚ|DRJEWO||MORE|'],
        ['urn:doc:1880', '1880', '|OTHER||drjewo||MORE|'],
        ['urn:doc:1890', '1890', '|OTHER||TEJ||MORE|'],
        ['urn:doc:1900', '1900', '|OTHER||DRJEWOWY||MORE|'],
      ] as $row
    ) {
      $statement->execute($row);
    }
  }

  private function seedMetadata(): void
  {
    $db = $this->server->dataDir() . '/metadata.db';
    @unlink($db);
    $pdo = FixtureDb::open($db);
    $pdo->exec('CREATE TABLE docmeta (urn TEXT, title TEXT, date TEXT, author TEXT, restricted TEXT, lang TEXT)');

    $statement = $pdo->prepare('INSERT INTO docmeta VALUES (?, ?, ?, ?, ?, ?)');
    foreach (
      [
        ['urn:doc:1870', 'First', '1870', 'Alena', '0', 'dsb'],
        ['urn:doc:1875', 'Second', '1875', 'Beno', '1', 'dsb'],
        ['urn:doc:1880', 'Third', '1880', 'Cilka', '0', 'de'],
      ] as $row
    ) {
      $statement->execute($row);
    }
  }

  private function insertLemmaRows(\PDO $pdo, string $table, array $lemmas): void
  {
    $statement = $pdo->prepare(
      "INSERT INTO {$table} (lemma, frequency, sortkey) VALUES (:lemma, :frequency, :sortkey)",
    );
    foreach ($lemmas as $index => $lemma) {
      $statement->execute([
        'lemma' => $lemma,
        'frequency' => count($lemmas) - $index,
        'sortkey' => dsb_sortkey(trim($lemma, '|')),
      ]);
    }
  }

  private function assertTextResponse(array $response, string $expectedBody): void
  {
    $this->assertSame(200, $response['status']);
    $this->assertSame($expectedBody, $response['body']);
    $this->assertMatchesRegularExpression(
      '/^Content-Type:\s*text\/plain/im',
      implode(PHP_EOL, $response['headers']),
    );
  }

  private function urnBody(array $rows): string
  {
    return implode(PHP_EOL, array_map(
      static fn(array $row): string => implode(chr(9), $row),
      $rows,
    )) . PHP_EOL;
  }

  private function metadataBody(string $urn): string
  {
    $rows = [
      'urn:doc:1870' => ['urn:doc:1870', 'First', '1870', 'Alena', '0', 'dsb'],
      'urn:doc:1875' => ['urn:doc:1875', 'Second', '1875', 'Beno', '1', 'dsb'],
      'urn:doc:1880' => ['urn:doc:1880', 'Third', '1880', 'Cilka', '0', 'de'],
    ];

    return implode(chr(9), $rows[$urn]) . PHP_EOL;
  }
}
