#!/usr/bin/env python3
"""Страница «Контакты» фулфилмента «Товар в деле».

Запуск из корня репозитория:  python3 tools/contacts_page.py
Пишет kontakty/index.html и kontakty/kontakty.css.
Шапка, меню, подвал, синяя плашка и стили берутся из главной (index.html),
поэтому после правок главной достаточно перезапустить скрипт.

Когда появятся адрес склада и телефон — заполнить константы ниже и перезапустить.
"""
import html, json, os, re
from urllib.parse import quote

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'kontakty')
BASE = 'https://x3-team.github.io/fulfillment-site/'

# ---- заполнить, когда заказчик пришлёт ----
# Адрес склада, как его искать в Яндекс.Картах, например 'Москва, ул. Складская, 1'.
WAREHOUSE = 'Тула, ул. Пролетарская, д. 127/1'
# Координаты склада 'долгота,широта' (из Яндекс.Карт: клик по точке → координаты, порядок поменять).
# Если пусто, карта ищет по адресу WAREHOUSE.
COORDS = '37.640777,54.206822'
# Телефон в любом виде, например '+7 (495) 123-45-67'. Пока пусто — карточка не показывается.
PHONE = '+7 (916) 728-42-46'
TG = 'https://t.me/'

# Реквизиты: по просьбе заказчика только ИП, ИНН и банковские (без адресов и ОГРНИП).
REQ = [
    ('Наименование', 'Индивидуальный предприниматель Зозуля Мария Алексеевна'),
    ('ИНН', '710709737470'),
    ('Расчётный счёт', '40802810500008078281'),
    ('Банк', 'АО «ТБанк»'),
    ('БИК банка', '044525974'),
    ('Корреспондентский счёт', '30101810145250000974'),
]

e = lambda s: html.escape(s, quote=True)
ARR = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h11M11 5.5l4.5 4.5-4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
COPY = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="5.5" y="5.5" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.4"/><path d="M10.5 3.5v-1h-8v8h1" stroke="currentColor" stroke-width="1.4"/></svg>'
PIN = '<svg width="44" height="56" viewBox="0 0 44 56" fill="none" aria-hidden="true"><path d="M22 54s20-19.6 20-32A20 20 0 0 0 2 22c0 12.4 20 32 20 32Z" fill="#1A5CFF" stroke="#0A1736" stroke-width="1.6"/><circle cx="22" cy="21" r="7" fill="#fff" stroke="#0A1736" stroke-width="1.6"/></svg>'

EXTRA_CSS = '''
/* ---- страница контактов ---- */
.hdr .nav a[aria-current]{color:var(--ink)}
.kh{padding:clamp(40px,6vw,72px) 0 clamp(72px,9vw,120px)}
.kh .l{display:grid;gap:20px;justify-items:start;margin-bottom:clamp(32px,4vw,56px)}
.kh h1{font-size:clamp(48px,8vw,120px);letter-spacing:-.04em;line-height:.95;color:var(--acc)}
.kh .lead{max-width:56ch}
.kgrid{display:grid;gap:16px}@media (min-width:1000px){.kgrid{grid-template-columns:420px 1fr;align-items:stretch}}
.kcards{display:grid;gap:16px;align-content:start}
.kc{display:grid;gap:10px;padding:24px 28px 26px;background:var(--card);border:1px solid var(--line);border-radius:4px;transition:border-color var(--base) var(--std)}
a.kc:hover{border-color:var(--acc)}
.kc .r{display:flex;justify-content:space-between;align-items:center;color:var(--ink5)}
.kc .r em{width:36px;height:36px;display:grid;place-items:center;background:var(--acc);color:#fff;border-radius:2px;font-style:normal}
.kc .r em svg{transition:transform var(--base) var(--std)}a.kc:hover .r em svg{transform:translateX(4px)}
.kc b{font-size:clamp(20px,1.8vw,24px);font-weight:600;letter-spacing:-.01em;line-height:1.25}
.kc p{color:var(--ink5);font-size:15px}
.map{position:relative;min-height:440px;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--card)}
.map iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.map .ph{position:absolute;inset:0;display:grid;place-content:center;justify-items:center;gap:16px;padding:32px;text-align:center}
.map .ph p{max-width:36ch;color:var(--ink7)}
.map .ph .mono{color:var(--ink5)}
.map .road{position:absolute;background:#fff;border:1px solid var(--line)}
@media (max-width:599px){.map{min-height:360px;margin-inline:-20px;border-radius:0;border-inline:0}.kc{padding:22px 20px 24px}}
.req{display:grid;gap:40px}@media (min-width:1000px){.req{grid-template-columns:400px 1fr;gap:80px;align-items:start}.req .l{position:sticky;top:96px}}
.req .l{display:grid;gap:20px;justify-items:start}
.req dl{margin:0;border-top:1px solid var(--line)}
.req .row{display:grid;gap:4px 24px;padding:18px 0;border-bottom:1px solid var(--line);align-items:center}
@media (min-width:700px){.req .row{grid-template-columns:240px 1fr auto}}
.req dt{color:var(--ink5);font-size:15px}
.req dd{margin:0;font-size:17px;font-weight:500;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.cp{display:inline-flex;align-items:center;gap:8px;height:32px;padding:0 10px;border:1px solid var(--line);border-radius:2px;color:var(--ink5);font-size:13px;justify-self:start;transition:color var(--fast),border-color var(--fast)}
.cp:hover{color:var(--acc);border-color:var(--acc)}.cp.ok{color:#14804A;border-color:#5CD48E}
.req .btn{margin-top:8px}
'''

