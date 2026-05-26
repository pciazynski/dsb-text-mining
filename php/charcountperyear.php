<?php
header('Content-Type: text/plain');

$PDO = new PDO('sqlite:../data/characters.db');
$query = 'SELECT * FROM chardatecount WHERE True';

(isset($_GET['char'])) ? $query .= ' AND char = "'.str_replace(",",'" OR char LIKE "',$_GET['char']).'"' : NULL;

(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;

$tab = "\t";
$nl = "\n";
$res = '';

foreach($PDO->query($query.';') as $row){
	$res.=$row['char'].$tab.$row['date'].$tab.$row['frequency'].$nl;
}
print($res);

?>
