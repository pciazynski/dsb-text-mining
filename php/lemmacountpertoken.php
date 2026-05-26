<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/lemmamapping.db');
$query = 'SELECT token, COUNT(lemma) as c FROM lemmatokenfrequency GROUP BY token';

(isset($_GET['sort'])) ? $query .= ' ORDER BY c DESC, token' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['token'].$tab.$row['c'].$nl;
}
print($res);
?>
