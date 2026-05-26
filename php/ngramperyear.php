<?php
header('Content-Type: text/plain');

$n = $_GET['n'];
$PDO = new PDO('sqlite:../data/ngram'.$n.'.db');
$query = 'SELECT * FROM ngramdatecount WHERE true';

(isset($_GET['filter'])) ? $query .= ' AND ngram LIKE "% '.$_GET['filter'].' %"' : NULL;
(isset($_GET['year'])) ? $query .= ' AND date = '.$_GET['year'] : NULL;
(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['ngram'].$tab.$row['date'].$tab.$row['frequency'].$nl;
}
print($res);

?>