JS = '''<script>
const $=s=>document.querySelector(s);
const hdr=$('#hdr');let lastY=0;addEventListener('scroll',()=>{const y=scrollY;hdr.classList.toggle('scrolled',y>80);hdr.classList.toggle('hide',y>160&&y>lastY);lastY=y},{passive:true});
const menu=$('#menu');const openMenu=o=>{menu.classList.toggle('open',o);menu.setAttribute('aria-hidden',!o);$('#menuBtn').setAttribute('aria-expanded',o);document.body.style.overflow=o?'hidden':''};
$('#menuBtn').onclick=()=>openMenu(true);$('#menuClose').onclick=()=>openMenu(false);menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>openMenu(false)));addEventListener('keydown',e=>{if(e.key==='Escape')openMenu(false)});
const tick=()=>{const d=new Date(Date.now()+3*36e5);$('#ftClock').textContent=String(d.getUTCHours()).padStart(2,'0')+':'+String(d.getUTCMinutes()).padStart(2,'0')};tick();setInterval(tick,30000);
const copy=(btn,text)=>{const done=()=>{const l=btn.querySelector('span'),t=l.textContent;btn.classList.add('ok');l.textContent='Скопировано';setTimeout(()=>{btn.classList.remove('ok');l.textContent=t},1600)};
 if(navigator.clipboard)navigator.clipboard.writeText(text).then(done,()=>{});else{const a=document.createElement('textarea');a.value=text;document.body.append(a);a.select();document.execCommand('copy');a.remove();done()}};
document.querySelectorAll('.cp').forEach(b=>b.onclick=()=>copy(b,b.dataset.v));
$('#copyAll').onclick=()=>copy($('#copyAll'),[...document.querySelectorAll('.req .row')].map(r=>r.querySelector('dt').textContent+': '+r.querySelector('dd').textContent).join('\\n'));
</script>'''


def block(src, start, end):
    i = src.index(start)
    return src[i:src.index(end, i) + len(end)]


def relink(s):
    """Ссылки главной → ссылки со страницы kontakty/."""
    s = re.sub(r'href="#"', 'href="../"', s)
    s = re.sub(r'href="#([^"]*)"', r'href="../#\1"', s)
    s = s.replace('href="agency/', 'href="../agency/').replace('href="kontakty/', 'href="./')
    return s


def map_html():
    if WAREHOUSE or COORDS:
        if COORDS:
            q = f'll={COORDS}&z=16&pt={COORDS},pm2blm'
        else:
            q = 'text=' + quote(WAREHOUSE) + '&z=16'
        return (f'<div class="map"><iframe src="https://yandex.ru/map-widget/v1/?{e(q)}" title="Склад «Товар в деле» на Яндекс.Картах" loading="lazy" allowfullscreen></iframe>'
                '</div>')
    # Заглушка: условная схема кварталов вместо карты, пока нет адреса.
    roads = ''.join(f'<i class="road" style="{s}"></i>' for s in (
        'left:-5%;right:-5%;top:34%;height:22px;transform:rotate(-8deg)',
        'left:-5%;right:-5%;top:72%;height:14px;transform:rotate(4deg)',
        'top:-5%;bottom:-5%;left:28%;width:18px;transform:rotate(12deg)',
        'top:-5%;bottom:-5%;left:70%;width:12px;transform:rotate(-6deg)'))
    return (f'<div class="map isogrid" id="map">{roads}<div class="ph">{PIN}'
            '<span class="mono">Склад</span>'
            '<p>Точный адрес склада и схему проезда пришлём в Telegram или вместе с расчётом.</p></div></div>')


