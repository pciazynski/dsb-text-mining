<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/searchfilter.php';

function literal_lemma_matches(string $lemmaCell, string $searchLemma, bool $caseSensitive): bool
{
	if (str_contains($searchLemma, '|')) {
		$candidate = '|' . trim($lemmaCell, '|') . '|';
		$target = '|' . trim($searchLemma, '|') . '|';
		return $caseSensitive
			? $candidate === $target
			: mb_strtolower($candidate, 'UTF-8') === mb_strtolower($target, 'UTF-8');
	}

	foreach (explode('|', $lemmaCell) as $lemma) {
		if ($lemma === '') {
			continue;
		}

		$match = $caseSensitive
			? $searchLemma === $lemma
			: mb_strtoupper($searchLemma, 'UTF-8') === mb_strtoupper($lemma, 'UTF-8');
		if ($match) {
			return true;
		}
	}

	return false;
}

function exact_cell_lemma_match(string $lemmaCell, string $searchLemma, bool $caseSensitive): bool
{
	if (!str_contains($searchLemma, '|')) {
		return false;
	}

	$candidate = '|' . trim($lemmaCell, '|') . '|';
	$target = '|' . trim($searchLemma, '|') . '|';
	return $caseSensitive
		? $candidate === $target
		: mb_strtolower($candidate, 'UTF-8') === mb_strtolower($target, 'UTF-8');
}

function regex_lemma_matches(string $lemmaCell, string $searchLemma, bool $caseSensitive): bool
{
	$pattern = compile_term_pattern($searchLemma, ['regex' => true, 'cs' => $caseSensitive]);
	if ($pattern === null) {
		return false;
	}

	foreach (explode('|', $lemmaCell) as $lemma) {
		if ($lemma !== '' && preg_match($pattern, $lemma) === 1) {
			return true;
		}
	}

	return false;
}

if (isset($_GET['lemma'])) {
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$options = search_options($_GET);
	$lemmas = split_terms((string) ($_GET['lemma'] ?? ''), $options);

	if ($lemmas === []) {
		exit;
	}

	$includeAmbiguous = $options['ambig'];
	$caseSensitive = $options['cs'];
	$useRegex = $options['regex'];

	$yearClause = array_key_exists('year', $_GET)
		? year_clause((string) $_GET['year'])
		: null;
	if ($yearClause === null && array_key_exists('year', $_GET)) {
		return;
	}

	$nonAmbigLemmas = [];
	if (!$includeAmbiguous) {
		$stmt = $PDO->prepare('SELECT lemma FROM lemmanonambig');
		$stmt->execute();
		foreach ($stmt->fetchAll(PDO::FETCH_COLUMN) as $lemma) {
			$nonAmbigLemmas[$lemma] = true;
		}
	}

	$query = 'SELECT urn, date, lemmabag FROM urndatelemmabag WHERE 1=1';
	$params = [];
	if ($yearClause !== null) {
		$query .= ' AND ' . $yearClause['sql'];
		$params = $yearClause['params'];
	}

	if (isset($_GET['sort'])) {
		$query .= ' ORDER BY date ASC';
	}

	$stmt = $PDO->prepare($query);
	$res = '';
	$results = [];

	try {
		$stmt->execute($params);
		foreach ($stmt as $row) {
			$matches = false;
			foreach (array_filter(explode('||', trim($row['lemmabag'], '|')), static fn(string $lemmaCell): bool => $lemmaCell !== '') as $lemmaCell) {
				foreach ($lemmas as $searchLemma) {
					if ($useRegex) {
						$match = regex_lemma_matches($lemmaCell, $searchLemma, $caseSensitive);
						$allowed = $match && ($includeAmbiguous || isset($nonAmbigLemmas['|' . trim($lemmaCell, '|') . '|']));
					} else {
						$match = literal_lemma_matches($lemmaCell, $searchLemma, $caseSensitive);
						$allowed = $match && ($includeAmbiguous || isset($nonAmbigLemmas['|' . trim($lemmaCell, '|') . '|']) || exact_cell_lemma_match($lemmaCell, $searchLemma, $caseSensitive));
					}

					if ($allowed) {
						$matches = true;
						break 2;
					}
				}
			}

			if ($matches) {
				$results[$row['urn']] = $row['date'];
			}
		}

		foreach ($results as $urn => $date) {
			$res .= $urn . "\t" . $date . "\n";
		}
	} catch (Exception) {
	}

	print($res);
}
