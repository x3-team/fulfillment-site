<?php
declare(strict_types=1);
define('TVD_ADMIN', 1);
require __DIR__ . '/lib.php';
header('X-Frame-Options: DENY');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
header("Content-Security-Policy: default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'");
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');

$flash = []; $err = [];
try { data_init(); } catch (Throwable $e) { $err[] = $e->getMessage(); }
session_start_secure();
$page = preg_replace('/[^a-z]/', '', $_GET['p'] ?? 'calc') ?: 'calc';
$post = $_SERVER['REQUEST_METHOD'] === 'POST';
if ($post && !csrf_ok()) { http_response_code(400); exit('CSRF: обновите страницу и повторите.'); }

if ($page === 'logout' && $post) { $_SESSION = []; session_regenerate_id(true); header('Location: ./'); exit; }
if (empty($_SESSION['user'])) {
    if ($post && isset($_POST['login'])) {
        if (throttled()) $err[] = 'Слишком много попыток. Подождите 15 минут.';
        elseif (login((string)$_POST['login'], (string)($_POST['password'] ?? ''))) { throttle_hit(false); audit('login'); header('Location: ./'); exit; }
        else { throttle_hit(true); $err[] = 'Неверный логин или пароль.'; }
    }
    if (!users()) $err[] = 'Админ ещё не создан: php admin/bin/create-admin.php <логин> (см. README).';
    layout('Вход', function () { ?>
      <form method="post" class="card narrow"><h1>Вход в админку</h1>
        <input type="hidden" name="csrf" value="<?= h($_SESSION['csrf']) ?>">
        <label>Логин<input name="login" autocomplete="username" required autofocus></label>
        <label>Пароль<input type="password" name="password" autocomplete="current-password" required></label>
        <button>Войти</button></form>
    <?php }, $err, [], false);
    exit;
}

$num = fn($k, $min = 0) => max($min, (float)str_replace(',', '.', (string)($_POST[$k] ?? '0')));
try {
    if ($post) {
        switch ($page) {
            case 'calc':
                $c = read_calc();
                foreach ($c['ops'] as $g => &$grp) foreach ($grp['items'] as $i => &$it) {
                    $f = $_POST['ops'][$g][$i] ?? [];
                    $it[1] = trim((string)($f['name'] ?? $it[1])); $it[2] = trim((string)($f['desc'] ?? $it[2]));
                    $pr = max(0, (float)str_replace(',', '.', (string)($f['price'] ?? $it[3]))); $it[3] = $pr == floor($pr) ? (int)$pr : $pr; $it[4] = trim((string)($f['unit'] ?? $it[4]));
                    if ($it[1] === '') throw new RuntimeException('Название операции не может быть пустым');
                }
                unset($grp, $it);
                $c['accept'] = $num('accept'); $c['store_rate'] = $num('store_rate'); $c['free_days'] = (int)$num('free_days');
                $c['disc'] = min(90, $num('disc_pct')) / 100;
                publish(build_calc($c), 'calc'); $flash[] = 'Калькулятор опубликован.'; break;
            case 'faq':
                $faq = [];
                foreach ((array)($_POST['q'] ?? []) as $i => $q) {
                    $q = trim((string)$q); $a = trim((string)($_POST['a'][$i] ?? ''));
                    if ($q === '' && $a === '') continue;
                    if ($q === '' || $a === '') throw new RuntimeException('У каждого вопроса должен быть ответ');
                    $faq[] = [htmlspecialchars($q, ENT_NOQUOTES), htmlspecialchars($a, ENT_NOQUOTES)];
                }
                if (!$faq) throw new RuntimeException('Нужен хотя бы один вопрос');
                publish(build_faq($faq), 'faq'); $flash[] = 'FAQ опубликован.'; break;
            case 'contacts':
                $phone = trim((string)($_POST['phone'] ?? '')); $email = trim((string)($_POST['email'] ?? ''));
                if (strlen(tel_digits($phone)) < 10) throw new RuntimeException('Телефон выглядит неверно');
                if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) throw new RuntimeException('Email выглядит неверно');
                publish(build_contacts($phone, $email), 'contacts'); $flash[] = 'Контакты обновлены на всех страницах.'; break;
            case 'seo':
                publish(build_seo((array)($_POST['pages'] ?? [])), 'seo'); $flash[] = 'SEO обновлено.'; break;
            case 'history':
                if (isset($_POST['reset'])) { restore_from(DATA_DIR . '/original', 'reset-original'); $flash[] = 'Сайт возвращён как в вёрстке.'; }
                elseif (isset($_POST['backup']) && preg_match('/^[\w-]+$/', (string)$_POST['backup'])) { restore_from(DATA_DIR . '/backups/' . $_POST['backup'], 'restore ' . $_POST['backup']); $flash[] = 'Версия восстановлена.'; }
                break;
        }
    }
} catch (Throwable $e) { $err[] = $e->getMessage(); }

