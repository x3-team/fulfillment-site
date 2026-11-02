#!/usr/bin/env python3
"""Генератор SEO-страниц услуг агентства «Madrocks agency».

Запуск из корня репозитория:  python3 tools/agency_pages.py
Пишет agency/uslugi/index.html, agency/uslugi/<slug>/index.html, agency/ceny/index.html (прайс),
через tools/agency_legal.py — agency/kontakty/ и agency/dokumenty/,
agency/uslugi/uslugi.css, agency/sitemap.xml и agency/robots.txt.
Пакеты на странице «Цены» берутся из const PLANS главной агентства.
Стили берутся из <style> главной агентства, поэтому после правок дизайна
главной достаточно перезапустить скрипт.
"""
import ast, html, json, os, re, sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(__file__))
import svc_layout as L  # общая вёрстка страниц услуг и цен (иллюстрации, иконки, CSS)
from agency_services import GROUPS, PRICES, SERVICES

ROOT = os.path.join(os.path.dirname(__file__), '..', 'agency')
# Адрес сайта агентства. Когда агентство переедет на свой домен, поменять здесь и перезапустить.
BASE = 'https://madrocks.agency/'
# Сайт фулфилмента живёт на своём домене, ссылки на него только абсолютные.
FF = 'https://tovarvdele.ru/'
BRAND = 'Madrocks agency'
TG = 'https://t.me/'
BY_SLUG = {s['slug']: s for s in SERVICES}
ARR = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h11M11 5.5l4.5 4.5-4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
e = lambda s: html.escape(s, quote=True)
L.e = e
LOGO = '<svg viewBox="0 0 40 38" aria-hidden="true"><path fill="#0056E0" d="M10 3 25 1 38 12 35 31 18 37 2 26Z"/><path fill="#0047C2" d="M27 12 38 12 35 31 18 37 20 23Z"/><path fill="#63AAFD" d="M10 3 25 1 21 13Z"/><path fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" d="M8 27 13 13 20 23 27 12 31 27"/></svg><span>Madrocks<br>agency</span>'
DOCK_ARR = '<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 8 8 2M3.5 2H8v4.5" stroke="currentColor" stroke-width="1.4"/></svg>'

EXTRA_CSS = L.CSS

FAQ_JS = "const f=$('#faqList');if(f)f.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)f.querySelectorAll('details').forEach(o=>{if(o!==d)o.open=false})}));"
JS = '''<script>
(function(){
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const hdr=$('#hdr');let lastY=0;addEventListener('scroll',()=>{const y=scrollY;hdr.classList.toggle('scrolled',y>80);hdr.classList.toggle('hide',y>160&&y>lastY);lastY=y},{passive:true});
const menu=$('#menu');const openMenu=o=>{menu.classList.toggle('open',o);menu.setAttribute('aria-hidden',!o);$('#menuBtn').setAttribute('aria-expanded',o);document.body.style.overflow=o?'hidden':''};
$('#menuBtn').onclick=()=>openMenu(true);$('#menuClose').onclick=()=>openMenu(false);menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>openMenu(false)));addEventListener('keydown',e=>{if(e.key==='Escape')openMenu(false)});
const f=$('#faqList');if(f)f.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)f.querySelectorAll('details').forEach(o=>{if(o!==d)o.open=false})}));
const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;e.target.classList.add('in');io.unobserve(e.target)}),{threshold:.15});$$('.rv').forEach(el=>io.observe(el));
const ct=$('#contact');if(ct)new IntersectionObserver(es=>es.forEach(e=>document.documentElement.classList.toggle('in-form',e.isIntersecting))).observe(ct);
const tick=()=>{const d=new Date(Date.now()+3*36e5);$('#ftClock').textContent=String(d.getUTCHours()).padStart(2,'0')+':'+String(d.getUTCMinutes()).padStart(2,'0')};tick();setInterval(tick,30000);
})();
</script>
<script>/* UTM и источник перехода: запоминаем на входе на сайт, уходят в заявку (api/lead.php) */(()=>{try{const q=new URLSearchParams(location.search),u={};['utm_source','utm_medium','utm_campaign','utm_content','utm_term','yclid','gclid'].forEach(k=>{const v=q.get(k);if(v)u[k]=v.slice(0,300)});const s=sessionStorage;if(Object.keys(u).length||!s.getItem('lead-utm')){const r=document.referrer;if(r&&new URL(r).host!==location.host)u.referrer=r.slice(0,300);u.landing=location.href.split('#')[0].slice(0,300);s.setItem('lead-utm',JSON.stringify(u))}}catch(_){}})();</script>'''


