<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class Token2lemmaRegressionsTest extends TestCase
{
	private DevServer $server;

	protected function setUp(): void
	{
		$this->server = DevServer::boot();

		$db = $this->server->dataDir() . '/lemmamapping.db';
		@unlink($db);
		$pdo = FixtureDb::open($db);
		$pdo->exec('CREATE TABLE tokenlemmatypesubtypedatefrequency (token TEXT, lemma TEXT, type TEXT, subtype TEXT, date TEXT, frequency INTEGER)');
		$pdo->exec("INSERT INTO tokenlemmatypesubtypedatefrequency VALUES ('woda', '|woda|', '', '', '1880', 5)");
		$pdo->exec("INSERT INTO tokenlemmatypesubtypedatefrequency VALUES ('luft', '|luft|', '', '', '1880', 1)");
	}

	public function testTokenParameterIsTreatedAsLiteralValue(): void
	{
		$response = $this->server->get(
			'/php/token2lemma.php?token=' . urlencode('" OR 1=1 -- ')
		);

		$this->assertSame('', $response['body']);
	}
}
