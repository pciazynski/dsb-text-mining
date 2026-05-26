<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/normmapping.db');
$query = 'SELECT norm, SUM(frequency) as sumfreq FROM tokennormtypesubtypedatefrequency';

(isset($_GET['norm'])) ? $query .= ' WHERE norm LIKE "%|'.str_replace(",",'|%" OR norm LIKE "%|',$_GET['norm']).'|%"' : NULL;

$query.=' GROUP BY norm ';

(isset($_GET['sort'])) ? $query .= ' ORDER BY sumfreq DESC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['norm'].$tab.$row['sumfreq'].$nl;
}
print($res);
?>
