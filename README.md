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

## SEO
Все SEO-настройки — в `data/seo.json`: заголовки и описания страниц, адрес и координаты склада, телефон,
часы работы, ссылки на соцсети и карточки (`same_as`), коды Яндекс.Вебмастера и Google Search Console,
номер счётчика Яндекс.Метрики. После правок запустить `python3 tools/seo.py`: он обновит блок
`<!-- seo --> … <!-- /seo -->` в `<head>` страниц (title, description, canonical, Open Graph, иконки,
гео-метки, разметка schema.org: LocalBusiness, FAQ, хлебные крошки), продублирует «Частые вопросы» на главной
статичным HTML и пересоберёт `robots.txt`, `sitemap.xml`, `llms.txt`. Генераторы контактов и документов
запускают его сами. Новую страницу добавить в `pages` в `data/seo.json`.

Картинки (превью ссылки `img/og.png`, логотип `img/logo-512.png`, `favicon.ico`, `apple-touch-icon.png`)
пересобирает `node tools/seo_images.js`.

Сайт открыт на домене https://tovarvdele.ru/ (хостинг reg.ru), он же прописан в `site.base_url`
в `data/seo.json` и в `BASE` в `tools/contacts_page.py` и `tools/legal_pages.py`. При смене домена поменять
все три и перезапустить генераторы.