def url(slug=None):
    return BASE + ('uslugi/' + slug + '/' if slug else 'uslugi/')


def cta_href(r, slug=None):
    # Целевое действие — модалка заявки на главной агентства: #lead=<тема>|<чипы услуг>.
    if slug:
        topic, chip = BY_SLUG[slug]['name'], BY_SLUG[slug]['chip']
    else:
        topic, chip = 'Бесплатный аудит', 'Аудит'
    return r + '#lead=' + quote(topic + '|' + chip, safe='')


def head(title, desc, canon, ld, r):
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:locale" content="ru_RU"><meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canon}">
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700;900&family=JetBrains+Mono:wght@500&display=swap">
<link rel="stylesheet" href="{r}uslugi/uslugi.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}</script>
</head>
<body>
'''


def header(r):
    # Шапка как на главной агентства (и у «Товар в деле»): логотип, меню по центру, справа ссылка на заявку.
    return f'''<header class="hdr" id="hdr"><div class="wrap wide">
 <a class="logo" href="{r}" aria-label="{BRAND} — на главную">{LOGO}</a>
 <nav class="nav" aria-label="Основное"><a href="{r}">Главная</a><a href="{r}uslugi/">Услуги</a><a href="{r}#cases">Кейсы</a><a href="{r}ceny/">Цены</a><a href="{FF}" target="_blank" rel="noopener">Фулфилмент ↗</a></nav>
 <a class="tel" href="{r}#lead">Обсудить проект</a>
 <div class="acts"><button class="btn ghost m" id="menuBtn" aria-controls="menu" aria-expanded="false"><span>Меню</span></button></div>
</div></header>
'''


def svc_links(r, cls=''):
    return ''.join(f'<a href="{r}uslugi/{s["slug"]}/">{e(s["short"])}</a>' for s in SERVICES)


def footer(r, slug=None):
    col = lambda g: ''.join(f'<a href="{r}uslugi/{s["slug"]}/">{e(s["short"])}</a>' for s in SERVICES if s['group'] == g)
    return f'''<div class="tape"></div>
<footer><div class="wrap">
 <div class="top"><span class="tag light"><i>Берём новые проекты</i></span><span class="mono">Москва · <span id="ftClock">14:32</span> МСК · 2026</span></div>
 <div class="wm">Madrocks®</div>
 <div class="cols"><div><p style="max-width:320px;color:#A9B6D0;font-size:14px">Digital-агентство для селлеров: маркетплейсы, свой интернет-магазин и маркетинг в связке с фулфилментом.</p></div>
  <div><span class="mono">Маркетплейсы</span>{col(GROUPS[0])}</div>
  <div><span class="mono">Свой канал</span>{col(GROUPS[1])}{col(GROUPS[2])}</div>
  <div><span class="mono">Компания</span><a href="{r}uslugi/">Все услуги</a><a href="{r}#cases">Кейсы</a><a href="{r}ceny/">Цены</a><a href="{r}#process">Как мы работаем</a><a href="{r}kontakty/">Контакты</a><a href="{r}kontakty/#rekvizity">Реквизиты</a><a href="{FF}" target="_blank" rel="noopener">Фулфилмент ↗</a></div></div>
 <div class="legal"><span>© 2026 {BRAND} · ИП Зозуля М. А. · ИНН 710709737470 · Работаем по ЭДО</span><span class="docs"><a href="{r}dokumenty/politika/">Политика обработки персональных данных</a><a href="{r}dokumenty/soglasie/">Согласие на обработку данных</a><a href="{r}dokumenty/cookies/">Cookies</a><a href="{r}dokumenty/soglashenie/">Пользовательское соглашение</a></span></div>
</div></footer>

