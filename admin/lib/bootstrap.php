<?php
// Общее для админки: пути, папка данных вне сайта, чтение и запись файлов.
declare(strict_types=1);

if (!defined('TVD_ADMIN')) {
    http_response_code(404);
    exit;
}

date_default_timezone_set('Europe/Moscow');
mb_internal_encoding('UTF-8');

// Корень сайта: папка, в которой лежит admin/. В тестах подменяется переменной окружения.
define('SITE_ROOT', rtrim(getenv('TVD_SITE_ROOT') ?: dirname(__DIR__, 2), '/'));

$tvdLocal = dirname(__DIR__) . '/config.local.php';   // не в git, см. config.sample.php
$tvdCfg = is_file($tvdLocal) ? (array) require $tvdLocal : [];

// Данные админки (пароли, настройки, копии вёрстки, история) — вне папки сайта.
// На Host-0: /var/www/<логин>/data/.tovarvdele-admin (домашняя папка, на два уровня выше www/tovarvdele.ru).
define('DATA_DIR', rtrim($tvdCfg['data_dir'] ?? (getenv('TVD_ADMIN_DATA') ?: dirname(SITE_ROOT, 2) . '/.tovarvdele-admin'), '/'));
unset($tvdLocal, $tvdCfg);

const HISTORY_KEEP = 50;

final class UserError extends RuntimeException {}

function h(mixed $s): string
{
    return htmlspecialchars((string) $s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function site_file(string $rel): string
{
    return SITE_ROOT . '/' . ltrim($rel, '/');
}

function data_file(string $rel): string
{
    return DATA_DIR . '/' . ltrim($rel, '/');
}

function data_init(): void
{
    $real = realpath(SITE_ROOT) ?: SITE_ROOT;
    $data = realpath(DATA_DIR) ?: DATA_DIR;
    if (str_starts_with($data . '/', $real . '/')) {
        throw new RuntimeException('Папка данных админки внутри сайта: ' . DATA_DIR . '. Укажите другую в admin/config.local.php.');
    }
    foreach (['', '/templates', '/history', '/sessions'] as $d) {
        if (!is_dir(DATA_DIR . $d) && !@mkdir(DATA_DIR . $d, 0700, true)) {
            throw new RuntimeException('Не удалось создать папку ' . DATA_DIR . $d);
        }
    }
    if (!is_file(DATA_DIR . '/.htaccess')) {
        @file_put_contents(DATA_DIR . '/.htaccess', "Require all denied\n");
    }
}

function read_file(string $path): string
{
    $s = @file_get_contents($path);
    if ($s === false) {
        throw new RuntimeException('Не читается файл ' . $path);
    }
    return $s;
}

/** Запись через временный файл и rename: сайт никогда не видит наполовину записанный файл. */
function write_file(string $path, string $data, int $mode = 0644): void
{
    $dir = dirname($path);
    if (!is_dir($dir) && !@mkdir($dir, 0755, true)) {
        throw new RuntimeException('Не создать папку ' . $dir);
    }
    $tmp = $dir . '/.tmp-' . bin2hex(random_bytes(6));
    if (@file_put_contents($tmp, $data) !== strlen($data)) {
        @unlink($tmp);
        throw new RuntimeException('Не записать ' . $path);
    }
    @chmod($tmp, $mode);
    if (!@rename($tmp, $path)) {
        @unlink($tmp);
        throw new RuntimeException('Не записать ' . $path);
    }
}

function json_read(string $path, mixed $default): mixed
{
    $s = @file_get_contents($path);
    if ($s === false) {
        return $default;
    }
    $v = json_decode($s, true);
    return $v ?? $default;
}

function json_write(string $path, mixed $value): void
{
    write_file($path, json_encode($value, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION) . "\n", 0600);
}

/** Изменение JSON-файла под блокировкой (лимит попыток входа и т. п.). */
function json_update(string $path, callable $fn): mixed
{
    $fp = fopen($path . '.lock', 'c');
    flock($fp, LOCK_EX);
    try {
        $v = $fn(json_read($path, []));
        json_write($path, $v);
        return $v;
    } finally {
        flock($fp, LOCK_UN);
        fclose($fp);
    }
}

function audit(string $msg): void
{
    @file_put_contents(data_file('audit.log'), date('Y-m-d H:i:s') . ' ' . ($_SESSION['user'] ?? 'cli') . ' ' . ($_SERVER['REMOTE_ADDR'] ?? '-') . ' ' . $msg . "\n", FILE_APPEND | LOCK_EX);
}
