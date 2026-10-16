# Бренд — фулфилмент для маркетплейсов

Главная страница сайта: один файл `index.html` (HTML + CSS + JS, 3D-сцена на three.js).
Внешние зависимости грузятся с CDN: three.js r128 (cdnjs) и шрифты Onest / JetBrains Mono (Google Fonts).

## Как выложить на GitHub Pages
1. Создайте репозиторий (например, `fulfillment-site`).
2. Загрузите `index.html` и `.nojekyll` в корень репозитория.
3. Settings → Pages → Build and deployment → Source: «Deploy from a branch», Branch: `main`, папка `/ (root)` → Save.
4. Через 1–2 минуты сайт откроется по адресу `https://<ваш-логин>.github.io/fulfillment-site/`.