<div class="dock"><div class="wrap wide"><p>Растим продажи — от карточки до своего магазина.</p><a href="{cta_href(r, slug)}">Заказать бесплатный аудит<i>{DOCK_ARR}</i></a></div></div>
<div class="menu" id="menu" aria-hidden="true"><div class="wrap">
 <div class="bar"><a class="logo" href="{r}" aria-label="{BRAND} — на главную">{LOGO}</a><button class="btn ghost m" id="menuClose"><span>Закрыть</span></button></div>
 <div class="cols">
  <nav class="prim" aria-label="Меню"><a href="{r}uslugi/"><span class="mono" style="color:var(--acc)">01</span>Услуги</a><a href="{r}#cases"><span class="mono muted">02</span>Кейсы</a><a href="{r}ceny/"><span class="mono muted">03</span>Цены</a><a href="{r}#process"><span class="mono muted">04</span>Как мы работаем</a><a href="{r}kontakty/"><span class="mono muted">05</span>Контакты</a></nav>
  <div class="sub"><span class="mono">Услуги</span>{svc_links(r)}</div>
  <div class="sub"><span class="mono">Фулфилмент · Товар в деле ↗</span><a href="{FF}" target="_blank" rel="noopener">FBS</a><a href="{FF}" target="_blank" rel="noopener">FBO</a><a href="{FF}" target="_blank" rel="noopener">Хранение</a><a href="{FF}#calc" target="_blank" rel="noopener">Калькулятор стоимости</a></div>
 </div>
</div></div>
'''


def crumbs(r, items):
    li = []
    for i, (name, href) in enumerate(items):
        if href:
            li.append(f'<li><a href="{href}">{e(name)}</a></li>')
        else:
            li.append(f'<li><span aria-current="page">{e(name)}</span></li>')
    return f'<nav class="crumbs mono" aria-label="Хлебные крошки"><ol>{"".join(li)}</ol></nav>'


def ld_crumbs(items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def final(r, h2, lead, slug=None):
    return f'''<section class="final" id="contact"><div class="wrap">
 <span class="tag acc"><b>→</b><i>Бесплатный аудит</i></span>
 <h2>{e(h2)}</h2>
 <p class="lead">{e(lead)}</p>
 <div class="ctas"><a class="btn primary" href="{cta_href(r, slug)}"><span>Заказать бесплатный аудит</span><em>{ARR}</em></a><a class="btn line" href="{TG}" target="_blank" rel="noopener"><span>Написать в Telegram</span></a></div>
