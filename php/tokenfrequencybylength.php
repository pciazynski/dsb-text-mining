<?php
header('Content-Type: text/plain');

if(isset($_GET['length'])){

	(isset($_GET['limit']))?$limit=$_GET['limit']:$limit=50;
	(isset($_GET['random']))?$order='random()':$order='token';
	(isset($_GET['frequency']))?$frequency=' AND frequency '.$_GET['frequency']:$frequency='';
	(isset($_GET['clean']))?$clean=' AND frequency>9':$clean='';

	#SUBSTR(token,1,1) and GROUP BY sub make sure that the words are not very similar
	$query = 'SELECT SUBSTR(token,1,1) as sub , token,frequency FROM tokencount WHERE LENGTH(token)=='.$_GET['length'].$frequency.$clean.' GROUP BY sub ORDER BY '.$order.' DESC LIMIT '.$limit;

	$nl = "\n";
	$tab = "\t";
	$res = '';

	$PDO = new PDO('sqlite:../data/bagofwords.db');
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$tab.$row['frequency'].$nl;
	}

	print($res);
}
?>
