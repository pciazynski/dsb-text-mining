<?php
header('Content-Type: text/plain');

if(isset($_GET['length'])){

	(isset($_GET['limit']))?$limit=$_GET['limit']:$limit=50;
	(isset($_GET['random']))?$order='random()':$order='lemma';
	(isset($_GET['frequency']))?$frequency=' AND frequency '.$_GET['frequency']:$frequency='';

	#SUBSTR(lemma,2,2) and GROUP BY sub make sure that the words are not very similar
	$query = 'SELECT SUBSTR(lemma,2,2) as sub , lemma FROM lemmafrequency WHERE LENGTH(lemma)=='.($_GET['length']+2).$frequency.' GROUP BY sub ORDER BY '.$order.' DESC LIMIT '.$limit;

	$nl = "\n";
	$res = '';

	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$nl;
	}

	print($res);
}
?>
