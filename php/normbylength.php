<?php
header('Content-Type: text/plain');

if(isset($_GET['length'])){

	(isset($_GET['limit']))?$limit=$_GET['limit']:$limit=50;
	(isset($_GET['random']))?$order='random()':$order='norm';
	(isset($_GET['frequency']))?$frequency=' AND frequency '.$_GET['frequency']:$frequency='';

	#SUBSTR(norm,2,2) and GROUP BY sub make sure that the words are not very similar
	$query = 'SELECT SUBSTR(norm,2,2) as sub , norm FROM normfrequency WHERE LENGTH(norm)=='.($_GET['length']+2).$frequency.' GROUP BY sub ORDER BY '.$order.' DESC LIMIT '.$limit;

	$nl = "\n";
	$res = '';

	$PDO = new PDO('sqlite:../data/normmapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=$row['norm'].$nl;
	}

	print($res);
}
?>
