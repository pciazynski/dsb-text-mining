<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^" . $pattern . "$/u", $string) === 1) ? $hit = true : $hit = false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);
	(isset($_GET['exact']) and $_GET['exact'] !== '0') ? $regexp = '\|'.$_GET['lemma'].'\|' : $regexp = '.*\|'.$_GET['lemma'].'\|.*';
	$query = 'SELECT lemma, sum(frequency) as sumfreq FROM tokenlemmatypesubtypedatefrequency WHERE lemma REGEXP ? GROUP BY lemma ';

	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC' : NULL;

	$tab = "\t";
	$nl = "\n";
	$res = '';

	$stmt = $PDO->prepare($query);
	$stmt->execute([$regexp]);
	foreach($stmt as $row){
		$res.=$row['lemma'].$tab.$row['sumfreq'].$nl;
	}
	print($res);
}
?>
