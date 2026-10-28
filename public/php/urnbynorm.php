<?php
header('Content-Type: text/plain');

require_once __DIR__ . '/dsb_collation.php';
require_once __DIR__ . '/searchfilter.php';

if (isset($_GET['norm'])) {
	$PDO = new PDO('sqlite:../data/normmapping.db');
	$cellSet = array_flip(resolve_request_cells($PDO, 'norm', $_GET));

	if ($cellSet === []) {
		exit;
	}

	print_matching_document_urns($PDO, 'urndatenormbag', 'normbag', $cellSet, $_GET);
}
