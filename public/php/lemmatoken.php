<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])){
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT token, lemma, frequency FROM lemmatokenfrequency';
	(isset($_GET['exact']) and $_GET['exact']==1) ? $query .= ' WHERE lemma = "|'.str_replace(',','|" OR lemma = "|',$_GET['lemma']).'|"' : $query .= ' WHERE lemma LIKE "%|'.str_replace(',','|%" OR lemma LIKE "%|',$_GET['lemma']).'|%"';
	
	(isset($_GET['sort'])) ? $query .= ' ORDER BY frequency DESC, token' : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$tab.$row['token'].$tab.$row['frequency'].$nl;
	}
	print($res);
}
?>
