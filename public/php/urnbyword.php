<?php
header('Content-Type: text/plain');

if (isset($_GET['word'])){
	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$query = 'SELECT urn, date FROM urndatewordbag WHERE wordbag LIKE "%|'.str_replace(",",'|%" OR wordbag LIKE "%|',$_GET['word']).'|%"';

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
