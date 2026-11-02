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
import svc_layout as L  # noqa: E402  общая вёрстка страниц услуг и цен (иллюстрации, иконки, CSS)
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
L.e = e  # экранирование общее с вёрсткой (с админкой — оборачивает цены калькулятора)
ARR = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h11M11 5.5l4.5 4.5-4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

EXTRA_CSS = L.CSS

JS = '''<script>
(function(){
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const hdr=$('#hdr');let lastY=0;addEventListener('scroll',()=>{const y=scrollY;hdr.classList.toggle('scrolled',y>80);hdr.classList.toggle('hide',y>160&&y>lastY);lastY=y},{passive:true});
const menu=$('#menu');const openMenu=o=>{menu.classList.toggle('open',o);menu.setAttribute('aria-hidden',!o);$('#menuBtn').setAttribute('aria-expanded',o);document.body.style.overflow=o?'hidden':''};
$('#menuBtn').onclick=()=>openMenu(true);$('#menuClose').onclick=()=>openMenu(false);menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>openMenu(false)));addEventListener('keydown',e=>{if(e.key==='Escape')openMenu(false)});
const f=$('#faqList');if(f){const ds=f.querySelectorAll('details');ds.forEach(d=>{d.classList.toggle('on',d.open);d.addEventListener('toggle',()=>{d.classList.toggle('on',d.open);if(d.open)ds.forEach(o=>{if(o!==d)o.open=false})})})}
if('IntersectionObserver' in window){const io=new IntersectionObserver(es=>es.forEach(e=>{if(!e.isIntersecting)return;e.target.classList.add('in');io.unobserve(e.target)}),{threshold:.15});$$('.rv').forEach(el=>io.observe(el))}else $$('.rv').forEach(el=>el.classList.add('in'));
const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches,EASE='cubic-bezier(.22,.8,.24,1)';
const slide=(d,open)=>{const b=d.querySelector('summary').nextElementSibling;d.classList.toggle('on',open);if(reduce){d.open=open;return}
  const cs=getComputedStyle(b),h0=d.open?b.offsetHeight:0,t0=d.open?cs.paddingTop:'0px',b0=d.open?cs.paddingBottom:'0px';if(d._a){d._a.cancel();d._a=null}
  d.open=true;const nat=getComputedStyle(b),pt=nat.paddingTop,pb=nat.paddingBottom,h1=open?b.offsetHeight:0;
  b.style.overflow='hidden';const a=d._a=b.animate([{height:h0+'px',paddingTop:t0,paddingBottom:b0},{height:h1+'px',paddingTop:open?pt:'0px',paddingBottom:open?pb:'0px'}],{duration:open?460:360,easing:open?EASE:'cubic-bezier(.4,0,.2,1)'});
  a.onfinish=()=>{b.style.overflow='';d._a=null;if(!open)d.open=false};a.oncancel=()=>{b.style.overflow=''}};
const acc=$('#acc');if(acc)acc.querySelectorAll('details').forEach(d=>{d.classList.toggle('on',d.open);d.querySelector('summary').addEventListener('click',e=>{e.preventDefault();
  const s=e.currentTarget,y0=s.getBoundingClientRect().top,open=!d.classList.contains('on');slide(d,open);if(open)acc.querySelectorAll('details.on').forEach(o=>{if(o!==d)slide(o,false)});
  if(reduce)return;const t0=performance.now(),pin=()=>{const dy=s.getBoundingClientRect().top-y0;if(Math.abs(dy)>.5)window.scrollBy({top:dy,behavior:'instant'});if(performance.now()-t0<560)requestAnimationFrame(pin)};requestAnimationFrame(pin)})});
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


# Графика страниц услуг: большое слово первого экрана, сцена, чипы над сценой, факты,
# иконки «Что входит» / «Кому подходит», картинки этапов. Ключи — slug из ff_services.py.
BIG = {'fbs': 'FBS', 'fbo': 'FBO', 'hranenie': 'Хранение', 'priemka': 'Приёмка', 'markirovka-i-upakovka': 'Маркировка',
       'vozvraty': 'Возвраты', 'zabor-i-dostavka': 'Доставка'}
ART = {'fbs': 'svc_fbs', 'fbo': 'svc_fbo', 'hranenie': 'svc_store', 'priemka': 'svc_accept', 'markirovka-i-upakovka': 'svc_pack',
       'vozvraty': 'svc_returns', 'zabor-i-dostavka': 'svc_truck'}
CHIPS = {'fbs': [('Wildberries · Ozon · Яндекс Маркет', 'tl', False), ('Отгрузка 12:00 и 21:00', 'br', True), ('Остатки онлайн в WMS', 'tr', False)],
         'fbo': [('Короба и паллеты по правилам площадки', 'tl', False), ('Слоты бронируем сами', 'tr', False), ('Приёмка с первого раза', 'br', True)],
         'hranenie': [('Адресные ячейки', 'tl', False), ('Тёплый склад', 'tr', False), ('Первые 14 дней бесплатно', 'br', True)],
         'priemka': [('Пересчёт каждой единицы', 'tl', False), ('Проверка на брак', 'tr', False), ('Акт с фото в день поставки', 'br', True)],
         'markirovka-i-upakovka': [('«Честный знак» и стикеры ШК', 'tl', False), ('Комплекты и вложения', 'tr', False), ('Проверка перед отправкой', 'br', True)],
         'vozvraty': [('Забор из ПВЗ и СЦ', 'tl', False), ('Фото и акт на каждый возврат', 'tr', False), ('Годный товар — снова в продажу', 'br', True)],
         'zabor-i-dostavka': [('Свой транспорт', 'tl', False), ('СЦ и склады WB, Ozon, ЯМ', 'tr', False), ('Доставка к забронированному слоту', 'br', True)]}
FACTS = {'fbs': [('12:00 и 21:00', 'две отгрузки каждый день', 'clock'), ('3–4 дня', 'от расчёта до первой отгрузки', 'calendar'), ('3 площадки', 'общий остаток для WB, Ozon и ЯМ', 'layers')],
         'fbo': [('1–2 дня', 'подготовка партии', 'clock'), ('с 1-го раза', 'приёмка на складе маркетплейса', 'check'), ('WB · Ozon · ЯМ', 'везём на любые склады', 'truck')],
         'hranenie': [('14 дней', 'бесплатно с даты приёмки', 'calendar'), ('по литрам', 'платите за объём, а не за ячейку', 'cube'), ('онлайн', 'остатки и движения в WMS', 'wms')],
         'priemka': [('в день поставки', 'пересчёт и акт с фото', 'clock'), ('100%', 'пересчитываем каждую единицу', 'scan'), ('короба и паллеты', 'разгружаем любую поставку', 'pallet')],
         'markirovka-i-upakovka': [('от 2 часов', 'на партию', 'clock'), ('«Честный знак»', 'и стикеры WB, Ozon, ЯМ', 'tag'), ('по правилам', 'каждой площадки', 'check')],
         'vozvraty': [('1–2 дня', 'возврат годного товара в продажу', 'clock'), ('фото + акт', 'на каждый возврат', 'photo'), ('переупаковка', 'и перемаркировка', 'repeat')],
         'zabor-i-dostavka': [('свой транспорт', 'Тула и область', 'truck'), ('СЦ и склады', 'WB, Ozon, Яндекс Маркет', 'warehouse'), ('в слот', 'доставка к забронированному времени', 'calendar')]}
INC_ICONS = {'fbs': ['api', 'scan', 'box', 'truck', 'wms', 'repeat'], 'fbo': ['doc', 'tag', 'pallet', 'calendar', 'truck', 'check'],
             'hranenie': ['grid', 'wms', 'thermo', 'list', 'boxes', 'shield'], 'priemka': ['truck', 'scan', 'eye', 'photo', 'grid'],
             'markirovka-i-upakovka': ['tag', 'box', 'boxes', 'layers', 'check'], 'vozvraty': ['truck', 'eye', 'box', 'repeat', 'photo'],
             'zabor-i-dostavka': ['map', 'warehouse', 'route', 'pallet']}
WHO_ICONS = {'fbs': ['wallet', 'layers', 'eye'], 'fbo': ['trend', 'shield', 'clock'], 'hranenie': ['pallet', 'rub', 'calendar'],
             'priemka': ['users', 'undo', 'globe'], 'markirovka-i-upakovka': ['label', 'cube', 'star'], 'vozvraty': ['tag', 'map', 'shield'],
             'zabor-i-dostavka': ['truck', 'route', 'calendar']}
STEP_ART = {'fbs': ['flow_doc', 'flow_work', 'flow_accept', 'flow_fbs'], 'fbo': ['flow_doc', 'flow_accept', 'flow_fbo', 'flow_pick'],
            'hranenie': ['flow_req', 'flow_doc', 'flow_accept', 'flow_store'], 'priemka': ['flow_req', 'flow_pick', 'flow_accept', 'flow_doc'],
            'markirovka-i-upakovka': ['flow_doc', 'flow_req', 'flow_fbo', 'flow_fbs'], 'vozvraty': ['flow_pick', 'flow_accept', 'flow_fbo', 'flow_store'],
            'zabor-i-dostavka': ['flow_req', 'flow_doc', 'flow_pick', 'flow_accept']}


def svc_card(r, s, wide=False, tag='h2'):
    n = SERVICES.index(s) + 1
    return L.card(f'{r}uslugi/{s["slug"]}/', ART[s['slug']], f'<b>{n:02d}</b> · {e(s["group"])}', s['name'], s['lead'],
                  e(s['price']), s['unit'], wide=wide, tag=tag)


def service_page(src, s):
    r = '../../'
    n = SERVICES.index(s) + 1
    k = s['slug']
    rel = ''.join(svc_card(r, BY_SLUG[x], tag='h3') for x in s['related'])
    rows = ''.join(f'<tr><td>{e(a)}</td><td class="p">{e(b)}</td><td class="u">{e(c)}</td></tr>' for a, b, c, _ in price_rows(k))
    tariff = f'''
