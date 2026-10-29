<?php
// Проверки админки без сети и без composer:  php admin/tests/run.php
// Копирует сайт во временную папку, гоняет подстановки и настоящий вход через встроенный сервер PHP.
declare(strict_types=1);
if (PHP_SAPI !== 'cli') {
    exit;
}

$repo = dirname(__DIR__, 2);
$tmp = sys_get_temp_dir() . '/tvd-test-' . bin2hex(random_bytes(3));
$site = "$tmp/www/tovarvdele.ru";
$data = "$tmp/data";
mkdir($site, 0777, true);
exec('cp -r ' . escapeshellarg($repo) . '/. ' . escapeshellarg($site) . ' && rm -rf ' . escapeshellarg("$site/.git"));
putenv("TVD_SITE_ROOT=$site");
putenv("TVD_ADMIN_DATA=$data");
define('TVD_ADMIN', 1);
require "$repo/admin/lib/bootstrap.php";
require "$repo/admin/lib/site.php";
require "$repo/admin/lib/forms.php";

$fails = 0;
$n = 0;
function ok(bool $cond, string $what): void
{
    global $fails, $n;
    $n++;
    echo ($cond ? '  ✓ ' : '  ✗ ') . $what . "\n";
    $fails += $cond ? 0 : 1;
}
function f(string $rel): string
{
    return file_get_contents(site_file($rel));
}

data_init();
$orig = [];
foreach (managed_files() as $rel) {
    $orig[$rel] = f($rel);
}

echo "Вёрстка\n";
$d = defaults();
ok($d['calculator']['accept'] === 5 && $d['calculator']['unload'][0]['price'] === 35 && $d['calculator']['storage']['rate'] === 0.07, 'цены калькулятора читаются из index.html');
ok(count($d['faq']) === 6 && count($d['texts']) === 17, 'вопросы и тексты читаются');
ok($d['contacts']['phone'] === '+7 (916) 728-42-46' && $d['contacts']['address'] !== '', 'контакты читаются из data/seo.json');
ok(count(managed_files()) === 8, 'админка управляет 7 страницами и llms.txt');
ok(apply_settings([]) === [], 'без правок сайт не меняется');

echo "Калькулятор\n";
$p = $d['calculator'];
$post = ['accept' => '6,5', 'discount' => '15', 'storage_rate' => '0,1', 'free_days' => '10', 'ops' => []];
foreach (CALC_GROUPS as $g => $_) {
    foreach ($p[$g] as $it) {
        $post['ops'][$g][] = ['id' => $it['id'], 'name' => $it['name'], 'sub' => $it['sub'], 'label' => $it['label'], 'price' => (string) $it['price'], 'per' => $it['per'], 'qty' => (string) ($it['qty'] ?? ''), 'on' => $it['on'] ? '1' : ''];
    }
}
[$same, $err] = form_calculator(array_replace($post, ['accept' => '5', 'discount' => '10', 'storage_rate' => '0.07', 'free_days' => '14']), $d['calculator']);
ok($same === null && !$err, 'форма без изменений = «как в вёрстке»');
$post['ops']['work'][0]['name'] = 'Маркировка </script><b>';
$post['ops']['work'][] = ['id' => '', 'name' => 'Фото товара', 'price' => '12', 'per' => 'за ед.'];
[$calc, $err] = form_calculator($post, $d['calculator']);
ok(!$err && $calc['accept'] === 6.5 && $calc['storage']['rate'] === 0.1 && count($calc['work']) === 5, 'числа с запятой и новая операция');
apply_settings(['calculator' => $calc]);
$h = f('index.html');
ok(str_contains($h, '"accept":6.5') && str_contains($h, '"name":"Фото товара"'), 'цены записаны в const CALC_CFG');
ok(!str_contains($h, 'Маркировка </script>') && str_contains($h, 'Маркировка \\u003C/script\\u003E'), '</script> в названии экранирован');
ok(substr_count($h, '<span class="cfg-disc">15</span>') === 3 && str_contains($h, '<span class="cfg-rate">0,1</span>') && substr_count($h, '<span class="cfg-free">10</span>') === 2, 'скидка и хранение в текстах');
ok(str_contains($h, 'Первые 10 дней бесплатно') && !str_contains($h, 'Первые 14 дней бесплатно'), 'и в разметке для поисковиков');
$bad = $post;
$bad['ops']['fbs'][0]['price'] = '-1';
$bad['ops']['unload'] = [];
[, $err] = form_calculator($bad, $d['calculator']);
ok(isset($err['ops.fbs.0.price'], $err['ops.unload']), 'отрицательная цена и пустая разгрузка не проходят');

