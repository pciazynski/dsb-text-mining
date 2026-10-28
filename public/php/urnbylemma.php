<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

if (isset($_GET['lemma'])) {
	$PDO = new PDO('sqlite:../data/lemmamapping.db');
	$cellSet = array_flip(resolve_request_cells($PDO, 'lemma', $_GET));

	if ($cellSet === []) {
		exit;
	}

	print_matching_document_urns($PDO, 'urndatelemmabag', 'lemmabag', $cellSet, $_GET);
}
