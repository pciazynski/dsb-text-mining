<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class LemmagroupEndpointTest extends TestCase
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

    $lemmaCells = [
      '|DRJEWO|',
      '|drjewo|',
      '|DRĚŚ|DRJEWO|',
      '|DRJEWO|DRJEWOWY|',
      '|TEJ|',
      '|NJEBYŚ LI|',
    ];
    $nonambiguousCells = [
      '|DRJEWO|',
      '|drjewo|',
      '|DRĚŚ|',
      '|DRJEWOWY|',
      '|TEJ|',
      '|NJEBYŚ LI|',
    ];

    $this->insertLemmaRows($pdo, 'lemmafrequency', $lemmaCells);
    $this->insertLemmaRows($pdo, 'lemmanonambig', $nonambiguousCells);

    $statement = $pdo->prepare(
      'INSERT INTO tokenlemmatypesubtypedatefrequency VALUES (:token, :lemma, :type, :subtype, :date, :frequency)',
    );
    foreach ($lemmaCells as $index => $lemma) {
      $statement->execute([
        'token' => 'token-' . $index,
        'lemma' => $lemma,
        'type' => '',
        'subtype' => '',
        'date' => '1880',
        'frequency' => count($lemmaCells) - $index,
      ]);
    }
  }

  public function testDefaultRequestReturnsCaseInsensitiveAmbiguousRowsSortedByFrequency(): void
  {
    $response = $this->server->get('/php/lemmagroup.php?lemma=drjewo&sort');

    $this->assertSame(200, $response['status']);
    $this->assertSame(
      $this->body([
        ['|DRJEWO|', 6],
        ['|drjewo|', 5],
        ['|DRĚŚ|DRJEWO|', 4],
        ['|DRJEWO|DRJEWOWY|', 3],
      ]),
      $response['body'],
    );
    $this->assertMatchesRegularExpression(
      '/^Content-Type:\s*text\/plain/im',
      implode(PHP_EOL, $response['headers']),
    );
  }

  public function testAmbigDisabledReturnsOnlyUnambiguousCells(): void
  {
    $response = $this->server->get('/php/lemmagroup.php?lemma=drjewo&ambig=0');

    $this->assertSame($this->body([
      ['|DRJEWO|', 6],
      ['|drjewo|', 5],
    ]), $response['body']);
  }

  public function testCaseSensitiveEnabledReturnsOnlyLowercaseCell(): void
  {
    $response = $this->server->get('/php/lemmagroup.php?lemma=drjewo&cs=1');

    $this->assertSame($this->body([
      ['|drjewo|', 5],
    ]), $response['body']);
  }

  public function testLegacyExactFlagMatchesAmbigDisabledBehavior(): void
  {
    $exact = $this->server->get('/php/lemmagroup.php?lemma=DRJEWO&exact=1');
    $nonambiguous = $this->server->get('/php/lemmagroup.php?lemma=DRJEWO&ambig=0');

    $this->assertSame($this->body([
      ['|DRJEWO|', 6],
      ['|drjewo|', 5],
    ]), $exact['body']);
    $this->assertSame($nonambiguous['body'], $exact['body']);
  }

  public function testTrimmedListReturnsRowsForEveryTerm(): void
  {
    $response = $this->server->get('/php/lemmagroup.php?lemma=drjewo,tej&list=1&trim=1');

    $this->assertSame(
      $this->body([
        ['|DRJEWO|', 6],
        ['|DRJEWO|DRJEWOWY|', 3],
        ['|DRĚŚ|DRJEWO|', 4],
        ['|TEJ|', 2],
        ['|drjewo|', 5],
      ]),
      $response['body'],
    );
  }

  public function testRegexFlagReturnsRegexMatches(): void
  {
    $response = $this->server->get('/php/lemmagroup.php?lemma=DR.*O&regex=1');

    $this->assertSame(
      $this->body([
        ['|DRJEWO|', 6],
        ['|DRJEWO|DRJEWOWY|', 3],
        ['|DRĚŚ|DRJEWO|', 4],
        ['|drjewo|', 5],
      ]),
      $response['body'],
    );
  }

  public function testRegexMetacharactersAreLiteralWithoutRegexFlag(): void
  {
    $response = $this->server->get('/php/lemmagroup.php?lemma=DR.*O');

    $this->assertSame('', $response['body']);
  }

  public function testMissingLemmaReturnsEmptySuccessfulResponse(): void
  {
    $response = $this->server->get('/php/lemmagroup.php');

    $this->assertSame(200, $response['status']);
    $this->assertSame('', $response['body']);
  }

  public function testSqlInjectionTextReturnsEmptyBody(): void
  {
    $payload = urlencode('woda" OR "1"="1');

    $response = $this->server->get('/php/lemmagroup.php?lemma=' . $payload);

    $this->assertSame('', $response['body']);
  }

  public function testAllSearchFlagsComposeWithoutError(): void
  {
    $response = $this->server->get(
      '/php/lemmagroup.php?lemma=drjewo&regex=1&list=1&trim=1&cs=1&ambig=0',
    );

    $this->assertSame(200, $response['status']);
    $this->assertSame($this->body([
      ['|drjewo|', 5],
    ]), $response['body']);
  }

  private function body(array $rows): string
  {
    return implode(PHP_EOL, array_map(
      static fn(array $row): string => implode(chr(9), $row),
      $rows,
    )) . PHP_EOL;
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
}
