<?php
header('Content-Type: text/plain');

(isset($_GET['word'])) ? $word = $_GET['word'] : NULL;

if (strlen($word)>=1){
	(isset($_GET['limit'])) ? $limit = $_GET['limit'] : $limit = 100;

	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$query = 'SELECT DISTINCT token FROM tokencount WHERE token LIKE "%'.$word.'" ORDER BY token LIMIT '.$limit;

	$nl = "\n";
	$res = '';
	
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$nl;
	}
	print($res);
}
?>
