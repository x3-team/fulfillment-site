<?php
// Админка сайта «Товар в деле»: /admin/?p=calculator|contacts|texts|seo|history
declare(strict_types=1);
define('TVD_ADMIN', 1);
require __DIR__ . '/lib/bootstrap.php';
require __DIR__ . '/lib/auth.php';
require __DIR__ . '/lib/site.php';
require __DIR__ . '/lib/forms.php';
require __DIR__ . '/lib/views.php';

header('X-Frame-Options: DENY');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header("Content-Security-Policy: default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'");
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex, nofollow');

try {
    data_init();
} catch (Throwable $e) {
    http_response_code(500);
    render_fatal($e->getMessage());
    exit;
}
session_boot();

$post = ($_SERVER['REQUEST_METHOD'] ?? 'GET') === 'POST';
$page = is_string($_GET['p'] ?? null) ? $_GET['p'] : 'calculator';
if ($post && !csrf_ok()) {
    http_response_code(400);
    render_fatal('Форма устарела. Обновите страницу и повторите.');
    exit;
}

// ---------- вход ----------
if (empty($_SESSION['user']) || !isset(users()[$_SESSION['user']])) {
    $error = null;
    $login = '';
    if ($post) {
        $login = post_str($_POST, 'login', 64);
        $wait = login_wait($login);
        if ($wait > 0) {
            http_response_code(429);
            $error = 'Слишком много попыток. Попробуйте через ' . max(1, (int) ceil($wait / 60)) . ' мин.';
        } elseif (login($login, (string) ($_POST['password'] ?? ''))) {
            audit('вход');
            redirect('./');
        } else {
            login_failed($login);
            $error = 'Неверный логин или пароль';
        }
    }
    if (!users()) {
        $error = 'Админ ещё не создан. Создайте его по SSH: php admin/bin/create-admin.php логин (см. admin/README.md).';
    }
    render_login($login, $error);
    exit;
}

if ($page === 'logout' && $post) {
    audit('выход');
    logout();
    redirect('./');
}

// ---------- разделы ----------
$sections = ['calculator' => 'Калькулятор', 'contacts' => 'Контакты', 'texts' => 'Тексты и вопросы', 'seo' => 'SEO', 'history' => 'История'];
if (!isset($sections[$page])) {
    $page = 'calculator';
}

$fresh = [];
try {
    $fresh = sync_templates();
    $d = defaults();
} catch (Throwable $e) {
    render_fatal($e->getMessage());
    exit;
}
$s = settings();
$errors = [];
$values = null;   // введённое, если форма не прошла проверку: [раздел => значение]

if ($post) {
    try {
        $action = is_string($_POST['action'] ?? null) ? $_POST['action'] : 'save';
        if ($action === 'apply') {
            $changed = apply_settings();
            audit('применены правки к вёрстке: ' . implode(', ', $changed));
            flash($changed ? 'Правки применены к новой вёрстке' : 'Сайт уже совпадает с правками');
            redirect("?p=$page");
        }
        if ($action === 'reset') {
            $what = $page === 'texts' ? ['texts', 'faq'] : [$page];
            foreach ($what as $k) {
                unset($s[$k]);
            }
            save_settings($s, "вернули как в вёрстке: {$sections[$page]}");
            apply_settings();
            flash('Раздел вернули как в вёрстке');
            redirect("?p=$page");
        }
        if ($page === 'history' && $action === 'restore') {
            $id = is_string($_POST['id'] ?? null) ? $_POST['id'] : '';
            $item = preg_match('/^[\w-]+$/', $id) ? json_read(data_file("history/$id.json"), null) : null;
            if (!$item) {
                throw new UserError('Нет такой версии');
            }
            save_settings($item['settings'] ?? [], "восстановлена версия $id");
            apply_settings();
            flash('Версия восстановлена');
            redirect('?p=history');
        }
        if ($page === 'history' && $action === 'reset_all') {
            save_settings([], 'весь сайт как в вёрстке');
            apply_settings();
            flash('Весь сайт вернули как в вёрстке');
            redirect('?p=history');
        }

        $forms = match ($page) {
            'calculator' => ['calculator' => form_calculator($_POST, $d['calculator'])],
            'contacts' => ['contacts' => form_contacts($_POST, $d['contacts'])],
            'texts' => ['texts' => form_texts($_POST, $d['texts']), 'faq' => form_faq($_POST, $d['faq'])],
            'seo' => ['seo' => form_seo($_POST, $d['seo'])],
            default => [],
        };
        $entered = [];
        foreach ($forms as $k => [$value, $err, $raw]) {
            $errors += $err;
            $s[$k] = $value;
            $entered[$k] = $raw;
        }
        if ($errors) {
            $values = $entered;
            http_response_code(422);
        } else {
            save_settings($s, "сохранён раздел «{$sections[$page]}»");
            $changed = apply_settings();
            flash($changed ? 'Сохранено и опубликовано на сайте' : 'Сохранено, на сайте уже это');
            redirect("?p=$page");
        }
    } catch (UserError $e) {
        $errors['_'] = $e->getMessage();
    } catch (Throwable $e) {
        audit('ошибка: ' . $e->getMessage());
        $errors['_'] = 'Не получилось: ' . $e->getMessage();
    }
}

$pending = $s ? pending_files() : [];
render_page($page, $sections, [
    'd' => $d,
    's' => $s,
    'errors' => $errors,
    'values' => $values,
    'pending' => $pending,
    'fresh' => $fresh,
]);
