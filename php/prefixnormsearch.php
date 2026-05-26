<?php
header('Content-Type: text/plain');

(isset($_GET['norm'])) ? $norm = $_GET['norm'] : NULL;

if (strlen($norm)>=1){
	(isset($_GET['limit'])) ? $limit = $_GET['limit'] : $limit = 100;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(norm,1,'.strlen($norm)+$_GET['cutoff'].')' : $cutoff = '';
	(isset($_GET['ambig'])) ? $dbname = 'normfrequency':$dbname = 'normnonambig';
	if(isset($_GET['sortby'])){
		($_GET['sortby'] =='alphabet') ? $sortby = ' ORDER BY norm ASC' :  $sortby = ' ORDER BY '.$_GET['sortby'] .' DESC';
	}else{
		$sortby = '';
	}

	$query = 'SELECT DISTINCT norm FROM '.$dbname.' WHERE norm LIKE "|'.$norm.'%"'.$cutoff.$sortby.' LIMIT '.$limit;
	$nl = "\n";
	$res = '';
	$PDO = new PDO('sqlite:../data/normmapping.db');
	foreach($PDO->query($query.';') as $row){
		$res.=trim($row['norm'],"|").$nl;
	}
	print($res);
}
?>
