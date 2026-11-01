<?php
// HTML админки. Без сборки: стили и скрипт лежат в admin/assets/.
declare(strict_types=1);

function redirect(string $to): never
{
    header('Location: ' . $to, true, 303);
    exit;
}

function flash(string $msg): void
{
    $_SESSION['flash'] = $msg;
}

function asset(string $f): string
{
    return 'assets/' . $f . '?v=' . @filemtime(dirname(__DIR__) . '/assets/' . $f);
}

function head_html(string $title): void
{ ?>
<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title><?= h($title) ?> — админка «Товар в деле»</title>
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap">
<link rel="stylesheet" href="<?= h(asset('admin.css')) ?>">
<script src="<?= h(asset('admin.js')) ?>" defer></script>
</head>
<?php }

function render_fatal(string $msg): void
{
    head_html('Ошибка'); ?>
<body class="center"><div class="card narrow"><h1>Админка не запустилась</h1><p class="err"><?= h($msg) ?></p><p class="muted">Подробности в admin/README.md.</p></div></body></html>
<?php }

function render_login(string $login, ?string $error): void
{
    head_html('Вход'); ?>
<body class="center">
<form method="post" action="./" class="card narrow login">
  <div class="brand"><img src="../favicon.svg" alt=""> Товар в деле</div>
  <h1>Вход в админку</h1>
  <?php if ($error) { ?><p class="err" role="alert"><?= h($error) ?></p><?php } ?>
  <?= csrf_field() ?>
  <label class="lbl" for="login">Логин</label>
  <input class="inp" id="login" name="login" value="<?= h($login) ?>" autocomplete="username" required autofocus>
  <label class="lbl" for="password">Пароль</label>
  <input class="inp" id="password" type="password" name="password" autocomplete="current-password" required>
  <button class="btn primary wide">Войти</button>
</form>
</body></html>
<?php }

/** Значение для поля: введённое (если форма не прошла проверку), сохранённое или из вёрстки. */
function model(array $v, string $k): mixed
{
    return $v['values'][$k] ?? $v['s'][$k] ?? $v['d'][$k];
}

function err(array $v, string $k): string
{
    return isset($v['errors'][$k]) ? '<p class="ferr">' . h($v['errors'][$k]) . '</p>' : '';
}

function bad(array $v, string $k): string
{
    return isset($v['errors'][$k]) ? ' bad' : '';
}

function render_page(string $page, array $sections, array $v): void
{
    $flash = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    head_html($sections[$page]); ?>
<body>
<header class="top">
  <div class="wrap bar">
    <a class="brand" href="../" target="_blank" rel="noopener"><img src="../favicon.svg" alt=""> Товар в деле <span class="tag">админка</span></a>
    <nav><?php foreach ($sections as $k => $t) { ?><a href="?p=<?= $k ?>"<?= $k === $page ? ' class="on" aria-current="page"' : '' ?>><?= h($t) ?></a><?php } ?></nav>
    <form method="post" action="?p=logout" class="who"><?= csrf_field() ?><span><?= h($_SESSION['user']) ?></span><button class="link">Выйти</button></form>
  </div>
</header>
<main class="wrap">
  <?php if ($v['pending']) { ?>
  <div class="note warn">
    <div><b>На сайте новая вёрстка, правки из админки к ней ещё не применены.</b><br>
      <span class="muted">Файлы: <?= h(implode(', ', $v['pending'])) ?>. Так бывает после выкладки из git.</span></div>
    <form method="post"><?= csrf_field() ?><button class="btn primary" name="action" value="apply">Применить правки</button></form>
  </div>
  <?php } ?>
  <?php if ($flash) { ?><p class="note ok" role="status">✓ <?= h($flash) ?></p><?php } ?>
  <?php if (isset($v['errors']['_'])) { ?><p class="note bad" role="alert"><?= h($v['errors']['_']) ?></p><?php } elseif ($v['errors']) { ?><p class="note bad" role="alert">Проверьте поля, отмеченные красным. Ничего не сохранено.</p><?php } ?>
  <?php ('view_' . $page)($v); ?>
</main>
</body></html>
<?php }

function save_bar(string $page, bool $changed, string $preview): void
{ ?>
<div class="savebar"><div class="wrap">
  <button class="btn primary" form="f" name="action" value="save">Сохранить и опубликовать</button>
  <a class="btn line" href="<?= h($preview) ?>" target="_blank" rel="noopener">Открыть на сайте ↗</a>
  <span class="dirty muted" hidden>Есть несохранённые изменения</span>
  <?php if ($changed) { ?>
  <form method="post" class="push" data-confirm="Вернуть раздел как в вёрстке? Ваши правки в нём удалятся (их можно вернуть в «Истории»)."><?= csrf_field() ?><button class="link" name="action" value="reset">Вернуть как в вёрстке</button></form>
  <?php } ?>
</div></div>
<?php }

