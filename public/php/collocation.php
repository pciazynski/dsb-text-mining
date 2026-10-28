<?php
header('Content-Type: text/plain');
$PDO = new PDO('sqlite:../data/collocation.db');

$condition = '';

(isset($_GET['frequency']) and strlen($_GET['frequency'])>0) ? $frequency = $_GET['frequency'] : $frequency = 0;
(isset($_GET['right']) and strlen($_GET['right'])>0) ? $condition = ' AND right == "'.$_GET['right'].'" AND frequency >='.$frequency : NULL;
(isset($_GET['left']) and strlen($_GET['left'])>0) ? $condition = ' AND left == "'.$_GET['left'].'" AND frequency >='.$frequency : NULL;
(strlen($condition) == 0 and $frequency==0) ? $frequency = 10 : NULL;

if (isset($_GET['logdice']) and strlen($_GET['logdice'])>0){
	if(str_contains($_GET['logdice'],"-")){
		$tmp = explode("-",$_GET['logdice']);
		$condition .= ' AND logdice BETWEEN '.$tmp[0].' AND '.$tmp[1].'.99999999999999999';
	}
	else{
		$condition .= ' AND logdice >= '.$_GET['logdice'];
	}
}

$query = 'SELECT * FROM collocation WHERE frequency >= '.$frequency.$condition;
if(isset($_GET['sortBy'])){
	$sortBy = $_GET['sortBy'];
	($sortBy == "logdice" or $sortBy == "frequency") ? $query.=' ORDER BY '.$sortBy.' DESC' : NULL;
}

(isset($_GET['limit']) and strlen($_GET['limit'])>0) ? $query.=' LIMIT '.$_GET['limit'] : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['left'].$tab.$row['right'].$tab.$row['frequency'].$tab.$row['logdice'].$nl;
}

print($res);
?>
