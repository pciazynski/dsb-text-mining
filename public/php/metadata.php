<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');

$slim = isset($_GET['slim']);
$query = $slim ? 'SELECT urn FROM docmeta WHERE 1=1' : 'SELECT * FROM docmeta WHERE 1=1';
$params = [];

$filters = [
	'author' => 'author',
	'restricted' => 'restricted',
	'year' => 'date',
	'lang' => 'lang',
];
foreach ($filters as $parameter => $column) {
	if (isset($_GET[$parameter])) {
		$query .= " AND {$column} = ?";
		$params[] = $_GET[$parameter];
	}
}
if (isset($_GET['sort'])) {
	$query .= ' ORDER BY date ASC';
}

$stmt = $PDO->prepare($query);
$stmt->execute($params);

$res = '';

if ($slim) {
	foreach ($stmt as $row) {
		$res .= $row['urn'] . "\n";
	}
} else {
	foreach ($stmt as $row) {
		$res .= implode("\t", [
			$row['urn'],
			$row['title'],
			$row['date'],
			$row['author'],
			$row['restricted'],
			$row['lang'],
		]) . "\n";
	}
}
print($res);
