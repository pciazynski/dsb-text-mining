<?php
header('Content-Type: text/plain');

if (isset($_GET['filter'])){
	$n = $_GET['n'];
	$PDO = new PDO('sqlite:../data/ngram'.$n.'.db');
	$query = 'SELECT * FROM ngramdatecount WHERE ngram = " '.$_GET['filter'].' "';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

	$res = '';
	$nl = "\n";
	$tab = "\t";

	foreach($PDO->query($query.";") as $row){
		$res.=$row['ngram'].$tab.$row['date'].$tab.$row['frequency'].$nl;
	}
	print($res);
}
?>
