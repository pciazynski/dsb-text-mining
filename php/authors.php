<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/authors.db');
$query = 'SELECT DISTINCT author FROM authors';
(isset($_GET['sort'])) ? $query .= ' ORDER BY author' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['author'].$nl;
}
print($res);

?>
