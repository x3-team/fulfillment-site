<?php
// Разбор и проверка форм. Каждая функция возвращает [значение для settings.json, ошибки по полям, введённое].
// В settings.json попадает только то, что отличается от вёрстки; null — «как в вёрстке».
declare(strict_types=1);

const CALC_GROUPS = [
    'unload' => ['title' => 'Разгрузка', 'hint' => 'Посетитель выбирает один вариант и указывает количество.', 'qty' => true],
    'work' => ['title' => 'Работы с товаром', 'hint' => 'Можно отметить несколько. Количество по умолчанию равно размеру партии.', 'qty' => false],
    'fbs' => ['title' => 'FBS под ключ', 'hint' => 'Можно выбрать только один вариант.', 'qty' => false],
    'fbo' => ['title' => 'FBO', 'hint' => '', 'qty' => false],
];

const TEXT_LABELS = [
    'hero_sub' => 'Первый экран — подзаголовок',
    'who_title' => 'Кому подходим — заголовок',
    'who_lead' => 'Кому подходим — подводка',
    'services_title' => 'Услуги — заголовок',
    'services_lead' => 'Услуги — подводка',
    'speed_title' => 'Скорость — заголовок',
    'speed_lead' => 'Скорость — подводка',
    'calc_title' => 'Калькулятор — заголовок',
    'calc_lead' => 'Калькулятор — подводка',
    'why_title' => 'Почему спокойно — заголовок',
    'why_lead' => 'Почему спокойно — подводка',
    'agency_title' => 'Агентство — заголовок',
    'agency_lead' => 'Агентство — подводка',
    'process_title' => 'Как начать — заголовок',
    'faq_title' => 'Вопросы — заголовок',
    'contact_title' => 'Финальный блок — заголовок',
    'contact_lead' => 'Финальный блок — подводка',
];

function post_str(array $a, string $k, int $max = 2000): string
{
    $v = $a[$k] ?? '';
    return is_string($v) ? mb_substr(trim(str_replace("\r\n", "\n", $v)), 0, $max) : '';
}

/** Число из поля: принимает и «0,07», и «0.07». null — не число. */
function post_num(array $a, string $k): float|int|null
{
    $v = str_replace([',', ' ', "\u{00A0}"], ['.', '', ''], post_str($a, $k, 40));
    if ($v === '' || !is_numeric($v)) {
        return null;
    }
    $f = (float) $v;
    return floor($f) == $f && abs($f) < 1e9 ? (int) $f : round($f, 4);
}

function form_calculator(array $p, array $default): array
{
    $err = [];
    $num = function (string $k, string $field, float $min, ?float $max = null) use ($p, &$err) {
        $v = post_num($p, $k);
        if ($v === null) {
            $err[$field] = 'Нужно число';
        } elseif ($v < $min || ($max !== null && $v > $max)) {
            $err[$field] = $max === null ? 'Не меньше ' . ru_num($min) : 'От ' . ru_num($min) . ' до ' . ru_num($max);
        }
        return $v ?? 0;
    };
    $c = [
        'accept' => $num('accept', 'accept', 0),
        'discount' => $num('discount', 'discount', 0, 100),
        'storage' => ['rate' => $num('storage_rate', 'storage_rate', 0), 'free_days' => (int) $num('free_days', 'free_days', 0, 365)],
    ];
    $ids = [];
    foreach (CALC_GROUPS as $g => $meta) {
        $c[$g] = [];
        $rows = is_array($p['ops'][$g] ?? null) ? array_values($p['ops'][$g]) : [];
        $onSeen = false;
        foreach ($rows as $i => $r) {
            if (!is_array($r)) {
                continue;
            }
            $key = "ops.$g.$i";
            $id = post_str($r, 'id', 40);
            if (!preg_match('/^[a-z][a-z0-9_]{0,39}$/', $id) || isset($ids[$id])) {
                $id = 'op' . substr(bin2hex(random_bytes(4)), 0, 6);
            }
            $ids[$id] = true;
            $it = ['id' => $id, 'name' => post_str($r, 'name', 120), 'sub' => post_str($r, 'sub', 300), 'label' => post_str($r, 'label', 120)];
            if ($it['name'] === '') {
                $err["$key.name"] = 'Заполните название';
            }
            $price = post_num($r, 'price');
            if ($price === null || $price < 0) {
                $err["$key.price"] = 'Цена — число от 0';
            }
            $it['price'] = $price ?? 0;
            $it['per'] = post_str($r, 'per', 40);
            if ($meta['qty']) {
                $q = post_num($r, 'qty');
                if ($q === null || $q < 1 || !is_int($q)) {
                    $err["$key.qty"] = 'Целое число от 1';
                }
                $it['qty'] = (int) ($q ?? 1);
            }
            // В «Разгрузке» и FBS посетитель выбирает один вариант — по умолчанию отмечен максимум один
            $on = !empty($r['on']) && !($onSeen && ($g === 'unload' || $g === 'fbs'));
            $onSeen = $onSeen || $on;
            $it['on'] = $on;
            $c[$g][] = $it;
        }
    }
    if (!$c['unload']) {
        $err['ops.unload'] = 'Нужен хотя бы один вариант разгрузки';
    }
    return [$c == $default ? null : $c, $err, $c];
}

