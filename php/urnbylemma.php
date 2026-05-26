<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])){
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT urn, date FROM urndatelemmabag WHERE lemmabag LIKE "%|'.str_replace(",",'|%" OR lemmabag LIKE "%|',$_GET['lemma']).'|%"';

	(isset($_GET['year'])) ? $query .= ' AND date '.$_GET['year'] : NULL;
	(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

	$tab = "\t";
	$nl = "\n";
	$res = '';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['urn'].$tab.$row['date'].$nl;
	}
	print($res);
}

?>
