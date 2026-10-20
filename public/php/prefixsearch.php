<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';

if (!isset($_GET['word']) || !is_string($_GET['word']) || $_GET['word'] === '') {
	return;
}

$word = $_GET['word'];
$limit = isset($_GET['limit']) ? (int) $_GET['limit'] : 100;
$limit = $limit > 0 ? min($limit, 100) : 100;
$caseSensitive = ($_GET['cs'] ?? '0') === '1';
$sortby = ($_GET['sortby'] ?? '') === 'alphabet' ? 'sortkey ASC' : 'frequency DESC';
$column = $caseSensitive ? 'token' : 'sortkey';
$prefix = $caseSensitive ? $word : dsb_sortkey($word);

$pdo = new PDO('sqlite:../data/bagofwords.db');
$query = "SELECT DISTINCT token FROM tokencount
	WHERE {$column} >= :lower AND {$column} < :upper
	ORDER BY {$sortby} LIMIT :limit";
$statement = $pdo->prepare($query);
$statement->bindValue(':lower', $prefix, PDO::PARAM_STR);
$statement->bindValue(':upper', $prefix . "\xFF", PDO::PARAM_STR);
$statement->bindValue(':limit', $limit, PDO::PARAM_INT);
$statement->execute();

$nl = "\n";
$tokens = array();
foreach ($statement as $row) {
	$tokens[] = $row['token'];
}

print(implode($nl, $tokens) . (count($tokens) ? $nl : ''));
