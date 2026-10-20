<?php

declare(strict_types=1);

namespace DsbTests;

use DsbTests\Support\DevServer;
use DsbTests\Support\FixtureDb;
use PHPUnit\Framework\Attributes\CoversNothing;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

#[CoversNothing]
final class WordSearchEndpointsTest extends TestCase
{
	private const SUGGESTIONS = [['woni'], ['woda'], ['Woda']];
	private DevServer $server;
	private \PDO $pdo;

	public static function setUpBeforeClass(): void
	{
		require_once dirname(__DIR__, 2) . '/public/php/dsb_collation.php';
	}

	protected function setUp(): void
	{
		$this->server = DevServer::boot();
		$db = $this->server->dataDir() . '/bagofwords.db';
		@unlink($db);
		$this->pdo = FixtureDb::open($db);
		$this->pdo->exec('CREATE TABLE tokencount (token TEXT, frequency INTEGER, sortkey TEXT)');
		$this->pdo->exec('CREATE INDEX tokenindex ON tokencount(token)');
		$this->pdo->exec('CREATE INDEX tokensortkeyindex ON tokencount(sortkey)');
		$this->pdo->exec('CREATE TABLE tokendatecount (token TEXT, date INTEGER, frequency INTEGER)');
		$this->pdo->exec('CREATE INDEX tokendateindex ON tokendatecount(token)');

		$this->insertToken('woda', 10789, 1870, 10);
		$this->insertToken('Woda', 1, 1880, 1);
		$this->insertToken('druge', 45489, 1880, 138);
		$this->insertToken('woni', 54783, 1900, 284);
	}

	public function testTokenCaseInsensitiveLiteralReturnsBothSpellings(): void
	{
		$response = $this->request('tokencountperyear.php', ['token' => 'woda', 'cs' => 0, 'sort' => '']);

		$this->assertResponse($response, [['woda', 1870, 10], ['Woda', 1880, 1]]);
	}

	public function testTokenCaseSensitiveLiteralReturnsOnlyRequestedSpelling(): void
	{
		$response = $this->request('tokencountperyear.php', ['token' => 'woda', 'cs' => 1, 'sort' => '']);

		$this->assertResponse($response, [['woda', 1870, 10]]);
	}

	public function testTokenCaseInsensitiveLiteralLookupUsesTokensortkeyindex(): void
	{
		$statement = $this->pdo->prepare(
			'EXPLAIN QUERY PLAN SELECT token FROM tokencount WHERE sortkey = :sortkey',
		);
		$statement->execute(['sortkey' => dsb_sortkey('woda')]);
		$plan = implode(PHP_EOL, array_column($statement->fetchAll(\PDO::FETCH_ASSOC), 'detail'));

		$this->assertStringContainsString('SEARCH tokencount USING INDEX tokensortkeyindex', $plan);
		$this->assertStringNotContainsString('SCAN tokencount', $plan);
		$statement = $this->pdo->prepare('SELECT token FROM tokencount WHERE sortkey = :sortkey ORDER BY rowid');
		$statement->execute(['sortkey' => dsb_sortkey('woda')]);
		$this->assertSame(['woda', 'Woda'], $statement->fetchAll(\PDO::FETCH_COLUMN));
	}

	public static function searches(): array
	{
		return [
			'token timeline' => ['tokencountperyear.php', ['token' => 'woni', 'sort' => ''], [['woni', 1900, 284]]],
			'word suggestions' => ['prefixsearch.php', ['word' => 'wo', 'sortby' => 'frequency'], self::SUGGESTIONS],
		];
	}

	#[DataProvider('searches')]
	public function testAmbigFlagDoesNotChangeWordSearchBodies(string $endpoint, array $query, array $rows): void
	{
		$disabled = $this->request($endpoint, $query + ['ambig' => 0]);
		$enabled = $this->request($endpoint, $query + ['ambig' => 1]);

		$this->assertResponse($disabled, $rows);
		$this->assertResponse($enabled, $rows);
		$this->assertSame($disabled['body'], $enabled['body']);
	}

