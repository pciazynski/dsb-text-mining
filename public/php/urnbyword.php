<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/searchfilter.php';

if (!isset($_GET['word']) || !is_string($_GET['word']) || trim($_GET['word']) === '') {
	exit;
}

if (array_key_exists('year', $_GET) && !is_string($_GET['year'])) {
	exit;
}

$yearClause = year_clause(array_key_exists('year', $_GET) ? $_GET['year'] : null);
if ($yearClause === null) {
	exit;
}

$terms = explode(',', $_GET['word']);
$conditions = array_fill(0, count($terms), 'wordbag LIKE ?');
$params = array_map(static fn(string $term): string => '%|' . $term . '|%', $terms);
$query = 'SELECT urn, date FROM urndatewordbag WHERE (' . implode(' OR ', $conditions) . ') AND ' . $yearClause['sql'];
$params = [...$params, ...$yearClause['params']];

if (isset($_GET['sort'])) {
	$query .= ' ORDER BY date ASC';
}

$PDO = new PDO('sqlite:../data/bagofwords.db');
$statement = $PDO->prepare($query);
$statement->execute($params);
$res = '';
foreach ($statement as $row) {
	$res .= $row['urn'] . "\t" . $row['date'] . "\n";
}
print($res);
