<?php
// Вход: пароли в users.json (password_hash), сессии в папке данных, CSRF, лимит неудачных попыток.
declare(strict_types=1);

const LOGIN_WINDOW = 900;        // 15 минут
const LOGIN_MAX_PER_IP = 5;
const LOGIN_MAX_PER_USER = 10;
const SESSION_IDLE = 4 * 3600;

function users(): array
{
    return json_read(data_file('users.json'), []);
}

function is_https(): bool
{
    return ($_SERVER['HTTPS'] ?? '') === 'on' || ($_SERVER['SERVER_PORT'] ?? '') === '443'
        || strtolower($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https';
}

function session_boot(): void
{
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    ini_set('session.gc_maxlifetime', (string) SESSION_IDLE);
    session_save_path(data_file('sessions'));   // не общая папка хостинга
    session_name('tvd_admin');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/admin/', 'secure' => is_https(), 'httponly' => true, 'samesite' => 'Strict']);
    session_start();
    if (!empty($_SESSION['user']) && (time() - ($_SESSION['seen'] ?? 0)) > SESSION_IDLE) {
        $_SESSION = [];
        session_regenerate_id(true);
    }
    $_SESSION['seen'] = time();
    $_SESSION['csrf'] ??= bin2hex(random_bytes(32));
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf" value="' . h($_SESSION['csrf']) . '">';
}

function csrf_ok(): bool
{
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($origin !== '' && parse_url($origin, PHP_URL_HOST) !== parse_url('//' . ($_SERVER['HTTP_HOST'] ?? ''), PHP_URL_HOST)) {
        return false;
    }
    return is_string($_POST['csrf'] ?? null) && hash_equals($_SESSION['csrf'], $_POST['csrf']);
}

/** Сколько секунд ещё ждать перед следующей попыткой (0 — можно). */
function login_wait(string $login): int
{
    $t = json_read(data_file('throttle.json'), []);
    $now = time();
    $wait = 0;
    foreach (['ip:' . ($_SERVER['REMOTE_ADDR'] ?? '-') => LOGIN_MAX_PER_IP, 'user:' . mb_strtolower($login) => LOGIN_MAX_PER_USER] as $k => $max) {
        $hits = array_values(array_filter($t[$k] ?? [], fn ($ts) => $ts > $now - LOGIN_WINDOW));
        if (count($hits) >= $max) {
            $wait = max($wait, $hits[count($hits) - $max] + LOGIN_WINDOW - $now);
        }
    }
    return $wait;
}

function login_failed(string $login): void
{
    $now = time();
    json_update(data_file('throttle.json'), function (array $t) use ($now, $login) {
        foreach (['ip:' . ($_SERVER['REMOTE_ADDR'] ?? '-'), 'user:' . mb_strtolower($login)] as $k) {
            $t[$k][] = $now;
        }
        foreach ($t as $k => $hits) {
            $t[$k] = array_values(array_filter($hits, fn ($ts) => $ts > $now - LOGIN_WINDOW));
            if (!$t[$k]) {
                unset($t[$k]);
            }
        }
        return $t;
    });
}

function login(string $login, string $password): bool
{
    $users = users();
    // Сравниваем с хешем и для несуществующего логина, чтобы время ответа не выдавало логины
    $hash = $users[$login]['hash'] ?? password_hash(bin2hex(random_bytes(8)), PASSWORD_DEFAULT);
    if (!password_verify($password, $hash) || !isset($users[$login])) {
        return false;
    }
    session_regenerate_id(true);
    $_SESSION['user'] = $login;
    // На хостинге сборщик старых сессий может быть выключен — чистим свою папку сами
    foreach (glob(data_file('sessions/sess_*')) ?: [] as $f) {
        if (filemtime($f) < time() - 2 * SESSION_IDLE) {
            @unlink($f);
        }
    }
    $_SESSION['csrf'] = bin2hex(random_bytes(32));
    return true;
}

function logout(): void
{
    $_SESSION = [];
    session_regenerate_id(true);
}
