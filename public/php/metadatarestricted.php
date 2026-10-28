<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/metadata.db');
$query = 'SELECT restricted,count(restricted) as freq FROM docmeta GROUP BY restricted';

(isset($_GET['sort'])) ? $query .= ' ORDER BY freq DESC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['restricted'].$tab.$row['freq'].$nl;
}
print($res);

?>
