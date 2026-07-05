<?php
header('Content-Type: text/plain');

if(isset($_GET['norm'])){
	
	$norm = $_GET['norm'];
	$res = '';
	$tab = "\t";
	$colon = ":";
	$nl = "\n";

	$PDO = new PDO('sqlite:../data/normmapping.db');
	
	$query = 'SELECT frequency FROM normfrequency WHERE norm="|'.$norm.'|"';
	foreach($PDO->query($query.';') as $row){
		$frequency = $row['frequency'];
	}
	$query = 'SELECT COUNT(*) as rank FROM normfrequency WHERE frequency>'.$frequency.'';
	foreach($PDO->query($query.';') as $row){
		$rank=$row['rank'];
	}
	$res .= $frequency.$tab.$rank.$nl;
	
	$query = 'SELECT Min(date) as mindate, Max(date) as maxdate FROM tokennormtypesubtypedatefrequency WHERE norm = "|'.$norm.'|"';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['mindate'].$tab.$row['maxdate'];
	}
	$res=trim($res,$tab).$nl;

	$query = 'SELECT norm, SUM(frequency) as c FROM normfrequency WHERE norm LIKE "%|'.$norm.'|%" GROUP BY norm ORDER BY c DESC,norm';
	foreach($PDO->query($query.';') as $row){
		$res.=trim($row['norm'],"|").$colon.$row['c'].$tab;
	}
	$res=trim($res,$tab).$nl;
	
	$query = 'SELECT token, frequency FROM normtokenfrequency WHERE norm = "|'.$norm.'|" ORDER BY frequency DESC,token';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$colon.$row['frequency'].$tab;
	}
	$res=trim($res,$tab).$nl;
	$query = 'SELECT token, frequency FROM normtokenfrequency WHERE norm LIKE "%|'.$norm.'|%" ORDER BY frequency DESC,token';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$colon.$row['frequency'].$tab;
	}
	$res=trim($res,$tab).$nl;	
	print($res);
}
?>
