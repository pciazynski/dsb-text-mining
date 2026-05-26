<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/normmapping.db');
$query = 'SELECT norm, count(token) as c FROM normtokenfrequency GROUP BY norm';

(isset($_GET['sort'])) ? $query .= ' ORDER BY c DESC':NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['norm'].$tab.$row['c'].$nl;
}
print($res);

?>
