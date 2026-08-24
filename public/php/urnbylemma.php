<?php
header('Content-Type: text/plain');

if (isset($_GET['lemma'])) {
	$PDO = new PDO('sqlite:../data/lemmamapping.db');

	$includeAmbiguous = !isset($_GET['ambig']) || intval($_GET['ambig']) !== 0;
	$caseInsensitive = !isset($_GET['ci']) || intval($_GET['ci']) !== 0;
	$useRegex = isset($_GET['regex']) && intval($_GET['regex']) === 1;

	if (isset($_GET['year']) && !preg_match('/^[0-9\s\-]*$/', $_GET['year'])) {
		return;
	}

	$nonAmbigLemmas = [];
	if (!$includeAmbiguous) {
		$stmt = $PDO->prepare('SELECT lemma FROM lemmanonambig');
		$stmt->execute();
		foreach ($stmt->fetchAll(PDO::FETCH_COLUMN) as $lemma) {
			$nonAmbigLemmas[$lemma] = true;
		}
	}

	if (isset($_GET['list']) && intval($_GET['list']) === 1) {
		$lemmas = preg_split('/[\s,]+/', $_GET['lemma'], -1, PREG_SPLIT_NO_EMPTY);
	} else {
		$lemmas = [$_GET['lemma']];
	}

	$query = 'SELECT urn, date, lemmabag FROM urndatelemmabag WHERE 1=1';
	$params = [];

	if (isset($_GET['year'])) {
		$yearParts = explode('-', trim($_GET['year']));
		if (count($yearParts) === 2) {
			$query .= ' AND date BETWEEN ? AND ?';
			$params = array_map('trim', $yearParts);
		} else {
			$query .= ' AND date = ?';
			$params[] = $_GET['year'];
		}
	}

	if (isset($_GET['sort'])) {
		$query .= ' ORDER BY date ASC';
	}

	$stmt = $PDO->prepare($query);
	$res = '';
	$results = [];

	try {
		$stmt->execute($params);
		foreach ($stmt as $row) {
			$matches = false;
			foreach (explode('||', trim($row['lemmabag'], '|')) as $lemmaCell) {
				foreach (explode('|', $lemmaCell) as $lemma) {
					foreach ($lemmas as $searchLemma) {
						if ($useRegex) {
							$modifiers = $caseInsensitive ? 'i' : '';
							$match = preg_match('/' . $searchLemma . '/' . $modifiers, $lemma) === 1;
						} else {
							$match = $caseInsensitive
								? strtoupper($searchLemma) === strtoupper($lemma)
								: $searchLemma === $lemma;
						}

						if ($match && ($includeAmbiguous || isset($nonAmbigLemmas['|' . $lemmaCell . '|']))) {
							$matches = true;
							break 3;
						}
					}
				}
			}

			if ($matches) {
				$results[$row['urn']] = $row['date'];
			}
		}

		foreach ($results as $urn => $date) {
			$res .= $urn . "\t" . $date . "\n";
		}
	} catch (Exception) {
	}

	print($res);
}