</div></section>
'''


# Графика страниц услуг агентства: большое слово первого экрана, сцена (tools/iso_scenes.py), факты,
# иконки «Что входит» / «Кому подходит», картинки этапов. Ключи — slug из agency_services.py.
BIG = {'podklyuchenie-kabinetov': 'Кабинеты', 'kontent-i-infografika': 'Контент', 'prodvizhenie-na-marketplejsah': 'Продвижение',
       'seo-kartochek': 'SEO', 'razrabotka-internet-magazina': 'Магазин', 'internet-marketing': 'Маркетинг',
       'integracii-i-chestnyj-znak': 'Интеграции', 'skvoznaya-analitika': 'Аналитика'}
ART = {'podklyuchenie-kabinetov': 'ag_cabinets', 'kontent-i-infografika': 'ag_content', 'prodvizhenie-na-marketplejsah': 'ag_promo',
       'seo-kartochek': 'ag_seo', 'razrabotka-internet-magazina': 'ag_shop', 'internet-marketing': 'ag_marketing',
       'integracii-i-chestnyj-znak': 'ag_integr', 'skvoznaya-analitika': 'ag_analytics'}
FACTS = {'podklyuchenie-kabinetov': [('2 недели', 'от брифа до первых продаж', 'calendar'), ('3 площадки', 'WB, Ozon, Яндекс Маркет', 'layers'), ('ЭДО', 'договоры и документы за вас', 'doc')],
         'kontent-i-infografika': [('от 5 дней', 'на партию карточек', 'clock'), ('CTR ↑', 'главная цель инфографики', 'trend'), ('фото · видео · rich', 'весь контент карточки', 'photo')],
         'prodvizhenie-na-marketplejsah': [('1–2 недели', 'до первых данных', 'clock'), ('ДРР', 'отчёт по доле рекламных расходов еженедельно', 'percent'), ('без % от оборота', 'фиксированная цена', 'wallet')],
         'seo-kartochek': [('5 дней', 'до загрузки новых текстов', 'clock'), ('позиции', 'мониторинг каждую неделю', 'trend'), ('юнит-экономика', 'считаем прибыль по каждому SKU', 'rub')],
         'razrabotka-internet-magazina': [('от 3 недель', 'до запуска', 'calendar'), ('каталог', 'из вашего учёта', 'grid'), ('фулфилмент', 'связка со складом «Товар в деле»', 'warehouse')],
         'internet-marketing': [('1–2 недели', 'до первых заявок', 'clock'), ('Директ · таргет · SEO', 'каналы под задачу', 'megaphone'), ('повторные продажи', 'email и ретаргетинг', 'repeat')],
         'integracii-i-chestnyj-znak': [('от 1 недели', 'аудит, настройка, тест', 'clock'), ('1С · МойСклад · CRM', 'учёт в одном месте', 'link'), ('«Честный знак»', 'коды и отчётность', 'label')],
         'skvoznaya-analitika': [('2 недели', 'до первого дашборда', 'calendar'), ('маржа по SKU', 'а не по магазину в целом', 'rub'), ('все площадки', 'в одном отчёте', 'layers')]}
INC_ICONS = {'podklyuchenie-kabinetov': ['users', 'layers', 'doc', 'boxes', 'warehouse', 'key'], 'kontent-i-infografika': ['search', 'list', 'photo', 'palette', 'monitor', 'edit'],
             'prodvizhenie-na-marketplejsah': ['search', 'target', 'megaphone', 'percent', 'star', 'chart'], 'seo-kartochek': ['search', 'edit', 'list', 'trend', 'users', 'rub'],
             'razrabotka-internet-magazina': ['palette', 'grid', 'wallet', 'users', 'link', 'bolt'], 'internet-marketing': ['target', 'globe', 'megaphone', 'users', 'send', 'chart'],
             'integracii-i-chestnyj-znak': ['search', 'link', 'users', 'api', 'label', 'warehouse'], 'skvoznaya-analitika': ['api', 'rub', 'boxes', 'megaphone', 'chart', 'send']}
WHO_ICONS = {'podklyuchenie-kabinetov': ['flag', 'globe', 'settings'], 'kontent-i-infografika': ['eye', 'chat', 'bolt'], 'prodvizhenie-na-marketplejsah': ['wallet', 'clock', 'trend'],
             'seo-kartochek': ['search', 'chart', 'wallet'], 'razrabotka-internet-magazina': ['layers', 'users', 'trend'], 'internet-marketing': ['globe', 'rub', 'repeat'],
             'integracii-i-chestnyj-znak': ['boxes', 'label', 'list'], 'skvoznaya-analitika': ['layers', 'wallet', 'target']}
STEP_ART = {'kontent-i-infografika': ['flow_req', 'flow_doc', 'flow_card', 'flow_work'], 'razrabotka-internet-magazina': ['flow_doc', 'flow_card', 'flow_work', 'flow_shop'],
            'integracii-i-chestnyj-znak': ['flow_req', 'flow_link', 'flow_work', 'flow_chart'], 'podklyuchenie-kabinetov': ['flow_req', 'flow_doc', 'flow_work', 'flow_shop']}
STEP_DEFAULT = ['flow_req', 'flow_doc', 'flow_work', 'flow_chart']


def chips(s):
    return [(t, pos, i == 2) for i, (t, pos) in enumerate(zip(s['tags'][:3], ('tl', 'tr', 'br')))]


def svc_card(r, s, wide=False, tag='h2'):
    n = SERVICES.index(s) + 1
    return L.card(f'{r}uslugi/{s["slug"]}/', ART[s['slug']], f'<b>{n:02d}</b> · {e(s["group"])}', s['name'], s['lead'], e(s['price']), wide=wide, tag=tag)


def service_page(s):
    r = '../../'
    n = SERVICES.index(s) + 1
    k = s['slug']
    canon = url(k)
    price_num = re.sub(r'\D', '', s['price'].split('₽')[0])
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Service', 'name': s['name'], 'serviceType': s['name'], 'description': s['description'], 'url': canon,
         'areaServed': {'@type': 'Country', 'name': 'Россия'},
         'provider': {'@type': 'Organization', 'name': BRAND, 'url': BASE},
         'offers': {'@type': 'Offer', 'priceCurrency': 'RUB', 'price': price_num,
                    'priceSpecification': {'@type': 'PriceSpecification', 'minPrice': price_num, 'priceCurrency': 'RUB'}}},
        ld_crumbs([(BRAND, BASE), ('Услуги', url()), (s['name'], canon)]),
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in s['faq']]},
    ]}
    rel = ''.join(svc_card(r, BY_SLUG[x], tag='h3') for x in s['related'])
    rows = ''.join(f'<tr><td>{e(a)}</td><td class="p">{e(b)}</td><td class="u">{e(c)}</td></tr>' for a, b, c in PRICES[k])
    facts = [(e(s['price']), s['price_note'], 'rub')] + FACTS[k]
    kick = f'<span class="tag"><b>{n:02d}</b><i>{e(s["group"])}</i></span><span class="mono">{e(s["term"])}</span>'
    ctas = f'<a class="btn primary" href="{cta_href(r, k)}"><span>Заказать бесплатный аудит</span><em>{ARR}</em></a><a class="btn ghost" href="#tarify"><span>Цены</span></a>'
    body = L.hero(crumbs(r, [('Главная', r), ('Услуги', r + 'uslugi/'), (s['short'], None)]), kick, s['h1'], BIG[k], s['lead'], ctas, ART[k], chips(s), facts) + f'''
