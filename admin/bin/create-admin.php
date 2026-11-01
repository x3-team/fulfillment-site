<?php
// Создать админа или сменить ему пароль:  php admin/bin/create-admin.php логин
// Удалить:                                 php admin/bin/create-admin.php логин --delete
// Пароль спрашивается в терминале (для скриптов — переменная TVD_PASS).
declare(strict_types=1);
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
define('TVD_ADMIN', 1);
require __DIR__ . '/../lib/bootstrap.php';

$login = $argv[1] ?? '';
if (!preg_match('/^[\w.@-]{3,64}$/u', $login)) {
    fwrite(STDERR, "Использование: php admin/bin/create-admin.php логин [--delete]\n");
    exit(1);
}
data_init();
$file = data_file('users.json');
$users = json_read($file, []);
if (in_array('--delete', $argv, true)) {
    unset($users[$login]);
    json_write($file, $users);
    audit("удалён админ $login");
    echo "Удалён: $login\n";
    exit;
}
$pass = getenv('TVD_PASS') ?: '';
if ($pass === '') {
    echo 'Пароль (не короче 12 знаков): ';
    @system('stty -echo');
    $pass = trim((string) fgets(STDIN));
    @system('stty echo');
    echo "\n";
}
if (mb_strlen($pass) < 12) {
    fwrite(STDERR, "Пароль короче 12 знаков\n");
    exit(1);
}
$users[$login] = ['hash' => password_hash($pass, PASSWORD_DEFAULT), 'created' => $users[$login]['created'] ?? date('c'), 'changed' => date('c')];
json_write($file, $users);
audit("админ $login создан или сменён пароль");
echo "Готово: $login. Данные админки: " . DATA_DIR . "\n";
