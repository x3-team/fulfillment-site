# Письмо с заявкой из калькулятора

Сайт статический, поэтому письмо отправляет [EmailJS](https://www.emailjs.com/) прямо из браузера (бесплатно до 200 писем в месяц).

1. Зарегистрироваться в EmailJS, в **Email Services** подключить почту, с которой будут уходить письма (Gmail, Яндекс, Mail.ru или SMTP). Запомнить **Service ID**.
2. В **Email Templates** создать шаблон:
   - **Subject:** `Заявка на расчёт: {{total}} · {{name}}`
   - **To Email:** адрес менеджера, куда приходят заявки
   - **Reply To:** `{{email}}` (ответ на письмо уйдёт клиенту)
   - **Content:** переключить на «Edit Content → Code» и вставить целиком `calc-request.html`.
   Запомнить **Template ID**.
3. В **Account → General** скопировать **Public Key**; в **Account → Security** добавить домен сайта в разрешённые.
4. В `index.html` заполнить `const LEAD={service:'…',template:'…',key:'…'}`.

Пока ключи пустые, форма работает в демо-режиме: показывает «Расчёт у менеджера», а данные заявки пишет только в консоль браузера.

Переменные шаблона: `name`, `phone`, `phone_link`, `email`, `total`, `per_unit`, `discount`, `units`, `ops`, `lines_html` (строки расчёта, вставляется как HTML: `{{{lines_html}}}`), `lines_text`, `sent_at`, `page`.