	public static function lists(): array
	{
		return [
			'semicolon' => ['druge;woni'],
			'trimmed semicolon' => [' druge ; woni '],
			'legacy comma' => ['druge,woni'],
		];
	}

	#[DataProvider('lists')]
	public function testTokenListReturnsBothTerms(string $token): void
	{
		$response = $this->request('tokencountperyear.php', [
			'token' => $token, 'list' => 1, 'trim' => 1, 'sort' => '',
		]);

		$this->assertResponse($response, [['druge', 1880, 138], ['woni', 1900, 284]]);
	}

	public function testTokenRegexMatchesWholeTokensOnly(): void
	{
		$this->insertToken('wona', 53102, 1870, 102);
		$this->insertToken('zwoni', 146, 1951, 1);
		$this->insertToken('wonich', 35, 1769, 1);

		$response = $this->request('tokencountperyear.php', [
			'token' => 'w(o|a)n(a|i)', 'regex' => 1, 'sort' => '',
		]);

		$this->assertResponse($response, [['wona', 1870, 102], ['woni', 1900, 284]]);
	}

	public function testPrefixDefaultsToCaseInsensitiveFrequencyDescending(): void
	{
		$default = $this->request('prefixsearch.php', ['word' => 'wo']);
		$explicit = $this->request('prefixsearch.php', ['word' => 'wo', 'cs' => 0, 'sortby' => 'frequency']);

		$this->assertResponse($default, self::SUGGESTIONS);
		$this->assertResponse($explicit, self::SUGGESTIONS);
	}

	public function testPrefixCaseSensitiveSearchExcludesCapitalizedSpelling(): void
	{
		$response = $this->request('prefixsearch.php', ['word' => 'wo', 'cs' => 1]);

		$this->assertResponse($response, [['woni'], ['woda']]);
	}

	public function testPrefixAlphabetSortUsesDsbSortkeyInsteadOfUnicodeTokenOrder(): void
	{
		$this->pdo->exec('DELETE FROM tokencount');
		$this->pdo->exec('DELETE FROM tokendatecount');
		$this->insertToken('wola', 1713);
		$this->insertToken('woła', 2314);

		$response = $this->request('prefixsearch.php', [
			'word' => 'wo', 'sortby' => 'alphabet',
		]);

		$this->assertResponse($response, [['woła'], ['wola']]);
	}

	public static function sortOptions(): array
	{
		return [
			'unknown column' => ['unknown'],
			'injected statement' => ['frequency; DROP TABLE tokencount --'],
		];
	}

	#[DataProvider('sortOptions')]
	public function testPrefixUnrecognizedSortFallsBackToFrequencyAndPreservesTable(string $sortby): void
	{
		$response = $this->request('prefixsearch.php', ['word' => 'wo', 'sortby' => $sortby]);
		$second = $this->request('prefixsearch.php', ['word' => 'wo', 'sortby' => 'frequency']);

		$this->assertResponse($second, self::SUGGESTIONS);
		$this->assertTablesIntact();
		$this->assertResponse($response, self::SUGGESTIONS);
	}

	public static function limits(): array
	{
		return [
			'integer' => ['2'],
			'cast before SQL' => ['2; DROP TABLE tokencount --'],
		];
	}

	#[DataProvider('limits')]
	public function testPrefixLimitIsAppliedAsAnInteger(string $limit): void
	{
		$response = $this->request('prefixsearch.php', [
			'word' => 'wo', 'sortby' => 'frequency', 'limit' => $limit,
		]);

		$this->assertResponse($response, [['woni'], ['woda']]);
		$this->assertTablesIntact();
	}

	public static function cutoffs(): array
	{
		return ['numeric' => ['2'], 'garbage' => ['x']];
	}

	#[DataProvider('cutoffs')]
	public function testPrefixIgnoresCutoffWithoutServerError(string $cutoff): void
	{
		$response = $this->request('prefixsearch.php', ['word' => 'wo', 'cutoff' => $cutoff]);

		$this->assertResponse($response, self::SUGGESTIONS);
	}

