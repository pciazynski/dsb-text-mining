<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency

if (isset($_GET['norm'])){
	$norm = str_replace(",",'|%" OR norm LIKE "%|',$_GET['norm']);
	$query = 'SELECT norm, SUM(frequency) as summe, date FROM tokennormtypesubtypedatefrequency';
	(isset($_GET['exact'])) ? $query .= ' WHERE norm = "|'.$norm.'|"' : $query .= ' WHERE norm LIKE "%|'.$norm.'|%"';
	
	$query.= ' GROUP BY norm, date ';
	(isset($_GET['sort'])) ? $query .= ' ORDER BY date ASC' : NULL;
	
	$tab = "\t";
	$nl = "\n";
	$res = '';

	$PDO = new PDO('sqlite:../data/normmapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=$row['norm'].$tab.$row['date'].$tab.$row['summe'].$nl;
	}
	print($res);
}

?>