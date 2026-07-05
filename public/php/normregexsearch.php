<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency

if (isset($_GET['norm'])) {
	function _sqliteRegexp($pattern, $string)
	{
		(preg_match("/^" . $pattern . "$/u", $string) === 1) ? $hit = true : $hit = false;
		return $hit;
	}

	$PDO = new PDO('sqlite:../data/normmapping.db');
	(isset($_GET['exact']) and $_GET['exact'] !== '0') ? $regexp = '\|' . $_GET['norm'] . '\|' : $regexp = '.*\|' . $_GET['norm'] . '\|.*';
	$query = 'SELECT * FROM tokennormtypesubtypedatefrequency WHERE norm REGEXP ? LIMIT 2100000';

	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);

	$tab = "\t";
	$nl = "\n";
	$res = '';

	$stmt = $PDO->prepare($query);
	$stmt->execute([$regexp]);
	foreach ($stmt as $row) {
		$res .= $row['norm'] . $tab . $row['date'] . $tab . $row['frequency'] . $tab . $row['token'] . $nl;
	}
	print($res);
}
