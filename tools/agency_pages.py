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
LOGO = '<svg viewBox="0 0 40 38" aria-hidden="true"><path fill="#0056E0" d="M10 3 25 1 38 12 35 31 18 37 2 26Z"/><path fill="#0047C2" d="M27 12 38 12 35 31 18 37 20 23Z"/><path fill="#63AAFD" d="M10 3 25 1 21 13Z"/><path fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round" d="M8 27 13 13 20 23 27 12 31 27"/></svg><span>Madrocks<br>agency</span>'
DOCK_ARR = '<svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2 8 8 2M3.5 2H8v4.5" stroke="currentColor" stroke-width="1.4"/></svg>'

EXTRA_CSS = '''
/* ---- страницы услуг ---- */
.crumbs{margin-bottom:28px;color:var(--ink5)}.crumbs ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px 10px}
.crumbs li{display:flex;gap:10px;align-items:center}.crumbs li+li::before{content:"/";color:var(--ink3)}
.crumbs a:hover{color:var(--acc)}.crumbs [aria-current]{color:var(--ink)}
.sh{padding:32px 0 clamp(64px,8vw,104px)}
.sh h1{max-width:22ch;font-size:clamp(36px,4.6vw,64px)}
.sh .row{display:grid;gap:32px;margin-top:32px;align-items:start}
@media (min-width:1000px){.sh .row{grid-template-columns:1fr 400px;gap:64px}}
.sh .lead{max-width:60ch}
.pcard{display:grid;gap:16px;padding:28px 28px 30px;background:var(--card);border:1px solid var(--line);border-radius:4px;box-shadow:0 12px 32px rgba(10,23,54,.07)}
.pcard .r{display:flex;justify-content:space-between;gap:12px;color:var(--ink5)}.pcard .r .mono:last-child{color:var(--acc)}
.pcard .price{font-size:clamp(32px,3.2vw,40px);line-height:1;font-weight:500;letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.pcard .note{color:var(--ink5);font-size:15px}
.pcard ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}.pcard li{padding:6px 10px;border-radius:2px;background:var(--acc1);color:var(--acc6)}
.pcard .btn{width:100%}.pcard .btn>span{flex:1;justify-content:center}
.inc{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}@media (min-width:1000px){.inc{grid-template-columns:repeat(3,1fr)}}
.inc article{display:grid;gap:12px;align-content:start;padding:26px 28px 30px;background:var(--paper);border-radius:4px;border:1px solid transparent;transition:border-color var(--base)}
.inc article:hover{border-color:var(--acc)}.inc .mono{color:var(--acc)}.inc h3{font-size:22px}.inc p{color:var(--ink5)}
.white .who article{background:var(--paper)}.paper .who article{background:var(--card)}
.who h3{font-size:24px}
.flow.f4{grid-template-columns:none}@media (min-width:900px){.flow.f4{grid-template-columns:repeat(4,1fr)}}
.prose{display:grid;gap:24px}@media (min-width:1000px){.prose{grid-template-columns:400px 1fr;gap:80px}}
.prose .l{display:grid;gap:20px;justify-items:start;align-content:start}
.prose .t{display:grid;gap:18px;max-width:68ch;font-size:18px;line-height:1.65;color:var(--ink7)}
.rel{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.rel a{display:grid;gap:12px;align-content:space-between;min-height:180px;padding:24px 26px;background:var(--card);border:1px solid var(--line);border-radius:4px;transition:border-color var(--base),transform var(--base) var(--std)}
.rel a:hover{border-color:var(--acc);transform:translateY(-4px)}.rel .mono{color:var(--ink5)}.rel h3{font-size:22px}
.rel .r{display:flex;justify-content:space-between;align-items:center;font-weight:600}.rel .r em{width:36px;height:36px;display:grid;place-items:center;background:var(--acc);color:#fff;border-radius:2px;font-style:normal}
.final .ctas{margin-top:40px}
.list{border-top:1px solid var(--line)}.list .grp{padding:28px 0 12px;color:var(--ink5)}
.list a{display:grid;grid-template-columns:72px 1fr auto;gap:24px;align-items:center;padding:24px 0;border-top:1px solid var(--line)}
.list a .num{color:var(--ink5)}.list a h2{font-size:clamp(24px,3.2vw,44px);transition:color var(--fast),transform var(--base) var(--std)}
.list a p{color:var(--ink5);margin-top:8px;max-width:70ch}.list a b{white-space:nowrap;font-weight:600;font-size:18px}
.list a:hover h2{color:var(--acc6);transform:translateX(8px)}
@media (max-width:699px){.list a{grid-template-columns:40px 1fr;gap:12px}.list a b{grid-column:2}}
/* ---- страница «Цены» ---- */
.links{display:flex;flex-wrap:wrap;gap:12px 24px;margin-top:32px}.links a{color:var(--acc);font-weight:500}.links a:hover{color:var(--acc6)}
.pt{display:grid;gap:16px}
.pg{display:grid;gap:8px 48px;padding:28px 28px 20px;background:var(--card);border:1px solid var(--line);border-radius:4px}
@media (min-width:1000px){.pg{grid-template-columns:300px 1fr}}
.pg .h{display:grid;gap:12px;align-content:start;justify-items:start}.pg .h h2{font-size:clamp(26px,2.6vw,34px)}
.pg .h a{color:var(--acc);font-weight:500;font-size:15px}.pg .h a:hover{color:var(--acc6)}
.pg table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
.pg td{padding:14px 0;border-top:1px solid var(--line);vertical-align:baseline}.pg tr:first-child td{border-top:0}
.pg td:first-child{padding-right:24px}.pg td.p{text-align:right;white-space:nowrap;font-weight:600;font-size:18px;color:var(--acc6)}
.pg td.u{text-align:right;white-space:nowrap;color:var(--ink5);font-size:14px;padding-left:12px;width:150px}
@media (max-width:599px){.pg{padding:22px 20px 14px}.pg tr{display:grid;grid-template-columns:1fr auto;gap:2px 12px;padding:12px 0;border-top:1px solid var(--line)}.pg tr:first-child{border-top:0}
 .pg td{padding:0;border:0}.pg td:first-child{grid-column:1/-1;padding:0}.pg td.p{text-align:left}.pg td.u{width:auto}}
.pnote{display:grid;gap:12px;margin-top:32px;max-width:80ch;color:var(--ink5)}
'''

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
</script>'''


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
 <div class="made"><a href="https://solentica.agency/" target="_blank" rel="noopener">Сайт сделан в студии <b>Solentica</b><i aria-hidden="true">↗</i></a></div>
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


def service_page(s):
    r = '../../'
    n = SERVICES.index(s) + 1
    canon = url(s['slug'])
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
    inc = ''.join(f'<article class="rv"><span class="mono">{i + 1:02d}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>' for i, (t, d) in enumerate(s['includes']))
    who = ''.join(f'<article class="rv"><span class="chip mono">Ситуация {i + 1}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>' for i, (t, d) in enumerate(s['who']))
    flow = ''.join(f'<li><span class="n">{i + 1}</span><span class="mono d">{e(a)}</span><h3>{e(b)}</h3><p>{e(c)}</p></li>' for i, (a, b, c) in enumerate(s['steps']))
    text = ''.join(f'<p>{e(p)}</p>' for p in s['text'])
    faq = ''.join(f'<details{"" if i else " open"}><summary><span class="num mono">0{i + 1}</span><span>{e(q)}</span><span class="pl"></span></summary><div class="a">{e(a)}</div></details>' for i, (q, a) in enumerate(s['faq']))
    rel = ''.join(f'<a class="rv" href="{r}uslugi/{x["slug"]}/"><span class="mono">{e(x["group"])}</span><h3>{e(x["name"])}</h3><div class="r"><span>{e(x["price"])}</span><em>{ARR}</em></div></a>' for x in (BY_SLUG[k] for k in s['related']))
    tags = ''.join(f'<li class="mono">{e(t)}</li>' for t in s['tags'])
    return head(s['title'], s['description'], canon, ld, r) + header(r) + f'''
