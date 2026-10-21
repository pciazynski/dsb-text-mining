<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency
require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$PDO = new PDO('sqlite:../data/normmapping.db');
$cells = resolve_request_cells($PDO, 'norm', $_GET);
if ($cells === []) {
	exit;
}

$clause = in_clause('norm', $cells);
$query = 'SELECT * FROM tokennormtypesubtypedatefrequency WHERE ' . $clause['sql'];
if (array_key_exists('sort', $_GET)) {
	$query .= ' ORDER BY date ASC';
}

$statement = $PDO->prepare($query);
$statement->execute($clause['params']);

$res = '';
foreach ($statement as $row) {
	$res .= $row['norm'] . "\t" . $row['date'] . "\t" . $row['frequency'] . "\t" . $row['token'] . "\n";
}
print($res);
