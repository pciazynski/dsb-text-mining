<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
$query = 'SELECT restricted,date,count(restricted) as freq FROM docmeta GROUP BY restricted,date';

(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['restricted'].$tab.$row['date'].$tab.$row['freq'].$nl;
}
print($res);

?>
