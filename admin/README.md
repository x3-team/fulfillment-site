# Админка «Товар в деле» (чистый PHP, без сборки)

`/admin/` — правка сайта без программиста: **Калькулятор** (цены операций, приёмка, хранение, бесплатные дни, скидка),
**Контакты** (телефон, email), **Тексты / FAQ**, **SEO** (title / description / og:title страниц из `data/seo.json`),
**История** (резервные копии и кнопка «Вернуть как в вёрстке»).

Почему так, а не Laravel: сайт статический и должен им остаться. Админка не держит отдельную БД — она читает
значения прямо из `index.html` (`const OPS`, `ACCEPT`, `STORE_RATE/FREE_DAYS/DISC`, `const FAQ`) и `data/seo.json`
и при публикации переписывает эти места в файлах (атомарно, с бэкапом). Посетители по-прежнему получают
статический HTML, PHP работает только в `/admin/`. Нет composer, vendor/, node, миграций — заливается как есть.

Требования: PHP 8.1+ (на Host-0 рег.ру — 8.3 для сайта, 8.2 в SSH), Apache с .htaccess. Расширения — только стандартные.

## Где лежат данные
Вне docroot: `<домашняя папка>/.tovarvdele-admin/` (на Host-0 это `/var/www/u3698839/data/.tovarvdele-admin/`):
`users.json` (логины + password_hash), `audit.log`, `backups/` (последние 30 версий), `original/` (снимок до первой правки),
`throttle.json` (5 неудачных входов → пауза 15 мин). Путь можно сменить в `admin/config.local.php`
(`<?php return ['data_dir' => '/путь'];`, файл в .gitignore) или переменной `TVD_ADMIN_DATA`.

## Создать админа (пароль в git не попадает)
```
ssh u3698839@37.140.192.11
cd www/tovarvdele.ru
php admin/bin/create-admin.php vitalii          # спросит пароль, мин. 12 символов
php admin/bin/create-admin.php vitalii          # повторно — смена пароля
php admin/bin/create-admin.php vitalii --delete # удалить
```

## Деплой на Host-0
1. Залить папку `admin/` в `www/tovarvdele.ru/admin/` (SFTP), включая `.htaccess` и `bin/.htaccess`.
2. Создать админа (см. выше). Открыть https://tovarvdele.ru/admin/.
3. Проверить, что закрыто: `/admin/lib.php` и `/admin/bin/create-admin.php` → 403.

**Важно про выкладку из git.** Правки из админки меняют файлы на сервере (`index.html`, `data/seo.json`,
`kontakty/`, `dokumenty/`, `llms.txt`). Если потом залить сайт из репозитория поверх — правки затрутся.
Перед выкладкой из git скачайте эти файлы с сервера и закоммитьте (или повторите правки в админке после выкладки).
После выкладки новой вёрстки удалите `~/.tovarvdele-admin/original/`, чтобы «как в вёрстке» означало новую версию.

`tools/seo.py` совместим: после правок из админки его можно запускать как обычно.

## Локальная проверка
```
TVD_ADMIN_DATA=/tmp/tvd TVD_PASS='test-password-123' php admin/bin/create-admin.php test
TVD_ADMIN_DATA=/tmp/tvd php -S 127.0.0.1:8099   # из корня сайта → http://127.0.0.1:8099/admin/
```