$tabs = ['calc' => 'Калькулятор', 'contacts' => 'Контакты', 'faq' => 'Тексты / FAQ', 'seo' => 'SEO', 'history' => 'История'];
if (!isset($tabs[$page])) $page = 'calc';
layout($tabs[$page], function () use ($page) {
    $csrf = '<input type="hidden" name="csrf" value="' . h($_SESSION['csrf']) . '">';
    try {
    if ($page === 'calc') { $c = read_calc();
        $gn = ['unload' => 'Приёмка: разгрузка', 'work' => 'Работы с товаром', 'fbs' => 'FBS', 'fbo' => 'FBO']; ?>
      <form method="post"><?= $csrf ?>
      <div class="card"><h2>Общее</h2><div class="grid4">
        <label>Приёмка, ₽ за ед.<input name="accept" inputmode="decimal" value="<?= h(ru_num($c['accept'])) ?>"></label>
        <label>Хранение, ₽ за литр в сутки<input name="store_rate" inputmode="decimal" value="<?= h(ru_num($c['store_rate'])) ?>"></label>
        <label>Бесплатных дней хранения<input name="free_days" inputmode="numeric" value="<?= (int)$c['free_days'] ?>"></label>
        <label>Скидка на первую партию, %<input name="disc_pct" inputmode="decimal" value="<?= h(ru_num($c['disc'] * 100)) ?>"></label>
      </div></div>
      <?php foreach ($c['ops'] as $g => $grp) { ?>
        <div class="card"><h2><?= h($gn[$g] ?? $g) ?></h2>
        <table><tr><th>Название</th><th>Описание</th><th>Цена, ₽</th><th>Единица</th></tr>
        <?php foreach ($grp['items'] as $i => $it) { $n = "ops[$g][$i]"; ?>
          <tr><td><input name="<?= $n ?>[name]" value="<?= h($it[1]) ?>"></td><td><input name="<?= $n ?>[desc]" value="<?= h($it[2]) ?>"></td>
          <td><input name="<?= $n ?>[price]" inputmode="decimal" class="s" value="<?= h(ru_num((float)$it[3])) ?>"></td><td><input name="<?= $n ?>[unit]" class="s" value="<?= h($it[4]) ?>"></td></tr>
        <?php } ?></table></div>
      <?php } ?><button>Опубликовать калькулятор</button></form>
    <?php } elseif ($page === 'contacts') { $o = seo_cfg()['organization']; ?>
      <form method="post" class="card narrow"><?= $csrf ?><h2>Контакты</h2>
        <label>Телефон<input name="phone" value="<?= h($o['phone'] ?? '') ?>" placeholder="+7 (916) 000-00-00"></label>
        <label>Email<input name="email" type="email" value="<?= h($o['email'] ?? '') ?>"></label>
        <p class="muted">Телефон заменится в шапке, подвале, на странице контактов, в документах, разметке schema.org и data/seo.json.</p>
        <button>Сохранить и опубликовать</button></form>
    <?php } elseif ($page === 'faq') { $faq = read_faq(); $faq[] = ['', '']; ?>
      <form method="post"><?= $csrf ?><div class="card"><h2>Частые вопросы</h2><p class="muted">Пустая пара удаляется. Последняя пустая строка — для нового вопроса. Сохраняется и в видимый FAQ, и в статичную копию для роботов, и в schema.org.</p>
      <div id="faq"><?php foreach ($faq as $i => [$q, $a]) { ?>
        <div class="qa"><label>Вопрос <?= $i + 1 ?><input name="q[]" value="<?= h(html_entity_decode($q)) ?>"></label><label>Ответ<textarea name="a[]" rows="3"><?= h(html_entity_decode($a)) ?></textarea></label></div>
      <?php } ?></div><button type="button" onclick="const d=document.querySelector('#faq .qa:last-child').cloneNode(true);d.querySelectorAll('input,textarea').forEach(e=>e.value='');document.getElementById('faq').append(d)">+ вопрос</button></div>
      <button>Опубликовать FAQ</button></form>
    <?php } elseif ($page === 'seo') { $cfg = seo_cfg(); ?>
      <form method="post"><?= $csrf ?><?php foreach ($cfg['pages'] as $i => $p) { ?>
        <div class="card"><h2>/<?= h($p['path']) ?> <span class="muted"><?= h($p['file']) ?></span></h2>
        <label>Title <small class="muted">(до ~70 символов)</small><input name="pages[<?= $i ?>][title]" value="<?= h($p['title'] ?? '') ?>" maxlength="200"></label>
        <label>Description <small class="muted">(до ~160)</small><textarea name="pages[<?= $i ?>][description]" rows="2" maxlength="400"><?= h($p['description'] ?? '') ?></textarea></label>
        <label>OG title <small class="muted">(пусто = как title)</small><input name="pages[<?= $i ?>][og_title]" value="<?= h($p['og_title'] ?? '') ?>" maxlength="200"></label></div>
      <?php } ?><button>Опубликовать SEO</button></form>
    <?php } elseif ($page === 'history') { $b = glob(DATA_DIR . '/backups/*', GLOB_ONLYDIR) ?: []; rsort($b); ?>
      <div class="card narrow"><h2>Как в вёрстке</h2>
        <?php if (is_dir(DATA_DIR . '/original')) { ?><p>Вернёт все файлы к состоянию до первой правки через админку (снимок от <?= date('d.m.Y H:i', filemtime(DATA_DIR . '/original')) ?>).</p>
        <form method="post" onsubmit="return confirm('Вернуть сайт как в вёрстке?')"><?= $csrf ?><button name="reset" value="1" class="danger">Вернуть как в вёрстке</button></form>
        <?php } else { ?><p class="muted">Правок ещё не было — сайт и так как в вёрстке.</p><?php } ?></div>
      <div class="card narrow"><h2>Резервные копии</h2><p class="muted">Перед каждой публикацией сохраняется копия (последние <?= MAX_BACKUPS ?>).</p>
        <?php foreach ($b as $d) { $n = basename($d); ?><form method="post" class="row" onsubmit="return confirm('Восстановить <?= h($n) ?>?')"><?= $csrf ?><span><?= h($n) ?></span><button name="backup" value="<?= h($n) ?>" class="ghost">Восстановить</button></form><?php } ?>
        <?php if (!$b) echo '<p class="muted">Пока пусто.</p>'; ?></div>
    <?php }
    } catch (Throwable $e) { echo '<p class="err">' . h($e->getMessage()) . '</p>'; }
}, $err, $flash, true, $tabs, $page);

