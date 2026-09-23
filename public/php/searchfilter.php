<?php

if (!defined('SEARCH_RESULT_CAP')) {
  define('SEARCH_RESULT_CAP', 500);
}

function search_options(array $get): array
{
  $defaults = [
    'cs' => false,
    'regex' => false,
    'list' => false,
    'trim' => true,
    'ambig' => true,
  ];

  $options = $defaults;

  foreach ($defaults as $key => $default) {
    if (!array_key_exists($key, $get)) {
      continue;
    }

    $parsed = _search_bool($get[$key]);
    $options[$key] = $parsed ?? $default;
  }

  if (array_key_exists('exact', $get) && !array_key_exists('ambig', $get)) {
    $parsed = _search_bool($get['exact']);
    if ($parsed !== null) {
      $options['ambig'] = !$parsed;
    }
  }

  return $options;
}

/** @return bool|null null = unrecognised, keep the option default */
function _search_bool(mixed $value): ?bool
{
  if (is_bool($value)) {
    return $value;
  }

  if (is_int($value) || is_float($value)) {
    return match ((float) $value) {
      0.0 => false,
      1.0 => true,
      default => null,
    };
  }

  if (!is_string($value)) {
    return null;
  }

  return match (strtolower(trim($value))) {
    '', '0', 'false' => false,
    '1', 'true' => true,
    default => null,
  };
}

function split_terms(string $raw, array $opts): array
{
  $separator = ($opts['regex'] ?? false) ? '/;/' : '/[;,]/';
  $terms = ($opts['list'] ?? false) ? preg_split($separator, $raw) : [$raw];
  $trim = $opts['trim'] ?? true;
  $result = [];

  foreach ($terms as $term) {
    if ($trim) {
      $term = preg_replace('/^\s+|\s+$/u', '', $term) ?? $term;
    }

    if ($term !== '') {
      $result[] = $term;
    }
  }

  return $result;
}

function in_clause(string $column, array $cells): array
{
  $allowedColumns = ['lemma', 'norm', 'token', 'lemmabag', 'normbag'];
  if (!in_array($column, $allowedColumns, true)) {
    throw new \InvalidArgumentException("Unsupported search column: $column");
  }

  if ($cells === []) {
    return ['sql' => '1=0', 'params' => []];
  }

  return [
    'sql' => $column . ' IN (' . implode(',', array_fill(0, count($cells), '?')) . ')',
    'params' => array_values($cells),
  ];
}

function compile_term_pattern(string $term, array $opts): ?string
{
  if (!($opts['regex'] ?? false)) {
    return null;
  }

  $term = str_replace('~', '\\~', $term);
  $modifiers = ($opts['cs'] ?? false) ? 'u' : 'iu';
  $pattern = '~^(?:' . $term . ')$~' . $modifiers;

  return @preg_match($pattern, '') === false ? null : $pattern;
}

/** Whole request path: read the flags, split the term(s) of the $column param, resolve them to cells. */
function resolve_request_cells(\PDO $pdo, string $column, array $get): array
{
  $options = search_options($get);
  $terms = split_terms((string) ($get[$column] ?? ''), $options);

  if ($terms === []) {
    return [];
  }

  return array_values(array_unique(resolve_cells($pdo, $column, $terms, $options)));
}

function resolve_cells(\PDO $pdo, string $column, array $terms, array $options): array
{
  if (!in_array($column, ['lemma', 'norm', 'token'], true)) {
    throw new \InvalidArgumentException("Unsupported search column: $column");
  }

  $caseSensitive = $options['cs'] ?? false;
  $ambig = $options['ambig'] ?? true;
  $regex = $options['regex'] ?? false;
  [$table, $nonAmbiguousTable] = _search_tables_for_column($column);

  _search_truncated(false);

  if (!$regex && $column !== 'token' && array_filter($terms, static fn(string $term): bool => str_contains($term, '|')) !== []) {
    return _resolve_mixed_literal_terms($pdo, $column, $table, $nonAmbiguousTable, $terms, $caseSensitive, $ambig);
  }

  $useAmbiguousCells = $column !== 'token' && $ambig;
  $results = $useAmbiguousCells
    ? _resolve_ambiguous_cells($pdo, $table, $column, $terms, $caseSensitive, $regex)
    : _resolve_nonambiguous_cells($pdo, $nonAmbiguousTable, $column, $terms, $caseSensitive, $regex);

  return _apply_search_result_cap($results);
}

