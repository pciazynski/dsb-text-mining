<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

if (isset($_GET['lemma'])) {
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$cellSet = array_flip(resolve_request_cells($PDO, 'lemma', $_GET));

	if ($cellSet === []) {
		exit;
	}

	$yearClause = array_key_exists('year', $_GET)
		? year_clause((string) $_GET['year'])
		: null;
	if ($yearClause === null && array_key_exists('year', $_GET)) {
		return;
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

	$stmt->execute($params);
	foreach ($stmt as $row) {
		$matches = false;
		foreach (explode('||', trim($row['lemmabag'], '|')) as $lemmaCell) {
			if (isset($cellSet['|' . $lemmaCell . '|'])) {
				$matches = true;
				break;
			}
		}

		if ($matches) {
			$results[$row['urn']] = $row['date'];
		}
	}

	foreach ($results as $urn => $date) {
		$res .= $urn . "\t" . $date . "\n";
	}

	print($res);
}