// ---------- калькулятор ----------

function calc_row(string $g, array $meta, int|string $i, array $it, array $v): void
{
    $n = "ops[$g][$i]";
    $e = "ops.$g.$i"; ?>
<div class="item" data-row>
  <input type="hidden" name="<?= $n ?>[id]" value="<?= h($it['id'] ?? '') ?>">
  <div class="grid g12">
    <div class="c5"><label class="lbl">Название</label><input class="inp<?= bad($v, "$e.name") ?>" name="<?= $n ?>[name]" value="<?= h($it['name'] ?? '') ?>"><?= err($v, "$e.name") ?></div>
    <div class="c2"><label class="lbl">Цена, ₽</label><input class="inp num<?= bad($v, "$e.price") ?>" name="<?= $n ?>[price]" inputmode="decimal" value="<?= h(isset($it['price']) ? ru_num($it['price']) : '') ?>"><?= err($v, "$e.price") ?></div>
    <div class="c2"><label class="lbl">Единица</label><input class="inp" name="<?= $n ?>[per]" value="<?= h($it['per'] ?? 'за ед.') ?>" placeholder="за ед."></div>
    <?php if ($meta['qty']) { ?>
    <div class="c2"><label class="lbl">Кол-во по умолч.</label><input class="inp num<?= bad($v, "$e.qty") ?>" name="<?= $n ?>[qty]" inputmode="numeric" value="<?= h($it['qty'] ?? 1) ?>"><?= err($v, "$e.qty") ?></div>
    <?php } ?>
    <div class="<?= $meta['qty'] ? 'c1' : 'c3' ?> tools">
      <button type="button" class="icon" data-move="-1" title="Выше" aria-label="Выше">↑</button>
      <button type="button" class="icon" data-move="1" title="Ниже" aria-label="Ниже">↓</button>
      <button type="button" class="icon del" data-remove title="Удалить" aria-label="Удалить">✕</button>
    </div>
    <div class="c7"><label class="lbl">Пояснение под названием</label><input class="inp" name="<?= $n ?>[sub]" value="<?= h($it['sub'] ?? '') ?>"></div>
    <div class="c5"><label class="lbl">Строка в расчёте <span class="muted">(пусто — как название)</span></label><input class="inp" name="<?= $n ?>[label]" value="<?= h($it['label'] ?? '') ?>"></div>
  </div>
  <label class="check"><input type="checkbox" name="<?= $n ?>[on]" value="1"<?= !empty($it['on']) ? ' checked' : '' ?>> Отмечено по умолчанию</label>
</div>
<?php }

function view_calculator(array $v): void
{
    $c = model($v, 'calculator'); ?>
<h1>Калькулятор</h1>
<p class="lead">Цены и операции калькулятора на главной. После сохранения сайт сразу считает по новым ценам.</p>
<form method="post" id="f" data-track>
  <?= csrf_field() ?>
  <section class="card">
    <h2>Общие параметры</h2>
    <div class="grid g4">
      <div><label class="lbl" for="accept">Приёмка, ₽ за ед.</label><input class="inp num<?= bad($v, 'accept') ?>" id="accept" name="accept" inputmode="decimal" value="<?= h(ru_num($c['accept'])) ?>"><?= err($v, 'accept') ?></div>
      <div><label class="lbl" for="discount">Скидка на первую партию, %</label><input class="inp num<?= bad($v, 'discount') ?>" id="discount" name="discount" inputmode="decimal" value="<?= h(ru_num($c['discount'])) ?>"><?= err($v, 'discount') ?></div>
      <div><label class="lbl" for="storage_rate">Хранение, ₽ за литр в сутки</label><input class="inp num<?= bad($v, 'storage_rate') ?>" id="storage_rate" name="storage_rate" inputmode="decimal" value="<?= h(ru_num($c['storage']['rate'])) ?>"><?= err($v, 'storage_rate') ?></div>
      <div><label class="lbl" for="free_days">Бесплатных дней хранения</label><input class="inp num<?= bad($v, 'free_days') ?>" id="free_days" name="free_days" inputmode="numeric" value="<?= h($c['storage']['free_days']) ?>"><?= err($v, 'free_days') ?></div>
    </div>
    <p class="muted small">Скидка и хранение подставятся и в тексты рядом с калькулятором («Скидка 10% на первую партию», «первые 14 дней бесплатно»).</p>
  </section>
  <?php foreach (CALC_GROUPS as $g => $meta) { ?>
  <section class="card" data-list="<?= $g ?>">
    <div class="head">
      <div><h2><?= h($meta['title']) ?></h2><?php if ($meta['hint']) { ?><p class="muted small"><?= h($meta['hint']) ?></p><?php } ?></div>
      <button type="button" class="btn line sm" data-add>+ Добавить</button>
    </div>
    <div class="rows">
      <?php foreach ($c[$g] ?? [] as $i => $it) {
          calc_row($g, $meta, $i, $it, $v);
      } ?>
    </div>
    <p class="empty muted small">Пока пусто: блок на сайте будет без вариантов.</p>
    <?= err($v, "ops.$g") ?>
    <template><?php calc_row($g, $meta, '__i__', ['id' => '', 'on' => false], ['errors' => []]); ?></template>
  </section>
  <?php } ?>
</form>
<?php save_bar('calculator', isset($v['s']['calculator']), '../#calc');
}