<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Что входит</i></span><h2>Что входит в услугу</h2></div><p class="lead muted">Можно заказать услугу целиком или отдельные пункты. Состав работ фиксируем в договоре.</p></div>
 <div class="inc">{L.includes(s['includes'], INC_ICONS[k])}</div>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Кому подходит</i></span><h2>С чем к нам приходят</h2></div><p class="lead muted">Узнали себя? Начните с бесплатного аудита: покажем, что исправить в первую очередь.</p></div>
 <div class="who w3">{L.who(s['who'], WHO_ICONS[k])}</div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>03</b><i>Как работаем</i></span><h2>Этапы и сроки</h2></div><p class="lead muted">Каждый шаг виден в общем чате и трекере. Отчёт — по выручке и заказам, а не по количеству задач.</p></div>
 <ol class="flow f4 rv">{L.flow(s['steps'], STEP_ART.get(k, STEP_DEFAULT))}</ol>
</div></section>

<section class="paper" id="tarify"><div class="wrap">
 <div class="pg rv"><div class="h"><span class="tag"><b>04</b><i>Цены</i></span><h2>Сколько стоит</h2><p style="color:var(--ink5)">{e(s['price_note'])}. Цена фиксируется в договоре до старта работ.</p><a href="{r}ceny/#{k}">Все цены и пакеты →</a></div>
 <table><tbody>{rows}</tbody></table></div>
</div></section>

<section class="white"><div class="wrap prose">
 <div class="l rv"><span class="tag"><b>05</b><i>Подробнее</i></span><h2>{e(s['name'])}: как это устроено</h2></div>
 <div class="t rv">{''.join(f'<p>{e(p)}</p>' for p in s['text'])}</div>
</div></section>

<section class="paper" id="faq"><div class="wrap faq">
 <div class="l rv"><span class="tag"><b>06</b><i>Вопросы</i></span><h2>Частые вопросы</h2><p class="muted">Не нашли свой вопрос? Задайте его на аудите — ответим на ваших цифрах.</p><a class="btn ghost" href="{TG}" target="_blank" rel="noopener"><span>Задать вопрос в Telegram</span></a>{L.faq_art()}</div>
 <div id="faqList">{L.faq(s['faq'])}</div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>07</b><i>Ещё услуги</i></span><h2>Часто заказывают вместе</h2></div><p class="lead muted">Контент, реклама и учёт в связке дают больше, чем по отдельности. <a href="{r}uslugi/" style="color:var(--acc)">Все услуги →</a></p></div>
 <div class="cards">{rel}</div>