	#[DataProvider('searches')]
	public function testMissingAndEmptySearchReturnEmptyBody(string $endpoint, array $query, array $rows): void
	{
		$parameter = $endpoint === 'prefixsearch.php' ? 'word' : 'token';
		$missing = $this->request($endpoint, []);
		$empty = $this->request($endpoint, [$parameter => '']);

		$this->assertResponse($missing, []);
		$this->assertResponse($empty, []);
	}

	public static function injections(): array
	{
		return [
			'token predicate' => ['tokencountperyear.php', 'token', 'woda" OR "1"="1'],
			'token statement' => ['tokencountperyear.php', 'token', 'woda"; DROP TABLE tokendatecount; --'],
			'word predicate' => ['prefixsearch.php', 'word', 'wo" OR "1"="1" --'],
			'word statement' => ['prefixsearch.php', 'word', 'wo"; DROP TABLE tokencount; --'],
		];
	}

	#[DataProvider('injections')]
	public function testInjectedSearchTextIsLiteralAndPreservesTables(string $endpoint, string $parameter, string $payload): void
	{
		$response = $this->request($endpoint, [$parameter => $payload]);
		$timeline = $this->request('tokencountperyear.php', ['token' => 'woni', 'cs' => 1]);
		$suggestions = $this->request('prefixsearch.php', ['word' => 'wo', 'sortby' => 'frequency']);

		$this->assertResponse($timeline, [['woni', 1900, 284]]);
		$this->assertResponse($suggestions, self::SUGGESTIONS);
		$this->assertTablesIntact();
		$this->assertResponse($response, []);
	}

	public static function clickedTokens(): array
	{
		return [
			'lowercase surface form' => ['woda', [['woda', 1870, 10]]],
			'capitalized surface form' => ['Woda', [['Woda', 1880, 1]]],
		];
	}

	#[DataProvider('clickedTokens')]
	public function testVariationClickExactOptionsReturnOnlyClickedToken(string $token, array $rows): void
	{
		$response = $this->request('tokencountperyear.php', [
			'token' => $token, 'cs' => 1, 'regex' => 0, 'list' => 0,
			'trim' => 1, 'ambig' => 0, 'sort' => '',
		]);

		$this->assertResponse($response, $rows);
	}

	private function insertToken(string $token, int $frequency, ?int $date = null, ?int $yearFrequency = null): void
	{
		$statement = $this->pdo->prepare('INSERT INTO tokencount VALUES (:token, :frequency, :sortkey)');
		$statement->execute(['token' => $token, 'frequency' => $frequency, 'sortkey' => dsb_sortkey($token)]);
		if ($date !== null) {
			$statement = $this->pdo->prepare('INSERT INTO tokendatecount VALUES (:token, :date, :frequency)');
			$statement->execute(['token' => $token, 'date' => $date, 'frequency' => $yearFrequency]);
		}
	}

	private function request(string $endpoint, array $query): array
	{
		return $this->server->get('/php/' . $endpoint . '?' . http_build_query($query));
	}

	private function assertResponse(array $response, array $rows): void
	{
		$lines = array_map(static fn(array $row): string => implode(chr(9), $row), $rows);
		$body = $lines === [] ? '' : implode(PHP_EOL, $lines) . PHP_EOL;

		$this->assertSame(200, $response['status']);
		$this->assertSame($body, $response['body']);
		$this->assertMatchesRegularExpression('/^Content-Type:\s*text\/plain/im', implode(PHP_EOL, $response['headers']));
	}

	private function assertTablesIntact(): void
	{
		$this->assertSame(4, (int) $this->pdo->query('SELECT COUNT(*) FROM tokencount')->fetchColumn());
		$this->assertSame(4, (int) $this->pdo->query('SELECT COUNT(*) FROM tokendatecount')->fetchColumn());
	}
}