// ---------- контакты ----------

function view_contacts(array $v): void
{
    $c = model($v, 'contacts');
    $d = $v['d']['contacts'];
    $fields = [
        'phone' => ['Телефон', 'Как показывать на сайте. Ссылка для звонка соберётся сама.'],
        'telegram' => ['Telegram', 'Полная ссылка, например https://t.me/tovarvdele'],
        'address' => ['Адрес склада', 'Улица и дом, город указан отдельно.'],
    ]; ?>
<h1>Контакты</h1>
<p class="lead">Меняются на всех страницах фулфилмента: в шапке, подвале, на «Контактах», в документах, в llms.txt и в разметке для поисковиков.</p>
<form method="post" id="f" data-track>
  <?= csrf_field() ?>
  <section class="card stack">
    <?php foreach ($fields as $k => [$label, $hint]) { ?>
    <div>
      <label class="lbl" for="<?= $k ?>"><?= h($label) ?></label>
      <input class="inp<?= bad($v, $k) ?>" id="<?= $k ?>" name="<?= $k ?>" value="<?= h($c[$k]) ?>">
      <?= err($v, $k) ?: '<p class="muted small">' . h($hint) . ($c[$k] !== $d[$k] ? ' В вёрстке: ' . h($d[$k]) : '') . '</p>' ?>
    </div>
    <?php } ?>
    <p class="note">Точку на Яндекс.Карте адрес не двигает: если склад переедет, координаты меняет разработчик.</p>
  </section>
</form>
<?php save_bar('contacts', isset($v['s']['contacts']), '../kontakty/');
}

// ---------- тексты и вопросы ----------

function faq_row(int|string $i, array $f, array $v): void
{ ?>
<div class="item" data-row>
  <div class="qrow">
    <span class="no mono" data-no><?= is_int($i) ? sprintf('%02d', $i + 1) : '' ?></span>
    <input class="inp strong<?= bad($v, "faq.$i.q") ?>" name="faq[<?= $i ?>][q]" value="<?= h($f['q']) ?>" placeholder="Вопрос" aria-label="Вопрос">
    <span class="tools">
      <button type="button" class="icon" data-move="-1" title="Выше" aria-label="Выше">↑</button>
      <button type="button" class="icon" data-move="1" title="Ниже" aria-label="Ниже">↓</button>
      <button type="button" class="icon del" data-remove title="Удалить" aria-label="Удалить">✕</button>
    </span>
  </div>
  <?= err($v, "faq.$i.q") ?>
  <textarea class="inp<?= bad($v, "faq.$i.a") ?>" name="faq[<?= $i ?>][a]" rows="3" placeholder="Ответ" aria-label="Ответ" data-grow><?= h($f['a']) ?></textarea>
  <?= err($v, "faq.$i.a") ?>
</div>
<?php }

function view_texts(array $v): void
{
    $texts = model($v, 'texts') + $v['d']['texts'];
    $faq = model($v, 'faq'); ?>
<h1>Тексты и вопросы</h1>
<p class="lead">Заголовки и подводки блоков главной и «Частые вопросы». Перенос строки — <code>&lt;br&gt;</code>. Вопросы попадут и в разметку для поисковиков, и в llms.txt.</p>
<form method="post" id="f" data-track>
  <?= csrf_field() ?>
  <section class="card stack">
    <h2>Заголовки блоков</h2>
    <?php foreach (TEXT_LABELS as $k => $label) {
        if (!array_key_exists($k, $v['d']['texts'])) {
            continue;
        } ?>
    <div>
      <label class="lbl" for="t_<?= $k ?>"><?= h($label) ?><?= ($texts[$k] ?? '') !== $v['d']['texts'][$k] ? ' <span class="acc">· изменено</span>' : '' ?></label>
      <textarea class="inp" id="t_<?= $k ?>" name="texts[<?= $k ?>]" rows="1" data-grow><?= h($texts[$k] ?? '') ?></textarea>
    </div>
    <?php } ?>
  </section>
  <section class="card" data-list="faq">
    <div class="head"><h2>Частые вопросы</h2><button type="button" class="btn line sm" data-add>+ Вопрос</button></div>
    <div class="rows">
      <?php foreach ($faq as $i => $f) {
          faq_row($i, $f, $v);
      } ?>
    </div>
    <p class="empty muted small">Пока пусто.</p>
    <?= err($v, 'faq') ?>
    <template><?php faq_row('__i__', ['q' => '', 'a' => ''], ['errors' => []]); ?></template>
  </section>
</form>
<?php save_bar('texts', isset($v['s']['texts']) || isset($v['s']['faq']), '../#faq');
}

