<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
(isset($_GET['slim']))?$query = 'SELECT urn FROM docmeta WHERE True ':$query = 'SELECT * FROM docmeta WHERE True ';

(isset($_GET['author'])) ? $query .= ' AND author ="'.$_GET['author'].'"' : NULL;
(isset($_GET['restricted'])) ? $query .= ' AND restricted ="'.$_GET['restricted'].'"' : NULL;
(isset($_GET['year'])) ? $query .= ' AND date ="'.$_GET['year'].'"' : NULL;
(isset($_GET['lang'])) ? $query .= ' AND lang ="'.$_GET['lang'].'"' : NULL;
(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

if (isset($_GET['slim'])){
	foreach($PDO->query($query.';') as $row){
		$res.=$row['urn'].$nl;
	}
}else{
	foreach($PDO->query($query.';') as $row){
		$res.=$row['urn'].$tab.$row['title'].$tab.$row['date'].$tab.$row['author'].$tab.$row['restricted'].$tab.$row['lang'].$nl;
	}
}
print($res);

?>
