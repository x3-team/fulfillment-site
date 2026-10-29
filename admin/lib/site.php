<?php
// Как правки из админки попадают в статические файлы сайта.
//
// Файлы, которые приходят из git (вёрстка), — шаблоны. Админка хранит у себя их копию (templates/) и свои
// настройки (settings.json), а на сайт пишет «шаблон + настройки». Если на сервер залили новую вёрстку,
// файл на сайте перестаёт совпадать с тем, что записала админка: эта новая версия становится шаблоном,
// и настройки достаточно применить заново (кнопка в админке или php admin/bin/apply.php).
declare(strict_types=1);

const JS_JSON = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_PRESERVE_ZERO_FRACTION;

/** Файлы сайта, которые меняет админка: страницы из data/seo.json и llms.txt. */
function managed_files(): array
{
    $files = [];
    foreach (seo_pages() as $p) {
        $files[] = $p['file'];
    }
    $files[] = 'llms.txt';
    return array_values(array_filter(array_unique($files), fn ($f) => is_file(site_file($f))));
}

function seo_cfg(): array
{
    $cfg = json_decode(read_file(site_file('data/seo.json')), true);
    if (!is_array($cfg)) {
        throw new RuntimeException('data/seo.json повреждён');
    }
    return $cfg;
}

function seo_pages(): array
{
    return seo_cfg()['pages'] ?? [];
}

// ---------- настройки и история ----------

function settings(): array
{
    return json_read(data_file('settings.json'), []);
}

function save_settings(array $settings, string $what): void
{
    $old = settings();
    $settings = array_filter($settings, fn ($v) => $v !== null && $v !== []);
    if ($old === $settings) {
        return;
    }
    // В истории — настройки до изменения: из неё можно вернуться на шаг назад
    json_write(data_file('history/' . date('Ymd-His') . '-' . bin2hex(random_bytes(2)) . '.json'), ['what' => $what, 'user' => $_SESSION['user'] ?? 'cli', 'settings' => $old]);
    $all = glob(data_file('history/*.json')) ?: [];
    sort($all);
    foreach (array_slice($all, 0, max(0, count($all) - HISTORY_KEEP)) as $f) {
        @unlink($f);
    }
    json_write(data_file('settings.json'), $settings);
    audit($what);
}

function history(): array
{
    $all = glob(data_file('history/*.json')) ?: [];
    rsort($all);
    return array_map(fn ($f) => ['id' => basename($f, '.json'), 'time' => filemtime($f)] + json_read($f, []), $all);
}

// ---------- шаблоны (вёрстка из git) ----------

/**
 * Сверяет файлы на сайте с тем, что записала админка. Файл, который изменился не через админку
 * (залили новую вёрстку), становится новым шаблоном. Возвращает такие файлы.
 */
function sync_templates(): array
{
    $state = json_read(data_file('state.json'), []);
    $fresh = [];
    foreach (managed_files() as $rel) {
        $served = read_file(site_file($rel));
        $tpl = data_file('templates/' . $rel);
        if (($state[$rel] ?? null) !== sha1($served) || !is_file($tpl)) {
            if (!is_file($tpl) || read_file($tpl) !== $served) {
                write_file($tpl, $served, 0600);
                $fresh[] = $rel;
            }
            $state[$rel] = sha1($served);
        }
    }
    json_write(data_file('state.json'), $state);
    return $fresh;
}

function template(string $rel): string
{
    $tpl = data_file('templates/' . $rel);
    return is_file($tpl) ? read_file($tpl) : read_file(site_file($rel));
}

/** Файлы, где сайт сейчас не совпадает с «вёрстка + настройки» (например, после выкладки). */
function pending_files(): array
{
    $s = settings();
    return array_values(array_filter(managed_files(), fn ($rel) => render_file($rel, $s) !== read_file(site_file($rel))));
}

/** Записывает на сайт «вёрстка + настройки». Возвращает изменённые файлы. */
function apply_settings(?array $settings = null): array
{
    sync_templates();
    $settings ??= settings();
    $state = json_read(data_file('state.json'), []);
    $changed = [];
    foreach (managed_files() as $rel) {
        $out = render_file($rel, $settings);
        if ($out !== read_file(site_file($rel))) {
            write_file(site_file($rel), $out);
            $changed[] = $rel;
        }
        $state[$rel] = sha1($out);
    }
    json_write(data_file('state.json'), $state);
    return $changed;
}

// ---------- что сейчас в вёрстке ----------

