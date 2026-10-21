<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

if (isset($_GET['norm'])) {
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$cellSet = array_flip(resolve_request_cells($PDO, 'norm', $_GET));

	if ($cellSet === []) {
		exit;
	}

	$yearClause = array_key_exists('year', $_GET)
		? year_clause((string) $_GET['year'])
		: ['sql' => '1=1', 'params' => []];
	if ($yearClause === null) {
		return;
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
		foreach (explode('||', trim($row['normbag'], '|')) as $normCell) {
			if (isset($cellSet['|' . $normCell . '|'])) {
				$matches = true;
				break;
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