<section class="paper" id="tarify"><div class="wrap">
 <div class="pg rv"><div class="h"><span class="tag"><b>04</b><i>Тарифы</i></span><h2>Сколько стоит</h2><p style="color:var(--ink5)">{e(s['price_note'])}. Точную цену фиксируем в приложении к договору.</p><a href="{r}ceny/#{k}">Весь прайс →</a></div>
 <table><tbody>{rows}</tbody></table></div>
</div></section>
''' if rows else ''
    facts = [(e(s['price']), s['unit'], 'rub')] + FACTS[k]
    kick = f'<span class="tag"><b>{n:02d}</b><i>{e(s["group"])}</i></span><span class="mono">{e(s["term"])}</span>'
    ctas = f'<a class="btn primary" href="{calc_href(r, s)}"><span>Рассчитать стоимость</span><em>{ARR}</em></a><a class="btn ghost" href="#tarify"><span>Тарифы</span></a>'
    body = L.hero(crumbs(r, [('Главная', r), ('Услуги', r + 'uslugi/'), (s['short'], None)]), kick, s['h1'], BIG[k], s['lead'], ctas,
                  ART[k], CHIPS[k], facts) + f'''
<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Что входит</i></span><h2>Что входит в услугу</h2></div><p class="lead muted">Платите только за операции, которые мы выполнили. Состав работ фиксируем в договоре.</p></div>
 <div class="inc">{L.includes(s['includes'], INC_ICONS[k])}</div>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Кому подходит</i></span><h2>Когда это выгодно</h2></div><p class="lead muted">Работаем от первой партии и без минимального ежемесячного платежа.</p></div>
 <div class="who w3">{L.who(s['who'], WHO_ICONS[k])}</div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>03</b><i>Как работаем</i></span><h2>Этапы и сроки</h2></div><p class="lead muted">Каждая операция видна в нашей WMS, персональный менеджер на связи в мессенджере.</p></div>
 <ol class="flow f4 rv">{L.flow(s['steps'], STEP_ART[k])}</ol>
