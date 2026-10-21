<?php

declare(strict_types=1);

namespace DsbTests\Support;

/**
 * Opens a throwaway SQLite fixture database.
 *
 * Fixture data is rebuilt in every setUp() and never has to survive a crash, so
 * durability is switched off. With the default synchronous=FULL every statement
 * costs one fsync (~8 ms on this project's dev hardware), which dominated the
 * whole PHP suite's runtime.
 */
final class FixtureDb
{
  public static function open(string $path): \PDO
  {
    $pdo = new \PDO('sqlite:' . $path);
    $pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
    $pdo->exec('PRAGMA synchronous=OFF');
    $pdo->exec('PRAGMA journal_mode=MEMORY');

    return $pdo;
  }
}
