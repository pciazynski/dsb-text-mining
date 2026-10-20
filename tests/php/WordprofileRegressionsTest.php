<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class WordprofileRegressionsTest extends TestCase
{
	private DevServer $server;

	protected function setUp(): void
	{
		$this->server = DevServer::boot();
		$dir = $this->server->dataDir();

		$bag = $dir . '/bagofwords.db';
		@unlink($bag);
		$pdo = new \PDO('sqlite:' . $bag);
		$pdo->exec('CREATE TABLE tokencount (token TEXT, frequency INTEGER)');
		$pdo->exec("INSERT INTO tokencount VALUES ('a', 100)");
		$pdo->exec('CREATE TABLE tokendatecount (token TEXT, date TEXT, frequency INTEGER)');
		$pdo->exec("INSERT INTO tokendatecount VALUES ('a', '1880', 60)");
		$pdo->exec("INSERT INTO tokendatecount VALUES ('a', '1890', 40)");

		$lemma = $dir . '/lemmamapping.db';
		@unlink($lemma);
		$pdo = new \PDO('sqlite:' . $lemma);
		$pdo->exec('CREATE TABLE lemmatokenfrequency (token TEXT, lemma TEXT, frequency INTEGER)');
		$pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('a', '|A|', 10)");
		$pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('a', '|AN|', 3)");
		$pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('a', '|ANA|', 2)");

		$norm = $dir . '/normmapping.db';
		@unlink($norm);
		$pdo = new \PDO('sqlite:' . $norm);
		$pdo->exec('CREATE TABLE normtokenfrequency (token TEXT, norm TEXT, frequency INTEGER)');
		$pdo->exec('CREATE TABLE tokennormtypesubtypedatefrequency (token TEXT, type TEXT, frequency INTEGER)');

		$colloc = $dir . '/collocation.db';
		@unlink($colloc);
		$pdo = new \PDO('sqlite:' . $colloc);
		$pdo->exec('CREATE TABLE collocation (left TEXT, right TEXT, logdice REAL)');
	}

	public function testAggregateLemmaCountIsLabelledPerLemma(): void
	{
		$response = $this->server->get('/php/wordprofile.php?word=a');
		$lines = explode("\n", $response['body']);

		$this->assertSame('A:10' . "\t" . 'AN:3' . "\t" . 'ANA:2', $lines[2]);
	}

	public function testWordParameterIsTreatedAsLiteralValue(): void
	{
		$response = $this->server->get(
			'/php/wordprofile.php?word=' . urlencode('a" OR 1=1 -- ')
		);

		$this->assertSame('NULL', $response['body']);
	}
}
