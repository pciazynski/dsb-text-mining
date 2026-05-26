<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/authors.db');
$query = 'SELECT * FROM coauthors';

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['author1'].$tab.$row['author2'].$tab.$row['year'].$tab.$row['urn'].$nl;
}
print($res);

?>
