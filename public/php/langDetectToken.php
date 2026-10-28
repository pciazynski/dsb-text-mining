<?php
header('Content-Type: text/plain');

if (isset($_GET['deu']) and strlen($_GET['deu'])>0 and isset($_GET['n']) and strlen($_GET['n'])>0){
	$n = $_GET['n'];
	$PDO = new PDO('sqlite:../data/langDetect'.$n.'.db');
	$deu = $_GET['deu'];
	
	(isset($_GET['frequency']) and strlen($_GET['filter'])>0) ? $frequency = $_GET['frequency'] : $frequency = 1;
	
	if($deu == 0){
		$query = 'SELECT token, frequency FROM langDetectdsbToken WHERE frequency >='.$frequency;
	}else if($deu == $_GET['n']){
		$query = 'SELECT token, frequency FROM langDetectdeuToken WHERE frequency >='.$frequency;
	}

	(isset($_GET['sort'])) ? $query .= ' ORDER BY frequency DESC' : NULL;
	(isset($_GET['count']) and strlen($_GET['count'])>0) ? $query.=' LIMIT '.$_GET['count'] : NULL;

	$tab = "\t";
	$nl = "\n";
	$res = '';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$tab.$row['frequency'].$nl;
	}
	print($res);
}
?>
