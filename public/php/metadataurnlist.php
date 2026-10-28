<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
$query = 'SELECT urn FROM docmeta WHERE True ';

(isset($_GET['author'])) ? $query .= ' AND author ="'.$_GET['author'].'"' : NULL;
(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['urn'].$nl;
}
print($res);

?>
