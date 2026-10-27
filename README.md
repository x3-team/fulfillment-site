# Бренд — фулфилмент для маркетплейсов

Главная страница сайта: один файл `index.html` (HTML + CSS + JS, 3D-сцена на three.js).
Внешние зависимости грузятся с CDN: three.js r128 (cdnjs) и шрифты Onest / JetBrains Mono (Google Fonts).

## Как выложить на GitHub Pages
1. Создайте репозиторий (например, `fulfillment-site`).
2. Загрузите `index.html` и `.nojekyll` в корень репозитория.
3. Settings → Pages → Build and deployment → Source: «Deploy from a branch», Branch: `main`, папка `/ (root)` → Save.
4. Через 1–2 минуты сайт откроется по адресу `https://<ваш-логин>.github.io/fulfillment-site/`.

## Сайт агентства «Бренд Digital»
Лежит в папке `agency/` и открывается по адресу `https://x3-team.github.io/fulfillment-site/agency/`.
Ссылки между сайтами относительные (`agency/` и `../`). Если агентство переедет на свой домен, их нужно заменить на полные адреса.

## Страница «Контакты»
`kontakty/` генерируется скриптом `python3 tools/contacts_page.py` из шапки, подвала и стилей главной.
Адрес склада (для Яндекс.Карты), координаты и телефон — константы `WAREHOUSE`, `COORDS`, `PHONE` в начале скрипта.
После правок главной или констант перезапустить скрипт и закоммитить `kontakty/`.