function _search_tables_for_column(string $column): array
{
  if ($column === 'token') {
    return ['tokencount', 'tokencount'];
  }

  return [$column . 'frequency', $column . 'nonambig'];
}

function _resolve_mixed_literal_terms(
  \PDO $pdo,
  string $column,
  string $table,
  string $nonAmbiguousTable,
  array $terms,
  bool $caseSensitive,
  bool $ambig,
): array {
  $explicitResults = [];
  $partResults = [];

  foreach ($terms as $term) {
    if (str_contains($term, '|')) {
      array_push($explicitResults, ..._resolve_explicit_cell($pdo, $table, $column, $term, $caseSensitive));
      continue;
    }

    $matches = $ambig
      ? _resolve_ambiguous_cells($pdo, $table, $column, [$term], $caseSensitive, false)
      : _resolve_nonambiguous_cells($pdo, $nonAmbiguousTable, $column, [$term], $caseSensitive, false);
    array_push($partResults, ...$matches);
  }

  return _apply_search_result_cap(array_values(array_unique([...$explicitResults, ...$partResults])));
}

function _resolve_explicit_cell(
  \PDO $pdo,
  string $table,
  string $column,
  string $term,
  bool $caseSensitive,
): array {
  $cell = '|' . trim($term, '|') . '|';
  $statement = $pdo->prepare("SELECT $column FROM $table WHERE sortkey = :sortkey ORDER BY rowid");
  $statement->execute(['sortkey' => dsb_sortkey(trim($cell, '|'))]);
  $matches = [];

  while ($candidate = $statement->fetchColumn()) {
    if (($caseSensitive && $candidate === $cell)
      || (!$caseSensitive && mb_strtolower($candidate, 'UTF-8') === mb_strtolower($cell, 'UTF-8'))
    ) {
      $matches[] = $candidate;
    }
  }

  return $matches;
}

/** One row per distinct part, so an indexed sortkey seek finds every candidate for a term. */
function _resolve_nonambiguous_cells(
  \PDO $pdo,
  string $table,
  string $column,
  array $terms,
  bool $caseSensitive,
  bool $regex,
): array {
  if ($regex) {
    return _resolve_ambiguous_cells($pdo, $table, $column, $terms, $caseSensitive, true);
  }

  $statement = $pdo->prepare(
    "SELECT $column, frequency FROM $table WHERE sortkey = :sortkey ORDER BY rowid",
  );
  $matches = [];
  $seen = [];

  foreach ($terms as $term) {
    $upperTerm = mb_strtoupper($term, 'UTF-8');
    $statement->execute(['sortkey' => dsb_sortkey($term)]);

    while ($row = $statement->fetch(\PDO::FETCH_ASSOC)) {
      $cell = $row[$column];
      $part = trim($cell, '|');

      if (isset($seen[$cell]) || ($caseSensitive && $part !== $term)) {
        continue;
      }
      $seen[$cell] = true;

      $matches[] = [
        'cell' => $cell,
        'frequency' => (int) $row['frequency'],
        'has_upper_match' => $part === $upperTerm,
        'is_exact' => true,
        'match_position' => 0,
      ];
    }
  }

  if (!$caseSensitive) {
    usort($matches, '_compare_cell_matches');
  }

  return array_column($matches, 'cell');
}

/**
 * CEILING: ambiguous cells have no per-part index, so this scans the table once
 * for all terms; upgrade: a part->cell join table or FTS.
 */
