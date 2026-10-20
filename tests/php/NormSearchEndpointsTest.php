<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class NormSearchEndpointsTest extends TestCase
{
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
    $pdo->exec('CREATE TABLE tokennormtypesubtypedatefrequency (token TEXT, norm TEXT, type TEXT, subtype TEXT, date TEXT, frequency INTEGER)');
    $pdo->exec('CREATE TABLE normfrequency (norm TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE normnonambig (norm TEXT, frequency INTEGER, sortkey TEXT)');
    $pdo->exec('CREATE TABLE normtokenfrequency (norm TEXT, token TEXT, frequency INTEGER)');

    $this->insertNormRows($pdo, 'normfrequency', [
      '|we|wě|wó|' => 15,
      '|drjewje|' => 11,
    ]);
    $this->insertNormRows($pdo, 'normnonambig', [
      '|drjewje|' => 11,
    ]);

    $rows = [
      ['we', '|we|wě|wó|', '1749', 11],
      ['weh', '|we|wě|wó|', '1749', 4],
      ['dṙeẇe', '|drjewje|', '1869', 8],
      ['dŕeẃe', '|drjewje|', '1906', 3],
    ];
    $statement = $pdo->prepare(
      'INSERT INTO tokennormtypesubtypedatefrequency VALUES (:token, :norm, "", "", :date, :frequency)',
    );
    foreach ($rows as [$token, $norm, $date, $frequency]) {
      $statement->execute(compact('token', 'norm', 'date', 'frequency'));
    }

    $tokenRows = [
      ['|we|wě|wó|', 'we', 11],
      ['|we|wě|wó|', 'weh', 4],
      ['|drjewje|', 'dṙeẇe', 8],
      ['|drjewje|', 'dŕeẃe', 3],
    ];
    $statement = $pdo->prepare('INSERT INTO normtokenfrequency VALUES (:norm, :token, :frequency)');
    foreach ($tokenRows as [$norm, $token, $frequency]) {
      $statement->execute(compact('norm', 'token', 'frequency'));
    }
  }

  public static function endpoints(): array
  {
    return [
      'group' => ['normgroup.php', 'group'],
      'count per year' => ['normcountperyear.php', 'count'],
      'sum per year' => ['normsumperyear.php', 'sum'],
      'token' => ['normtoken.php', 'token'],
    ];
  }

  #[DataProvider('endpoints')]
  public function testDefaultRequestReturnsCaseInsensitiveAmbiguousRows(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?norm=WE&sort=1');

    $this->assertResponse($response, $this->defaultRows($kind));
  }

  #[DataProvider('endpoints')]
  public function testAmbigDisabledReturnsOnlyUnambiguousCells(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?norm=drjewje&ambig=0&sort=1');

    $this->assertResponse($response, $this->unambiguousRows($kind));
  }

  #[DataProvider('endpoints')]
  public function testCaseSensitiveEnabledReturnsOnlyExactCase(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?norm=we&cs=1&sort=1');
    $differentCase = $this->server->get('/php/' . $endpoint . '?norm=WE&cs=1&sort=1');

    $this->assertResponse($response, $this->defaultRows($kind));
    $this->assertResponse($differentCase, []);
  }

  #[DataProvider('endpoints')]
  public function testSemicolonListReturnsRowsForEveryTrimmedTerm(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?norm=drjewje%3B%20we&list=1&sort=1');

    $this->assertResponse($response, $this->listRows($kind));
  }

  #[DataProvider('endpoints')]
  public function testRegexFlagReturnsRegexMatches(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?norm=drjewj.&regex=1&sort=1');

    $this->assertResponse($response, $this->regexRows($kind));
  }

  #[DataProvider('endpoints')]
  public function testLegacyExactFlagMatchesAmbigDisabledBehavior(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint . '?norm=drjewje&exact=1&sort=1');

    $this->assertResponse($response, $this->unambiguousRows($kind));
  }

  #[DataProvider('endpoints')]
  public function testMissingNormReturnsEmptySuccessfulResponse(string $endpoint, string $kind): void
  {
    $response = $this->server->get('/php/' . $endpoint);

    $this->assertResponse($response, []);
  }

  #[DataProvider('endpoints')]
  public function testSqlInjectionTextReturnsEmptyBody(string $endpoint, string $kind): void
  {
    $payload = urlencode('woda" OR "1"="1');

    $response = $this->server->get('/php/' . $endpoint . '?norm=' . $payload);

    $this->assertResponse($response, []);
  }

  #[DataProvider('endpoints')]
  public function testWholeAmbiguousCellReturnsItsRows(string $endpoint, string $kind): void
  {
    $response = $this->server->get(
      '/php/' . $endpoint . '?norm=' . rawurlencode('we|wě|wó') . '&cs=1&ambig=0',
    );

    $this->assertResponse($response, $this->wholeCellRows($kind));
  }

  #[DataProvider('endpoints')]
  public function testRegexOverResultCapSendsTruncationHeader(string $endpoint, string $kind): void
  {
    $pdo = FixtureDb::open($this->server->dataDir() . '/normmapping.db');
    $statement = $pdo->prepare('INSERT INTO normfrequency (norm, frequency, sortkey) VALUES (:norm, 1, :sortkey)');
    for ($index = 0; $index < 501; $index++) {
      $norm = sprintf('|ITEM%03d|', $index);
      $statement->execute(['norm' => $norm, 'sortkey' => dsb_sortkey(trim($norm, '|'))]);
    }

    $response = $this->server->get('/php/' . $endpoint . '?norm=.%2A&regex=1');

    $this->assertSame(200, $response['status']);
    $this->assertContains('X-Dsb-Result-Truncated: 1', $response['headers']);
  }

  private function defaultRows(string $kind): array
  {
    return match ($kind) {
      'group' => [['|we|wě|wó|', 15]],
      'count' => [
        ['|we|wě|wó|', '1749', 11, 'we'],
        ['|we|wě|wó|', '1749', 4, 'weh'],
      ],
      'sum' => [['|we|wě|wó|', '1749', 15]],
      'token' => [
        ['|we|wě|wó|', 'we', 11],
        ['|we|wě|wó|', 'weh', 4],
      ],
    };
  }

  private function unambiguousRows(string $kind): array
  {
    return match ($kind) {
      'group' => [['|drjewje|', 11]],
      'count' => [
        ['|drjewje|', '1869', 8, 'dṙeẇe'],
        ['|drjewje|', '1906', 3, 'dŕeẃe'],
      ],
      'sum' => [
        ['|drjewje|', '1869', 8],
        ['|drjewje|', '1906', 3],
      ],
      'token' => [
        ['|drjewje|', 'dṙeẇe', 8],
        ['|drjewje|', 'dŕeẃe', 3],
      ],
    };
  }

  private function listRows(string $kind): array
  {
    return match ($kind) {
      'group' => [
        ['|we|wě|wó|', 15],
        ['|drjewje|', 11],
      ],
      'count' => [
        ['|we|wě|wó|', '1749', 11, 'we'],
        ['|we|wě|wó|', '1749', 4, 'weh'],
        ['|drjewje|', '1869', 8, 'dṙeẇe'],
        ['|drjewje|', '1906', 3, 'dŕeẃe'],
      ],
      'sum' => [
        ['|we|wě|wó|', '1749', 15],
        ['|drjewje|', '1869', 8],
        ['|drjewje|', '1906', 3],
      ],
      'token' => [
        ['|we|wě|wó|', 'we', 11],
        ['|drjewje|', 'dṙeẇe', 8],
        ['|we|wě|wó|', 'weh', 4],
        ['|drjewje|', 'dŕeẃe', 3],
      ],
    };
  }

  private function regexRows(string $kind): array
  {
    return match ($kind) {
      'group' => [
        ['|drjewje|', 11],
      ],
      'count' => [
        ['|drjewje|', '1869', 8, 'dṙeẇe'],
        ['|drjewje|', '1906', 3, 'dŕeẃe'],
      ],
      'sum' => [
        ['|drjewje|', '1869', 8],
        ['|drjewje|', '1906', 3],
      ],
      'token' => [
        ['|drjewje|', 'dṙeẇe', 8],
        ['|drjewje|', 'dŕeẃe', 3],
      ],
    };
  }

  private function wholeCellRows(string $kind): array
  {
    return match ($kind) {
      'group' => [['|we|wě|wó|', 15]],
      'count' => [
        ['|we|wě|wó|', '1749', 11, 'we'],
        ['|we|wě|wó|', '1749', 4, 'weh'],
      ],
      'sum' => [['|we|wě|wó|', '1749', 15]],
      'token' => [
        ['|we|wě|wó|', 'we', 11],
        ['|we|wě|wó|', 'weh', 4],
      ],
    };
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

  private function insertNormRows(\PDO $pdo, string $table, array $norms): void
  {
    $statement = $pdo->prepare(
      "INSERT INTO {$table} (norm, frequency, sortkey) VALUES (:norm, :frequency, :sortkey)",
    );
    foreach ($norms as $norm => $frequency) {
      $statement->execute([
        'norm' => $norm,
        'frequency' => $frequency,
        'sortkey' => dsb_sortkey(trim($norm, '|')),
      ]);
    }
  }
}