<main>
<section class="paper sh"><div class="wrap">
 {crumbs(r, [(BRAND, r), ('Услуги', r + 'uslugi/'), (s['short'], None)])}
 <p class="eyebrow mono" style="color:var(--ink5);margin-bottom:20px">[ <b style="color:var(--acc);font-weight:500">Услуга {n:02d}</b> · {e(s['group'])} ]</p>
 <h1>{e(s['h1'])}</h1>
 <div class="row">
  <div><p class="lead">{e(s['lead'])}</p>
   <div class="ctas"><a class="btn primary" href="{cta_href(r, s['slug'])}"><span>Заказать бесплатный аудит</span><em>{ARR}</em></a><a class="btn ghost" href="{r}ceny/#{s['slug']}"><span>Цены и пакеты</span></a></div></div>
  <aside class="pcard" aria-label="Стоимость"><div class="r"><span class="mono">Стоимость</span><span class="mono">Срок · {e(s['term'])}</span></div><div class="price">{e(s['price'])}</div><p class="note">{e(s['price_note'])}. Цена фиксируется в договоре до старта работ.</p><ul>{tags}</ul><a href="{r}ceny/#{s['slug']}" style="color:var(--acc);font-size:15px">Все цены на странице «Цены» →</a></aside>
 </div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Что входит</i></span><h2>Что входит в услугу</h2></div><p class="lead muted">Можно заказать услугу целиком или отдельные пункты. Состав работ фиксируем в договоре.</p></div>
 <div class="inc">{inc}</div>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Кому подходит</i></span><h2>С чем к нам приходят</h2></div><p class="lead muted">Если узнали себя хотя бы в одной ситуации, начните с бесплатного аудита: покажем, что исправить в первую очередь.</p></div>
 <div class="who">{who}</div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>03</b><i>Как работаем</i></span><h2>Этапы и сроки</h2></div><p class="lead muted">Каждый шаг виден в общем чате и трекере. Отчёт — по выручке и заказам, а не по количеству сделанных задач.</p></div>
 <ol class="flow f4 rv">{flow}</ol>
