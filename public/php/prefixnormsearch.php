<?php
header('Content-Type: text/plain');
require_once __DIR__.'/dsb_collation.php';

(isset($_GET['norm'])) ? $norm = $_GET['norm'] : NULL;

if (strlen($norm)>=1){
	$normSort = mb_strtoupper($norm,'UTF-8');
	(isset($_GET['limit'])) ? $limit = (int)$_GET['limit'] : $limit = 100;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(norm,1,'.strlen($norm)+$_GET['cutoff'].')' : $cutoff = '';
	(isset($_GET['ambig'])) ? $dbname = 'normfrequency':$dbname = 'normnonambig';
	$where = ' WHERE norm LIKE "|'.$norm.'%"';

	if(isset($_GET['sortby'])){
		if($_GET['sortby'] == 'alphabet'){
			$sortkeyPrefix = dsb_sortkey($normSort);
			# Prefix filter on sortkey keeps modern dsb alphabet sorting fast on large ranges.
			$where .= ' AND sortkey LIKE "'.$sortkeyPrefix.'%"';
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

	$query = 'SELECT DISTINCT norm FROM '.$dbname.$where.$cutoff.$sortby.$sqlLimit;

	$nl = "\n";
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$norms = array();
	foreach($PDO->query($query.';') as $row){
		$norms[] = trim($row['norm'],"|");
	}

	print(implode($nl, $norms).(count($norms) ? $nl : ''));
}
?>