function _resolve_ambiguous_cells(
  \PDO $pdo,
  string $table,
  string $column,
  array $terms,
  bool $caseSensitive,
  bool $regex,
): array {
  $matchers = _build_term_matchers($terms, $caseSensitive, $regex);
  if ($matchers === []) {
    return [];
  }

  $statement = $pdo->prepare("SELECT $column, frequency FROM $table ORDER BY rowid");
  $statement->execute();
  // separate accumulator: appending into $matchers while iterating it would copy it per row
  $buckets = array_fill(0, count($matchers), []);

  while ($row = $statement->fetch(\PDO::FETCH_ASSOC)) {
    $cell = $row[$column];
    $parts = array_values(array_filter(explode('|', $cell)));
    $comparableParts = (!$caseSensitive && !$regex)
      ? array_map(static fn(string $part): string => mb_strtolower($part, 'UTF-8'), $parts)
      : $parts;

    foreach ($matchers as $index => $matcher) {
      $hit = _match_cell_parts($parts, $comparableParts, $matcher);
      if ($hit === null) {
        continue;
      }

      $buckets[$index][] = [
        'cell' => $cell,
        'frequency' => (int) $row['frequency'],
        'has_upper_match' => $hit['has_upper_match'],
        'is_exact' => count($parts) === 1 && $hit['position'] === 0,
        'match_position' => $hit['position'],
        'term_index' => $index,
      ];
      break; // the first matching term claims the cell, so results stay deduplicated
    }
  }

  $results = [];
  foreach ($buckets as $matches) {
    usort($matches, '_compare_cell_matches');

    foreach ($matches as $match) {
      $results[] = $match['cell'];
    }
  }

  return $results;
}

/** Hoists the per-term work (casing, pattern compilation) out of the row loop. Unusable regexes drop out. */
function _build_term_matchers(array $terms, bool $caseSensitive, bool $regex): array
{
  $matchers = [];

  foreach ($terms as $term) {
    $pattern = $regex ? compile_term_pattern($term, ['regex' => true, 'cs' => $caseSensitive]) : null;
    if ($regex && $pattern === null) {
      continue;
    }

    $matchers[] = [
      'pattern' => $pattern,
      'comparable' => $caseSensitive ? $term : mb_strtolower($term, 'UTF-8'),
      'upper' => $caseSensitive ? null : mb_strtoupper($term, 'UTF-8'),
    ];
  }

  return $matchers;
}

/** @return array{position:int,has_upper_match:bool}|null the last matching part, or null if none matches */
function _match_cell_parts(array $parts, array $comparableParts, array $matcher): ?array
{
  $position = -1;
  $hasUpperMatch = false;

  foreach ($parts as $index => $part) {
    $isMatch = $matcher['pattern'] !== null
      ? preg_match($matcher['pattern'], $part) === 1
      : $comparableParts[$index] === $matcher['comparable'];

    if (!$isMatch) {
      continue;
    }

    $position = $index;
    $hasUpperMatch = $hasUpperMatch || ($matcher['upper'] !== null && $part === $matcher['upper']);
  }

  return $position === -1 ? null : ['position' => $position, 'has_upper_match' => $hasUpperMatch];
}

function resolve_was_truncated(): bool
{
  return _search_truncated();
}

/** Truncation flag of the last resolve_cells() call; pass a bool to set it. */
function _search_truncated(?bool $value = null): bool
{
  static $truncated = false;

  if ($value !== null) {
    $truncated = $value;
  }

  return $truncated;
}

function _apply_search_result_cap(array $results): array
{
  if (count($results) <= SEARCH_RESULT_CAP) {
    return $results;
  }

  _search_truncated(true);

  return array_slice($results, 0, SEARCH_RESULT_CAP);
}

function _compare_cell_matches(array $left, array $right): int
{
  if ($left['has_upper_match'] !== $right['has_upper_match']) {
    return $right['has_upper_match'] <=> $left['has_upper_match'];
  }
  if ($left['is_exact'] !== $right['is_exact']) {
    return $right['is_exact'] <=> $left['is_exact'];
  }
  if ($left['match_position'] !== $right['match_position']) {
    return $left['match_position'] <=> $right['match_position'];
  }

  return $left['is_exact']
    ? $right['frequency'] <=> $left['frequency']
    : $left['frequency'] <=> $right['frequency'];
}
