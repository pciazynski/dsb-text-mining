<?php
header('Content-Type: text/plain');

$n = $_GET['n'];
$PDO = new PDO('sqlite:../data/ngram'.$n.'.db');

(isset($_GET['frequency'])) ? $frequency = $_GET['frequency'] : $frequency = 1;

$query = 'SELECT ngram, frequency FROM ngramcount WHERE frequency >='.$frequency;
(isset($_GET['filter'])) ? $query .= ' AND ngram LIKE "% '.$_GET['filter'].' %" ' : NULL;
(isset($_GET['sort'])) ? $query .= ' ORDER BY frequency DESC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.";") as $row){
	$res.=$row['ngram'].$tab.$row['frequency'].$nl;
}
print($res);

?>
