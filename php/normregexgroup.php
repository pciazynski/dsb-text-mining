<?php
header('Content-Type: text/plain');

if (isset($_GET['norm'])){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^".$pattern."$/", $string)) ? $hit = true : $hit =  false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);
	$query = 'SELECT norm, sum(frequency) as sumfreq FROM tokennormtypesubtypedatefrequency WHERE norm REGEXP "\|'.$_GET['norm'].'\|" GROUP BY norm ';

	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC' : NULL;

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['norm'].$tab.$row['sumfreq'].$nl;
	}
	print($res);
}
?>
