<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/authors.db');
$query = 'SELECT author, COUNT(urn) as c FROM authors GROUP BY author';
(isset($_GET['sort'])) ? $query .= ' ORDER BY c DESC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['author'].$tab.$row['c'].$nl;
}
print($res);

?>
