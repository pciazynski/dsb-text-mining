<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^".$pattern."$/", $string)) ? $hit = true : $hit =  false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);
	$query = 'SELECT lemma, sum(frequency) as sumfreq FROM tokenlemmatypesubtypedatefrequency WHERE lemma REGEXP "\|'.$_GET['lemma'].'\|" GROUP BY lemma ';

	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC' : NULL;

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$tab.$row['sumfreq'].$nl;
	}
	print($res);
}
?>
