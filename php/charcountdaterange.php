<?php
header('Content-Type: text/plain');

if(isset($_GET['year']))
{
	$PDO = new PDO('sqlite:../data/characters.db');
	$query = 'SELECT char, SUM(frequency) as summe FROM chardatecount WHERE date '.$_GET['year'];

	(isset($_GET['char'])) ? $query .= ' AND char ="'.$_GET['char'].'"' : NULL;
	$query .= ' GROUP BY char';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY summe DESC' : NULL;
	(isset($_GET['limit'])) ? $query .= ' LIMIT '.$_GET['limit'] : $query .= ' LIMIT 10000' ;
	(isset($_GET['offset'])) ? $query .= ' OFFSET '.$_GET['offset'] : NULL;
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['char'].$tab.$row['summe'].$nl;
	}
	print($res);
}
?>
