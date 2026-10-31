<?php
/**
 * Заявки с сайтов «Товар в деле» (tovarvdele.ru) и «Madrocks agency» (madrocks.agency) → Telegram.
 *
 * Один и тот же файл лежит в api/lead.php (фулфилмент) и agency/api/lead.php (агентство):
 * сайт определяется по домену запроса. Файлы должны совпадать байт в байт (проверяет api/tests/run.php).
 *
 * POST application/json (или обычная форма) → {"ok":true} | {"ok":false,"error":"…"}.
 * Поля: form, name, phone, email, comment, topic, services, shop, calc{…}, page, utm{…}, ts, company (ловушка).
 *
 * Токен и chat_id лежат вне docroot и в репозиторий не попадают:
 *   /var/www/u3698839/data/config/telegram.php → return ['bot_token' => '…', 'chat_id' => '…'];
 * Только sendMessage: webhook бота не трогаем (его использует другой сервис).
 */
declare(strict_types=1);

const LEAD_CONFIG = '/var/www/u3698839/data/config/telegram.php';
const LEAD_HOSTS = [
    'tovarvdele.ru' => 'Товар в деле',
    'madrocks.agency' => 'Madrocks agency',
];
const LEAD_FORMS = [
    'calc' => 'Калькулятор · «Получить точный расчёт»',
    'audit' => 'Заявка в агентство · «Обсудить проект»',
    'callback' => 'Обратный звонок',
    'lead' => 'Заявка с сайта',
];
const LEAD_RATE = [[5, 600], [20, 86400]];  // не больше 5 заявок за 10 минут и 20 в сутки с одного IP
const LEAD_RATE_ALL = [60, 3600];           // и не больше 60 в час со всех IP вместе
const LEAD_MIN_FILL = 2;                    // форму заполнили быстрее чем за 2 секунды — бот

function lead_out(int $code, array $body): void
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    header('X-Robots-Tag: noindex');
    echo json_encode($body, JSON_UNESCAPED_UNICODE);
}

function lead_str($v, int $max): string
{
    if (!is_scalar($v)) {
        return '';
    }
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', (string)$v) ?? '';
    $v = trim(preg_replace('/[ \t]+/u', ' ', $v) ?? '');
    return mb_substr($v, 0, $max);
}

function lead_h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Домен запроса без www и порта; null — чужой домен. */
function lead_host(array $server): ?string
{
    $host = strtolower((string)($server['HTTP_HOST'] ?? ''));
    $host = preg_replace('/:\d+$/', '', $host) ?? '';
    $host = preg_replace('/^www\./', '', $host) ?? '';
    return isset(LEAD_HOSTS[$host]) ? $host : null;
}

/** Проверка Origin/Referer: запрос должен прийти со своего сайта. */
function lead_same_site(array $server, string $host): bool
{
    $src = (string)(($server['HTTP_ORIGIN'] ?? '') ?: ($server['HTTP_REFERER'] ?? ''));
    if ($src === '') {
        return false;
    }
    $h = strtolower((string)parse_url($src, PHP_URL_HOST));
    return $h === $host || $h === 'www.' . $host;
}

function lead_digits(string $phone): string
{
    $d = preg_replace('/\D/', '', $phone) ?? '';
    if ($d !== '' && $d[0] === '8') {
        $d = '7' . substr($d, 1);
    }
    return $d;
}

