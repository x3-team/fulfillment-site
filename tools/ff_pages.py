#!/usr/bin/env python3
"""Страницы «Услуги» и «Цены» фулфилмента «Товар в деле».

Запуск из корня репозитория:  python3 tools/ff_pages.py
Пишет uslugi/index.html (все услуги), uslugi/<slug>/index.html (страница услуги),
ceny/index.html (прайс) и uslugi/uslugi.css. Тексты и цены — в tools/ff_services.py.
Шапка, меню, подвал, синяя плашка и стили берутся из главной (index.html), поэтому
после правок главной достаточно перезапустить скрипт. Заодно обновляет цены и ссылки
«Подробнее» в блоке «Что мы делаем» на главной, добавляет страницы в data/seo.json
и запускает tools/seo.py (title, description, разметка, sitemap.xml, Метрика).

Целевое действие на всех страницах одно — калькулятор на главной (../#calc).
Ссылка вида #calc=fbs,mark сразу отмечает нужные операции, #calc=store включает хранение.
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo  # noqa: E402
from ff_services import GROUPS, PRICES, SERVICES  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
BASE = 'https://tovarvdele.ru/'
TG = 'https://t.me/tovarvdele_bot'
AGENCY = 'https://madrocks.agency/'
BY_SLUG = {s['slug']: s for s in SERVICES}
# Заголовок услуги в блоке «Что мы делаем» на главной → страница услуги.
HOME = {'FBS': 'fbs', 'FBO': 'fbo', 'Хранение': 'hranenie', 'Маркировка и упаковка': 'markirovka-i-upakovka',
        'Возвраты и переупаковка': 'vozvraty', 'Забор товара и доставка до СЦ': 'zabor-i-dostavka'}

e = lambda s: html.escape(s, quote=True)
ARR = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h11M11 5.5l4.5 4.5-4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

EXTRA_CSS = '''
/* ---- страницы услуг и цен ---- */
.hdr .nav a[aria-current]{color:var(--ink)}
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
.pcard .price small{font-size:16px;letter-spacing:0;color:var(--ink5);margin-left:8px}
.pcard .note{color:var(--ink5);font-size:15px}
.pcard ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px}.pcard li{padding:6px 10px;border-radius:2px;background:var(--acc1);color:var(--acc6)}
.pcard .btn{width:100%}.pcard .btn>span{flex:1;justify-content:center}
.pcard a.all{color:var(--acc);font-size:15px}
.inc{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}@media (min-width:1000px){.inc{grid-template-columns:repeat(3,1fr)}}
.inc article{display:grid;gap:12px;align-content:start;padding:26px 28px 30px;background:var(--paper);border-radius:4px;border:1px solid transparent;transition:border-color var(--base)}
.inc article:hover{border-color:var(--acc)}.inc .mono{color:var(--acc)}.inc h3{font-size:22px}.inc p{color:var(--ink5)}
.who.w3{display:grid;gap:16px}@media (min-width:900px){.who.w3{grid-template-columns:repeat(3,1fr)}}
.paper .who article{background:var(--card)}.who.w3 article{padding:28px 28px 32px}.who.w3 article>*{margin:0}
.flow.f4{grid-template-columns:none}@media (min-width:900px){.flow.f4{grid-template-columns:repeat(4,1fr)}}
.prose{display:grid;gap:24px}@media (min-width:1000px){.prose{grid-template-columns:400px 1fr;gap:80px}}
.prose .l{display:grid;gap:20px;justify-items:start;align-content:start}
.prose .t{display:grid;gap:18px;max-width:68ch;font-size:18px;line-height:1.65;color:var(--ink7)}
.rel{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.rel a{display:grid;gap:12px;align-content:space-between;min-height:180px;padding:24px 26px;background:var(--card);border:1px solid var(--line);border-radius:4px;transition:border-color var(--base),transform var(--base) var(--std)}
.rel a:hover{border-color:var(--acc);transform:translateY(-4px)}.rel .mono{color:var(--ink5)}.rel h3{font-size:22px}
.rel .r{display:flex;justify-content:space-between;align-items:center;font-weight:600}.rel .r em{width:36px;height:36px;display:grid;place-items:center;background:var(--acc);color:#fff;border-radius:2px;font-style:normal}
.final .ctas{margin-top:40px}
.list{border-top:1px solid var(--line)}.list .grp{padding:28px 0 12px;color:var(--ink5)}
.list a{display:grid;grid-template-columns:72px 1fr auto;gap:24px;align-items:center;padding:24px 0;border-top:1px solid var(--line)}
.list a .num{color:var(--ink5)}.list a h2{font-size:clamp(24px,3.2vw,44px);transition:color var(--fast),transform var(--base) var(--std)}
.list a p{color:var(--ink5);margin-top:8px;max-width:70ch}.list a b{white-space:nowrap;font-weight:600;font-size:18px;color:var(--acc6)}
.list a b small{display:block;font-weight:400;font-size:14px;color:var(--ink5);text-align:right}
.list a:hover h2{color:var(--acc6);transform:translateX(8px)}
@media (max-width:699px){.list a{grid-template-columns:40px 1fr;gap:12px}.list a b{grid-column:2}.list a b small{text-align:left}}
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

JS = '''<script>
(function(){
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const hdr=$('#hdr');let lastY=0;addEventListener('scroll',()=>{const y=scrollY;hdr.classList.toggle('scrolled',y>80);hdr.classList.toggle('hide',y>160&&y>lastY);lastY=y},{passive:true});
const menu=$('#menu');const openMenu=o=>{menu.classList.toggle('open',o);menu.setAttribute('aria-hidden',!o);$('#menuBtn').setAttribute('aria-expanded',o);document.body.style.overflow=o?'hidden':''};
$('#menuBtn').onclick=()=>openMenu(true);$('#menuClose').onclick=()=>openMenu(false);menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>openMenu(false)));addEventListener('keydown',e=>{if(e.key==='Escape')openMenu(false)});
const f=$('#faqList');if(f){const ds=f.querySelectorAll('details');ds.forEach(d=>{d.classList.toggle('on',d.open);d.addEventListener('toggle',()=>{d.classList.toggle('on',d.open);if(d.open)ds.forEach(o=>{if(o!==d)o.open=false})})})}
if('IntersectionObserver' in window){const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;e.target.classList.add('in');io.unobserve(e.target)}),{threshold:.15});$$('.rv').forEach(el=>io.observe(el))}else $$('.rv').forEach(el=>el.classList.add('in'));
const tick=()=>{const d=new Date(Date.now()+3*36e5);$('#ftClock').textContent=String(d.getUTCHours()).padStart(2,'0')+':'+String(d.getUTCMinutes()).padStart(2,'0')};tick();setInterval(tick,30000);
})();
</script>'''


def block(src, start, end):
    i = src.index(start)
    return src[i:src.index(end, i) + len(end)]


def relink(s, up):
    """Относительные ссылки главной → ссылки со страницы на глубине up."""
    p = '../' * up

    def fix(m):
        attr, url = m.group(1), m.group(2)
        if re.match(r'(https?:|tel:|mailto:|data:|/|\$\{)', url):
            return m.group(0)
        if url == '#':
            url = ''
        return f'{attr}="{p}{url}"' if p or url else f'{attr}="./"'
    return re.sub(r'(href|src)="([^"]*)"', fix, s)


def current(s, href):
    return s.replace(f'<a href="{href}">', f'<a href="{href}" aria-current="page">', 1)


def calc_href(r, s=None):
    preset = s.get('calc') if s else ''
    return f'{r}#calc' + (f'={preset}' if preset else '')


def crumbs(r, items):
    li = ''.join(f'<li><a href="{h}">{e(n)}</a></li>' if h else f'<li><span aria-current="page">{e(n)}</span></li>' for n, h in items)
    return f'<nav class="crumbs mono" aria-label="Хлебные крошки"><ol>{li}</ol></nav>'


def final(r, h2, lead, s=None):
    return f'''<section class="final" id="contact"><div class="wrap">
 <span class="tag acc"><b>→</b><i>Расчёт</i></span>
 <h2>{e(h2)}</h2>
 <p class="lead">{e(lead)}</p>
 <div class="ctas"><a class="btn primary" href="{calc_href(r, s)}"><span>Рассчитать стоимость</span><em>{ARR}</em></a><a class="btn line" href="{TG}" target="_blank" rel="noopener"><span>Написать в Telegram</span></a></div>
</div></section>
'''


def shell(src, up, nav_href, body):
    p = '../' * up
    head = src[:src.index('<style>')].rstrip()
    header = current(relink(block(src, '<header class="hdr"', '</header>'), up), nav_href)
    tail = relink(src[src.index('<div class="tape">'):src.index('<dialog')], up).rstrip()
    return f'''{head}
<link rel="stylesheet" href="{p}uslugi/uslugi.css">
</head>
<body>
{header}

<main>
{body}</main>
{tail}
{JS}
</body>
</html>
'''


def price_rows(slug):
    g = next((g for g in PRICES if g['slug'] == slug), None)
    return g['rows'] if g else []


def service_page(src, s):
    r = '../../'
    n = SERVICES.index(s) + 1
    inc = ''.join(f'<article class="rv"><span class="mono">{i + 1:02d}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>' for i, (t, d) in enumerate(s['includes']))
    who = ''.join(f'<article class="rv"><span class="chip mono">Ситуация {i + 1}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>' for i, (t, d) in enumerate(s['who']))
    flow = ''.join(f'<li><span class="n">{i + 1}</span><span class="mono d">{e(a)}</span><h3>{e(b)}</h3><p>{e(c)}</p></li>' for i, (a, b, c) in enumerate(s['steps']))
    text = ''.join(f'<p>{e(p)}</p>' for p in s['text'])
    faq = ''.join(f'<details{"" if i else " open"}><summary><span class="num mono">0{i + 1}</span><span>{e(q)}</span><span class="pl"></span></summary><div class="a">{e(a)}</div></details>' for i, (q, a) in enumerate(s['faq']))
    rel = ''.join(f'<a class="rv" href="{r}uslugi/{x["slug"]}/"><span class="mono">{e(x["group"])}</span><h3>{e(x["name"])}</h3><div class="r"><span>{e(x["price"])} {e(x["unit"])}</span><em>{ARR}</em></div></a>' for x in (BY_SLUG[k] for k in s['related']))
    tags = ''.join(f'<li class="mono">{e(t)}</li>' for t in s['tags'])
    rows = ''.join(f'<tr><td>{e(a)}</td><td class="p">{e(b)}</td><td class="u">{e(c)}</td></tr>' for a, b, c, _ in price_rows(s['slug']))
    tariff = f'''
<section class="white" id="tarify"><div class="wrap">
 <div class="pg rv"><div class="h"><span class="tag"><b>04</b><i>Тарифы</i></span><h2>Сколько стоит</h2><a href="{r}ceny/#{s['slug']}">Весь прайс →</a></div>
 <table><tbody>{rows}</tbody></table></div>
</div></section>
''' if rows else ''
    body = f'''<section class="paper sh"><div class="wrap">
 {crumbs(r, [('Главная', r), ('Услуги', r + 'uslugi/'), (s['short'], None)])}
 <p class="mono" style="color:var(--ink5);margin-bottom:20px">[ <b style="color:var(--acc);font-weight:500">Услуга {n:02d}</b> · {e(s['group'])} ]</p>
 <h1>{e(s['h1'])}</h1>
 <div class="row">
  <div><p class="lead">{e(s['lead'])}</p>
   <div class="ctas"><a class="btn primary" href="{calc_href(r, s)}"><span>Рассчитать стоимость</span><em>{ARR}</em></a><a class="btn ghost" href="{r}ceny/#{s['slug']}"><span>Цены</span></a></div></div>
  <aside class="pcard" aria-label="Стоимость"><div class="r"><span class="mono">Стоимость</span><span class="mono">{e(s['term'])}</span></div><div class="price">{e(s['price'])}<small>{e(s['unit'])}</small></div><p class="note">{e(s['price_note'])}. Точную цену фиксируем в приложении к договору.</p><ul>{tags}</ul><a class="all" href="{r}ceny/#{s['slug']}">Все тарифы на странице «Цены» →</a></aside>
 </div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Что входит</i></span><h2>Что входит в услугу</h2></div><p class="lead muted">Состав работ и тарифы фиксируем в договоре. Платите только за операции, которые мы выполнили.</p></div>
 <div class="inc">{inc}</div>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Кому подходит</i></span><h2>Когда это выгодно</h2></div><p class="lead muted">Работаем от первой партии и без минимального ежемесячного платежа.</p></div>
 <div class="who w3">{who}</div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>03</b><i>Как работаем</i></span><h2>Этапы и сроки</h2></div><p class="lead muted">Каждая операция видна в нашей WMS, персональный менеджер на связи в мессенджере.</p></div>
 <ol class="flow f4 rv">{flow}</ol>
</div></section>
{tariff}
<section class="paper"><div class="wrap prose">
 <div class="l rv"><span class="tag"><b>05</b><i>Подробнее</i></span><h2>{e(s['name'])}: как это устроено</h2></div>
 <div class="t rv">{text}</div>
</div></section>

<section class="white" id="faq"><div class="wrap faq">
 <div class="l rv"><span class="tag"><b>06</b><i>Вопросы</i></span><h2>Частые вопросы</h2><p class="muted">Не нашли свой вопрос? Спросите менеджера — ответим лично.</p><a class="btn ghost" href="{TG}" target="_blank" rel="noopener"><span>Задать вопрос в Telegram</span></a></div>
 <div id="faqList">{faq}</div>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>07</b><i>Ещё услуги</i></span><h2>Часто заказывают вместе</h2></div><p class="lead muted"><a href="{r}uslugi/" style="color:var(--acc)">Все услуги →</a></p></div>
 <div class="rel">{rel}</div>
</div></section>

{final(r, 'Посчитайте свою партию', 'Отметьте операции в калькуляторе и нажмите «Получить точный расчёт». Менеджер сверит габариты и объёмы и пришлёт расчёт по каждой строке прайса и проект договора.', s)}'''
    return shell(src, 2, '../../uslugi/', body)


def index_page(src):
    r = '../'
    rows, n = '', 0
    for g in GROUPS:
        rows += f'<p class="grp mono">{e(g)}</p>'
        for s in SERVICES:
            if s['group'] != g:
                continue
            n += 1
            rows += f'<a href="{s["slug"]}/"><span class="num mono">({n:02d})</span><div><h2>{e(s["name"])}</h2><p>{e(s["lead"])}</p></div><b>{e(s["price"])}<small>{e(s["unit"])}</small></b></a>'
    body = f'''<section class="paper sh"><div class="wrap">
 {crumbs(r, [('Главная', r), ('Услуги', None)])}
 <h1>Услуги фулфилмента для маркетплейсов</h1>
 <div class="row"><p class="lead">Всё, что происходит с товаром между поставщиком и покупателем: приёмка, хранение, маркировка, сборка заказов FBS и поставок FBO, возвраты и доставка. Склад в Туле, работаем с Wildberries, Ozon, Яндекс Маркетом и интернет-магазинами.</p></div>
 <div class="ctas"><a class="btn primary" href="{r}#calc"><span>Рассчитать стоимость</span><em>{ARR}</em></a><a class="btn ghost" href="{r}ceny/"><span>Цены на все услуги</span></a></div>
 <div class="list" style="margin-top:48px">{rows}</div>
 <p class="links"><a href="{AGENCY}uslugi/" target="_blank" rel="noopener">Интернет-магазин, маркетинг и контент — в агентстве Madrocks ↗</a></p>
</div></section>
{final(r, 'Не знаете, какая схема выгоднее?', 'Посчитайте партию в калькуляторе и оставьте контакты. Менеджер сравнит FBS и FBO на ваших объёмах и пришлёт точный расчёт.')}'''
    return shell(src, 1, '../uslugi/', body)


def prices_page(src):
    r = '../'
    groups = ''
    for g in PRICES:
        s = BY_SLUG[g['slug']]
        rows = ''.join(f'<tr><td>{e(a)}</td><td class="p">{e(b)}</td><td class="u">{e(c)}</td></tr>' for a, b, c, _ in g['rows'])
        groups += (f'<div class="pg rv" id="{g["slug"]}"><div class="h"><h2>{e(g["name"])}</h2><a href="{r}uslugi/{g["slug"]}/">{e(s["name"])}: подробнее →</a></div>'
                   f'<table><tbody>{rows}</tbody></table></div>')
    body = f'''<section class="paper sh"><div class="wrap">
 {crumbs(r, [('Главная', r), ('Цены', None)])}
 <h1>Цены на фулфилмент</h1>
 <div class="row"><p class="lead">Базовый прайс по группам услуг. Итог складывается из операций, которые нужны вашему товару: посчитайте партию в калькуляторе — он считает по этим же ценам.</p></div>
 <div class="ctas"><a class="btn primary" href="{r}#calc"><span>Рассчитать стоимость партии</span><em>{ARR}</em></a><a class="btn ghost" href="{r}uslugi/"><span>Все услуги</span></a></div>
</div></section>

<section class="white"><div class="wrap">
 <div class="pt">{groups}</div>
 <div class="pnote"><p>Цены указаны за операцию, без НДС. Скидка 10% на первую партию. Минимального объёма и ежемесячного платежа нет.</p><p>Это справочный прайс, не публичная оферта. Точная стоимость зависит от габаритов и объёмов и фиксируется в приложении к договору.</p></div>
 <p class="links"><a href="{AGENCY}ceny/" target="_blank" rel="noopener">Цены на маркетинг, контент и интернет-магазин — у агентства Madrocks ↗</a></p>
</div></section>
{final(r, 'Посчитаем вашу партию за 15 минут', 'Отметьте операции в калькуляторе и нажмите «Получить точный расчёт» — менеджер пришлёт расчёт по каждой строке прайса и проект договора.')}'''
    return shell(src, 1, '../ceny/', body)


def sync_home(src):
    """Цены и ссылки «Подробнее» в блоке «Что мы делаем» на главной — из ff_services.py."""
    def fix(m):
        d = m.group(0)
        name = re.search(r'<h3>(.*?)</h3>', d).group(1)
        s = BY_SLUG.get(HOME.get(name, ''))
        if not s:
            return d
        pr = (f'<div class="pr"><span>{e(s["price"])} {e(s["unit"])}</span><a class="btn ghost m" href="uslugi/{s["slug"]}/">'
              f'<span>Подробнее</span><em>{ARR}</em></a></div>')
        return re.sub(r'<div class="pr">.*?</div>(?=</div><div class="ilbox)', lambda _: pr, d, count=1, flags=re.S)
    i = src.index('<div class="acc" id="acc">')
    j = src.index('</section>', i)
    return src[:i] + re.sub(r'<details.*?</details>', fix, src[i:j], flags=re.S) + src[j:]


def seo_pages():
    """Добавить страницы в data/seo.json (если их там нет) — title и description берутся оттуда."""
    with open(seo.CFG, encoding='utf-8') as f:
        raw = f.read()
    cfg = json.loads(raw)
    have = {p['path'] for p in cfg['pages']}
    new = [{'path': 'uslugi/', 'file': 'uslugi/index.html',
            'title': 'Услуги фулфилмента для Wildberries, Ozon и Яндекс Маркета — Товар в деле',
            'description': 'Все услуги фулфилмента «Товар в деле»: FBS, FBO, хранение, приёмка, маркировка «Честный знак», упаковка, возвраты и доставка до складов маркетплейсов. Склад в Туле.',
            'changefreq': 'monthly', 'priority': 0.9, 'schema': ['breadcrumbs', 'services'], 'breadcrumb': 'Услуги'},
           {'path': 'ceny/', 'file': 'ceny/index.html',
            'title': 'Цены на фулфилмент: прайс на FBS, FBO, хранение и маркировку — Товар в деле',
            'description': 'Прайс фулфилмента «Товар в деле»: приёмка от 5 ₽, FBS от 10 ₽, FBO от 5 ₽ за единицу, хранение 0,07 ₽ за литр в сутки, первые 14 дней бесплатно.',
            'changefreq': 'monthly', 'priority': 0.9, 'schema': ['breadcrumbs', 'prices'], 'breadcrumb': 'Цены'}]
    new += [{'path': f'uslugi/{s["slug"]}/', 'file': f'uslugi/{s["slug"]}/index.html', 'title': s['title'],
             'description': s['description'], 'changefreq': 'monthly', 'priority': 0.8,
             'schema': ['breadcrumbs', 'service', 'service_faq'], 'breadcrumb': s['short'], 'service': s['slug']} for s in SERVICES]
    add = [p for p in new if p['path'] not in have]
    if add:
        cfg['pages'] += add
        with open(seo.CFG, 'w', encoding='utf-8') as f:
            f.write(json.dumps(cfg, ensure_ascii=False, indent=2) + '\n')


def main():
    w = lambda p, t: open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(t)
    src = sync_home(open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())
    w('index.html', src)
    css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    for d in ['uslugi', 'ceny'] + [f'uslugi/{s["slug"]}' for s in SERVICES]:
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    w('uslugi/uslugi.css', '/* Сгенерировано tools/ff_pages.py из index.html — не править руками */' + css + EXTRA_CSS)
    w('uslugi/index.html', index_page(src))
    w('ceny/index.html', prices_page(src))
    for s in SERVICES:
        w(f'uslugi/{s["slug"]}/index.html', service_page(src, s))
    seo_pages()
    print(f'uslugi/: {len(SERVICES)} страниц услуг + список, ceny/')
    ph = [(g['name'], a, b, c) for g in PRICES for a, b, c, p in g['rows'] if p]
    ph += [(s['name'], 'цена на странице услуги', s['price'], s['unit']) for s in SERVICES
           if s.get('price_ph') and not any(b == s['price'] for _, _, b, _ in ph)]
    if ph:
        print('Плейсхолдеры цен (заменить на цены заказчика):')
        for g, a, b, c in ph:
            print(f'  - {g} · {a}: {b} {c}')
    seo.main()


if __name__ == '__main__':
    main()
