<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency

if (isset($_GET['lemma'])){
	$lemma = str_replace(",",'|%" OR lemma LIKE "%|',$_GET['lemma']);
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT lemma, SUM(frequency) as summe, date FROM tokenlemmatypesubtypedatefrequency';
	(isset($_GET['exact'])) ? $query .= ' WHERE lemma = "|'.$lemma.'|"' : $query .= ' WHERE lemma LIKE "%|'.$lemma.'|%"';
	
	$query.= ' GROUP BY lemma, date ';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;
	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.';') as $row){
		$res.=$row['lemma'].$tab.$row['date'].$tab.$row['summe'].$nl;
	}
	print($res);
}

?>