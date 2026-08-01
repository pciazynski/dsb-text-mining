<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])) {

	$lemma = $_GET['lemma'];
	$res = '';
	$tab = "\t";
	$colon = ":";
	$nl = "\n";

	$PDO = new PDO('sqlite:../data/lemmamapping.db');

	$frequencyQuery = $PDO->prepare('SELECT frequency FROM lemmafrequency WHERE lemma = :lemma');
	$frequencyQuery->execute(['lemma' => '|' . $lemma . '|']);
	$frequency = $frequencyQuery->fetchColumn();

	if ($frequency === false) {
		$relatedQuery = $PDO->prepare(
			'SELECT lemma FROM lemmafrequency WHERE lemma LIKE :lemma ORDER BY frequency DESC, lemma'
		);
		$relatedQuery->execute(['lemma' => '%|' . $lemma . '|%']);

		while (($relatedLemma = $relatedQuery->fetchColumn()) !== false) {
			foreach (explode('|', trim($relatedLemma, '|')) as $candidate) {
				if ($candidate === $lemma) {
					continue;
				}

				$frequencyQuery->execute(['lemma' => '|' . $candidate . '|']);
				$candidateFrequency = $frequencyQuery->fetchColumn();
				if ($candidateFrequency !== false) {
					$lemma = $candidate;
					$frequency = $candidateFrequency;
					break 2;
				}
			}
		}
	}

	if ($frequency === false) {
		http_response_code(404);
		exit;
	}

	$query = 'SELECT COUNT(*) as rank FROM lemmafrequency WHERE frequency>' . $frequency . '';
	foreach ($PDO->query($query . ';') as $row) {
		$rank = $row['rank'];
	}
	$res .= $frequency . $tab . $rank . $nl;

	$query = 'SELECT Min(date) as mindate, Max(date) as maxdate FROM tokenlemmatypesubtypedatefrequency WHERE lemma = "|' . $lemma . '|"';
	foreach ($PDO->query($query . ';') as $row) {
		$res .= $row['mindate'] . $tab . $row['maxdate'];
	}
	$res = trim($res, $tab) . $nl;

	$query = 'SELECT lemma, SUM(frequency) as c FROM lemmafrequency WHERE lemma LIKE "%|' . $lemma . '|%" GROUP BY lemma ORDER BY c DESC, lemma';
	foreach ($PDO->query($query . ';') as $row) {
		$res .= trim($row['lemma'], "|") . $colon . $row['c'] . $tab;
	}
	$res = trim($res, $tab) . $nl;

	$query = 'SELECT token, frequency FROM lemmatokenfrequency WHERE lemma = "|' . $lemma . '|" ORDER BY frequency DESC,token';
	foreach ($PDO->query($query . ';') as $row) {
		$res .= $row['token'] . $colon . $row['frequency'] . $tab;
	}
	$res = trim($res, $tab) . $nl;

	$query = 'SELECT token, SUM(frequency) as c FROM lemmatokenfrequency WHERE lemma LIKE "%|' . $lemma . '|%" GROUP BY token ORDER BY c DESC,token';
	foreach ($PDO->query($query . ';') as $row) {
		$res .= trim($row['token'], "|") . $colon . $row['c'] . $tab;
	}
	$res = trim($res, $tab) . $nl;
	$res .= $lemma . $nl;

	print($res);
}
