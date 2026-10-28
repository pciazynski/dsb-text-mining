<?php
header('Content-Type: text/plain');

if (isset($_GET['char'])){
	$PDO = new PDO('sqlite:../data/characters.db');
	$query = 'SELECT urn, date FROM urncharbag WHERE charbag LIKE "%|'.str_replace(",",'|%" OR charbag LIKE "%|',$_GET['char']).'|%"';

	(isset($_GET['year'])) ? $query .= ' AND date =='.$_GET['year'] : NULL;
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
