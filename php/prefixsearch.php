<?php
header('Content-Type: text/plain');

(isset($_GET['word'])) ? $word = $_GET['word'] :  $word = '';

if (strlen($word)>=1){
	(isset($_GET['limit'])) ? $limit = $_GET['limit'] : $limit = 100;
	(isset($_GET['cutoff'])) ? $cutoff = ' GROUP BY SUBSTRING(word,0,'.strlen($word)+$_GET['cutoff'].')' : $cutoff = "";
	if(isset($_GET['sortby'])){
		($_GET['sortby'] =='alphabet') ? $sortby = ' ORDER BY token ASC' :  $sortby = ' ORDER BY '.$_GET['sortby'] .' DESC';
	}else{
		$sortby = '';
	}

	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$query = 'SELECT DISTINCT token FROM tokencount WHERE token LIKE "'.$word.'%"'.$cutoff.$sortby.' LIMIT '.$limit;

	$nl = "\n";
	$res = '';
	
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$nl;
	}
	print($res);
}
?>
