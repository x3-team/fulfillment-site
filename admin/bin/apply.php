<?php
// После выкладки сайта из git: применить правки из админки к новой вёрстке.
//   php admin/bin/apply.php          — применить
//   php admin/bin/apply.php --check  — только показать, что не совпадает
declare(strict_types=1);
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
define('TVD_ADMIN', 1);
require __DIR__ . '/../lib/bootstrap.php';
require __DIR__ . '/../lib/site.php';

data_init();
$fresh = sync_templates();
if ($fresh) {
    echo "Новая вёрстка: " . implode(', ', $fresh) . "\n";
}
if (in_array('--check', $argv, true)) {
    $p = pending_files();
    echo $p ? "Правки не применены: " . implode(', ', $p) . "\n" : "Сайт совпадает с правками\n";
    exit($p ? 2 : 0);
}
$changed = apply_settings();
audit('apply.php: ' . ($changed ? implode(', ', $changed) : 'без изменений'));
echo $changed ? "Применено: " . implode(', ', $changed) . "\n" : "Сайт уже совпадает с правками\n";
