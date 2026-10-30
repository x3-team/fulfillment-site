<?php
// Лёгкая админка «Товар в деле» для shared-хостинга (PHP 8.2+, без composer и сборки).
// Источник правды — сами файлы сайта: админка читает константы калькулятора/FAQ из index.html
// и data/seo.json, а при сохранении переписывает их на месте (с резервной копией).
declare(strict_types=1);
if (!defined('TVD_ADMIN')) { http_response_code(403); exit; }

date_default_timezone_set('Europe/Moscow');
const SITE_ROOT = __DIR__ . '/..';
$local = __DIR__ . '/config.local.php';          // не в git: переопределение путей
$cfg = is_file($local) ? (array)require $local : [];
define('DATA_DIR', rtrim($cfg['data_dir'] ?? (getenv('TVD_ADMIN_DATA') ?: dirname(__DIR__, 3) . '/.tovarvdele-admin'), '/'));
const MAX_BACKUPS = 30;

function site_path(string $rel): string { return SITE_ROOT . '/' . ltrim($rel, '/'); }
function rd(string $rel): string { $s = @file_get_contents(site_path($rel)); if ($s === false) throw new RuntimeException("Не читается $rel"); return $s; }
function data_init(): void {
    if (!is_dir(DATA_DIR) && !@mkdir(DATA_DIR, 0700, true)) throw new RuntimeException('Не создать папку данных ' . DATA_DIR);
    if (!is_file(DATA_DIR . '/.htaccess')) file_put_contents(DATA_DIR . '/.htaccess', "Require all denied\n");
}
function atomic_write(string $path, string $data): void {
    $tmp = $path . '.tmp' . bin2hex(random_bytes(4));
    if (file_put_contents($tmp, $data, LOCK_EX) === false || !rename($tmp, $path)) { @unlink($tmp); throw new RuntimeException("Не записать $path"); }
}
function json_read(string $file, $def) { $s = @file_get_contents($file); if ($s === false) return $def; $v = json_decode($s, true); return $v ?? $def; }
function json_write(string $file, $v): void { atomic_write($file, json_encode($v, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n"); }

// ---------- auth ----------
function users(): array { return json_read(DATA_DIR . '/users.json', []); }
function session_start_secure(): void {
    $https = ($_SERVER['HTTPS'] ?? '') === 'on' || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https';
    session_name('tvd_admin');
    session_set_cookie_params(['lifetime' => 0, 'path' => '/admin/', 'secure' => $https, 'httponly' => true, 'samesite' => 'Strict']);
    ini_set('session.use_strict_mode', '1');
    session_start();
    if (empty($_SESSION['csrf'])) $_SESSION['csrf'] = bin2hex(random_bytes(32));
    if (!empty($_SESSION['user']) && (time() - ($_SESSION['seen'] ?? 0)) > 8 * 3600) { $_SESSION = []; session_regenerate_id(true); }
    $_SESSION['seen'] = time();
}
function csrf_ok(): bool { return is_string($_POST['csrf'] ?? null) && hash_equals($_SESSION['csrf'], $_POST['csrf']); }
function throttle_key(): string { return DATA_DIR . '/throttle.json'; }
function throttled(): bool {
    $t = json_read(throttle_key(), []); $ip = $_SERVER['REMOTE_ADDR'] ?? '-';
    $rec = array_filter($t[$ip] ?? [], fn($ts) => $ts > time() - 900);
    return count($rec) >= 5;
}
function throttle_hit(bool $fail): void {
    $t = json_read(throttle_key(), []); $ip = $_SERVER['REMOTE_ADDR'] ?? '-';
    if ($fail) $t[$ip] = array_values(array_filter(array_merge($t[$ip] ?? [], [time()]), fn($ts) => $ts > time() - 900)); else unset($t[$ip]);
    json_write(throttle_key(), $t);
}
function login(string $u, string $p): bool {
    $users = users(); $h = $users[$u]['hash'] ?? password_hash('x', PASSWORD_DEFAULT);
    $ok = password_verify($p, $h) && isset($users[$u]);
    if ($ok) { session_regenerate_id(true); $_SESSION['user'] = $u; }
    return $ok;
}
function audit(string $msg): void { @file_put_contents(DATA_DIR . '/audit.log', date('c') . ' ' . ($_SESSION['user'] ?? '-') . ' ' . ($_SERVER['REMOTE_ADDR'] ?? '-') . ' ' . $msg . "\n", FILE_APPEND | LOCK_EX); }

// ---------- JS literal <-> PHP ----------
// Разбирает литерал из index.html (ключи без кавычек, строки в '...', true/false, числа вида .07).
function js_parse(string $s) {
    $out = ''; $n = strlen($s);
    for ($i = 0; $i < $n; $i++) {
        $c = $s[$i];
        if ($c === "'" || $c === '"') {
            $q = $c; $buf = '';
            for ($i++; $i < $n && $s[$i] !== $q; $i++) { if ($s[$i] === '\\') { $i++; $e = $s[$i]; $buf .= ['n' => "\n", 't' => "\t"][$e] ?? $e; } else $buf .= $s[$i]; }
            $out .= json_encode($buf, JSON_UNESCAPED_UNICODE);
        } elseif (preg_match('/\G[A-Za-z_$][\w$]*/', $s, $m, 0, $i)) {
            $w = $m[0]; $i += strlen($w) - 1;
            $out .= in_array($w, ['true', 'false', 'null'], true) ? $w : json_encode($w);
        } elseif ($c === '.' && preg_match('/\G\.\d+/', $s, $m, 0, $i)) { $out .= '0' . $m[0]; $i += strlen($m[0]) - 1; }
        else $out .= $c;
    }
    $v = json_decode($out, true);
    if ($v === null) throw new RuntimeException('Не разобрать литерал JS: ' . json_last_error_msg());
    return $v;
}
function js_enc($v): string { return str_replace('</', '<\/', json_encode($v, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION)); }
function num_js(float $f): string { $s = rtrim(rtrim(sprintf('%.4F', $f), '0'), '.'); return $s === '' ? '0' : $s; }
function ru_num(float $f): string { return str_replace('.', ',', num_js($f)); }

// ---------- чтение текущего состояния ----------
function grab(string $re, string $src, string $what): array { if (!preg_match($re, $src, $m)) throw new RuntimeException("В index.html не найден блок: $what"); return $m; }
function read_calc(): array {
    $src = rd('index.html');
    $ops = js_parse(grab('/const OPS=(\{.*?\}\});/s', $src, 'OPS')[1]);
    $m = grab('/const STORE_RATE=([\d.]+),FREE_DAYS=(\d+),DISC=([\d.]+);/', $src, 'STORE_RATE');
    $a = grab('/const ACCEPT=([\d.]+),/', $src, 'ACCEPT');
    return ['ops' => $ops, 'accept' => (float)$a[1], 'store_rate' => (float)$m[1], 'free_days' => (int)$m[2], 'disc' => (float)$m[3]];
}
function read_faq(): array { return js_parse(grab('/const FAQ=(\[.*?\]);\n/s', rd('index.html'), 'FAQ')[1]); }
function seo_enc(array $v): string { // как json.dump(indent=2, ensure_ascii=False)
    $j = json_encode($v, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRESERVE_ZERO_FRACTION);
    return preg_replace_callback('/^( +)/m', fn($m) => str_repeat(' ', intdiv(strlen($m[1]), 2)), $j) . "\n";
}
function seo_cfg(): array { $v = json_decode(rd('data/seo.json'), true); if (!is_array($v)) throw new RuntimeException('data/seo.json повреждён'); return $v; }

// ---------- запись с бэкапом ----------
const TRACKED = ['index.html', 'data/seo.json', 'llms.txt', 'kontakty/index.html', 'dokumenty/index.html', 'dokumenty/politika/index.html',
    'dokumenty/soglasie/index.html', 'dokumenty/cookies/index.html', 'dokumenty/soglashenie/index.html'];
function snapshot(string $dir): void {
    foreach (TRACKED as $rel) if (is_file(site_path($rel))) { $d = "$dir/$rel"; @mkdir(dirname($d), 0700, true); copy(site_path($rel), $d); }
}
/** @param array<string,string> $files rel => new content */
function publish(array $files, string $what): void {
    data_init();
    if (!is_dir(DATA_DIR . '/original')) snapshot(DATA_DIR . '/original');   // «как в вёрстке» — состояние до первой правки
    $changed = array_filter($files, fn($c, $rel) => $c !== rd($rel), ARRAY_FILTER_USE_BOTH);
    if (!$changed) return;
    $b = DATA_DIR . '/backups/' . date('Ymd-His') . '-' . bin2hex(random_bytes(2));
    snapshot($b);
    foreach ($changed as $rel => $c) atomic_write(site_path($rel), $c);
    audit("$what: " . implode(',', array_keys($changed)));
    $all = glob(DATA_DIR . '/backups/*', GLOB_ONLYDIR) ?: []; sort($all);
    foreach (array_slice($all, 0, max(0, count($all) - MAX_BACKUPS)) as $old) rrm($old);
}
function rrm(string $d): void { foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($d, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST) as $f) $f->isDir() ? rmdir((string)$f) : unlink((string)$f); rmdir($d); }
function restore_from(string $dir, string $what): void {
    if (!is_dir($dir)) throw new RuntimeException('Нет снимка');
    $files = [];
    foreach (TRACKED as $rel) if (is_file("$dir/$rel")) $files[$rel] = file_get_contents("$dir/$rel");
    publish($files, $what);
}

// ---------- сборка правок ----------
function build_calc(array $c): array {
    $src = rd('index.html');
    $src = preg_replace_callback('/const OPS=\{.*?\}\};/s', fn() => 'const OPS=' . js_enc($c['ops']) . ';', $src, 1);
    $src = preg_replace('/const ACCEPT=[\d.]+,/', 'const ACCEPT=' . num_js($c['accept']) . ',', $src, 1);
    $src = preg_replace('/const STORE_RATE=[\d.]+,FREE_DAYS=\d+,DISC=[\d.]+;/', 'const STORE_RATE=' . num_js($c['store_rate']) . ',FREE_DAYS=' . (int)$c['free_days'] . ',DISC=' . num_js($c['disc']) . ';', $src, 1);
    // Тексты рядом с калькулятором, где цифры вписаны в вёрстку.
    $pct = num_js($c['disc'] * 100) . '%';
    $src = preg_replace('/(Скидка |скидкой )\d+(?:[.,]\d+)?%/u', '${1}' . $pct, $src);
    $src = preg_replace('/\d+(?:,\d+)? ₽ за литр в сутки, первые \d+ дней бесплатно/u', ru_num($c['store_rate']) . ' ₽ за литр в сутки, первые ' . (int)$c['free_days'] . ' дней бесплатно', $src);
    $src = preg_replace('/(× \$\{paid\} дн\. × )\d+(?:,\d+)? ₽/u', '${1}' . ru_num($c['store_rate']) . ' ₽', $src);
    $src = preg_replace('/Первые \d+ дней бесплатно/u', 'Первые ' . (int)$c['free_days'] . ' дней бесплатно', $src);
    return ['index.html' => $src];
}
function build_faq(array $faq): array {
    $src = rd('index.html');
    $src = preg_replace_callback('/const FAQ=\[.*?\];\n/s', fn() => 'const FAQ=' . js_enc($faq) . ";\n", $src, 1);
    // статичная копия для роботов (как в tools/seo.py faq_html)
    $html = '';
    foreach ($faq as $i => [$q, $a]) $html .= '<details' . ($i ? '' : ' open') . '><summary><span class="num mono">0' . ($i + 1) . "</span><span>$q</span><span class=\"pl\"></span></summary><div class=\"a\">$a</div></details>";
    $src = preg_replace_callback('/(<div id="faqList">).*?(<\/div>\n<\/div><\/section>)/s', fn($m) => $m[1] . $html . $m[2], $src, 1);
    // JSON-LD FAQPage
    $src = preg_replace_callback('/<script type="application\/ld\+json">(.*?)<\/script>/s', function ($m) use ($faq) {
        $ld = json_decode(str_replace('<\/', '</', $m[1]), true); if (!is_array($ld) || !isset($ld['@graph'])) return $m[0];
        foreach ($ld['@graph'] as &$n) if (($n['@type'] ?? '') === 'FAQPage')
            $n['mainEntity'] = array_map(fn($f) => ['@type' => 'Question', 'name' => strip_tags(html_entity_decode($f[0])), 'acceptedAnswer' => ['@type' => 'Answer', 'text' => strip_tags(html_entity_decode($f[1]))]], $faq);
        return '<script type="application/ld+json">' . str_replace('</', '<\/', json_encode($ld, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)) . '</script>';
    }, $src, 1);
    return ['index.html' => $src];
}
function tel_digits(string $p): string { $d = preg_replace('/\D/', '', $p); return ($d !== '' && $d[0] === '8' && strlen($d) === 11) ? '7' . substr($d, 1) : $d; }
function build_contacts(string $phone, string $email): array {
    $cfg = seo_cfg(); $old = (string)($cfg['organization']['phone'] ?? ''); $oldMail = (string)($cfg['organization']['email'] ?? '');
    $files = [];
    foreach (TRACKED as $rel) {
        if ($rel === 'data/seo.json' || !is_file(site_path($rel))) continue;
        $s = rd($rel);
        if ($old !== '' && $old !== $phone) {
            $s = str_replace([$old, htmlspecialchars($old), 'tel:+' . tel_digits($old)], [$phone, htmlspecialchars($phone), 'tel:+' . tel_digits($phone)], $s);
            $s = str_replace(['"' . tel_digits($old) . '"', '"+' . tel_digits($old) . '"'], ['"' . tel_digits($phone) . '"', '"+' . tel_digits($phone) . '"'], $s);
        }
        if ($oldMail !== '' && $oldMail !== $email) $s = str_replace($oldMail, $email, $s);
        $files[$rel] = $s;
    }
    $cfg['organization']['phone'] = $phone; $cfg['organization']['email'] = $email;
    $files['data/seo.json'] = seo_enc($cfg);
    return $files;
}
function set_meta(string $s, string $attr, string $key, string $val): string {
    $q = preg_quote($key, '/');
    return preg_replace('/(<meta ' . $attr . '="' . $q . '" content=")[^"]*(">)/u', '${1}' . str_replace(['\\', '$'], ['\\\\', '\\$'], htmlspecialchars($val, ENT_QUOTES)) . '${2}', $s, 1);
}
function build_seo(array $pages): array {
    $cfg = seo_cfg(); $files = [];
    foreach ($cfg['pages'] as $i => &$p) {
        if (!isset($pages[$i])) continue;
        foreach (['title', 'description', 'og_title'] as $k) $p[$k] = trim((string)($pages[$i][$k] ?? ''));
        if (!is_file(site_path($p['file']))) continue;
        $s = rd($p['file']);
        $s = preg_replace('/<title>.*?<\/title>/s', '<title>' . str_replace(['\\', '$'], ['\\\\', '\\$'], htmlspecialchars($p['title'], ENT_NOQUOTES)) . '</title>', $s, 1);
        $s = set_meta($s, 'name', 'description', $p['description']);
        $s = set_meta($s, 'property', 'og:description', $p['description']);
        $s = set_meta($s, 'property', 'og:title', $p['og_title'] !== '' ? $p['og_title'] : $p['title']);
        $files[$p['file']] = $s;
    }
    unset($p);
    $files['data/seo.json'] = seo_enc($cfg);
    return $files;
}
function h($s): string { return htmlspecialchars((string)$s, ENT_QUOTES); }
