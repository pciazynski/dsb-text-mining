<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
$query = 'SELECT lang,date,count(lang) as freq FROM docmeta WHERE lang NOT NULL GROUP BY lang,date';

(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['lang'].$tab.$row['date'].$tab.$row['freq'].$nl;
}
print($res);

?>
