<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class LemmatokenEndpointTest extends TestCase
{
  private DevServer $server;

  protected function setUp(): void
  {
    $this->server = DevServer::boot();

    $db = $this->server->dataDir() . '/lemmamapping.db';
    @unlink($db);
    $pdo = new \PDO('sqlite:' . $db);
    $pdo->exec('CREATE TABLE lemmatokenfrequency (token TEXT, lemma TEXT, frequency INTEGER)');
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('woda', '|woda|', 5)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('wodu', '|woda|', 2)");
    $pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('luft', '|luft|', 1)");
  }

  public function testReturnsTabSeparatedRowsForTheRequestedLemma(): void
  {
    $response = $this->server->get('/php/lemmatoken.php?lemma=woda&exact=1&sort=1');

    $this->assertSame(200, $response['status']);
    $this->assertSame("|woda|\twoda\t5\n|woda|\twodu\t2\n", $response['body']);
  }

  public function testReturnsEmptyBodyWhenTheLemmaParameterIsMissing(): void
  {
    $response = $this->server->get('/php/lemmatoken.php');

    $this->assertSame(200, $response['status']);
    $this->assertSame('', $response['body']);
  }
}
