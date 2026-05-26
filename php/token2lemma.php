<?php
header('Content-Type: text/plain');

if (isset($_GET['token'])){

	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT DISTINCT lemma,token,type,subtype FROM tokenlemmatypesubtypedatefrequency';
	$query .= ' WHERE token = "'.$_GET['token'].'"';

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$tab.$row['token'].$tab.$row['type'].$tab.$row['subtype'].$nl;
	}
	
	print($res);
}
?>
