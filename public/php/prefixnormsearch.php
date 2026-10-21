<?php
header('Content-Type: text/plain');
require_once __DIR__ . '/dsb_collation.php';

if (!isset($_GET['norm']) || !is_string($_GET['norm']) || $_GET['norm'] === '') {
	return;
}

$norm = $_GET['norm'];
$limit = isset($_GET['limit']) && is_string($_GET['limit']) && ctype_digit($_GET['limit']) && (int) $_GET['limit'] > 0
	? min((int) $_GET['limit'], 100)
	: 100;
$sortby = ($_GET['sortby'] ?? '') === 'alphabet' ? 'sortkey ASC' : 'frequency DESC';
$caseSensitive = ($_GET['cs'] ?? '0') === '1';
$column = $caseSensitive ? 'norm' : 'sortkey';
$prefix = $caseSensitive ? '|' . $norm : dsb_sortkey($norm);
$cutoff = isset($_GET['cutoff']) && is_string($_GET['cutoff']) && ctype_digit($_GET['cutoff'])
	? (int) $_GET['cutoff']
	: null;

$query = "SELECT norm FROM normnonambig
	WHERE {$column} >= :lower AND {$column} < :upper";
if ($cutoff !== null) {
	$query .= ' GROUP BY SUBSTR(norm, 1, :groupLength)';
}
$query .= " ORDER BY {$sortby} LIMIT :limit";

$pdo = new PDO('sqlite:../data/normmapping.db');
$statement = $pdo->prepare($query);
$statement->bindValue(':lower', $prefix, PDO::PARAM_STR);
$statement->bindValue(':upper', $prefix . "\xFF", PDO::PARAM_STR);
$statement->bindValue(':limit', $limit, PDO::PARAM_INT);
if ($cutoff !== null) {
	$statement->bindValue(':groupLength', mb_strlen($norm, 'UTF-8') + $cutoff + 1, PDO::PARAM_INT);
}
$statement->execute();

$norms = array();
foreach ($statement as $row) {
	$norms[] = trim($row['norm'], '|');
}

print(implode("\n", $norms) . (count($norms) ? "\n" : ''));
