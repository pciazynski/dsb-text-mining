<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])) {
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	function _sqliteRegexp($pattern, $string)
	{
		(preg_match("/^" . $pattern . "$/u", $string) === 1) ? $hit = true : $hit = false;
		return $hit;
	}
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);
	(isset($_GET['exact']) and $_GET['exact'] !== '0') ? $regexp = '\|' . $_GET['lemma'] . '\|' : $regexp = '.*\|' . $_GET['lemma'] . '\|.*';
	$params = [$regexp];
	$query = 'SELECT lemma, token, SUM(frequency) as sumfreq FROM tokenlemmatypesubtypedatefrequency WHERE lemma REGEXP ?';
	if (isset($_GET['year']) and preg_match('/(\d+)\D+(\d+)/', $_GET['year'], $y)) {
		$query .= ' AND date BETWEEN ? AND ?';
		$params[] = (int)$y[1];
		$params[] = (int)$y[2];
	}
	$query .= ' GROUP BY token,lemma';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC' : NULL;
	$tab = "\t";
	$nl = "\n";
	$res = '';
	$stmt = $PDO->prepare($query . "  LIMIT 2100000;");
	$stmt->execute($params);
	foreach ($stmt as $row) {
		$res .= $row['lemma'] . $tab . $row['token'] . $tab . $row['sumfreq'] . $nl;
	}
	print($res);
}
