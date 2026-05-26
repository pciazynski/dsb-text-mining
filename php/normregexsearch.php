<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency

if (isset($_GET['norm'])){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^".$pattern."$/", $string)) ? $hit = true : $hit =  false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$query = 'SELECT * FROM tokennormtypesubtypedatefrequency WHERE norm REGEXP "\|'.$_GET['norm'].'\|" LIMIT 2100000';

	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.";") as $row){
		$res.=$row['norm'].$tab.$row['date'].$tab.$row['frequency'].$tab.$row['token'].$nl;
	}
	print($res);
}

?>