echo "Контакты\n";
[$c, $err] = form_contacts(['phone' => '8 (900) 111-22-33', 'telegram' => 'https://t.me/tovarvdele', 'address' => 'ул. Новая, д. 1'], $d['contacts']);
ok(!$err, 'форма контактов');
apply_settings(['calculator' => $calc, 'contacts' => $c]);
$all = implode("\n", array_map('f', managed_files()));
ok(!str_contains($all, '728-42-46') && !str_contains($all, '79167284246'), 'старого телефона не осталось нигде');
ok(substr_count(f('kontakty/index.html'), 'tel:+79001112233') >= 1 && str_contains(f('llms.txt'), '8 (900) 111-22-33'), 'новый телефон и ссылка tel:');
ok(str_contains(f('index.html'), 'href="https://t.me/tovarvdele"') && str_contains(f('kontakty/index.html'), 'ул. Новая, д. 1'), 'Telegram и адрес');
[, $err] = form_contacts(['phone' => 'abc', 'telegram' => 'javascript:alert(1)', 'address' => ''], $d['contacts']);
ok(count($err) === 3, 'неверные контакты не проходят');

echo "Тексты и вопросы\n";
[$t] = form_texts(['texts' => ['calc_title' => 'Цена за минуту'] + $d['texts']], $d['texts']);
[$q, $err] = form_faq(['faq' => [['q' => 'Новый вопрос?', 'a' => 'Ответ & <b>жирно</b>'], ['q' => '', 'a' => '']]], $d['faq']);
ok($t === ['calc_title' => 'Цена за минуту'] && !$err && count($q) === 1, 'в настройки попадает только изменённое');
apply_settings(['texts' => $t, 'faq' => $q]);
$h = f('index.html');
ok(str_contains($h, '<!--t:calc_title-->Цена за минуту<!--/t-->'), 'заголовок блока');
ok(str_contains($h, 'const FAQ=[["Новый вопрос?","Ответ & \\u003Cb\\u003Eжирно\\u003C/b\\u003E"]];'), 'вопросы в скрипте');
ok(str_contains($h, '<span>Новый вопрос?</span><span class="pl"></span></summary><div class="a">Ответ & <b>жирно</b></div>') && !str_contains($h, 'Есть ли минимальный объём'), 'вопросы для роботов без JS');
ok(str_contains($h, '"name":"Новый вопрос?","acceptedAnswer":{"@type":"Answer","text":"Ответ & жирно"}'), 'FAQPage в JSON-LD');
ok(str_contains(f('llms.txt'), "## Частые вопросы\n\n- Новый вопрос? Ответ & жирно\n\n## Страницы"), 'вопросы в llms.txt');
[, $err] = form_faq(['faq' => [['q' => 'Без ответа', 'a' => '']]], $d['faq']);
ok(isset($err['faq.0.a']), 'вопрос без ответа не проходит');

echo "SEO\n";
$row = $d['seo'];
$row['kontakty/index.html']['title'] = 'Контакты склада в Туле';
$row['kontakty/index.html']['description'] = 'Телефон & "адрес"';
[$seo] = form_seo(['seo' => $row], $d['seo']);
ok($seo === ['kontakty/index.html' => ['title' => 'Контакты склада в Туле', 'description' => 'Телефон & "адрес"']], 'в настройки попадает только изменённое');
apply_settings(['seo' => $seo]);
$k = f('kontakty/index.html');
ok(str_contains($k, '<title>Контакты склада в Туле</title>') && str_contains($k, '<meta name="description" content="Телефон &amp; &quot;адрес&quot;">') && str_contains($k, '<meta property="og:description" content="Телефон &amp; &quot;адрес&quot;">'), 'title, description, og:description с экранированием');
ok(str_contains(f('llms.txt'), '/kontakty/): Телефон & "адрес"'), 'описание страницы в llms.txt');

echo "Откат и новая вёрстка\n";
apply_settings([]);
$same = true;
foreach ($orig as $rel => $s) {
    $same = $same && f($rel) === $s;
}
ok($same, '«как в вёрстке» возвращает файлы байт в байт');
json_write(data_file('settings.json'), ['contacts' => $c]);
apply_settings();
// Имитируем выкладку из git: на сайт заливают новую вёрстку со старым телефоном
file_put_contents(site_file('kontakty/index.html'), str_replace('Контакты', 'Контакты (новая вёрстка)', $orig['kontakty/index.html']));
ok(pending_files() === ['kontakty/index.html'], 'админка замечает, что выложили новую вёрстку');
apply_settings();
$k = f('kontakty/index.html');
ok(str_contains($k, 'Контакты (новая вёрстка)') && str_contains($k, '8 (900) 111-22-33') && !str_contains($k, '728-42-46'), 'правки ложатся поверх новой вёрстки');
ok(pending_files() === [], 'после применения всё совпадает');

