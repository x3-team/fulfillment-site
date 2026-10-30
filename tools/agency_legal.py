#!/usr/bin/env python3
"""Документы и «Контакты» сайта агентства «Madrocks agency».

Запуск из корня репозитория:  python3 tools/agency_legal.py
Пишет agency/dokumenty/ (список + politika, soglasie, cookies, soglashenie), agency/kontakty/
и agency/dokumenty/legal.css. Оператор и реквизиты те же, что у фулфилмента «Товар в деле»
(ИП Зозуля М. А.): берутся из tools/legal_pages.py и tools/contacts_page.py, тексты документов —
общий шаблон docs() из legal_pages.py с формулировками агентства ниже.
Шапка, подвал и стили — из генератора страниц услуг агентства (tools/agency_pages.py).
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agency_pages as ap  # noqa: E402
import contacts_page as cp  # noqa: E402
import legal_pages as lp  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), '..', 'agency')
BASE, BRAND = ap.BASE, ap.BRAND
e = lambda s: html.escape(s, quote=True)

AGENCY = dict(lp.FF)
AGENCY.update({
 'base': BASE, 'brand': BRAND,
 'form': 'форму заявки «Обсудить проект» / «Заказать бесплатный аудит»',
 'data': 'имя; номер телефона; адрес электронной почты; ссылка на магазин или артикулы (если указаны); выбранные услуги и тема заявки; дата и время отправки заявки',
 'purpose': 'рассмотреть заявку, связаться с пользователем, провести бесплатный аудит, подготовить предложение и проект договора на услуги интернет-маркетинга, продвижения и разработки',
 'consent_purpose': 'Рассмотрение моей заявки на услуги агентства «Madrocks agency» (продвижение на маркетплейсах, контент, разработка интернет-магазина, маркетинг, интеграции), связь со мной по телефону, электронной почте и в мессенджерах, проведение аудита и направление предложения и проекта договора.',
 'tech': 'обеспечить работу Сайта и встроенных сервисов (шрифты, анимация), их безопасность и корректное отображение',
 'tech_basis': 'согласие пользователя, выраженное продолжением использования Сайта, и действия по запросу пользователя на показ страниц Сайта',
 'processors': ['сервис отправки электронных писем из формы заявки (EmailJS, emailjs.com);',
                'почтовый сервис, на котором размещён ящик Оператора для заявок;',
                'Google Fonts — загрузка шрифтов страниц.'],
 'cookies_own': 'Сайт {SITE} не устанавливает рекламных и аналитических cookies и не подключает счётчики посещаемости.',
 'cookies_svc': ['<b>Google Fonts</b> — загрузка шрифтов страниц. Сервис получает IP-адрес и сведения о браузере. Условия: <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">политика конфиденциальности Google</a>.',
                 '<b>EmailJS</b> — отправка заявки из формы на Сайте, только в момент отправки заявки.'],
 'cookies_why': 'Для корректного отображения страниц и работы формы заявки, защиты от злоупотреблений и технических сбоев.',
 'cookies_off': 'Вы можете запретить сохранение cookies или удалить их в настройках браузера, а также пользоваться режимом «Инкогнито». Сайт при этом продолжит работать.',
 'cookies_agree': 'Продолжая пользоваться Сайтом, вы соглашаетесь',
 'about': 'для информирования об услугах Владельца в области интернет-маркетинга, продвижения на маркетплейсах и разработки под брендом «Madrocks agency» и приёма заявок',
 'info': 'включая описание услуг, пакеты и цены',
 'info_h': 'Информация и цены на сайте',
 'estimate': '2.2. Цены на Сайте указаны как минимальные («от») и носят ориентировочный характер. Точная стоимость, состав и сроки работ определяются после аудита в предложении и договоре.',
 'agree_desc': 'Текст согласия, которое пользователь даёт, отмечая галочку в форме заявки на сайте агентства.',
 'terms_desc': 'Условия использования сайта: статус информации и цен, права на материалы, ответственность.',
})

KONTAKTY_CSS = cp.EXTRA_CSS.replace('.hdr .nav a[aria-current]{color:var(--ink)}\n', '')

COPY_JS = '''<script>
(function(){const $=s=>document.querySelector(s);
const copy=(btn,text)=>{const done=()=>{const l=btn.querySelector('span'),t=l.textContent;btn.classList.add('ok');l.textContent='Скопировано';setTimeout(()=>{btn.classList.remove('ok');l.textContent=t},1600)};
 if(navigator.clipboard)navigator.clipboard.writeText(text).then(done,()=>{});else{const a=document.createElement('textarea');a.value=text;document.body.append(a);a.select();document.execCommand('copy');a.remove();done()}};
document.querySelectorAll('.cp').forEach(b=>b.onclick=()=>copy(b,b.dataset.v));
$('#copyAll').onclick=()=>copy($('#copyAll'),[...document.querySelectorAll('.req .row')].map(r=>r.querySelector('dt').textContent+': '+r.querySelector('dd').textContent).join('\\n'));
})();
</script>'''


def page(r, title, desc, path, crumb, body, ld_extra=None, js=''):
    canon = BASE + path
    ld = {'@context': 'https://schema.org', '@graph': [ap.ld_crumbs([(BRAND, BASE)] + crumb)] + (ld_extra or [])}
    head = ap.head(title, desc, canon, ld, r).replace(f'{r}uslugi/uslugi.css', f'{r}dokumenty/legal.css')
    return head + ap.header(r) + f'\n<main>\n{body}\n</main>\n' + ap.footer(r) + ap.JS + js + '\n</body>\n</html>\n'


def kontakty():
    r = '../'
    rows = ''.join(f'<div class="row"><dt>{e(k)}</dt><dd>{e(v)}</dd><button class="cp" type="button" data-v="{e(v)}" aria-label="Скопировать: {e(k)}">{cp.COPY}<span>Копировать</span></button></div>' for k, v in cp.REQ)
    A = ap.ARR
    cards = (f'<a class="kc" href="{ap.cta_href(r)}"><div class="r"><span class="mono">Заявка</span><em>{A}</em></div><b>Заказать бесплатный аудит</b><p>Оставьте контакты и ссылку на магазин — свяжемся в течение рабочего дня.</p></a>'
             f'<a class="kc" href="{ap.TG}" target="_blank" rel="noopener"><div class="r"><span class="mono">Telegram</span><em>{A}</em></div><b>Написать менеджеру</b><p>Ответим на вопросы по услугам и срокам.</p></a>'
             f'<a class="kc" href="{ap.FF}" target="_blank" rel="noopener"><div class="r"><span class="mono">Фулфилмент</span><em>{A}</em></div><b>Товар в деле ↗</b><p>Склад, FBS и FBO в связке с маркетингом.</p></a>')
    body = f'''<section class="paper kh"><div class="wrap">
 {ap.crumbs(r, [(BRAND, r), ('Контакты', None)])}
 <div class="l"><span class="tag acc"><b>01</b><i>Контакты</i></span><h1>Контакты</h1><p class="lead">Digital-агентство {e(BRAND)}. Оставьте заявку на бесплатный аудит или напишите в Telegram — пришлём план с бюджетом и сроками.</p></div>
 <div class="kcards" style="grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">{cards}</div>
</div></section>

<section class="white" id="rekvizity"><div class="wrap req">
 <div class="l"><span class="tag"><b>02</b><i>Реквизиты</i></span><h2>Реквизиты</h2><p class="lead muted">Работаем по договору с ИП, документы — по ЭДО.</p><button class="btn ghost m cp" id="copyAll" type="button" data-v=""><span>Скопировать все реквизиты</span></button></div>
 <dl>{rows}</dl>
</div></section>'''
    org = {'@type': 'Organization', 'name': BRAND, 'url': BASE, 'legalName': cp.REQ[0][1], 'taxID': lp.INN}
    return page(r, f'Контакты и реквизиты — {BRAND}', f'Контакты digital-агентства {BRAND}: заявка на бесплатный аудит, Telegram и реквизиты ({lp.OP_SHORT}, ИНН {lp.INN}).',
                'kontakty/', [('Контакты', BASE + 'kontakty/')], body, [org], COPY_JS)


def main():
    os.makedirs(os.path.join(ROOT, 'dokumenty'), exist_ok=True)
    css = open(os.path.join(ROOT, 'uslugi', 'uslugi.css'), encoding='utf-8').read().split('\n', 1)[1]
    with open(os.path.join(ROOT, 'dokumenty', 'legal.css'), 'w', encoding='utf-8') as f:
        f.write('/* Сгенерировано tools/agency_legal.py из agency/uslugi/uslugi.css — не править руками */\n' + css + lp.EXTRA_CSS + KONTAKTY_CSS)
    docs = lp.docs(AGENCY)
    cards = ''
    for slug, title, lead, secs in docs:
        os.makedirs(os.path.join(ROOT, 'dokumenty', slug), exist_ok=True)
        with open(os.path.join(ROOT, 'dokumenty', slug, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(page('../../', f'{title} — {BRAND}', lead, f'dokumenty/{slug}/',
                         [('Документы', BASE + 'dokumenty/'), (title, BASE + f'dokumenty/{slug}/')], lp.doc_body(title, lead, secs)))
        cards += f'<a class="kc" href="{slug}/"><div class="r"><span class="mono">Редакция от {lp.LEGAL_ED}</span><em>{ap.ARR}</em></div><b>{e(title)}</b><p>{e(lead)}</p></a>'
    body = (f'<section class="paper lh"><div class="wrap"><div class="l"><span class="tag acc"><b>01</b><i>Документы</i></span><h1>Документы</h1>'
            f'<p class="lead">Правила работы сайта «{BRAND}» и обработки персональных данных. Оператор — {e(lp.OP_SHORT)}, ИНН {lp.INN}.</p></div></div></section>\n'
            f'<section class="paper"><div class="wrap dl">{cards}</div></section>')
    with open(os.path.join(ROOT, 'dokumenty', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page('../', f'Документы — {BRAND}', f'Политика обработки персональных данных, согласие, политика cookies и пользовательское соглашение сайта «{BRAND}».',
                     'dokumenty/', [('Документы', BASE + 'dokumenty/')], body))
    os.makedirs(os.path.join(ROOT, 'kontakty'), exist_ok=True)
    with open(os.path.join(ROOT, 'kontakty', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(kontakty())
    print('agency/dokumenty/: index +', ', '.join(d[0] for d in docs), '; agency/kontakty/')


if __name__ == '__main__':
    main()
