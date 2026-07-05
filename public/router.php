<?php
// Redirect directory requests so php -S behaves like a real web server during local development.
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = urldecode($path);
$fullPath = __DIR__ . $path;

if (is_dir($fullPath) && substr($path, -1) !== '/') {
	$query = $_SERVER['QUERY_STRING'] ?? '';
	$location = $path . '/';
	if ($query !== '') {
		$location .= '?' . $query;
	}
	header('Location: ' . $location, true, 302);
	exit;
}

return false;
