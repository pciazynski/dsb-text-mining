<?php
header('Content-Type: text/plain');

if (isset($_GET['norm'])){
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^" . $pattern . "$/u", $string) === 1) ? $hit = true : $hit = false;
		return $hit;
	}
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);
	(isset($_GET['exact'])) ? $regexp = '\|'.$_GET['norm'].'\|' : $regexp = '.*\|'.$_GET['norm'].'\|.*';
	$query = 'SELECT norm, token, SUM(frequency) as sumfreq FROM tokennormtypesubtypedatefrequency WHERE norm REGEXP "'.$regexp.'"  LIMIT 2100000';
	(isset($_GET['year'])) ? $query .= ' AND date '.$_GET['year'] : NULL;
	$query.=' GROUP BY token,norm';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC' : NULL;
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.";") as $row){
		$res.=$row['norm'].$tab.$row['token'].$tab.$row['sumfreq'].$nl;
	}
	print($res);
}
?>
