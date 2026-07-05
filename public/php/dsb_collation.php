<?php

function dsb_sortkey($s) {
	$map = array(
		'A' => 1,  'B' => 2,  'C' => 3,  'Č' => 4,  'Ć' => 5,  'D' => 6,
		'E' => 7,  'Ě' => 8,  'F' => 9,  'G' => 10, 'H' => 11, 'I' => 12,
		'J' => 13, 'K' => 14, 'Ł' => 15, 'L' => 16, 'M' => 17, 'N' => 18,
		'Ń' => 19, 'O' => 20, 'Ó' => 21, 'P' => 22, 'R' => 23, 'Ŕ' => 24,
		'S' => 25, 'Š' => 26, 'Ś' => 27, 'T' => 28, 'U' => 29, 'V' => 30,
		'W' => 31, 'X' => 32, 'Y' => 33, 'Z' => 34, 'Ž' => 35, 'Ź' => 36,
	);

	$s = mb_strtoupper($s, 'UTF-8');
	$chars = preg_split('//u', $s, -1, PREG_SPLIT_NO_EMPTY);
	$key = '';

	foreach ($chars as $ch) {
		if (isset($map[$ch])) {
			$key .= sprintf('%02d', $map[$ch]);
		} else {
			$codepoint = mb_ord($ch, 'UTF-8');
			$key .= '99' . sprintf('%08d', $codepoint);
		}
	}

	return $key;
}

?>