<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/collocation.db');

$leftright = "";
(isset($_GET['right']) and strlen($_GET['right'])>0) ? $leftright = 'right == "'.$_GET['right'].'"' : NULL;
(isset($_GET['left']) and strlen($_GET['left'])>0) ? $leftright = 'left == "'.$_GET['left'].'"' : NULL;
(isset($_GET['year'])) ? $year = $_GET['year'] : $year = "";
(isset($_GET['frequency'])  and strlen($_GET['frequency'])>0) ? $frequency = $_GET['frequency'] : $frequency = 0;

$tab = "\t";
$nl = "\n";
$res = '';

if(strlen($leftright) > 0 and strlen($year)==4){
	$query = 'SELECT left, right, frequency, date FROM collocationperyear WHERE '.$leftright.' AND date '.$year.' AND frequency >= '.$frequency;
	foreach($PDO->query($query.';') as $row){
		$res.=$row['date'].$tab.$row['left'].$tab.$row['right'].$tab.$row['frequency'].$nl;
	}
}
elseif(strlen($leftright) > 0){
	$query = 'SELECT left, right, frequency, date FROM collocationperyear WHERE '.$leftright.' AND frequency >= '.$frequency;
	foreach($PDO->query($query.';') as $row){
		$res.=$row['date'].$tab.$row['left'].$tab.$row['right'].$tab.$row['frequency'].$nl;
	}
}
elseif(strlen($year)==4){
	$query = 'SELECT left, right, frequency, date FROM collocationperyear WHERE date '.$year.' AND frequency >= '.$frequency;
	foreach($PDO->query($query.';') as $row){
		$res.=$row['date'].$tab.$row['left'].$tab.$row['right'].$tab.$row['frequency'].$nl;
	}
}
print($res);

?>
