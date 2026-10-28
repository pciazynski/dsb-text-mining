<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
$query = 'SELECT author,date,count(author) as freq FROM docmeta WHERE author NOT NULL GROUP BY author,date';

(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['author'].$tab.$row['date'].$tab.$row['freq'].$nl;
}
print($res);

?>
