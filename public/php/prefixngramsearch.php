<?php
header('Content-Type: text/plain');

(isset($_GET['token'])) ? $token = $_GET['token'] : NULL;

if (strlen($token)>=1){
	(isset($_GET['limit'])) ? $limit = $_GET['limit'] : $limit = 100;
	(isset($_GET['n'])) ? $n = $_GET['n'] : $n=3;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(ngram,0,'.(1+strlen($token)+$_GET['cutoff']).')' : $cutoff = "";
	if(isset($_GET['sortby'])){
		($_GET['sortby'] =='alphabet') ? $sortby = ' ORDER BY ngram ASC' :  $sortby = ' ORDER BY '.$_GET['sortby'] .' DESC';
	}else{
		$sortby = '';
	}
	
	$query = 'SELECT DISTINCT SUBSTRING(ngram,2,LENGTH(ngram)-2) as ngram FROM ngramcount WHERE ngram LIKE " '.$token.'%"'.$cutoff.$sortby.' LIMIT '.$limit;
	$res = '';
	$nl = "\n";

	$PDO = new PDO('sqlite:../data/ngram'.$n.'.db');
	foreach($PDO->query($query.';') as $row){
		$res.=$row['ngram'].$nl;
	}
	print($res);
}
?>
