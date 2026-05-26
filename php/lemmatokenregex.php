<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])){

	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^".$pattern."$/", $string)) ? $hit = true : $hit =  false;
		return $hit;
	}
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);

	$query = 'SELECT token, lemma, frequency FROM lemmatokenfrequency';
	$query .= ' WHERE lemma REGEXP "\|'.$_GET['lemma'].'\|"';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY frequency DESC' : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.";") as $row){
		$res.=$row['lemma'].$tab.$row['token'].$tab.$row['frequency'].$nl;
	}
	print($res);
}
?>
