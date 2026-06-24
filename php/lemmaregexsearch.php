<?php
header('Content-Type: text/plain');

#token,lemma,norm,type,subtype,date,frequency

if (isset($_GET['lemma'])){
	function _sqliteRegexp($pattern,$string) {
		(preg_match("/^" . $pattern . "$/u", $string) === 1) ? $hit = true : $hit = false;
		return $hit;
	}
	
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	(isset($_GET['exact'])) ? $regexp = '\|'.$_GET['lemma'].'\|' : $regexp = '.*\|'.$_GET['lemma'].'\|.*';
	$query = 'SELECT * FROM tokenlemmatypesubtypedatefrequency WHERE lemma REGEXP ? LIMIT 2100000';

	$PDO->sqliteCreateFunction('regexp', '_sqliteRegexp', 2);

	$tab = "\t";
	$nl = "\n";
	$res = '';

	$stmt = $PDO->prepare($query);
	$stmt->execute([$regexp]);
	foreach($stmt as $row){
		$res.=$row['lemma'].$tab.$row['date'].$tab.$row['frequency'].$tab.$row['token'].$nl;
	}
	print($res);
}

?>
