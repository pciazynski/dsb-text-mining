<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/searchfilter.php';

function literal_norm_matches(string $normCell, string $searchNorm, bool $caseSensitive): bool
{
	if (str_contains($searchNorm, '|')) {
		return exact_cell_norm_match($normCell, $searchNorm, $caseSensitive);
	}

	foreach (explode('|', $normCell) as $norm) {
		if ($norm === '') {
			continue;
		}

		$match = $caseSensitive
			? $searchNorm === $norm
			: mb_strtolower($searchNorm, 'UTF-8') === mb_strtolower($norm, 'UTF-8');
		if ($match) {
			return true;
		}
	}

	return false;
}

function exact_cell_norm_match(string $normCell, string $searchNorm, bool $caseSensitive): bool
{
	if (!str_contains($searchNorm, '|')) {
		return false;
	}

	$candidate = '|' . trim($normCell, '|') . '|';
	$target = '|' . trim($searchNorm, '|') . '|';
	return $caseSensitive
		? $candidate === $target
		: mb_strtolower($candidate, 'UTF-8') === mb_strtolower($target, 'UTF-8');
}

function regex_norm_matches(string $normCell, string $searchNorm, bool $caseSensitive): bool
{
	$pattern = compile_term_pattern($searchNorm, ['regex' => true, 'cs' => $caseSensitive]);
	if ($pattern === null) {
		return false;
	}

	foreach (explode('|', $normCell) as $norm) {
		if ($norm !== '' && preg_match($pattern, $norm) === 1) {
			return true;
		}
	}

	return false;
}

if (isset($_GET['norm'])) {
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$options = search_options($_GET);
	$norms = split_terms((string) ($_GET['norm'] ?? ''), $options);

	if ($norms === []) {
		exit;
	}

	$includeAmbiguous = $options['ambig'];
	$caseSensitive = $options['cs'];
	$useRegex = $options['regex'];
	$yearClause = array_key_exists('year', $_GET)
		? year_clause((string) $_GET['year'])
		: ['sql' => '1=1', 'params' => []];
	if ($yearClause === null) {
		return;
	}

	$nonAmbigNorms = [];
	if (!$includeAmbiguous) {
		$stmt = $PDO->prepare('SELECT norm FROM normnonambig');
		$stmt->execute();
		foreach ($stmt->fetchAll(PDO::FETCH_COLUMN) as $norm) {
			$nonAmbigNorms[$norm] = true;
		}
	}

	$query = 'SELECT urn, date, normbag FROM urndatenormbag WHERE ' . $yearClause['sql'];
	if (isset($_GET['sort'])) {
		$query .= ' ORDER BY date ASC';
	}

	$stmt = $PDO->prepare($query);
	$stmt->execute($yearClause['params']);
	$results = [];
	foreach ($stmt as $row) {
		$matches = false;
		$normCells = array_filter(explode('||', trim($row['normbag'], '|')), static fn(string $normCell): bool => $normCell !== '');
		foreach ($normCells as $normCell) {
			foreach ($norms as $searchNorm) {
				if ($useRegex) {
					$match = regex_norm_matches($normCell, $searchNorm, $caseSensitive);
					$allowed = $match && ($includeAmbiguous || isset($nonAmbigNorms['|' . trim($normCell, '|') . '|']));
				} else {
					$match = literal_norm_matches($normCell, $searchNorm, $caseSensitive);
					$allowed = $match && ($includeAmbiguous || isset($nonAmbigNorms['|' . trim($normCell, '|') . '|']) || exact_cell_norm_match($normCell, $searchNorm, $caseSensitive));
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

	$res = '';
	foreach ($results as $urn => $date) {
		$res .= $urn . "\t" . $date . "\n";
	}
	print($res);
}