/** Нормализует и проверяет данные. Возвращает [данные, ошибка|null]. */
function lead_validate(array $in): array
{
    $d = [
        'form' => lead_str($in['form'] ?? 'lead', 20),
        'name' => lead_str($in['name'] ?? '', 80),
        'phone' => lead_str($in['phone'] ?? '', 30),
        'email' => lead_str($in['email'] ?? '', 120),
        'comment' => lead_str($in['comment'] ?? '', 2000),
        'topic' => lead_str($in['topic'] ?? '', 200),
        'services' => lead_str(is_array($in['services'] ?? null) ? implode(', ', array_filter($in['services'], 'is_scalar')) : ($in['services'] ?? ''), 300),
        'shop' => lead_str($in['shop'] ?? '', 300),
        'page' => lead_str($in['page'] ?? '', 500),
        'consent' => lead_str($in['consent'] ?? '', 200),
        'calc' => [],
        'utm' => [],
    ];
    if (!isset(LEAD_FORMS[$d['form']])) {
        $d['form'] = 'lead';
    }
    $c = is_array($in['calc'] ?? null) ? $in['calc'] : [];
    foreach (['units', 'total', 'per_unit', 'discount', 'ops'] as $k) {
        if (isset($c[$k])) {
            $d['calc'][$k] = lead_str($c[$k], 40);
        }
    }
    if (is_array($c['lines'] ?? null)) {
        foreach (array_slice($c['lines'], 0, 20) as $l) {
            if (is_array($l) && count($l) >= 2) {
                $d['calc']['lines'][] = [lead_str($l[0], 160), lead_str($l[1], 40)];
            }
        }
    }
    $u = is_array($in['utm'] ?? null) ? $in['utm'] : [];
    foreach (['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'yclid', 'gclid', 'referrer', 'landing'] as $k) {
        if (isset($u[$k]) && lead_str($u[$k], 300) !== '') {
            $d['utm'][$k] = lead_str($u[$k], 300);
        }
    }

    if (mb_strlen($d['name']) < 2) {
        return [$d, 'Укажите имя'];
    }
    $digits = lead_digits($d['phone']);
    $hasPhone = strlen($digits) === 11 && $digits[0] === '7';
    $hasEmail = $d['email'] !== '' && filter_var($d['email'], FILTER_VALIDATE_EMAIL) !== false;
    if ($d['phone'] !== '' && !$hasPhone) {
        return [$d, 'Проверьте номер телефона'];
    }
    if ($d['email'] !== '' && !$hasEmail) {
        return [$d, 'Проверьте адрес почты'];
    }
    if (!$hasPhone && !$hasEmail) {
        return [$d, 'Укажите телефон или почту'];
    }
    if ($hasPhone) {
        $d['phone'] = sprintf('+7 (%s) %s-%s-%s', substr($digits, 1, 3), substr($digits, 4, 3), substr($digits, 7, 2), substr($digits, 9, 2));
    }
    // Ссылки в имени и комментарии — почти всегда спам.
    if (preg_match('~https?://|www\.|\[url~i', $d['name'] . ' ' . $d['comment'])) {
        return [$d, 'spam'];
    }
    return [$d, null];
}

/** Текст сообщения для Telegram (parse_mode=HTML). */
function lead_message(array $d, string $site, string $now): string
{
    $L = ['🟦 <b>Новая заявка · ' . lead_h($site) . '</b>', lead_h(LEAD_FORMS[$d['form']])];
    if ($d['topic'] !== '') {
        $L[] = 'Тема: <b>' . lead_h($d['topic']) . '</b>';
    }
    $L[] = '';
    $L[] = '👤 ' . lead_h($d['name']);
    if ($d['phone'] !== '') {
        $L[] = '📞 ' . lead_h($d['phone']);
    }
    if ($d['email'] !== '') {
        $L[] = '✉️ ' . lead_h($d['email']);
    }
    if ($d['services'] !== '') {
        $L[] = '🧩 Услуги: ' . lead_h($d['services']);
    }
    if ($d['shop'] !== '') {
        $L[] = '🛒 Магазин: ' . lead_h($d['shop']);
    }
    if ($d['comment'] !== '') {
        $L[] = '';
        $L[] = '💬 ' . lead_h($d['comment']);
    }
    $c = $d['calc'];
    if ($c) {
        $L[] = '';
        $L[] = '🧮 <b>Расчёт' . (isset($c['total']) ? ': ' . lead_h($c['total']) : '') . '</b>';
        $meta = [];
        foreach (['units' => '', 'per_unit' => 'за ед. ', 'discount' => 'со скидкой ', 'ops' => 'операций: '] as $k => $p) {
            if (isset($c[$k]) && $c[$k] !== '') {
                $meta[] = $p . lead_h($c[$k]);
            }
        }
        if ($meta) {
            $L[] = implode(' · ', $meta);
        }
        foreach ($c['lines'] ?? [] as [$a, $b]) {
            $L[] = '• ' . lead_h($a) . ' — ' . lead_h($b);
        }
    }
    $L[] = '';
    if ($d['page'] !== '') {
        $L[] = '🔗 ' . lead_h($d['page']);
    }
    if ($d['utm']) {
        $L[] = '📈 ' . implode(' · ', array_map(fn($k, $v) => lead_h($k) . '=' . lead_h($v), array_keys($d['utm']), $d['utm']));
    }
    $L[] = '🕒 ' . lead_h($now) . ' МСК';
    if ($d['consent'] !== '') {
        $L[] = '✅ ' . lead_h($d['consent']);
    }
    $text = implode("\n", $L);
    // Лимит Telegram — 4096 символов; режем по строкам, чтобы не порвать HTML-сущность.
    while (mb_strlen($text) > 4000 && count($L) > 6) {
        array_splice($L, -4, 1);
        $text = implode("\n", $L);
    }
    return $text;
}

/** Ограничение частоты: файлы с метками времени вне docroot. true — можно. */
function lead_rate_ok(string $dir, string $ip, int $now): bool
{
    if (!is_dir($dir) && !@mkdir($dir, 0700, true) && !is_dir($dir)) {
        return true;  // хранилище недоступно — не блокируем клиентов
    }
    $check = function (string $file, array $limits) use ($now): bool {
        $fh = @fopen($file, 'c+');
        if (!$fh) {
            return true;
        }
        flock($fh, LOCK_EX);
        $ts = json_decode((string)stream_get_contents($fh), true);
        $ts = is_array($ts) ? array_filter($ts, fn($t) => is_int($t) && $t > $now - 86400) : [];
        $ok = true;
        foreach ($limits as [$max, $win]) {
            if (count(array_filter($ts, fn($t) => $t > $now - $win)) >= $max) {
                $ok = false;
            }
        }
        if ($ok) {
            $ts[] = $now;
        }
        ftruncate($fh, 0);
        rewind($fh);
        fwrite($fh, json_encode(array_values($ts)));
        flock($fh, LOCK_UN);
        fclose($fh);
        return $ok;
    };
    return $check($dir . '/ip-' . hash('sha256', $ip) . '.json', LEAD_RATE)
        && $check($dir . '/all.json', [LEAD_RATE_ALL]);
}

function lead_rate_dir(): string
{
    $base = dirname(LEAD_CONFIG, 2);  // /var/www/u3698839/data
    return is_dir($base) ? $base . '/tmp/lead-rate' : sys_get_temp_dir() . '/lead-rate';
}

/** Отправка в Telegram. Возвращает true при ok от Bot API. */
function lead_send(array $cfg, string $text): bool
{
    $url = 'https://api.telegram.org/bot' . $cfg['bot_token'] . '/sendMessage';
    $body = http_build_query([
        'chat_id' => $cfg['chat_id'],
        'text' => $text,
        'parse_mode' => 'HTML',
        'disable_web_page_preview' => 'true',
    ]);
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_TIMEOUT => 10,
        ]);
        $res = curl_exec($ch);
        curl_close($ch);
    } else {
        $res = @file_get_contents($url, false, stream_context_create(['http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
            'content' => $body,
            'timeout' => 10,
            'ignore_errors' => true,
        ]]));
    }
    $j = is_string($res) ? json_decode($res, true) : null;
    if (!is_array($j) || empty($j['ok'])) {
        error_log('lead.php: Telegram sendMessage failed: ' . (is_array($j) ? ($j['description'] ?? 'no description') : 'no response'));
        return false;
    }
    return true;
}

