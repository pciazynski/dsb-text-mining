<?php
header('Content-Type: text/plain');

if(isset($_GET['year']))
{
	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$query = 'SELECT token, SUM(frequency) as summe FROM tokendatecount WHERE date '.$_GET['year'];

	(isset($_GET['token'])) ? $query .= ' AND token LIKE "'.str_replace(",",'" OR token LIKE "',$_GET['token']).'"' : NULL;
	(isset($_GET['token'])) ? $query .= ' AND token LIKE "'.str_replace(",",'" OR token LIKE "',$_GET['token']).'"' : NULL;
	$query .= ' GROUP BY token';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY summe DESC' : NULL;
	(isset($_GET['limit'])) ? $query .= ' LIMIT '.$_GET['limit'] : $query .= ' LIMIT 10000' ;
	(isset($_GET['offset'])) ? $query .= ' OFFSET '.$_GET['offset'] : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$tab.$row['summe'].$nl;
	}
	print($res);
}
?>
