<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/bagofwords.db');
$query = 'SELECT * FROM tokendatecount WHERE True';

(isset($_GET['token'])) ? $query .= ' AND token LIKE "'.str_replace(",",'" OR token LIKE "',$_GET['token']).'"' : NULL;
(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['token'].$tab.$row['date'].$tab.$row['frequency'].$nl;
}
print($res);

?>
