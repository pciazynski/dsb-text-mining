<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$pdo = new PDO('sqlite:../data/normmapping.db');
$cells = resolve_request_cells($pdo, 'norm', $_GET);
$year = year_clause(isset($_GET['year']) ? (string) $_GET['year'] : null);

if ($cells === [] || $year === null) {
	exit;
}

$cellClause = in_clause('norm', $cells);
$query = 'SELECT norm, token, SUM(frequency) AS sumfreq FROM tokennormtypesubtypedatefrequency WHERE '
	. $cellClause['sql'] . ' AND ' . $year['sql'] . ' GROUP BY norm, token';
if (array_key_exists('sort', $_GET)) {
	$query .= ' ORDER BY sumfreq DESC, token';
}

$statement = $pdo->prepare($query);
$statement->execute([...$cellClause['params'], ...$year['params']]);

$res = '';
foreach ($statement as $row) {
	$res .= $row['norm'] . "\t" . $row['token'] . "\t" . $row['sumfreq'] . "\n";
}
print($res);
