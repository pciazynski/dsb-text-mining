<?php
header('Content-Type: text/plain');

if (isset($_GET['norm'])){
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$query = 'SELECT urn, date FROM urndatenormbag WHERE normbag LIKE "%|'.str_replace(",",'|%" OR normbag LIKE "%|',$_GET['norm']).'|%"';

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
