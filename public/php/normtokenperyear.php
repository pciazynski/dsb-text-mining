<?php
header('Content-Type: text/plain');

if (isset($_GET['norm']) and isset($_GET['year'])){
	$query = 'SELECT norm,token, SUM(frequency) as sumfreq FROM tokennormtypesubtypedatefrequency WHERE date '.$_GET['year'];
	(isset($_GET['exact']) and $_GET['exact']==1) ? $query .= ' AND norm = "|'.$_GET['norm'].'|"' : $query .= ' AND norm LIKE "%|'.str_replace(',','|%" OR norm LIKE "%|',$_GET['norm']).'|%"';
	$query.= ' GROUP BY norm,token';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC, token' : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res = "";

	$PDO = new PDO('sqlite:../data/normmapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=$row['norm'].$tab.$row['token'].$tab.$row['sumfreq'].$nl;
	}
	print($res);
}
?>