</div></section>

{final(r, 'Покажем, где теряются продажи', 'Пришлите ссылку на магазин или артикулы. За 2 рабочих дня сделаем аудит и пришлём план с бюджетом и сроками.', k)}</main>
'''
    return (head(s['title'], s['description'], canon, ld, r) + header(r).replace('<a href="../../uslugi/">Услуги</a>', '<a href="../../uslugi/" aria-current="page">Услуги</a>')
            + '\n<main>\n' + body + footer(r, k) + f'<script src="{r}accordion.js"></script>\n' + JS.replace(FAQ_JS, 'initAccordions();') + '\n</body>\n</html>\n')


def index_page():
    r = '../'
    canon = url()
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_crumbs([(BRAND, BASE), ('Услуги', canon)]),
        {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': s['name'], 'url': url(s['slug'])} for i, s in enumerate(SERVICES)]},
    ]}
    acc = L.accordion([(s['group'], s['name'], s['lead'], e(s['price']), '', f'{r}uslugi/{s["slug"]}/', ART[s['slug']], s['tags'])
                       for g in GROUPS for s in SERVICES if s['group'] == g], GROUPS)
    facts = [('8 направлений', 'от первой карточки до своего магазина', 'layers'), ('2 дня', 'бесплатный аудит карточек и рекламы', 'clock'),
             ('без %', 'от оборота: фиксированная цена', 'wallet'), ('отчёт', 'по выручке и ДРР каждую неделю', 'chart')]
    kick = '<span class="tag"><b>→</b><i>Все услуги</i></span><span class="mono">Wildberries · Ozon · Яндекс Маркет · свой сайт</span>'
    ctas = f'<a class="btn primary" href="{cta_href(r)}"><span>Заказать бесплатный аудит</span><em>{ARR}</em></a><a class="btn ghost" href="{r}ceny/"><span>Цены</span></a>'
    way = L.path([('flow_work', 'Кабинеты', 'Регистрация, схема, ЭДО.', f'{r}uslugi/podklyuchenie-kabinetov/'),
                  ('flow_card', 'Контент', 'Фото, инфографика, rich-контент.', f'{r}uslugi/kontent-i-infografika/'),
                  ('flow_req', 'SEO', 'Семантика, тексты, позиции.', f'{r}uslugi/seo-kartochek/'),
                  ('flow_chart', 'Продвижение', 'Реклама, акции, отзывы.', f'{r}uslugi/prodvizhenie-na-marketplejsah/'),
                  ('flow_shop', 'Свой магазин', 'Сайт, маркетинг, повторные продажи.', f'{r}uslugi/razrabotka-internet-magazina/'),
                  ('flow_link', 'Учёт и аналитика', 'Интеграции, маржа по SKU.', f'{r}uslugi/skvoznaya-analitika/')])
    title = 'Услуги для селлеров: маркетплейсы, интернет-магазин, маркетинг — Madrocks agency'
    desc = 'Все услуги digital-агентства «Madrocks agency» для селлеров: подключение кабинетов WB и Ozon, инфографика, продвижение, SEO карточек, интернет-магазин, маркетинг, интеграции и аналитика.'
    body = L.hero(crumbs(r, [('Главная', r), ('Услуги', None)]), kick, 'Услуги для селлеров маркетплейсов и интернет-магазинов', 'Услуги',
                  'Восемь направлений, которые закрывают весь путь селлера: от первой карточки до собственного магазина. Любую услугу можно заказать отдельно.',
                  ctas, 'ag_hero_services', [('Карточки · реклама · аналитика', 'tl', False), ('Свой интернет-магазин', 'tr', False), ('Связка с фулфилментом', 'br', True)], facts) + f'''
<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Услуги</i></span><h2>Выберите, с чего начать</h2></div><p class="lead muted">Любую услугу можно заказать отдельно или в пакете. Цены «от», без процента от оборота.</p></div>
 {acc}
 <p class="links"><a href="{FF}uslugi/" target="_blank" rel="noopener">Склад, FBS, FBO и доставка — у фулфилмента «Товар в деле» ↗</a></p>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Путь селлера</i></span><h2>От первой карточки до своего магазина</h2></div><p class="lead muted">Услуги работают в связке: контент, реклама и учёт дают больше, чем каждая по отдельности.</p></div>
 {way}
