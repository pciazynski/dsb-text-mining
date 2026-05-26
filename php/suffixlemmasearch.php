<?php
header('Content-Type: text/plain');

(isset($_GET['lemma'])) ? $lemma = $_GET['lemma'] : NULL;

if (strlen($lemma)>=1){
	(isset($_GET['limit'])) ? $limit = $_GET['limit'] : $limit = 100;
	(isset($_GET['ambig'])) ? $dbname = 'lemmafrequency':$dbname = 'lemmanonambig';
	
	$query = 'SELECT DISTINCT lemma FROM '.$dbname.' WHERE lemma LIKE "|%'.$lemma.'|" ORDER BY lemma LIMIT '.$limit;

	$nl = "\n";
	$res = '';
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=trim($row['lemma'],"|").$nl;
	}
	print($res);
}
?>
