<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$pdo = new PDO('sqlite:../data/lemmamapping.db');
$cells = resolve_request_cells($pdo, 'lemma', $_GET);
$year = year_clause(isset($_GET['year']) ? (string) $_GET['year'] : null);

if ($cells === [] || $year === null) {
	exit;
}

$cellClause = in_clause('lemma', $cells);
$query = 'SELECT lemma, token, SUM(frequency) AS sumfreq FROM tokenlemmatypesubtypedatefrequency WHERE '
	. $cellClause['sql'] . ' AND ' . $year['sql'] . ' GROUP BY lemma, token';
if (array_key_exists('sort', $_GET)) {
	$query .= ' ORDER BY sumfreq DESC, token';
}

$statement = $pdo->prepare($query);
$statement->execute([...$cellClause['params'], ...$year['params']]);

$res = '';
foreach ($statement as $row) {
	$res .= $row['lemma'] . "\t" . $row['token'] . "\t" . $row['sumfreq'] . "\n";
}
print($res);