</div></section>

<section class="paper"><div class="wrap prose">
 <div class="l rv"><span class="tag"><b>04</b><i>Подробнее</i></span><h2>{e(s['name'])}: как это устроено</h2></div>
 <div class="t rv">{text}</div>
</div></section>

<section class="white" id="faq"><div class="wrap faq">
 <div class="l rv"><span class="tag"><b>05</b><i>Вопросы</i></span><h2>Частые вопросы</h2><p class="muted">Не нашли свой вопрос? Задайте его на аудите — ответим на ваших цифрах.</p><a class="btn ghost" href="{TG}" target="_blank" rel="noopener"><span>Задать вопрос в Telegram</span></a></div>
 <div id="faqList">{faq}</div>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>06</b><i>Ещё услуги</i></span><h2>Часто заказывают вместе</h2></div><p class="lead muted">Услуги работают в связке: контент, реклама и учёт дают больше, чем каждая по отдельности. <a href="{r}uslugi/" style="color:var(--acc)">Все услуги →</a></p></div>
 <div class="rel">{rel}</div>
</div></section>

{final(r, 'Покажем, где теряются продажи', 'Пришлите ссылку на магазин или артикулы. За 2 рабочих дня сделаем аудит и пришлём план с бюджетом и сроками.', s['slug'])}</main>
''' + footer(r, s['slug']) + f'<script src="{r}accordion.js"></script>\n' + JS.replace(FAQ_JS, 'initAccordions();') + '\n</body>\n</html>\n'


def index_page():
    r = '../'
    canon = url()
    ld = {'@context': 'https://schema.org', '@graph': [
        ld_crumbs([(BRAND, BASE), ('Услуги', canon)]),
        {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': s['name'], 'url': url(s['slug'])} for i, s in enumerate(SERVICES)]},
    ]}
    rows, n = '', 0
    for g in GROUPS:
        rows += f'<p class="grp mono">{e(g)}</p>'
        for s in SERVICES:
            if s['group'] != g:
                continue
            n += 1
            rows += f'<a href="{s["slug"]}/"><span class="num mono">({n:02d})</span><div><h2>{e(s["name"])}</h2><p>{e(s["lead"])}</p></div><b>{e(s["price"])}</b></a>'
    title = 'Услуги для селлеров: маркетплейсы, интернет-магазин, маркетинг — Madrocks agency'
    desc = 'Все услуги digital-агентства «Madrocks agency» для селлеров: подключение кабинетов WB и Ozon, инфографика, продвижение, SEO карточек, интернет-магазин, маркетинг, интеграции и аналитика.'
    return head(title, desc, canon, ld, r) + header(r) + f'''