</div></section>
{tariff}
<section class="white"><div class="wrap prose">
 <div class="l rv"><span class="tag"><b>05</b><i>Подробнее</i></span><h2>{e(s['name'])}: как это устроено</h2></div>
 <div class="t rv">{''.join(f'<p>{e(p)}</p>' for p in s['text'])}</div>
</div></section>

<section class="paper" id="faq"><div class="wrap faq">
 <div class="l rv"><span class="tag"><b>06</b><i>Вопросы</i></span><h2>Частые вопросы</h2><p class="muted">Не нашли свой вопрос? Спросите менеджера — ответим лично.</p><a class="btn ghost" href="{TG}" target="_blank" rel="noopener"><span>Задать вопрос в Telegram</span></a>{L.faq_art()}</div>
 <div id="faqList">{L.faq(s['faq'])}</div>
</div></section>

<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>07</b><i>Ещё услуги</i></span><h2>Часто заказывают вместе</h2></div><p class="lead muted"><a href="{r}uslugi/" style="color:var(--acc)">Все услуги →</a></p></div>
 <div class="cards">{rel}</div>
</div></section>

{final(r, 'Посчитайте свою партию', 'Отметьте операции в калькуляторе и нажмите «Получить точный расчёт». Менеджер сверит габариты и объёмы и пришлёт расчёт по каждой строке прайса и проект договора.', s)}'''
    return shell(src, 2, '../../uslugi/', body)


def index_page(src):
    r = '../'
    acc = L.accordion([(s['group'], s['name'], s['lead'], e(s['price']), s['unit'], f'{r}uslugi/{s["slug"]}/', ART[s['slug']], ())
                       for g in GROUPS for s in SERVICES if s['group'] == g], GROUPS)
    facts = [('7 услуг', 'от приёмки до доставки покупателю', 'layers'), ('2 отгрузки', 'в день: 12:00 и 21:00', 'clock'),
             ('14 дней', 'хранения бесплатно', 'calendar'), ('Тула', 'склад, свой транспорт до СЦ', 'map')]
    kick = '<span class="tag"><b>→</b><i>Все услуги</i></span><span class="mono">Wildberries · Ozon · Яндекс Маркет</span>'
    ctas = f'<a class="btn primary" href="{r}#calc"><span>Рассчитать стоимость</span><em>{ARR}</em></a><a class="btn ghost" href="{r}ceny/"><span>Цены</span></a>'
    way = L.path([('flow_pick', 'Забор', 'У поставщика, из ТК или с рынка.', f'{r}uslugi/zabor-i-dostavka/'),
                  ('flow_accept', 'Приёмка', 'Пересчёт, проверка на брак, акт с фото.', f'{r}uslugi/priemka/'),
                  ('flow_store', 'Хранение', 'Адресные ячейки, остатки онлайн.', f'{r}uslugi/hranenie/'),
                  ('flow_doc', 'Маркировка', '«Честный знак», стикеры, упаковка.', f'{r}uslugi/markirovka-i-upakovka/'),
                  ('flow_fbs', 'Сборка', 'Заказы FBS и поставки FBO.', f'{r}uslugi/fbs/'),
                  ('flow_fbo', 'Доставка', 'До СЦ и складов маркетплейсов.', f'{r}uslugi/fbo/')])
    body = L.hero(crumbs(r, [('Главная', r), ('Услуги', None)]), kick, 'Услуги фулфилмента для маркетплейсов и интернет-магазинов', 'Услуги',
                  'Всё, что происходит с товаром между поставщиком и покупателем. Склад в Туле, цены за операцию, расчёт в калькуляторе за минуту.',
                  ctas, 'hero_services', [('Склад в Туле', 'tl', False), ('FBS · FBO · хранение', 'tr', False), ('Отгрузка дважды в день', 'br', True)], facts) + f'''
