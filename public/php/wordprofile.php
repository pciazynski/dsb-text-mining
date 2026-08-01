<?php
header('Content-Type: text/plain');

if (isset($_GET['word'])) {

	$token = $_GET['word'];
	$result = '';
	$openDatabase = static function (string $filename): PDO {
		$pdo = new PDO('sqlite:../data/' . $filename);
		$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

		return $pdo;
	};

	$pdo = $openDatabase('bagofwords.db');

	$frequencyStatement = $pdo->prepare('SELECT frequency FROM tokencount WHERE token = :token');
	$frequencyStatement->execute([':token' => $token]);
	$frequency = $frequencyStatement->fetchColumn();
	if ($frequency === false) {
		print("NULL");
		exit;
	}

	$rankStatement = $pdo->prepare('SELECT COUNT(*) as rank FROM tokencount WHERE frequency > :frequency');
	$rankStatement->execute([':frequency' => $frequency]);
	$rank = $rankStatement->fetchColumn();

	$result .= $frequency . "\t" . ($rank + 1) . "\n";

	$dateRangeStatement = $pdo->prepare('SELECT Min(date) as mindate, Max(date) as maxdate FROM tokendatecount WHERE token = :token');
	$dateRangeStatement->execute([':token' => $token]);
	if ($row = $dateRangeStatement->fetch(PDO::FETCH_ASSOC)) {
		$result .= $row['mindate'] . "\t" . $row['maxdate'] . "\n";
	}
	$pdo = $openDatabase('lemmamapping.db');

	$stmt = $pdo->prepare('SELECT lemma, SUM(frequency) as c FROM lemmatokenfrequency WHERE token = :token GROUP BY lemma ORDER BY c DESC');
	$stmt->execute([':token' => $token]);
	while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
		$result .= trim($row['lemma'], "|") . ':' . $row['c'] . "\t";
	}

	$result = trim($result, "\t") . "\n";

	$pdo = $openDatabase('normmapping.db');
	$stmt = $pdo->prepare('SELECT norm, SUM(frequency) as c FROM normtokenfrequency WHERE token = :token ORDER BY c DESC');
	$stmt->execute([':token' => $token]);
	while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
		$result .= trim($row['norm'], "|") . ':' . $row['c'] . "\t";
	}
	$result = trim($result, "\t") . "\n";

	$stmt = $pdo->prepare('SELECT type, SUM(frequency) as c FROM tokennormtypesubtypedatefrequency WHERE token = :token GROUP BY type');
	$stmt->execute([':token' => $token]);
	while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
		if (strlen(trim($row['type'])) > 0) {
			$result .= $row['type'] . ':' . $row['c'] . "\t";
		}
	}
	$result = trim($result, "\t") . "\n";

	$pdo = $openDatabase('collocation.db');
	$stmt = $pdo->prepare('SELECT left, ROUND(logdice,0) as c FROM collocation WHERE right = :token ORDER BY logdice DESC LIMIT 10');
	$stmt->execute([':token' => $token]);
	while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
		$result .= $row['left'] . ':' . $row['c'] . "\t";
	}
	$result = trim($result, "\t") . "\n";
	$stmt = $pdo->prepare('SELECT right, ROUND(logdice,0) as c FROM collocation WHERE left = :token ORDER BY logdice DESC LIMIT 10');
	$stmt->execute([':token' => $token]);
	while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
		$result .= $row['right'] . ':' . $row['c'] . "\t";
	}
	$result = trim($result, "\t") . "\n";

	print($result);
}
