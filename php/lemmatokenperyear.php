<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma']) and isset($_GET['year'])){
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT lemma,token, SUM(frequency) as sumfreq FROM tokenlemmatypesubtypedatefrequency WHERE date '.$_GET['year'];
	(isset($_GET['exact']) and $_GET['exact']==1) ? $query .= ' AND lemma = "|'.$_GET['lemma'].'|"' : $query .= ' AND lemma LIKE "%|'.str_replace(',','|%" OR lemma LIKE "%|',$_GET['lemma']).'|%"';
	$query.= ' GROUP BY lemma,token';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC, token' : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res = "";

	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$tab.$row['token'].$tab.$row['sumfreq'].$nl;
	}
	print($res);
}
?>