</div></section>
{final(r, 'Не знаете, с чего начать?', 'Начните с бесплатного аудита: за 2 рабочих дня разберём карточки и рекламу и покажем, какие услуги дадут результат быстрее всего.')}</main>
'''
    return (head(title, desc, canon, ld, r) + header(r).replace('<a href="../uslugi/">Услуги</a>', '<a href="../uslugi/" aria-current="page">Услуги</a>')
            + '\n<main>\n' + body + footer(r) + f'<script src="{r}accordion.js"></script>\n' + JS.replace(FAQ_JS, 'initAccordions();') + '\n</body>\n</html>\n')


def plans(src):
    """Пакеты с главной агентства (const PLANS), чтобы цены пакетов были в одном месте."""
    m = re.search(r'const PLANS=(\[.*?\]);\n', src, re.S)
    return ast.literal_eval(m.group(1)) if m else []


def prices_page(src):
    r = '../'
    canon = BASE + 'ceny/'
    pk = plans(src)
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_crumbs([(BRAND, BASE), ('Цены', canon)]),
        {'@type': 'OfferCatalog', 'name': 'Цены Madrocks agency', 'url': canon, 'itemListElement': [
            {'@type': 'Offer', 'url': url(s['slug']), 'priceCurrency': 'RUB',
             'itemOffered': {'@type': 'Service', 'name': a, 'provider': {'@type': 'Organization', 'name': BRAND, 'url': BASE}},
             'priceSpecification': {'@type': 'UnitPriceSpecification', 'minPrice': re.sub(r'\D', '', b), 'priceCurrency': 'RUB', 'unitText': c}}
            for s in SERVICES for a, b, c in PRICES[s['slug']]]},
    ]}
    cards = ''.join(f'''<article class="plan rv {p[6]}"><div class="r"><span class="mono">{e(p[0])}</span><span class="mono">{'Чаще выбирают' if p[6] else ''}</span></div><h3>{e(p[1])}</h3><div class="price">от {e(p[2])}<small>{e(p[3])}</small></div><p>{e(p[4])}</p><ul>{''.join('<li>' + e(f) + '</li>' for f in p[5])}</ul><a class="btn {'primary' if p[6] else 'dark'}" href="{r}#lead={quote('Пакет «' + p[0] + '»|' + p[7], safe='')}"><span>Обсудить пакет</span><em>{ARR}</em></a></article>''' for p in pk)
    groups = ''
    for g in GROUPS:
        for s in (x for x in SERVICES if x['group'] == g):
            rows = ''.join(f'<tr><td>{e(a)}</td><td class="p">{e(b)}</td><td class="u">{e(c)}</td></tr>' for a, b, c in PRICES[s['slug']])
            groups += (f'<div class="pg rv" id="{s["slug"]}"><div class="h"><div class="th isogrid">{L.ART[ART[s["slug"]]]()}</div><span class="mono">{e(g)}</span><h2>{e(s["short"])}</h2>'
                       f'<a href="{r}uslugi/{s["slug"]}/">Подробнее об услуге →</a></div><table><tbody>{rows}</tbody></table></div>')
    facts = [(e(BY_SLUG[k]['price']), lbl, ic) for k, lbl, ic in (
        ('podklyuchenie-kabinetov', 'Подключение кабинетов · разово', 'key'), ('kontent-i-infografika', 'Инфографика · за слайд', 'photo'),
        ('prodvizhenie-na-marketplejsah', 'Продвижение · в месяц', 'megaphone'), ('razrabotka-internet-magazina', 'Интернет-магазин · разово', 'cart'))]
    kick = '<span class="tag"><b>₽</b><i>Прайс</i></span><span class="mono">цены «от» · без НДС</span>'
    ctas = f'<a class="btn primary" href="{cta_href(r)}"><span>Заказать бесплатный аудит</span><em>{ARR}</em></a><a class="btn ghost" href="#pakety"><span>Пакеты</span></a>'
    title = 'Цены на продвижение на маркетплейсах, контент и интернет-магазин — Madrocks agency'
    desc = 'Прайс digital-агентства Madrocks agency: подключение кабинетов от 30 000 ₽, инфографика от 1 500 ₽ за слайд, продвижение от 40 000 ₽ в месяц, интернет-магазин от 350 000 ₽. Пакеты и цены «от».'
    body = L.hero(crumbs(r, [('Главная', r), ('Цены', None)]), kick, 'Цены на услуги агентства для селлеров', 'Цены',
                  'Пакеты с понятной ценой и прайс по услугам. Точную стоимость считаем после бесплатного аудита и фиксируем в договоре.', ctas, 'ag_hero_prices',
                  [('Без процента от оборота', 'tl', False), ('Рекламный бюджет — напрямую площадке', 'tr', False), ('Цена фиксируется до старта', 'br', True)], facts) + f'''
