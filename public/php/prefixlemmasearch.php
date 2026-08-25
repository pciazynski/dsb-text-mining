<?php

/**
 * Autocomplete suggestions for the lemma search box (newline-separated plain text).
 *
 * Called on every keystroke, so both sort orders must stay on a prefix range scan
 * of an index: sortkey for the case-insensitive default, lemma for ci=0.
 */

header('Content-Type: text/plain');
require_once __DIR__ . '/dsb_collation.php';

if (!isset($_GET['lemma']) || $_GET['lemma'] === '') {
	return;
}

$lemma = $_GET['lemma'];
$limit = isset($_GET['limit']) && ctype_digit($_GET['limit']) && (int) $_GET['limit'] > 0
	? (int) $_GET['limit']
	: 100;
$limit = min($limit, 100);
$sortby = ($_GET['sortby'] ?? '') === 'alphabet' ? 'sortkey ASC' : 'frequency DESC';
$caseInsensitive = ($_GET['ci'] ?? '1') !== '0';
$column = $caseInsensitive ? 'sortkey' : 'lemma';
// Both columns are ordered prefixes, so "prefix <= value < prefix\xFF" is a range scan.
$prefix = $caseInsensitive ? dsb_sortkey($lemma) : '|' . $lemma;
$cutoff = isset($_GET['cutoff']) && ctype_digit($_GET['cutoff'])
	? (int) $_GET['cutoff']
	: null;

// No DISTINCT: lemmanonambig holds one row per lemma, and deduplicating would cost
// a temp B-tree over the whole prefix range instead of stopping at LIMIT.
$query = "SELECT lemma FROM lemmanonambig
	WHERE {$column} >= :lower AND {$column} < :upper";
if ($cutoff !== null) {
	$query .= ' AND length(lemma) <= :maximumLength';
}
$query .= " ORDER BY {$sortby} LIMIT :limit";

$pdo = new PDO('sqlite:../data/lemmamapping.db');
$statement = $pdo->prepare($query);
$statement->bindValue(':lower', $prefix, PDO::PARAM_STR);
$statement->bindValue(':upper', $prefix . "\xFF", PDO::PARAM_STR);
$statement->bindValue(':limit', $limit, PDO::PARAM_INT);
if ($cutoff !== null) {
	// length() counts the two "|" delimiters, hence the + 2.
	$statement->bindValue(':maximumLength', mb_strlen($lemma, 'UTF-8') + $cutoff + 2, PDO::PARAM_INT);
}
$statement->execute();

$lemmas = array();
foreach ($statement as $row) {
	$lemmas[] = trim($row['lemma'], '|');
}

print(implode("\n", $lemmas) . (count($lemmas) ? "\n" : ''));