function defaults(): array
{
    $home = template('index.html');
    $calc = grab('/const CALC_CFG=(\{.*?\});\n/', $home, 'const CALC_CFG');
    $faq = grab('/const FAQ=(\[.*?\]);\n/', $home, 'const FAQ');
    preg_match_all('/<!--t:(\w+)-->(.*?)<!--\/t-->/s', $home, $t);
    $org = seo_cfg()['organization'] ?? [];
    preg_match('/href="(https:\/\/t\.me\/[^"]*)"/', $home, $tg);
    $seo = [];
    foreach (seo_pages() as $p) {
        if (is_file(site_file($p['file']))) {
            $seo[$p['file']] = read_seo(template($p['file']));
        }
    }
    return [
        'calculator' => json_decode($calc, true),
        'faq' => array_map(fn ($qa) => ['q' => $qa[0], 'a' => $qa[1]], json_decode($faq, true)),
        'texts' => array_combine($t[1], $t[2]),
        'contacts' => ['phone' => (string) ($org['phone'] ?? ''), 'telegram' => $tg[1] ?? 'https://t.me/', 'address' => (string) ($org['address']['street'] ?? '')],
        'seo' => $seo,
    ];
}

function grab(string $re, string $src, string $what): string
{
    if (!preg_match($re, $src, $m)) {
        throw new RuntimeException("В вёрстке главной не найден блок «{$what}». Возможно, index.html собран старой версией.");
    }
    return $m[1];
}

function read_seo(string $html): array
{
    $get = function (string $re) use ($html) {
        return preg_match($re, $html, $m) ? html_entity_decode($m[1], ENT_QUOTES | ENT_HTML5, 'UTF-8') : '';
    };
    return [
        'title' => $get('/<title>(.*?)<\/title>/s'),
        'description' => $get('/<meta name="description" content="([^"]*)">/'),
        'og_title' => $get('/<meta property="og:title" content="([^"]*)">/'),
    ];
}

// ---------- подстановки ----------

function render_file(string $rel, array $s): string
{
    $out = template($rel);
    $d = null;
    $lazy = function () use (&$d) {
        return $d ??= defaults();
    };
    if ($rel === 'index.html') {
        if (isset($s['calculator'])) {
            $out = put_calculator($out, $s['calculator']);
        }
        if (isset($s['texts'])) {
            $out = put_texts($out, $s['texts']);
        }
        if (isset($s['faq'])) {
            $out = put_faq($out, $s['faq']);
        }
    }
    if ($rel === 'llms.txt') {
        if (isset($s['faq'])) {
            $out = put_llms_faq($out, $s['faq']);
        }
        if (isset($s['seo'])) {
            $out = put_llms_pages($out, $s['seo']);
        }
    }
    if (isset($s['contacts'])) {
        $out = put_contacts($out, $s['contacts'], $lazy()['contacts']);
    }
    if (isset($s['seo'][$rel])) {
        $out = put_seo($out, $s['seo'][$rel]);
    }
    return $out;
}

function ru_num(float|int $v): string
{
    $s = rtrim(rtrim(sprintf('%.4F', $v), '0'), '.');
    return str_replace('.', ',', $s === '' || $s === '-0' ? '0' : $s);
}

function put_calculator(string $html, array $c): string
{
    $html = preg_replace_callback('/const CALC_CFG=\{.*?\};\n/', fn () => 'const CALC_CFG=' . json_encode($c, JS_JSON) . ";\n", $html, 1);
    $vals = ['cfg-disc' => ru_num($c['discount']), 'cfg-rate' => ru_num($c['storage']['rate']), 'cfg-free' => (string) (int) $c['storage']['free_days']];
    foreach ($vals as $cls => $v) {
        $html = preg_replace_callback('/(<span class="' . $cls . '">)[^<]*(<\/span>)/', fn ($m) => $m[1] . $v . $m[2], $html);
    }
    // То же в разметке для поисковиков (описание услуги «Хранение»)
    return mapJsonLd($html, function (array $n) use ($c) {
        array_walk_recursive($n, function (&$v) use ($c) {
            if (is_string($v)) {
                $v = preg_replace('/Первые \d+ дней бесплатно/u', 'Первые ' . (int) $c['storage']['free_days'] . ' дней бесплатно', $v);
            }
        });
        return $n;
    });
}

function put_texts(string $html, array $texts): string
{
    return preg_replace_callback('/<!--t:(\w+)-->(.*?)<!--\/t-->/s', function ($m) use ($texts) {
        $v = $texts[$m[1]] ?? null;
        return '<!--t:' . $m[1] . '-->' . ($v === null || trim($v) === '' ? $m[2] : $v) . '<!--/t-->';
    }, $html);
}

