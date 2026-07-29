<?php

declare(strict_types=1);

namespace DsbTests\Support;

/**
 * Boots PHP's built-in server against an isolated copy of public/ so endpoint
 * smoke tests never touch the developer's real public/data/ databases.
 *
 * The endpoints open their SQLite files with relative DSNs ('sqlite:../data/x.db'),
 * which PHP resolves against the process CWD. The server is therefore started with
 * CWD = <root>/php, exactly like Apache serving public/php/, so '../data' lands in
 * the throwaway dataDir().
 */
final class DevServer
{
  private static ?self $instance = null;

  /** @var resource|null */
  private $process = null;

  /** @var array<int, resource> */
  private array $pipes = [];

  private function __construct(
    private readonly string $root,
    private readonly string $baseUrl,
  ) {}

  /** Shared server for the whole test run; started on first use, stopped at shutdown. */
  public static function boot(): self
  {
    if (self::$instance !== null) {
      return self::$instance;
    }

    $projectDir = dirname(__DIR__, 3);
    $root = sys_get_temp_dir() . '/dsb-php-' . bin2hex(random_bytes(6));
    mkdir($root . '/php', 0777, true);
    mkdir($root . '/data', 0777, true);

    foreach (glob($projectDir . '/public/php/*.php') ?: [] as $script) {
      copy($script, $root . '/php/' . basename($script));
    }
    copy($projectDir . '/public/router.php', $root . '/router.php');

    $port = self::freePort();
    $server = new self($root, 'http://127.0.0.1:' . $port);
    $server->start($port);

    self::$instance = $server;
    register_shutdown_function(static fn() => $server->stop());

    return $server;
  }

  /** Throwaway directory the copied endpoints see as '../data/'. */
  public function dataDir(): string
  {
    return $this->root . '/data';
  }

  /**
   * Perform a GET request against the dev server.
   *
   * @return array{status:int, body:string, headers:array<int, string>}
   */
  public function get(string $path): array
  {
    $context = stream_context_create([
      'http' => ['ignore_errors' => true, 'timeout' => 10, 'header' => "Connection: close\r\n"],
    ]);

    $body = @file_get_contents($this->baseUrl . $path, false, $context);
    $headers = $http_response_header ?? [];
    $status = 0;
    if (isset($headers[0]) && preg_match('#^HTTP/\S+\s+(\d{3})#', $headers[0], $m) === 1) {
      $status = (int) $m[1];
    }

    return ['status' => $status, 'body' => $body === false ? '' : $body, 'headers' => $headers];
  }

  private function start(int $port): void
  {
    $command = [PHP_BINARY, '-S', '127.0.0.1:' . $port, '-t', $this->root, $this->root . '/router.php'];
    $descriptors = [1 => ['pipe', 'w'], 2 => ['pipe', 'w']];

    $this->process = proc_open($command, $descriptors, $this->pipes, $this->root . '/php');
    if (!is_resource($this->process)) {
      throw new \RuntimeException('Could not start the PHP dev server.');
    }

    for ($attempt = 0; $attempt < 100; $attempt++) {
      $socket = @fsockopen('127.0.0.1', $port, $errno, $errstr, 0.2);
      if ($socket !== false) {
        fclose($socket);
        return;
      }
      usleep(50_000);
    }

    throw new \RuntimeException('PHP dev server did not come up on port ' . $port . '.');
  }

  private function stop(): void
  {
    foreach ($this->pipes as $pipe) {
      if (is_resource($pipe)) {
        fclose($pipe);
      }
    }
    $this->pipes = [];

    if (is_resource($this->process)) {
      proc_terminate($this->process);
      proc_close($this->process);
      $this->process = null;
    }

    self::removeTree($this->root);
  }

  private static function freePort(): int
  {
    $socket = stream_socket_server('tcp://127.0.0.1:0', $errno, $errstr);
    if ($socket === false) {
      throw new \RuntimeException('Could not reserve a port: ' . $errstr);
    }
    $name = stream_socket_get_name($socket, false);
    fclose($socket);

    return (int) substr((string) $name, strrpos((string) $name, ':') + 1);
  }

  private static function removeTree(string $dir): void
  {
    if (!is_dir($dir)) {
      return;
    }
    $items = new \RecursiveIteratorIterator(
      new \RecursiveDirectoryIterator($dir, \FilesystemIterator::SKIP_DOTS),
      \RecursiveIteratorIterator::CHILD_FIRST,
    );
    foreach ($items as $item) {
      $item->isDir() ? rmdir($item->getPathname()) : unlink($item->getPathname());
    }
    rmdir($dir);
  }
}
