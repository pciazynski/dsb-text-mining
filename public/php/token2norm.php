<?php
header('Content-Type: text/plain');

if (isset($_GET['token'])) {

	$pdo = new PDO('sqlite:../data/normmapping.db');
	$statement = $pdo->prepare(
		'SELECT DISTINCT token,norm,type,subtype FROM tokennormtypesubtypedatefrequency WHERE token = :token'
	);
	$statement->execute(['token' => $_GET['token']]);

	$tab = "\t";
	$nl = "\n";
	$res = '';

	foreach ($statement as $row) {
		$res .= $row['token'] . $tab . $row['norm'] . $tab . $row['type'] . $tab . $row['subtype'] . $nl;
	}

	print($res);
}
