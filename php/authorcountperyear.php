<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/authors.db');
$query = 'SELECT author, year, COUNT(urn) as c FROM authors GROUP BY author, year';
(isset($_GET['sort'])) ? $query .= ' ORDER BY year' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['author'].$tab.$row['year'].$tab.$row['c'].$nl;
}
print($res);

?>