// ---------- SEO ----------

function view_seo(array $v): void
{
    $values = $v['values']['seo'] ?? null;
    $saved = $v['s']['seo'] ?? [];
    $names = [];
    foreach (seo_pages() as $p) {
        $names[$p['file']] = [$p['breadcrumb'] ?? ($p['path'] === '' ? 'Главная' : $p['path']), $p['path']];
    } ?>
<h1>SEO</h1>
<p class="lead">Заголовок и описание страниц для поисковиков и превью ссылок в мессенджерах. Title — до 60–70 знаков, description — до 160.</p>
<form method="post" id="f" data-track>
  <?= csrf_field() ?>
  <?php foreach ($v['d']['seo'] as $file => $d) {
      $cur = $values[$file] ?? (($saved[$file] ?? []) + $d);
      [$name, $path] = $names[$file] ?? [$file, '']; ?>
  <section class="card stack">
    <div class="head"><h2><?= h($name) ?></h2><a class="mono small" href="../<?= h($path) ?>" target="_blank" rel="noopener">/<?= h($path) ?></a></div>
    <div><label class="lbl">Title <span class="count mono" data-count="70"></span></label><input class="inp" name="seo[<?= h($file) ?>][title]" value="<?= h($cur['title']) ?>"></div>
    <div><label class="lbl">Description <span class="count mono" data-count="160"></span></label><textarea class="inp" name="seo[<?= h($file) ?>][description]" rows="2" data-grow><?= h($cur['description']) ?></textarea></div>
    <div><label class="lbl">Заголовок превью (og:title) <span class="count mono" data-count="90"></span></label><input class="inp" name="seo[<?= h($file) ?>][og_title]" value="<?= h($cur['og_title']) ?>"></div>
  </section>
  <?php } ?>
</form>
<?php save_bar('seo', isset($v['s']['seo']), '../');
}

// ---------- история ----------

function view_history(array $v): void
{
    $names = ['calculator' => 'калькулятор', 'contacts' => 'контакты', 'texts' => 'тексты', 'faq' => 'вопросы', 'seo' => 'SEO'];
    $log = @file(data_file('audit.log'), FILE_IGNORE_NEW_LINES) ?: []; ?>
<h1>История</h1>
<p class="lead">Перед каждым сохранением админка запоминает предыдущую версию правок (последние <?= HISTORY_KEEP ?>). Вёрстку из git это не трогает.</p>
<section class="card stack">
  <h2>Сейчас изменено</h2>
  <?php if ($v['s']) { ?>
  <p><?= h(implode(', ', array_map(fn ($k) => $names[$k] ?? $k, array_keys($v['s'])))) ?>. Остальное — как в вёрстке.</p>
  <form method="post" data-confirm="Вернуть весь сайт как в вёрстке? Правки из админки удалятся (их можно вернуть отсюда же)."><?= csrf_field() ?><button class="btn danger" name="action" value="reset_all">Вернуть весь сайт как в вёрстке</button></form>
  <?php } else { ?><p class="muted">Ничего: сайт как в вёрстке.</p><?php } ?>
</section>
<section class="card">
  <h2>Предыдущие версии</h2>
  <?php $hist = history();
    if (!$hist) { ?><p class="muted">Пока пусто.</p><?php } ?>
  <?php foreach ($hist as $item) {
      $keys = array_keys($item['settings'] ?? []); ?>
  <form method="post" class="hrow" data-confirm="Вернуть правки к версии от <?= h(date('d.m.Y H:i', $item['time'])) ?>?">
    <?= csrf_field() ?><input type="hidden" name="id" value="<?= h($item['id']) ?>">
    <span class="mono small"><?= h(date('d.m.Y H:i', $item['time'])) ?></span>
    <span>Как было до «<?= h($item['what'] ?? '') ?>» <span class="muted small">· изменено: <?= h($keys ? implode(', ', array_map(fn ($k) => $names[$k] ?? $k, $keys)) : 'ничего, всё как в вёрстке') ?></span></span>
    <button class="btn line sm" name="action" value="restore">Вернуть эту версию</button>
  </form>
  <?php } ?>
</section>
<section class="card">
  <h2>Журнал</h2>
  <pre class="log"><?= h(implode("\n", array_slice(array_reverse($log), 0, 30))) ?: 'Пусто' ?></pre>
</section>
<?php }
