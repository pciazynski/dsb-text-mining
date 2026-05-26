<?php
header('Content-Type: text/plain');

#lemma,summe

$PDO = new PDO('sqlite:../data/lemmamapping.db');
$query = 'SELECT type, subtype, SUM(frequency) as summe FROM tokenlemmatypesubtypedatefrequency WHERE LENGTH(type)>0 OR LENGTH(subtype)>0 GROUP BY type, subtype ';
(isset($_GET['sort'])) ? $query .= ' ORDER BY summe DESC' : NULL;

$tab = "\t";
$nl = "\n";
$res='';
foreach($PDO->query($query.';') as $row){
	$res.=$row['type'].$tab.$row['subtype'].$tab.$row['summe'].$nl;
}
print($res);

?>