<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Услуги</i></span><h2>Выберите, что нужно товару</h2></div><p class="lead muted">Любую услугу можно заказать отдельно. Цены — за операцию, без минимального платежа.</p></div>
 {acc}
 <p class="links"><a href="{AGENCY}uslugi/" target="_blank" rel="noopener">Интернет-магазин, маркетинг и контент — в агентстве Madrocks ↗</a></p>
</div></section>

<section class="paper"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>02</b><i>Путь товара</i></span><h2>От поставщика до покупателя</h2></div><p class="lead muted">Шесть шагов, каждый виден в WMS. Подключайте те, что нужны именно вашему товару.</p></div>
 {way}
</div></section>
{final(r, 'Не знаете, какая схема выгоднее?', 'Посчитайте партию в калькуляторе и оставьте контакты. Менеджер сравнит FBS и FBO на ваших объёмах и пришлёт точный расчёт.')}'''
    return shell(src, 1, '../uslugi/', body)


def prices_page(src):
    r = '../'
    groups = ''
    for g in PRICES:
        s = BY_SLUG[g['slug']]
        rows = ''.join(f'<tr><td>{e(a)}</td><td class="p">{e(b)}</td><td class="u">{e(c)}</td></tr>' for a, b, c, _ in g['rows'])
        groups += (f'<div class="pg rv" id="{g["slug"]}"><div class="h"><div class="th isogrid">{L.ART[ART[g["slug"]]]()}</div><h2>{e(g["name"])}</h2><a href="{r}uslugi/{g["slug"]}/">{e(s["name"])}: подробнее →</a></div>'
                   f'<table><tbody>{rows}</tbody></table></div>')
    facts = [(e(BY_SLUG[k]['price']), BY_SLUG[k]['short'] + ' · ' + BY_SLUG[k]['unit'], ic)
             for k, ic in (('priemka', 'scan'), ('fbs', 'phone'), ('fbo', 'pallet'), ('hranenie', 'warehouse'))]
    kick = '<span class="tag"><b>₽</b><i>Прайс</i></span><span class="mono">за операцию · без НДС</span>'
    ctas = f'<a class="btn primary" href="{r}#calc"><span>Рассчитать стоимость партии</span><em>{ARR}</em></a><a class="btn ghost" href="{r}uslugi/"><span>Все услуги</span></a>'
    form = L.formula([('scan', 'Приёмка', 'за единицу + разгрузка'), ('tag', 'Работы с товаром', 'маркировка, упаковка, комплекты'),
                      ('boxes', 'Сборка', 'заказ FBS или поставка FBO'), ('rub', 'Цена за единицу', 'хранение — после 14 бесплатных дней')])
    body = L.hero(crumbs(r, [('Главная', r), ('Цены', None)]), kick, 'Цены на фулфилмент для маркетплейсов', 'Цены',
                  'Платите за операции, которые нужны вашему товару. Калькулятор на главной считает по этим же ценам.', ctas, 'hero_prices',
                  [('Скидка 10% на первую партию', 'tl', True), ('Без минимального платежа', 'tr', False), ('Цена видна до договора', 'br', False)], facts) + f'''
<section class="white"><div class="wrap">
 <div class="sec-head rv"><div class="l"><span class="tag"><b>01</b><i>Прайс</i></span><h2>Из чего складывается цена</h2></div><p class="lead muted">Итог за единицу — сумма операций. Хранение считается по объёму и начинается после бесплатного периода.</p></div>
 {form}
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
    import cachebust  # метки ?v= у CSS/JS, см. tools/cachebust.py
    cachebust.main()


if __name__ == '__main__':
    main()