// ---------- вход через встроенный сервер ----------
echo "Вход и защита\n";
putenv('TVD_PASS=correct-horse-battery');
exec('php ' . escapeshellarg("$site/admin/bin/create-admin.php") . ' admin 2>&1', $out, $code);
ok($code === 0 && password_verify('correct-horse-battery', json_read(data_file('users.json'), [])['admin']['hash']), 'create-admin.php хранит password_hash');
$port = 18000 + random_int(0, 999);
$srv = proc_open(['php', '-S', "127.0.0.1:$port", '-t', $site], [['pipe', 'r'], ['file', '/dev/null', 'w'], ['file', '/dev/null', 'w']], $pipes, null, ['TVD_SITE_ROOT' => $site, 'TVD_ADMIN_DATA' => $data, 'PATH' => getenv('PATH')]);
usleep(400000);
$jar = '';
function req(string $method, string $path, array $form = []): array
{
    global $port, $jar;
    $ctx = stream_context_create(['http' => ['method' => $method, 'ignore_errors' => true, 'follow_location' => 0,
        'header' => "Content-Type: application/x-www-form-urlencoded\r\nCookie: $jar\r\n", 'content' => http_build_query($form)]]);
    $body = @file_get_contents("http://127.0.0.1:$port$path", false, $ctx);
    $code = (int) explode(' ', $http_response_header[0] ?? 'x 0')[1];
    foreach ($http_response_header ?? [] as $hd) {
        if (preg_match('/^Set-Cookie: (tvd_admin=[^;]+)/i', $hd, $m)) {
            $jar = $m[1];
        }
    }
    return [$code, (string) $body, $http_response_header ?? []];
}
function csrf(string $html): string
{
    return preg_match('/name="csrf" value="([0-9a-f]+)"/', $html, $m) ? $m[1] : '';
}
[$code, $html, $hdr] = req('GET', '/admin/');
ok($code === 200 && str_contains($html, 'Вход в админку') && in_array('X-Frame-Options: DENY', $hdr, true), 'страница входа и заголовки безопасности');
[$code] = req('POST', '/admin/', ['login' => 'admin', 'password' => 'correct-horse-battery']);
ok($code === 400, 'вход без CSRF-токена отклонён');
[$code, $html] = req('POST', '/admin/', ['csrf' => csrf($html), 'login' => 'admin', 'password' => 'wrong']);
ok($code === 200 && str_contains($html, 'Неверный логин или пароль'), 'неверный пароль');
[$code, , $hdr] = req('POST', '/admin/', ['csrf' => csrf($html), 'login' => 'admin', 'password' => 'correct-horse-battery']);
ok($code === 303, 'верный пароль пускает');
[$code, $html] = req('GET', '/admin/?p=contacts');
ok($code === 200 && str_contains($html, '8 (900) 111-22-33'), 'раздел «Контакты» открывается');
$form = ['csrf' => csrf($html), 'action' => 'save', 'phone' => '+7 (999) 000-00-00', 'telegram' => 'https://t.me/', 'address' => $d['contacts']['address']];
[$code] = req('POST', '/admin/?p=contacts', $form);
ok($code === 303 && str_contains(f('index.html'), '+7 (999) 000-00-00'), 'сохранение из формы публикует на сайт');
[$code] = req('POST', '/admin/?p=contacts', ['csrf' => 'bad'] + $form);
ok($code === 400, 'сохранение с чужим токеном отклонено');
[$code, $html] = req('GET', '/admin/?p=history');
ok($code === 200 && str_contains($html, 'Вернуть эту версию'), 'история');
foreach (['/admin/lib/site.php', '/admin/bin/create-admin.php'] as $u) {
    [$code, $body] = req('GET', $u);
    ok($code === 404 || $body === '', "$u из веба ничего не отдаёт");
}
// Лимит попыток: 5 неудач с одного адреса — дальше пауза
req('POST', '/admin/?p=logout', ['csrf' => csrf($html)]);
[, $html] = req('GET', '/admin/');
for ($i = 0; $i < 5; $i++) {
    [, $html] = req('POST', '/admin/', ['csrf' => csrf($html), 'login' => 'admin', 'password' => 'nope']);
}
[$code, $html] = req('POST', '/admin/', ['csrf' => csrf($html), 'login' => 'admin', 'password' => 'correct-horse-battery']);
ok($code === 429 && str_contains($html, 'Слишком много попыток'), 'после 5 неудач вход закрыт даже с верным паролем');
proc_terminate($srv);

exec('rm -rf ' . escapeshellarg($tmp));
echo "\n" . ($fails ? "Не прошло: $fails из $n\n" : "Все проверки прошли: $n\n");
exit($fails ? 1 : 0);