function layout(string $title, callable $body, array $err, array $flash, bool $auth, array $tabs = [], string $cur = ''): void { ?>
<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title><?= h($title) ?> — админка «Товар в деле»</title>
<style>
:root{--acc:#0056E0;--dark:#0A1736;--bg:#F3F5F9}*{box-sizing:border-box}body{margin:0;font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--dark)}
header{background:var(--dark);color:#fff;display:flex;gap:4px;align-items:center;padding:10px 20px;flex-wrap:wrap}header b{margin-right:16px}header a{color:#C9D3E6;text-decoration:none;padding:6px 10px;border-radius:4px}header a.on,header a:hover{background:#1d2c55;color:#fff}
header form{margin-left:auto}main{max-width:1100px;margin:24px auto;padding:0 16px}.card{background:#fff;border-radius:6px;padding:20px 24px;margin-bottom:16px;box-shadow:0 1px 2px rgba(0,0,0,.05)}.narrow{max-width:560px}
h1,h2{margin:0 0 12px;font-size:20px}label{display:block;margin:0 0 12px;font-weight:600;font-size:13px}input,textarea{display:block;width:100%;margin-top:4px;padding:8px 10px;border:1px solid #cdd5e3;border-radius:4px;font:inherit;font-weight:400}
table{width:100%;border-collapse:collapse}th{text-align:left;font-size:12px;color:#5b6b8c;padding:4px}td{padding:4px;vertical-align:top}td input{margin:0}.s{width:110px}
.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}button{background:var(--acc);color:#fff;border:0;border-radius:4px;padding:10px 18px;font:inherit;font-weight:600;cursor:pointer}
button.ghost,header button{background:transparent;color:inherit;border:1px solid currentColor;padding:6px 12px}button.danger{background:#c62828}.muted{color:#6b7a99;font-weight:400}.qa{border-top:1px solid #eef1f6;padding-top:12px}
.row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-top:1px solid #eef1f6}.err,.ok{padding:10px 14px;border-radius:4px;margin-bottom:12px}.err{background:#fdecea;color:#8a1c1c}.ok{background:#e7f6ec;color:#17582c}
</style></head><body>
<?php if ($auth) { ?><header><b>Товар в деле · админка</b><?php foreach ($tabs as $k => $t) echo '<a href="?p=' . $k . '"' . ($k === $cur ? ' class="on"' : '') . '>' . h($t) . '</a>'; ?>
<a href="../" target="_blank">Сайт ↗</a><form method="post" action="?p=logout"><input type="hidden" name="csrf" value="<?= h($_SESSION['csrf']) ?>"><button><?= h($_SESSION['user']) ?> · выйти</button></form></header><?php } ?>
<main><?php foreach ($err as $e) echo '<p class="err">' . h($e) . '</p>'; foreach ($flash as $f) echo '<p class="ok">' . h($f) . '</p>'; $body(); ?></main></body></html>
<?php }
