<?php
header('Content-Type: text/plain');

if(isset($_GET['word'])){
	
	$token = $_GET['word'];
	$res = '';
	$tab = "\t";
	$colon = ":";
	$nl = "\n";
	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$lemma = "";

	$query = 'SELECT frequency FROM tokencount WHERE token="'.$token.'"';
	foreach($PDO->query($query.';') as $row){
		$frequency = $row['frequency'];
	}
	
	$query = 'SELECT COUNT(*) as rank FROM tokencount WHERE frequency>'.$frequency.'';
	foreach($PDO->query($query.';') as $row){
		$rank=$row['rank'];
	}
	
	$res .= $frequency.$tab.($rank+1).$nl;

	$query = 'SELECT Min(date) as mindate, Max(date) as maxdate FROM tokendatecount WHERE token="'.$token.'"';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['mindate'].$tab.$row['maxdate'].$nl;
	}
	
	if(strlen(trim($res))==0){
		print("NULL");
		exit();
	}
	$PDO = new PDO('sqlite:../data/lemmamapping.db');

	$query = 'SELECT lemma, SUM(frequency) as c FROM lemmatokenfrequency WHERE token = "'.$token.'" ORDER BY c DESC';
	foreach($PDO->query($query.';') as $row){
		$lemma=trim($row['lemma'],"|");
		$res.=$lemma.$colon.$row['c'].$tab;
	}

	$res=trim($res,$tab).$nl;

	
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$query = 'SELECT norm, SUM(frequency) as c FROM normtokenfrequency WHERE token = "'.$token.'" ORDER BY c DESC';
	foreach($PDO->query($query.';') as $row){
		$res.=trim($row['norm'],"|").$colon.$row['c'].$tab;
	}
	$res=trim($res,$tab).$nl;
	
	$query = 'SELECT type, SUM(frequency) as c FROM tokennormtypesubtypedatefrequency WHERE token = "'.$token.'" GROUP BY type';
	foreach($PDO->query($query.';') as $row){
		(strlen(trim($row['type']))>0) ? $res.=$row['type'].$colon.$row['c'].$tab:NULL;
	}
	$res=trim($res,$tab).$nl;
	
	$PDO = new PDO('sqlite:../data/collocation.db');
	$query = 'SELECT left,ROUND(logdice,0) as c FROM collocation WHERE right = "'.$token.'" ORDER BY logdice DESC LIMIT 10';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['left'].$colon.$row['c'].$tab;
	}
	$res=trim($res,$tab).$nl;
	$query = 'SELECT right,ROUND(logdice,0) as c  FROM collocation WHERE left = "'.$token.'" ORDER BY logdice DESC LIMIT 10';
	foreach($PDO->query($query.';') as $row){
		$res.=$row['right'].$colon.$row['c'].$tab;
	}
	$res=trim($res,$tab).$nl;
	
	print($res);
}
?>
