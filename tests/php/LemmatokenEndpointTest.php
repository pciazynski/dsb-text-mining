<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class LemmatokenEndpointTest extends TestCase
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
    $pdo->exec('CREATE TABLE lemmatokenfrequency (token TEXT, lemma TEXT, frequency INTEGER)');
    $pdo->exec('CREATE TABLE lemmafrequency (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE lemmanonambig (lemma TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('woda', '|woda|', 5)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('wodu', '|woda|', 2)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('luft', '|luft|', 1)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('dṙewo', '|DRJEWO|', 6)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('drjewa', '|DRJEWO|', 5)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('drjewje', '|DRJEWO|DRJEWOWY|', 4)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('drjewo', '|drjewo|', 3)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('tej', '|TEJ|', 2)");

    $this->insertLemmaRows($pdo, 'lemmafrequency', [
      '|woda|',
      '|luft|',
      '|DRJEWO|',
      '|DRJEWO|DRJEWOWY|',
      '|drjewo|',
      '|TEJ|',
    ]);
    $this->insertLemmaRows($pdo, 'lemmanonambig', [
      '|woda|',
      '|luft|',
      '|DRJEWO|',
      '|DRJEWOWY|',
      '|drjewo|',
      '|TEJ|',
    ]);
  }

  public function testReturnsTabSeparatedRowsForTheRequestedLemma(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=woda&exact=1&sort=1');

    $this->assertSame(200, $response['status']);
    $this->assertSame($this->body([
      ['|woda|', 'woda', 5],
      ['|woda|', 'wodu', 2],
    ]), $response['body']);
  }

  public function testReturnsEmptyBodyWhenTheLemmaParameterIsMissing(): void
  {
    $response = $this->server->get('/php/lemmatoken.php');

    $this->assertSame(200, $response['status']);
    $this->assertSame('', $response['body']);
  }

  public function testDefaultRequestReturnsCaseInsensitiveAmbiguousRows(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=drjewo&sort=1');

    $this->assertSame(200, $response['status']);
    $this->assertSame($this->body([
      ['|DRJEWO|', 'dṙewo', 6],
      ['|DRJEWO|', 'drjewa', 5],
      ['|DRJEWO|DRJEWOWY|', 'drjewje', 4],
      ['|drjewo|', 'drjewo', 3],
    ]), $response['body']);
  }

  public function testAmbigDisabledReturnsOnlyUnambiguousCells(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=drjewo&ambig=0&sort=1');

    $this->assertSame($this->body([
      ['|DRJEWO|', 'dṙewo', 6],
      ['|DRJEWO|', 'drjewa', 5],
      ['|drjewo|', 'drjewo', 3],
    ]), $response['body']);
  }

  public function testCaseSensitiveEnabledReturnsOnlyExactCase(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=drjewo&cs=1&sort=1');

    $this->assertSame($this->body([
      ['|drjewo|', 'drjewo', 3],
    ]), $response['body']);
  }

  public function testSemicolonSeparatedListReturnsRowsForEveryTrimmedTerm(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=drjewo%3B%20tej&list=1&sort=1');

    $this->assertSame($this->body([
      ['|DRJEWO|', 'dṙewo', 6],
      ['|DRJEWO|', 'drjewa', 5],
      ['|DRJEWO|DRJEWOWY|', 'drjewje', 4],
      ['|drjewo|', 'drjewo', 3],
      ['|TEJ|', 'tej', 2],
    ]), $response['body']);
  }

  public function testCommaSeparatedListReturnsRowsForEveryTrimmedTerm(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=drjewo%2C%20tej&list=1&sort=1');

    $this->assertSame($this->body([
      ['|DRJEWO|', 'dṙewo', 6],
      ['|DRJEWO|', 'drjewa', 5],
      ['|DRJEWO|DRJEWOWY|', 'drjewje', 4],
      ['|drjewo|', 'drjewo', 3],
      ['|TEJ|', 'tej', 2],
    ]), $response['body']);
  }

  public function testRegexFlagReturnsRegexMatches(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=dr.*o&regex=1&sort=1');

    $this->assertSame($this->body([
      ['|DRJEWO|', 'dṙewo', 6],
      ['|DRJEWO|', 'drjewa', 5],
      ['|DRJEWO|DRJEWOWY|', 'drjewje', 4],
      ['|drjewo|', 'drjewo', 3],
    ]), $response['body']);
  }

  public function testLegacyExactFlagMatchesAmbigDisabledBehavior(): void
  {
    $exact = $this->server->get('/php/lemmatoken.php?lemma=drjewo&exact=1&sort=1');
    $nonambiguous = $this->server->get('/php/lemmatoken.php?lemma=drjewo&ambig=0&sort=1');

    $this->assertSame($this->body([
      ['|DRJEWO|', 'dṙewo', 6],
      ['|DRJEWO|', 'drjewa', 5],
      ['|drjewo|', 'drjewo', 3],
    ]), $exact['body']);
    $this->assertSame($nonambiguous['body'], $exact['body']);
  }

  public function testSqlInjectionTextReturnsEmptyBody(): void
  {
    $payload = urlencode('woda" OR "1"="1');

    $response = $this->server->get('/php/lemmatoken.php?lemma=' . $payload);

    $this->assertSame('', $response['body']);
  }

  public function testInclusiveFlagPreservesLegacyResponseWithoutNewSearchFlags(): void
  {
    $legacy = $this->server->get('/php/lemmatoken.php?lemma=woda&sort=1');
    $inclusive = $this->server->get('/php/lemmatoken.php?lemma=woda&sort=1&inclusive');

    $this->assertSame($this->body([
      ['|woda|', 'woda', 5],
      ['|woda|', 'wodu', 2],
    ]), $legacy['body']);
    $this->assertSame($legacy['body'], $inclusive['body']);
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
