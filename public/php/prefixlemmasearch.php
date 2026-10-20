<?php
header('Content-Type: text/plain');
require_once __DIR__ . '/dsb_collation.php';

(isset($_GET['lemma'])) ? $lemma = $_GET['lemma'] : NULL;

if (strlen($lemma) >= 1) {

	#Workaround bc LIKE is case sensitive for multibyte. Does not apply to normprefixsearch.
	$lemma = mb_strtoupper($lemma, 'UTF-8');

	(isset($_GET['limit'])) ? $limit = (int)$_GET['limit'] : $limit = 100;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(lemma,1,' . strlen($lemma) + $_GET['cutoff'] . ')' : $cutoff = '';
	(isset($_GET['ambig'])) ? $dbname = 'lemmafrequency' : $dbname = 'lemmanonambig';
	$where = ' WHERE lemma LIKE "|' . $lemma . '%"';

	if (isset($_GET['sortby'])) {
		if ($_GET['sortby'] == 'alphabet') {
			$sortkeyPrefix = dsb_sortkey($lemma);
			# Prefix filter on sortkey keeps modern dsb alphabet sorting fast on large ranges.
			$where .= ' AND sortkey LIKE "' . $sortkeyPrefix . '%"';
			$sortby = ' ORDER BY sortkey ASC';
			$sqlLimit = ' LIMIT ' . $limit;
		} else {
			$sortby = ' ORDER BY ' . $_GET['sortby'] . ' DESC';
			$sqlLimit = ' LIMIT ' . $limit;
		}
	} else {
		$sortby = '';
		$sqlLimit = ' LIMIT ' . $limit;
	}

	$query = 'SELECT DISTINCT lemma FROM ' . $dbname . $where . $cutoff . $sortby . $sqlLimit;

	$nl = "\n";
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$lemmas = array();
	foreach ($PDO->query($query . ';') as $row) {
		$lemmas[] = trim($row['lemma'], "|");
	}

	print(implode($nl, $lemmas) . (count($lemmas) ? $nl : ''));
}