<main>
<section class="paper sh"><div class="wrap">
 {crumbs(r, [(BRAND, r), ('Услуги', None)])}
 <h1>Услуги для селлеров маркетплейсов</h1>
 <div class="row"><p class="lead">Восемь направлений, которые закрывают весь путь селлера: от первой карточки до собственного магазина. Любую услугу можно заказать отдельно или в пакете.</p></div>
 <div class="list" style="margin-top:48px">{rows}</div>
</div></section>
{final(r, 'Не знаете, с чего начать?', 'Начните с бесплатного аудита: за 2 рабочих дня разберём карточки и рекламу и покажем, какие услуги дадут результат быстрее всего.')}</main>
''' + footer(r) + JS + '\n</body>\n</html>\n'


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
            groups += (f'<div class="pg rv" id="{s["slug"]}"><div class="h"><span class="mono">{e(g)}</span><h2>{e(s["short"])}</h2>'
                       f'<a href="{r}uslugi/{s["slug"]}/">Подробнее об услуге →</a></div><table><tbody>{rows}</tbody></table></div>')
    title = 'Цены на продвижение на маркетплейсах, контент и интернет-магазин — Madrocks agency'
    desc = 'Прайс digital-агентства Madrocks agency: подключение кабинетов от 30 000 ₽, инфографика от 1 500 ₽ за слайд, продвижение от 40 000 ₽ в месяц, интернет-магазин от 350 000 ₽. Пакеты и цены «от».'
    return head(title, desc, canon, ld, r) + header(r).replace('<a href="../ceny/">Цены</a>', '<a href="../ceny/" aria-current="page">Цены</a>') + f'''
<main>
<section class="paper sh"><div class="wrap">
 {crumbs(r, [(BRAND, r), ('Цены', None)])}
 <h1>Цены на услуги агентства</h1>
 <div class="row"><p class="lead">Обобщённый прайс по группам услуг: цены «от» и единицы. Точную стоимость считаем после бесплатного аудита и фиксируем в договоре до старта работ.</p></div>
 <div class="ctas"><a class="btn primary" href="{cta_href(r)}"><span>Заказать бесплатный аудит</span><em>{ARR}</em></a><a class="btn ghost" href="{r}uslugi/"><span>Все услуги</span></a></div>
</div></section>

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
''' + footer(r) + JS + '\n</body>\n</html>\n'


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
    w(os.path.join(ROOT, 'robots.txt'), f'User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n')
    print(f'{len(SERVICES)} страниц услуг + список, ceny/, sitemap: {len(urls)} адресов')
    print('Плейсхолдеры цен агентства (все цены страницы agency/ceny/ и пакетов):')
    for s in SERVICES:
        for a, b, c in PRICES[s['slug']]:
            print(f'  - {s["short"]} · {a}: {b} {c}')
    for p in plans(src):
        print(f'  - Пакет «{p[0]}»: от {p[2]} {p[3]}')


if __name__ == '__main__':
    main()
