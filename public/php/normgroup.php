<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$PDO = new PDO('sqlite:../data/normmapping.db');
$cells = resolve_request_cells($PDO, 'norm', $_GET);
if ($cells === []) {
	exit;
}

$clause = in_clause('norm', $cells);
$query = 'SELECT norm, SUM(frequency) as sumfreq FROM tokennormtypesubtypedatefrequency WHERE '
	. $clause['sql'] . ' GROUP BY norm';
if (array_key_exists('sort', $_GET)) {
	$query .= ' ORDER BY sumfreq DESC';
}

$statement = $PDO->prepare($query);
$statement->execute($clause['params']);

$res = '';
foreach ($statement as $row) {
	$res .= $row['norm'] . "\t" . $row['sumfreq'] . "\n";
}
print($res);
