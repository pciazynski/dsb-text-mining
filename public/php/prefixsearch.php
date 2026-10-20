<?php
header('Content-Type: text/plain');

(isset($_GET['word'])) ? $word = $_GET['word'] :  $word = '';

if (strlen($word) >= 1) {
	(isset($_GET['limit'])) ? $limit = (int)$_GET['limit'] : $limit = 100;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(word,0,' . strlen($word) + $_GET['cutoff'] . ')' : $cutoff = "";

	if (isset($_GET['sortby'])) {
		if ($_GET['sortby'] == 'alphabet') {
			# Wortformen: alphabet mode uses Unicode token order (not dsb sortkey).
			$sortby = ' ORDER BY token ASC';
			$sqlLimit = ' LIMIT ' . $limit;
		} else {
			$sortby = ' ORDER BY ' . $_GET['sortby'] . ' DESC';
			$sqlLimit = ' LIMIT ' . $limit;
		}
	} else {
		$sortby = '';
		$sqlLimit = ' LIMIT ' . $limit;
	}

	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$query = 'SELECT DISTINCT token FROM tokencount WHERE token LIKE "' . $word . '%"' . $cutoff . $sortby . $sqlLimit;

	$nl = "\n";
	$tokens = array();
	foreach ($PDO->query($query . ';') as $row) {
		$tokens[] = $row['token'];
	}

	print(implode($nl, $tokens) . (count($tokens) ? $nl : ''));
}
