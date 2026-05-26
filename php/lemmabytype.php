<?php
header('Content-Type: text/plain');

#lemma,summe

if (isset($_GET['type'])){
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT lemma, subtype, SUM(frequency) as summe FROM tokenlemmatypesubtypedatefrequency WHERE type="'.$_GET['type'].'"';
	(isset($_GET['subtype'])) ?	$query.=' AND subtype="'.$_GET['subtype'].'"':NULL;

	$query.=" GROUP BY lemma, subtype ";
	(isset($_GET['sort'])) ? $query .= ' ORDER BY summe DESC' : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res="";
	
	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$tab.$row['subtype'].$tab.$row['summe'].$nl;
	}
	print($res);
}

?>
