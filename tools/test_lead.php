<?php
// Тесты эндпоинта заявок api/lead.php и agency/api/lead.php:  php tools/test_lead.php
declare(strict_types=1);
const LEAD_TEST = true;
$root = dirname(__DIR__);
require $root . '/api/lead.php';

$fails = 0;
$n = 0;
function check(string $name, bool $ok): void
{
    global $fails, $n;
    $n++;
    if (!$ok) {
        $fails++;
        echo "FAIL $name\n";
    }
}

$dir = sys_get_temp_dir() . '/lead-test-' . getmypid();
$cfg = ['bot_token' => 'TEST', 'chat_id' => '1'];
$sent = [];
$send = function (array $c, string $text) use (&$sent): bool { $sent[] = $text; return true; };
$srv = fn(array $o = []) => $o + ['REQUEST_METHOD' => 'POST', 'HTTP_HOST' => 'tovarvdele.ru', 'HTTP_ORIGIN' => 'https://tovarvdele.ru',
    'CONTENT_TYPE' => 'application/json', 'REMOTE_ADDR' => '10.0.0.' . random_int(1, 250)];
$calc = ['form' => 'calc', 'name' => 'Иван <b>', 'phone' => '8 900 123-45-67', 'email' => 'ivan@example.ru', 'ts' => (time() - 30) * 1000,
    'calc' => ['units' => '100 ед.', 'total' => '2 350 ₽', 'per_unit' => '23,5 ₽', 'discount' => '2 115 ₽', 'ops' => '3',
        'lines' => [['Приёмка: 100 × 5 ₽', '500 ₽'], ['FBS & <ЧЗ>', '1 500 ₽']]],
    'page' => 'https://tovarvdele.ru/', 'utm' => ['utm_source' => 'yandex', 'utm_campaign' => 'ff'], 'consent' => 'Согласие дано'];
$run = function (array $in, array $s = [], ?array $c = null) use (&$cfg, $send, $dir, $srv) {
    return lead_handle($srv($s), json_encode($in), [], $c ?? $cfg, $send, $dir);
};

check('GET → 405', lead_handle(['REQUEST_METHOD' => 'GET'] + $srv(), '', [], $cfg, $send, $dir)[0] === 405);
check('чужой Origin → 403', $run($calc, ['HTTP_ORIGIN' => 'https://evil.example'])[0] === 403);
check('чужой домен → 403', $run($calc, ['HTTP_HOST' => 'evil.example', 'HTTP_ORIGIN' => 'https://evil.example'])[0] === 403);
check('без Origin и Referer → 403', $run($calc, ['HTTP_ORIGIN' => ''])[0] === 403);
check('Referer своего сайта → 200', $run($calc, ['HTTP_ORIGIN' => '', 'HTTP_REFERER' => 'https://www.tovarvdele.ru/uslugi/'])[0] === 200);
$sent = [];
$r = $run($calc);
check('расчёт → 200 ok', $r[0] === 200 && $r[1]['ok'] === true && count($sent) === 1);
$m = $sent[0] ?? '';
check('сайт и форма', str_contains($m, 'Товар в деле') && str_contains($m, 'Калькулятор'));
check('телефон нормализован', str_contains($m, '+7 (900) 123-45-67'));
check('HTML экранирован', str_contains($m, 'Иван &lt;b&gt;') && str_contains($m, 'FBS &amp; &lt;ЧЗ&gt;') && !str_contains($m, '<ЧЗ>'));
check('расчёт и UTM', str_contains($m, '2 350 ₽') && str_contains($m, 'utm_source=yandex') && str_contains($m, 'https://tovarvdele.ru/'));
check('время МСК', (bool)preg_match('/🕒 \d\d\.\d\d\.\d{4}, \d\d:\d\d МСК/u', $m));

$sent = [];
check('ловушка company → 200 без отправки', $run(['company' => 'ACME'] + $calc)[0] === 200 && !$sent);
check('заполнено за 0 с → 200 без отправки', $run(['ts' => time() * 1000] + $calc)[0] === 200 && !$sent);
check('ссылка в имени → 200 без отправки', $run(['name' => 'http://spam.example'] + $calc)[0] === 200 && !$sent);
check('без имени → 422', $run(['name' => 'A'] + $calc)[0] === 422);
check('плохой телефон → 422', $run(['phone' => '123'] + $calc)[0] === 422);
check('плохая почта → 422', $run(['email' => 'nope'] + $calc)[0] === 422);
check('ни телефона, ни почты → 422', $run(['phone' => '', 'email' => ''] + $calc)[0] === 422);
check('битый JSON → 400', lead_handle($srv(), '{', [], $cfg, $send, $dir)[0] === 400);
check('обычная форма (POST) → 200', lead_handle($srv(['CONTENT_TYPE' => 'application/x-www-form-urlencoded']), '', $calc, $cfg, $send, $dir)[0] === 200);
check('нет конфига → 503', $run($calc, [], [])[0] === 503);
check('Telegram не ответил → 502', lead_handle($srv(), json_encode($calc), [], $cfg, fn() => false, $dir)[0] === 502);

$ip = ['REMOTE_ADDR' => '192.0.2.7'];
$codes = [];
for ($i = 0; $i < 6; $i++) {
    $codes[] = $run($calc, $ip)[0];
}
check('rate limit: 6-я заявка за 10 минут → 429', $codes === [200, 200, 200, 200, 200, 429]);

$sent = [];
$agency = ['form' => 'audit', 'name' => 'Мария', 'phone' => '+7 (912) 000-11-22', 'email' => 'm@shop.ru', 'topic' => 'Пакет «Рост»',
    'services' => ['Продвижение', 'Контент'], 'shop' => 'https://www.wildberries.ru/seller/1', 'comment' => "Нужна реклама\nсрочно", 'ts' => (time() - 20) * 1000];
$r = $run($agency, ['HTTP_HOST' => 'madrocks.agency', 'HTTP_ORIGIN' => 'https://madrocks.agency']);
$m = $sent[0] ?? '';
check('агентство → 200 и своё имя', $r[0] === 200 && str_contains($m, 'Madrocks agency') && str_contains($m, 'Обсудить проект'));
check('агентство: тема, услуги, магазин, комментарий', str_contains($m, 'Пакет «Рост»') && str_contains($m, 'Продвижение, Контент') && str_contains($m, 'wildberries') && str_contains($m, "Нужна реклама\nсрочно"));
check('нет расчёта у агентства', !str_contains($m, 'Расчёт'));

$long = $calc;
$long['calc']['lines'] = array_fill(0, 20, [str_repeat('Очень длинная строка ', 7), '1 ₽']);
$long['comment'] = str_repeat('текст ', 330);
$sent = [];
$run($long, ["REMOTE_ADDR" => "198.51.100.1"]);
check('сообщение не длиннее лимита Telegram', isset($sent[0]) && mb_strlen($sent[0]) <= 4096);

check('api/lead.php и agency/api/lead.php совпадают', file_get_contents($root . '/api/lead.php') === file_get_contents($root . '/agency/api/lead.php'));

array_map('unlink', glob($dir . '/*') ?: []);
@rmdir($dir);
echo $fails ? "$fails из $n проверок не прошли\n" : "OK: $n проверок\n";
exit($fails ? 1 : 0);
