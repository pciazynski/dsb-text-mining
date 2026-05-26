<?php
header('Content-Type: text/plain');

(isset($_GET['token'])) ? $token = $_GET['token'] : NULL ;

if (strlen($token)>=1){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^".$pattern."$/", $string)) ? $hit = true : $hit =  false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/bagofwords.db');
	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);
	$query = 'SELECT DISTINCT * FROM tokendatecount WHERE token REGEXP "'.$token.'" LIMIT 2100000';

	$res = '';
	$tab = "\t";
	$nl = "\n";
	foreach($PDO->query($query.';') as $row){
		$res.=$row['token'].$tab.$row['date'].$tab.$row['frequency'].$nl;
	}
	print($res);
}
?>
