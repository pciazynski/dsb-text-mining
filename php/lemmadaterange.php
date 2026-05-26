<?php
header('Content-Type: text/plain');

	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT Min(date) as mindate, Max(date) as maxdate FROM tokenlemmatypesubtypedatefrequency ';
	
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['mindate'].$tab.$row['maxdate'].$nl;
	}
	print($res);
?>
