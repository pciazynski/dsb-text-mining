<?php
header('Content-Type: text/plain');

if (isset($_GET['token'])) {

	$pdo = new PDO('sqlite:../data/lemmamapping.db');
	$statement = $pdo->prepare(
		'SELECT DISTINCT lemma,token,type,subtype FROM tokenlemmatypesubtypedatefrequency WHERE token = :token'
	);
	$statement->execute(['token' => $_GET['token']]);

	$result = '';

	foreach ($statement as $row) {
		$result .= implode("\t", [$row['lemma'], $row['token'], $row['type'], $row['subtype']]) . "\n";
	}

	print($result);
}
