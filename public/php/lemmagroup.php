<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

$pdo = new PDO('sqlite:../data/lemmamapping.db');
$options = search_options($_GET);
$terms = split_terms((string) ($_GET['lemma'] ?? ''), $options);

if ($terms === []) {
	exit;
}

$cells = resolve_cells($pdo, 'lemma', $terms, $options);
if ($cells === []) {
	exit;
}

if (array_key_exists('sort', $_GET)) {
	$placeholders = implode(',', array_fill(0, count($cells), '?'));
	$statement = $pdo->prepare(
		'SELECT lemma, SUM(frequency) AS sumfreq FROM tokenlemmatypesubtypedatefrequency WHERE lemma IN (' . $placeholders . ') GROUP BY lemma ORDER BY sumfreq DESC',
	);
	$statement->execute($cells);

	$res = '';
	foreach ($statement as $row) {
		$res .= $row['lemma'] . "\t" . (int) $row['sumfreq'] . "\n";
	}
	print($res);
	exit;
}

usort($cells, static function (string $left, string $right): int {
	$leftLemma = trim($left, '|');
	$rightLemma = trim($right, '|');

	$leftPrefer = $leftLemma === mb_strtoupper($leftLemma, 'UTF-8') ? 1 : 0;
	$rightPrefer = $rightLemma === mb_strtoupper($rightLemma, 'UTF-8') ? 1 : 0;

	return $rightPrefer <=> $leftPrefer;
});

$placeholders = implode(',', array_fill(0, count($cells), '?'));
$statement = $pdo->prepare(
	'SELECT lemma, frequency FROM lemmafrequency WHERE lemma IN (' . $placeholders . ')',
);
$statement->execute($cells);

$frequencies = [];
foreach ($statement as $row) {
	$frequencies[$row['lemma']] = (int) $row['frequency'];
}

$res = '';
foreach ($cells as $cell) {
	if (!array_key_exists($cell, $frequencies)) {
		continue;
	}

	$res .= $cell . "\t" . $frequencies[$cell] . "\n";
}

print($res);
