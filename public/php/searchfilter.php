<?php

function search_options(array $get): array
{
  $defaults = [
    'ci' => true,
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
    $number = (float) $value;
    if ($number === 0.0) {
      return false;
    }
    if ($number === 1.0) {
      return true;
    }
    return null;
  }

  if (!is_string($value)) {
    return null;
  }

  $normalized = strtolower(trim($value));

  if ($normalized === '' || $normalized === '0' || $normalized === 'false') {
    return false;
  }

  if ($normalized === '1' || $normalized === 'true') {
    return true;
  }

  return null;
}

function split_terms(string $raw, array $opts): array
{
  $terms = ($opts['list'] ?? false) ? preg_split('/[;,]/', $raw) : [$raw];
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

function compile_term_pattern(string $term, array $opts): ?string
{
  if (!($opts['regex'] ?? false)) {
    return null;
  }

  $term = str_replace('~', '\\~', $term);
  $modifiers = ($opts['ci'] ?? true) ? 'iu' : 'u';
  $pattern = '~^(?:' . $term . ')$~' . $modifiers;

  return @preg_match($pattern, '') === false ? null : $pattern;
}