def page(src):
    css_link = '<link rel="stylesheet" href="kontakty.css">'
    head = block(src, '<!doctype html>', '<style>')[:-len('<style>')]
    head = re.sub(r'<title>.*?</title>', '<title>Контакты и реквизиты — Товар в деле</title>', head)
    head = re.sub(r'<meta name="description"[^>]*>', '<meta name="description" content="Контакты фулфилмента «Товар в деле»: телефон, Telegram, адрес склада в Туле и реквизиты ИП Зозуля М. А.">'
                  f'\n<link rel="canonical" href="{BASE}kontakty/">', head)
    header = relink(block(src, '<header class="hdr"', '</header>'))
    header = header.replace('<a href="./">Контакты</a>', '<a href="./" aria-current="page">Контакты</a>')
    tail = relink(src[src.index('<div class="tape">'):src.index('<dialog')]).rstrip()

    cards = ''
    if PHONE:
        tel = re.sub(r'[^\d+]', '', PHONE)
        cards += f'<a class="kc" href="tel:{tel}"><div class="r"><span class="mono">Телефон</span><em>{ARR}</em></div><b>{e(PHONE)}</b><p>Позвоните менеджеру — ответим на вопросы и посчитаем партию.</p></a>'
    cards += (f'<a class="kc" href="{TG}" target="_blank" rel="noopener"><div class="r"><span class="mono">Telegram</span><em>{ARR}</em></div><b>Написать менеджеру</b><p>В рабочее время отвечаем в течение 10 минут.</p></a>'
              f'<a class="kc" href="../#calc"><div class="r"><span class="mono">Расчёт</span><em>{ARR}</em></div><b>Посчитать в калькуляторе</b><p>Цена за единицу до договора. Нажмите «Получить точный расчёт» — менеджер пришлёт расчёт и проект договора.</p></a>'
              )
    addr = e(WAREHOUSE) if WAREHOUSE else 'Адрес уточняется'
    cards += f'<div class="kc"><div class="r"><span class="mono">Склад</span></div><b>{addr}</b><p>Приезжайте на экскурсию: покажем приёмку, упаковку и хранение вашего товара.</p></div>'

    rows = ''.join(f'<div class="row"><dt>{e(k)}</dt><dd>{e(v)}</dd><button class="cp" type="button" data-v="{e(v)}" aria-label="Скопировать: {e(k)}">{COPY}<span>Копировать</span></button></div>' for k, v in REQ)
    ld = {'@context': 'https://schema.org', '@type': 'LocalBusiness', 'name': 'Товар в деле', 'url': BASE,
          'legalName': REQ[0][1], 'taxID': REQ[1][1], 'description': 'Фулфилмент для маркетплейсов и интернет-магазинов',
          'address': {'@type': 'PostalAddress', 'addressLocality': 'Тула', 'addressCountry': 'RU', **({'streetAddress': WAREHOUSE} if WAREHOUSE else {})}}
    if PHONE:
        ld['telephone'] = PHONE

    return f'''{head.rstrip()}
{css_link}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
{header}

<main>
<section class="paper kh"><div class="wrap">
 <div class="l"><span class="tag acc"><b>01</b><i>Контакты</i></span><h1>Контакты</h1><p class="lead">Фулфилмент «Товар в деле». Звоните, пишите в Telegram или посчитайте партию в калькуляторе — пришлём точный расчёт и проект договора.</p></div>
 <div class="kgrid">
  <div class="kcards">{cards}</div>
  {map_html()}
 </div>
</div></section>

<section class="white" id="rekvizity"><div class="wrap req">
 <div class="l"><span class="tag"><b>02</b><i>Реквизиты</i></span><h2>Реквизиты</h2><p class="lead muted">Работаем по договору с ИП, документы — по ЭДО.</p><button class="btn ghost m cp" id="copyAll" type="button" data-v=""><span>Скопировать все реквизиты</span></button></div>
 <dl>{rows}</dl>
</div></section>
</main>
{tail}
{JS}
</body>
</html>
'''


def main():
    src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'kontakty.css'), 'w', encoding='utf-8') as f:
        f.write('/* Сгенерировано tools/contacts_page.py из index.html — не править руками */' + css + EXTRA_CSS)
    with open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page(src))
    print('kontakty/index.html, kontakty/kontakty.css')


if __name__ == '__main__':
    main()
