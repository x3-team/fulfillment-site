# Товар в деле — сайт фулфилмента и админка

Сайт: https://tovarvdele.ru, админка: https://tovarvdele.ru/admin

Laravel 12 + Inertia + Vue 3 + Tailwind (как в проекте alexallergotest).

## Как устроено
- `public/` — сам сайт: `index.html`, `kontakty/`, `dokumenty/`, `agency/`, картинки, стили. HTML-файлы здесь — шаблоны:
  в них лежат значения «как в вёрстке».
- Страницы отдаёт Laravel (`app/Site/PageRenderer.php`): берёт HTML из `public/` и подставляет то, что поменяли в админке
  (цены калькулятора, контакты, заголовки блоков, частые вопросы, title и description). Готовые страницы кэшируются,
  кэш сбрасывается при каждом сохранении в админке.
- Настройки лежат в таблице `settings` (по записи на раздел). «Вернуть как в вёрстке» удаляет запись.
- Что можно править, описано в `config/site.php`. Тексты на главной размечены комментариями `<!--t:ключ-->…<!--/t-->`.
- Админка: `routes/web.php`, `app/Http/Controllers/Admin/`, страницы `resources/js/Pages/`.

## Локально
```bash
composer install && npm install
cp .env.example .env && php artisan key:generate
touch database/database.sqlite && php artisan migrate
php artisan admin:create you@example.com "Имя"   # печатает пароль
npm run build && php artisan serve
```
Тесты: `php artisan test`.

## Сервер
- PHP 8.2+, MySQL (или SQLite), nginx — пример конфига в `deploy/nginx.conf` (важно: каталоги страниц идут в Laravel).
- Выкладка: `composer install --no-dev -o`, `npm ci && npm run build`, `php artisan migrate --force`,
  `php artisan config:cache route:cache`. Права на запись: `storage/`, `bootstrap/cache/`.
- Первый админ: `php artisan admin:create почта "Имя"`.

## Генераторы страниц (Python, `tools/`)
- `tools/contacts_page.py` — `public/kontakty/` из шапки, подвала и стилей главной.
- `tools/legal_pages.py` — `public/dokumenty/`.
- `tools/agency_pages.py` — `public/agency/uslugi/`.
- `tools/seo.py` — мета-теги, разметка, `robots.txt`, `sitemap.xml`, `llms.txt` по `data/seo.json`.
После правок главной перезапустить нужный генератор и закоммитить результат.