function form_contacts(array $p, array $default): array
{
    $err = [];
    $c = ['phone' => post_str($p, 'phone', 40), 'telegram' => post_str($p, 'telegram', 200), 'address' => post_str($p, 'address', 200)];
    if (!preg_match('/^\+?[\d\s()\-]{7,25}$/', $c['phone']) || strlen(preg_replace('/\D/', '', $c['phone'])) < 10) {
        $err['phone'] = 'Телефон в виде +7 (900) 000-00-00';
    }
    if (!preg_match('~^https://t\.me/[A-Za-z0-9_+/-]*$~', $c['telegram'])) {
        $err['telegram'] = 'Ссылка вида https://t.me/tovarvdele';
    }
    if ($c['address'] === '') {
        $err['address'] = 'Заполните адрес';
    }
    return [$c == $default ? null : $c, $err, $c];
}

function form_texts(array $p, array $default): array
{
    $texts = [];
    $all = [];
    foreach (TEXT_LABELS as $k => $_) {
        $v = post_str(is_array($p['texts'] ?? null) ? $p['texts'] : [], $k, 2000);
        $all[$k] = $v;
        if ($v !== '' && $v !== ($default[$k] ?? null)) {
            $texts[$k] = $v;
        }
    }
    return [$texts ?: null, [], $all];
}

function form_faq(array $p, array $default): array
{
    $err = [];
    $faq = [];
    $qs = is_array($p['faq'] ?? null) ? array_values($p['faq']) : [];
    foreach ($qs as $i => $f) {
        $q = post_str(is_array($f) ? $f : [], 'q', 300);
        $a = post_str(is_array($f) ? $f : [], 'a', 3000);
        if ($q === '' && $a === '') {
            continue;
        }
        if ($q === '') {
            $err["faq.$i.q"] = 'Заполните вопрос';
        }
        if ($a === '') {
            $err["faq.$i.a"] = 'Заполните ответ';
        }
        $faq[] = ['q' => $q, 'a' => $a];
    }
    if (!$faq) {
        $err['faq'] = 'Нужен хотя бы один вопрос';
    }
    return [$faq === $default ? null : $faq, $err, $faq];
}

function form_seo(array $p, array $default): array
{
    $seo = [];
    $all = [];
    foreach ($default as $file => $d) {
        $row = is_array($p['seo'][$file] ?? null) ? $p['seo'][$file] : [];
        $v = [];
        foreach (['title' => 200, 'description' => 400, 'og_title' => 200] as $k => $max) {
            $x = preg_replace('/\s+/u', ' ', post_str($row, $k, $max));
            $all[$file][$k] = $x;
            if ($x !== '' && $x !== $d[$k]) {
                $v[$k] = $x;
            }
        }
        if ($v) {
            $seo[$file] = $v;
        }
    }
    return [$seo ?: null, [], $all];
}
