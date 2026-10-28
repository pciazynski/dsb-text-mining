<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
$query = 'SELECT author,count(author) as freq FROM docmeta WHERE author NOT NULL GROUP BY author';

(isset($_GET['sort'])) ? $query .= ' ORDER BY freq DESC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['author'].$tab.$row['freq'].$nl;
}
print($res);

?>
