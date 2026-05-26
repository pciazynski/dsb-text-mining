<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency

if (isset($_GET['lemma'])){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^".$pattern."$/", $string)) ? $hit = true : $hit =  false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$query = 'SELECT * FROM tokenlemmatypesubtypedatefrequency WHERE lemma REGEXP "\|'.$_GET['lemma'].'\|" LIMIT 2100000';

	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach($PDO->query($query.";") as $row){
		$res.=$row['lemma'].$tab.$row['date'].$tab.$row['frequency'].$tab.$row['token'].$nl;
	}
	print($res);
}

?>
