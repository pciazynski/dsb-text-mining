<?php
header('Content-Type: text/plain');

(isset($_GET['norm'])) ? $norm = $_GET['norm'] : NULL;

if (strlen($norm)>=1){
	(isset($_GET['limit'])) ? $limit = $_GET['limit'] : $limit = 100;
	(isset($_GET['ambig'])) ? $dbname = 'normfrequency':$dbname = 'normnonambig';

	$query = 'SELECT DISTINCT norm FROM '.$dbname.' WHERE norm LIKE "|%'.$norm.'|" ORDER BY norm LIMIT '.$limit;

	$nl = "\n";
	$res = '';
	$PDO = new PDO('sqlite:../data/normmapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=trim($row['norm'],"|").$nl;
	}
	print($res);
}
?>
