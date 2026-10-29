<?php
// Создать/сменить пароль админа: php admin/bin/create-admin.php <логин>   (пароль спросит; или TVD_PASS=... для скриптов)
// Удалить: php admin/bin/create-admin.php <логин> --delete
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(403); exit; }
define('TVD_ADMIN', 1);
require __DIR__ . '/../lib.php';
$u = $argv[1] ?? ''; if (!preg_match('/^[\w.@-]{3,64}$/', $u)) { fwrite(STDERR, "usage: php admin/bin/create-admin.php <login> [--delete]\n"); exit(1); }
data_init(); $f = DATA_DIR . '/users.json'; $users = json_read($f, []);
if (in_array('--delete', $argv, true)) { unset($users[$u]); json_write($f, $users); echo "deleted $u\n"; exit; }
$p = getenv('TVD_PASS') ?: '';
if ($p === '') { echo 'Пароль (мин. 12 символов): '; system('stty -echo'); $p = trim((string)fgets(STDIN)); system('stty echo'); echo "\n"; }
if (mb_strlen($p) < 12) { fwrite(STDERR, "Пароль короче 12 символов\n"); exit(1); }
$users[$u] = ['hash' => password_hash($p, PASSWORD_DEFAULT), 'created' => date('c')];
json_write($f, $users); @chmod($f, 0600);
echo "ok: $u → " . $f . "\n";