function put_faq(string $html, array $faq): string
{
    $pairs = array_map(fn ($f) => [$f['q'], $f['a']], $faq);
    $html = preg_replace_callback('/const FAQ=\[.*?\];\n/', fn () => 'const FAQ=' . json_encode($pairs, JS_JSON) . ";\n", $html, 1);
    // Та же разметка, что строят скрипт главной и tools/seo.py: роботы без JS видят ответы
    $list = '';
    foreach ($pairs as $i => [$q, $a]) {
        $list .= '<details' . ($i ? '' : ' open') . '><summary><span class="num mono">0' . ($i + 1) . '</span><span>' . $q . '</span><span class="pl"></span></summary><div class="a">' . $a . '</div></details>';
    }
    $html = preg_replace_callback('/(<div id="faqList">).*?(<\/div>\n<\/div><\/section>)/s', fn ($m) => $m[1] . $list . $m[2], $html, 1);
    return mapJsonLd($html, function (array $n) use ($pairs) {
        if (($n['@type'] ?? null) === 'FAQPage') {
            $n['mainEntity'] = array_map(fn ($p) => ['@type' => 'Question', 'name' => plain($p[0]), 'acceptedAnswer' => ['@type' => 'Answer', 'text' => plain($p[1])]], $pairs);
        }
        return $n;
    });
}

function put_llms_faq(string $txt, array $faq): string
{
    $lines = implode("\n", array_map(fn ($f) => '- ' . plain($f['q']) . ' ' . plain($f['a']), $faq));
    return preg_replace_callback('/(## Частые вопросы\n\n).*?(\n\n## |\n?$)/s', fn ($m) => $m[1] . $lines . $m[2], $txt, 1);
}

function put_llms_pages(string $txt, array $seo): string
{
    $base = rtrim((string) (seo_cfg()['site']['base_url'] ?? ''), '/') . '/';
    foreach (seo_pages() as $p) {
        $desc = trim($seo[$p['file']]['description'] ?? '');
        if ($desc !== '') {
            $url = preg_quote($base . $p['path'], '/');
            $txt = preg_replace_callback('/^(- \[[^\]]*\]\(' . $url . '\): ).*$/m', fn ($m) => $m[1] . $desc, $txt, 1);
        }
    }
    return $txt;
}

function put_contacts(string $out, array $c, array $d): string
{
    $map = [];
    if (($c['phone'] ?? '') !== '' && $c['phone'] !== $d['phone'] && $d['phone'] !== '') {
        $map[$d['phone']] = $c['phone'];
        $map[h($d['phone'])] = h($c['phone']);
        $map['tel:' . tel($d['phone'])] = 'tel:' . tel($c['phone']);
        $map['"' . tel($d['phone']) . '"'] = '"' . tel($c['phone']) . '"';
    }
    if (($c['telegram'] ?? '') !== '' && $c['telegram'] !== $d['telegram']) {
        $map['href="' . $d['telegram'] . '"'] = 'href="' . h($c['telegram']) . '"';
    }
    if (($c['address'] ?? '') !== '' && $c['address'] !== $d['address'] && $d['address'] !== '') {
        $map[$d['address']] = $c['address'];
        $map[h($d['address'])] = h($c['address']);
    }
    return strtr($out, $map);
}

function put_seo(string $html, array $p): string
{
    if (($p['title'] ?? '') !== '') {
        $html = preg_replace_callback('/<title>.*?<\/title>/s', fn () => '<title>' . h($p['title']) . '</title>', $html, 1);
    }
    if (($p['description'] ?? '') !== '') {
        $html = set_meta($html, 'name="description"', $p['description']);
        $html = set_meta($html, 'property="og:description"', $p['description']);
    }
    if (($p['og_title'] ?? '') !== '') {
        $html = set_meta($html, 'property="og:title"', $p['og_title']);
    }
    return $html;
}

// ---------- помощники ----------

function set_meta(string $html, string $attr, string $value): string
{
    return preg_replace_callback('/(<meta ' . preg_quote($attr, '/') . ' content=")[^"]*(">)/', fn ($m) => $m[1] . h($value) . $m[2], $html, 1);
}

function mapJsonLd(string $html, callable $fn): string
{
    return preg_replace_callback('/(<script type="application\/ld\+json">)(.*?)(<\/script>)/s', function ($m) use ($fn) {
        $ld = json_decode(str_replace('<\/', '</', $m[2]), true);
        if (!is_array($ld)) {
            return $m[0];
        }
        if (isset($ld['@graph'])) {
            $ld['@graph'] = array_map($fn, $ld['@graph']);
        } else {
            $ld = $fn($ld);
        }
        $new = str_replace('</', '<\/', json_encode($ld, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
        // Если ничего не поменялось, оставляем исходный текст как есть (форматирование tools/seo.py)
        return json_decode(str_replace('<\/', '</', $m[2]), true) === $ld ? $m[0] : $m[1] . $new . $m[3];
    }, $html);
}

function plain(string $html): string
{
    return trim(preg_replace('/\s+/u', ' ', html_entity_decode(strip_tags($html), ENT_QUOTES | ENT_HTML5, 'UTF-8')));
}

function tel(string $phone): string
{
    $d = preg_replace('/\D/', '', $phone);
    if (strlen($d) === 11 && $d[0] === '8') {
        $d = '7' . substr($d, 1);
    }
    return '+' . $d;
}
