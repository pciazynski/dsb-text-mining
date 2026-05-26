<?php
header('Content-Type: text/plain');

if (isset($_GET['word'])){
	$word = $_GET['word'];
	$word = str_replace(array("ł","ć","č","ė","é","ě","ź","ž","ś","š","ŕ","ó"),array("l4","c1","c2","e1","e1","e2","z1","z2","s1","s2","r1","o1"),$word);
	$word = str_replace(',','-%" OR url LIKE "',$word);

	$PDO = new PDO('sqlite:../data/psedcytas.db');
	$query = 'SELECT url FROM urls WHERE url LIKE "'.$word.'-%" LIMIT 1';
	
	foreach($PDO->query($query.';') as $row){
		print($row['url']);
	}
}
?>
