<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/lemmamapping.db');
$query = 'SELECT lemma, count(token) as c FROM lemmatokenfrequency GROUP BY lemma';

(isset($_GET['sort'])) ? $query .= ' ORDER BY c DESC':NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['lemma'].$tab.$row['c'].$nl;
}
print($res);

?>
