<?php
header('Content-Type: text/plain');

(isset($_GET['norm'])) ? $norm = $_GET['norm'] : NULL;

if (strlen($norm)>=1){
	(isset($_GET['limit'])) ? $limit = (int)$_GET['limit'] : $limit = 100;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(norm,1,'.strlen($norm)+$_GET['cutoff'].')' : $cutoff = '';
	(isset($_GET['ambig'])) ? $dbname = 'normfrequency':$dbname = 'normnonambig';

	if(isset($_GET['sortby'])){
		if($_GET['sortby'] == 'alphabet'){
			# Ordered by the precomputed Lower Sorbian collation key (built in Python),
			# so SQL can apply the correct order via index and LIMIT directly.
			$sortby = ' ORDER BY sortkey ASC';
			$sqlLimit = ' LIMIT '.$limit;
		}else{
			$sortby = ' ORDER BY '.$_GET['sortby'] .' DESC';
			$sqlLimit = ' LIMIT '.$limit;
		}
	}else{
		$sortby = '';
		$sqlLimit = ' LIMIT '.$limit;
	}

	$query = 'SELECT DISTINCT norm FROM '.$dbname.' WHERE norm LIKE "|'.$norm.'%"'.$cutoff.$sortby.$sqlLimit;

	$nl = "\n";
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$norms = array();
	foreach($PDO->query($query.';') as $row){
		$norms[] = trim($row['norm'],"|");
	}

	print(implode($nl, $norms).(count($norms) ? $nl : ''));
}
?>
