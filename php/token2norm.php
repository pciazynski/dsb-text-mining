<?php
header('Content-Type: text/plain');

if (isset($_GET['token'])){

	$PDO = new PDO('sqlite:../data/normmapping.db');
	$query = 'SELECT DISTINCT token,norm,type,subtype FROM tokennormtypesubtypedatefrequency';
	$query .= ' WHERE token = "'.$_GET['token'].'"';

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$tab.$row['norm'].$tab.$row['type'].$tab.$row['subtype'].$nl;
	}
	
	print($res);
}
?>
