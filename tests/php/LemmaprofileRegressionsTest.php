<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class LemmaprofileRegressionsTest extends TestCase
{
	private DevServer $server;

	protected function setUp(): void
	{
		$this->server = DevServer::boot();

		$db = $this->server->dataDir() . '/lemmamapping.db';
		@unlink($db);
		$pdo = new \PDO('sqlite:' . $db);

		// Default autocomplete draws from lemmanonambig (flattened single lemmas).
		$pdo->exec('CREATE TABLE lemmanonambig (lemma TEXT, frequency INTEGER, sortkey TEXT)');
		$pdo->exec("INSERT INTO lemmanonambig VALUES ('|TO|', 10, 'to')");

		// TO only occurs in an ambiguous record connected to the exact lemma TEN.
		$pdo->exec('CREATE TABLE lemmafrequency (lemma TEXT, frequency INTEGER, sortkey TEXT)');
		$pdo->exec("INSERT INTO lemmafrequency VALUES ('|TEN|', 8, 'ten')");
		$pdo->exec("INSERT INTO lemmafrequency VALUES ('|TEN|TO|', 10, 'ten')");
		$pdo->exec('CREATE TABLE tokenlemmatypesubtypedatefrequency (token TEXT, lemma TEXT, type TEXT, subtype TEXT, date TEXT, frequency INTEGER)');
		$pdo->exec("INSERT INTO tokenlemmatypesubtypedatefrequency VALUES ('ten', '|TEN|', '', '', '1870', 8)");
		$pdo->exec("INSERT INTO tokenlemmatypesubtypedatefrequency VALUES ('tog', '|TEN|TO|', '', '', '1880', 10)");
		$pdo->exec('CREATE TABLE lemmatokenfrequency (token TEXT, lemma TEXT, frequency INTEGER)');
		$pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('ten', '|TEN|', 8)");
		$pdo->exec("INSERT INTO lemmatokenfrequency VALUES ('tog', '|TEN|TO|', 10)");
	}

	public function testAmbiguousOnlyAutocompleteCandidateUsesConnectedExactProfile(): void
	{
		$autocomplete = $this->server->get('/php/prefixlemmasearch.php?lemma=to');
		$candidates = array_values(array_filter(
			explode("\n", trim($autocomplete['body'])),
			'strlen'
		));

		$this->assertSame(['TO'], $candidates);

		$profile = $this->server->get('/php/lemmaprofile.php?lemma=TO');
		$lines = explode("\n", trim($profile['body']));

		$this->assertSame(200, $profile['status']);
		$this->assertSame("8\t1", $lines[0]);
		$this->assertSame('TEN', $lines[5]);
	}
}
