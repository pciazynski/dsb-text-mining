<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$pdo = new PDO('sqlite:../data/lemmamapping.db');
$cells = resolve_request_cells($pdo, 'lemma', $_GET);

if ($cells === []) {
	exit;
}

$clause = in_clause('lemma', $cells);
$query = 'SELECT lemma, SUM(frequency) AS summe, date FROM tokenlemmatypesubtypedatefrequency WHERE ' . $clause['sql'];
$query .= ' GROUP BY lemma, date';
if (array_key_exists('sort', $_GET)) {
	$query .= ' ORDER BY date ASC';
}

$statement = $pdo->prepare($query);
$statement->execute($clause['params']);

$res = '';
foreach ($statement as $row) {
	$res .= $row['lemma'] . "\t" . $row['date'] . "\t" . $row['summe'] . "\n";
}
print($res);