function lead_handle(array $server, string $raw, array $post, ?array $cfg, callable $send, string $rateDir): array
{
    if (($server['REQUEST_METHOD'] ?? '') !== 'POST') {
        return [405, ['ok' => false, 'error' => 'Метод не поддерживается']];
    }
    $host = lead_host($server);
    if ($host === null || !lead_same_site($server, $host)) {
        return [403, ['ok' => false, 'error' => 'Запрос не с сайта']];
    }
    if (strlen($raw) > 64000) {
        return [413, ['ok' => false, 'error' => 'Слишком большая заявка']];
    }
    $in = str_contains((string)($server['CONTENT_TYPE'] ?? ''), 'application/json') ? json_decode($raw, true) : $post;
    if (!is_array($in)) {
        return [400, ['ok' => false, 'error' => 'Неверный формат']];
    }
    // Ловушки для ботов: скрытое поле и слишком быстрое заполнение. Боту отвечаем «ок», чтобы не подбирал обход.
    $ts = (int)($in['ts'] ?? 0);
    $now = time();
    if (lead_str($in['company'] ?? '', 200) !== '' || ($ts > 0 && $now - intdiv($ts, 1000) < LEAD_MIN_FILL)) {
        return [200, ['ok' => true]];
    }
    [$d, $err] = lead_validate($in);
    if ($err === 'spam') {
        return [200, ['ok' => true]];
    }
    if ($err !== null) {
        return [422, ['ok' => false, 'error' => $err]];
    }
    $ip = (string)($server['REMOTE_ADDR'] ?? '');
    if (!lead_rate_ok($rateDir, $ip, $now)) {
        return [429, ['ok' => false, 'error' => 'Слишком много заявок, попробуйте позже']];
    }
    if (!$cfg || empty($cfg['bot_token']) || empty($cfg['chat_id'])) {
        error_log('lead.php: no Telegram config at ' . LEAD_CONFIG);
        return [503, ['ok' => false, 'error' => 'Канал заявок не настроен']];
    }
    $msk = (new DateTimeImmutable('@' . $now))->setTimezone(new DateTimeZone('Europe/Moscow'))->format('d.m.Y, H:i');
    if (!$send($cfg, lead_message($d, LEAD_HOSTS[$host], $msk))) {
        return [502, ['ok' => false, 'error' => 'Не удалось отправить заявку']];
    }
    return [200, ['ok' => true]];
}

// Запуск как веб-эндпоинта (при подключении из тестов — только функции).
if (!defined('LEAD_TEST')) {
    $cfg = is_file(LEAD_CONFIG) ? (require LEAD_CONFIG) : null;
    [$code, $body] = lead_handle($_SERVER, (string)file_get_contents('php://input'), $_POST, is_array($cfg) ? $cfg : null, 'lead_send', lead_rate_dir());
    lead_out($code, $body);
}