<section class="white" id="pakety"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Пакеты</i></span><h2>Пакеты с понятной ценой</h2></div><p class="lead muted">Пакет закрывает типовую задачу целиком. Любую услугу из прайса ниже можно взять отдельно.</p></div>
 <div class="plans">{cards}</div>
</div></section>

<section class="paper" id="prajs"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Прайс</i></span><h2>Цены по услугам</h2></div><p class="lead muted">Без процента от оборота и без скрытых доплат. Рекламный бюджет маркетплейса оплачиваете напрямую.</p></div>
 <div class="pt">{groups}</div>
 <div class="pnote"><p>Цены без НДС, указаны минимальные. Это справочный прайс, не публичная оферта.</p></div>
 <p class="links"><a href="{FF}ceny/" target="_blank" rel="noopener">Цены на фулфилмент — у «Товар в деле» ↗</a></p>
</div></section>
{final(r, 'Посчитаем бюджет под вашу задачу', 'Пришлите ссылку на магазин или артикулы. За 2 рабочих дня сделаем аудит и пришлём план с бюджетом и сроками.')}</main>
'''
    return (head(title, desc, canon, ld, r) + header(r).replace('<a href="../ceny/">Цены</a>', '<a href="../ceny/" aria-current="page">Цены</a>')
            + '\n<main>\n' + body + footer(r) + JS + '\n</body>\n</html>\n')


def main():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    out = os.path.join(ROOT, 'uslugi')
    os.makedirs(out, exist_ok=True)
    w = lambda p, t: open(p, 'w', encoding='utf-8').write(t)
    w(os.path.join(out, 'uslugi.css'), '/* Сгенерировано tools/agency_pages.py из agency/index.html — не править руками */' + css + EXTRA_CSS)
    w(os.path.join(out, 'index.html'), index_page())
    for s in SERVICES:
        os.makedirs(os.path.join(out, s['slug']), exist_ok=True)
        w(os.path.join(out, s['slug'], 'index.html'), service_page(s))
    os.makedirs(os.path.join(ROOT, 'ceny'), exist_ok=True)
    w(os.path.join(ROOT, 'ceny', 'index.html'), prices_page(src))
    import agency_legal  # документы и контакты: та же шапка и подвал
    agency_legal.main()
    urls = ([BASE, url(), BASE + 'ceny/'] + [url(s['slug']) for s in SERVICES]
            + [BASE + 'kontakty/', BASE + 'dokumenty/'] + [BASE + f'dokumenty/{d}/' for d in ('politika', 'soglasie', 'cookies', 'soglashenie')])
    w(os.path.join(ROOT, 'sitemap.xml'), '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
      + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    w(os.path.join(ROOT, 'robots.txt'), f'User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {BASE}sitemap.xml\n')
    print(f'{len(SERVICES)} страниц услуг + список, ceny/, sitemap: {len(urls)} адресов')
    print('Плейсхолдеры цен агентства (все цены страницы agency/ceny/ и пакетов):')
    for s in SERVICES:
        for a, b, c in PRICES[s['slug']]:
            print(f'  - {s["short"]} · {a}: {b} {c}')
    for p in plans(src):
        print(f'  - Пакет «{p[0]}»: от {p[2]} {p[3]}')
    import cachebust  # метки ?v= у CSS/JS, см. tools/cachebust.py
    cachebust.main()


if __name__ == '__main__':
    main()
