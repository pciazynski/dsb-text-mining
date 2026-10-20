<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$pdo = new PDO('sqlite:../data/bagofwords.db');
$tokens = resolve_request_cells($pdo, 'token', $_GET);
if ($tokens === []) {
	exit;
}

$tokenClause = in_clause('token', $tokens);
$query = 'SELECT token, date, frequency FROM tokendatecount WHERE ' . $tokenClause['sql'];
if (array_key_exists('sort', $_GET)) {
	$query .= ' ORDER BY date ASC';
}

$statement = $pdo->prepare($query);
$statement->execute($tokenClause['params']);

$tab = "\t";
$nl = "\n";
$res = '';

foreach ($statement as $row) {
	$res .= $row['token'] . $tab . $row['date'] . $tab . $row['frequency'] . $nl;
}
print($res);
