"""Общая вёрстка страниц «Услуги», «Цены» и страниц услуг для обоих сайтов.

Используют tools/ff_pages.py (фулфилмент) и tools/agency_pages.py (агентство): первый экран с большим
синим словом и изометрической сценой (tools/iso_scenes.py), полоса фактов, карточки услуг с графикой,
«Что входит» и «Кому подходит» с иконками (tools/icons.py), этапы с картинками. CSS добавляется
после стилей главной каждого сайта. Экранирование текста — функция e, её назначает генератор
(у фулфилмента она же оборачивает цены из калькулятора для админки).
"""
import html

from icons import icon  # noqa: F401
from iso_scenes import ART

e = lambda s: html.escape(s, quote=True)  # noqa: E731  генератор заменяет на свою

ARR = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 10h11M11 5.5l4.5 4.5-4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'

CSS = '''
/* ---- страницы услуг и цен (tools/svc_layout.py) ---- */
.hdr .nav a[aria-current]{color:var(--ink)}
.crumbs{color:var(--ink5)}.crumbs ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px 10px}
.crumbs li{display:flex;gap:10px;align-items:center}.crumbs li+li::before{content:"/";color:var(--ink3)}
.crumbs a:hover{color:var(--acc)}.crumbs [aria-current]{color:var(--ink)}
/* первый экран: сетка, большое синее слово, изометрическая сцена */
.ph{position:relative;padding:20px 0 clamp(40px,5vw,64px);background-color:var(--paper);overflow:clip;isolation:isolate}
.ph::before{content:"";position:absolute;inset:0;z-index:-1;background-image:linear-gradient(var(--line) 1px,transparent 1px),linear-gradient(90deg,var(--line) 1px,transparent 1px);background-size:80px 80px;background-position:center top;opacity:.55;-webkit-mask-image:linear-gradient(#000 20%,transparent 96%);mask-image:linear-gradient(#000 20%,transparent 96%)}
.ph .g{display:grid;gap:24px;margin-top:28px;align-items:end}
@media (min-width:1000px){.ph .g{grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:48px;margin-top:16px}}
.ph .kick{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:22px}
.ph .kick .mono{color:var(--ink5)}.ph .kick .mono b{color:var(--acc);font-weight:500}
.ph h1{font-size:clamp(20px,1.9vw,28px);font-weight:500;line-height:1.3;letter-spacing:-.01em;color:var(--acc6);max-width:34ch}
.ph .big{margin:4px 0 0 -.04em;font-size:var(--big);line-height:.95;font-weight:500;letter-spacing:-.05em;color:var(--acc);overflow-wrap:anywhere}
.ph .big.xl{--big:clamp(84px,13vw,176px)}.ph .big.l{--big:clamp(60px,9.2vw,132px)}.ph .big.m{--big:clamp(46px,6.6vw,96px)}
.ph .lead{margin-top:20px;max-width:46ch}
.ph .ctas{margin-top:28px}
.ph .art{position:relative;display:grid;place-items:center;min-height:min(360px,60vw);padding:20px 0 8px}
.ph .art svg.il{width:100%;height:auto;max-height:min(520px,56vh);overflow:visible;filter:drop-shadow(0 28px 36px rgba(10,23,54,.12))}
@media (max-width:999px){.ph .art svg.il{max-height:300px}}
.ph .fl{position:absolute;display:inline-flex;align-items:center;gap:8px;padding:8px 12px;background:var(--card);border:1px solid var(--line);border-radius:2px;color:var(--ink);box-shadow:0 8px 24px rgba(10,23,54,.10);font-size:12px;line-height:1.2;white-space:nowrap}
.ph .fl i{width:8px;height:8px;border-radius:50%;background:var(--acc);flex:none}.ph .fl.ok i{background:#2BB673}
.ph .fl.tl{left:2%;top:4%}.ph .fl.tr{right:0;top:16%}.ph .fl.br{right:4%;bottom:8%}.ph .fl.bl{left:0;bottom:14%}
@media (max-width:479px){.ph .fl{font-size:11px;padding:6px 10px}.ph .fl.tr{top:2%}}
/* полоса фактов */
.facts{display:grid;gap:1px;margin-top:clamp(28px,4vw,48px);background:var(--line);border:1px solid var(--line);border-radius:4px;overflow:hidden;grid-template-columns:1fr 1fr}
@media (min-width:900px){.facts{grid-template-columns:repeat(4,1fr)}}
.facts>div{position:relative;display:grid;gap:6px;align-content:start;padding:20px 22px 22px;background:var(--card)}
.facts b{font-size:clamp(22px,2.2vw,32px);line-height:1.05;font-weight:500;letter-spacing:-.03em;color:var(--acc6);font-variant-numeric:tabular-nums;padding-right:28px;text-wrap:balance}
.facts span{color:var(--ink5);font-size:14px;line-height:1.35}
.facts svg.i{position:absolute;right:16px;top:18px;width:22px;height:22px;color:var(--acc)}
@media (max-width:479px){.facts>div{padding:16px 16px 18px}.facts b{font-size:20px;padding-right:0}.facts svg.i{display:none}}
/* карточки услуг */
.isogrid{background-color:var(--paper);background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='34.64' height='20'%3E%3Cpath d='M0 0L34.64 20M34.64 0L0 20' stroke='%23D3E0F3' stroke-width='.6' fill='none'/%3E%3C/svg%3E");background-size:34.64px 20px}
.ilbox{position:relative;display:grid;place-items:center;aspect-ratio:4/3;border-radius:4px;overflow:hidden;padding:20px}.ilbox svg{width:100%;height:100%;max-height:240px}
.cards{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{display:grid;align-content:start;background:var(--card);border:1px solid var(--line);border-radius:4px;overflow:hidden;color:inherit;transition:border-color var(--base),transform var(--base) var(--std),box-shadow var(--base)}
.card:hover{border-color:var(--acc);transform:translateY(-4px);box-shadow:0 16px 40px rgba(10,23,54,.08)}
.card .ilbox{border-radius:0;padding:20px}.card .ilbox svg{max-height:190px}
.card .b{display:grid;gap:10px;align-content:start;padding:20px 22px 22px}
.card .b .mono{color:var(--ink5)}.card .b .mono b{color:var(--acc);font-weight:500}
.card h2,.card h3{font-size:clamp(21px,1.9vw,25px);line-height:1.15}
.card p{color:var(--ink5);font-size:15px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .r{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:4px;padding-top:14px;border-top:1px solid var(--line)}
.card .r b{font-weight:600;color:var(--acc6);font-size:17px;font-variant-numeric:tabular-nums}.card .r b small{display:block;font-weight:400;font-size:13px;color:var(--ink5)}
.card .r em{flex:none;width:36px;height:36px;display:grid;place-items:center;background:var(--acc1);color:var(--acc);border-radius:2px;font-style:normal;transition:background var(--base),color var(--base)}
.card:hover .r em{background:var(--acc);color:#fff}
@media (min-width:1000px){.cards{grid-template-columns:repeat(3,1fr)}.card.wide{grid-column:span 2;grid-template-columns:1fr 1fr;align-items:stretch}
 .card.wide .ilbox{aspect-ratio:auto;height:100%;min-height:260px}.card.wide .ilbox svg{max-height:240px}.card.wide .b{padding:28px 30px 28px 8px;align-content:center}
 .card.wide h2{font-size:clamp(26px,2.4vw,34px)}.card.wide p{-webkit-line-clamp:3}}
/* путь товара / связки услуг */
.path{list-style:none;margin:0;padding:0;display:grid;gap:12px;grid-template-columns:repeat(2,1fr)}
@media (min-width:700px){.path{grid-template-columns:repeat(3,1fr)}}@media (min-width:1000px){.path{grid-template-columns:repeat(6,1fr)}}
.path li{position:relative;display:grid;gap:8px;align-content:start;padding:18px 18px 20px;background:var(--card);border:1px solid var(--line);border-radius:4px}
.path .fi{height:84px;display:grid;place-items:center;margin-bottom:4px}.path .fi svg{height:100%;width:auto;max-width:100%}
.path .mono{color:var(--acc)}.path h3{font-size:17px;font-weight:600}.path p{color:var(--ink5);font-size:14px}
.path li a{color:var(--acc);font-size:14px;font-weight:500}.path li a:hover{color:var(--acc6)}
@media (min-width:1000px){.path li:not(:last-child)::after{content:"";position:absolute;right:-13px;top:50%;width:14px;height:1px;background:var(--ink3)}}
/* иконки */
.ic{width:52px;height:52px;display:grid;place-items:center;border-radius:4px;background:var(--acc1);color:var(--acc)}.ic svg{width:26px;height:26px}
/* что входит */
.inc{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}@media (min-width:1000px){.inc{grid-template-columns:repeat(3,1fr)}}
.inc article{display:grid;gap:14px;align-content:start;padding:24px 24px 26px;background:var(--paper);border-radius:4px;border:1px solid transparent;transition:border-color var(--base)}
.paper .inc article{background:var(--card);border-color:var(--line)}
.inc article:hover{border-color:var(--acc)}.inc h3{font-size:20px}.inc p{color:var(--ink5);font-size:15px}
/* кому подходит */
.who.w3{display:grid;gap:16px;grid-template-columns:none}@media (min-width:900px){.who.w3{grid-template-columns:repeat(3,1fr)}}
.who.w3 article{display:grid;gap:14px;align-content:start;padding:26px 26px 30px;background:var(--card);border:1px solid var(--line);border-radius:4px}
.who.w3 article:hover{border-color:var(--acc);transform:none}
.who.w3 h3{font-size:22px;font-weight:600}.who.w3 p{color:var(--ink5)}
/* этапы */
.flow.f4{grid-template-columns:none}@media (min-width:900px){.flow.f4{grid-template-columns:repeat(4,1fr)}}
.flow .fi{display:block;height:84px;margin-bottom:4px}.flow .fi svg{height:100%;width:auto;max-width:100%}
/* подробнее, вопросы, ещё услуги */
.prose{display:grid;gap:24px}@media (min-width:1000px){.prose{grid-template-columns:400px 1fr;gap:80px}}
.prose .l{display:grid;gap:20px;justify-items:start;align-content:start}
.prose .t{display:grid;gap:18px;max-width:68ch;font-size:17px;line-height:1.6;color:var(--ink7)}
.faq .faqart{width:100%;max-width:360px;aspect-ratio:4/3;margin-top:8px}
.final .ctas{margin-top:40px}
.links{display:flex;flex-wrap:wrap;gap:12px 24px;margin-top:32px}.links a{color:var(--acc);font-weight:500}.links a:hover{color:var(--acc6)}
/* прайс */
.formula{display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin-bottom:clamp(32px,4vw,56px)}
.formula .f{display:grid;grid-template-columns:auto 1fr;gap:2px 14px;align-items:center;padding:12px 18px 12px 12px;background:var(--card);border:1px solid var(--line);border-radius:4px}
.formula .f .ic{grid-row:span 2;width:44px;height:44px}.formula .f .ic svg{width:22px;height:22px}
.formula .f b{font-weight:600;font-size:15px}.formula .f span{color:var(--ink5);font-size:13px}
.formula .op{font-size:28px;line-height:1;font-weight:500;color:var(--acc);width:20px;text-align:center}
.pt{display:grid;gap:16px}
.pg{display:grid;gap:8px 48px;padding:28px 28px 20px;background:var(--card);border:1px solid var(--line);border-radius:4px}
@media (min-width:1000px){.pg{grid-template-columns:300px 1fr}}
.pg .h{display:grid;gap:12px;align-content:start;justify-items:start}.pg .h h2{font-size:clamp(26px,2.6vw,34px)}
.pg .h .mono{color:var(--ink5)}.pg .h a{color:var(--acc);font-weight:500;font-size:15px}.pg .h a:hover{color:var(--acc6)}
.pg .h .th{width:min(100%,240px);aspect-ratio:4/3;display:grid;place-items:center;padding:14px;border-radius:4px;margin-bottom:4px}.pg .h .th svg{width:100%;height:100%}
@media (max-width:999px){.pg .h .th{display:none}}
.pg table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;align-self:start}
.pg td{padding:14px 0;border-top:1px solid var(--line);vertical-align:baseline}.pg tr:first-child td{border-top:0}
.pg td:first-child{padding-right:24px}.pg td.p{text-align:right;white-space:nowrap;font-weight:600;font-size:18px;color:var(--acc6)}
.pg td.u{text-align:right;white-space:nowrap;color:var(--ink5);font-size:14px;padding-left:12px;width:150px}
@media (max-width:599px){.pg{padding:22px 20px 14px}.pg tr{display:grid;grid-template-columns:1fr auto;gap:2px 12px;padding:12px 0;border-top:1px solid var(--line)}.pg tr:first-child{border-top:0}
 .pg td{padding:0;border:0}.pg td:first-child{grid-column:1/-1;padding:0}.pg td.p{text-align:left}.pg td.u{width:auto}}
.pnote{display:grid;gap:12px;margin-top:32px;max-width:80ch;color:var(--ink5)}
'''


def big_class(word):
    n = len(word)
    return 'xl' if n <= 4 else 'l' if n <= 8 else 'm'


def hero(crumbs_html, kick_html, h1, big, lead, ctas_html, art, chips=(), facts=()):
    """Первый экран. art — имя сцены из iso_scenes.ART; chips — [(текст, tl|tr|br|bl, ok)];
    facts — [(значение HTML, подпись, иконка|None)]."""
    fl = ''.join(f'<span class="fl {pos}{" ok" if ok else ""}"><i></i>{e(t)}</span>' for t, pos, ok in chips)
    fx = ''.join(f'<div>{icon(ic, "i") if ic else ""}<b>{v}</b><span>{e(l)}</span></div>' for v, l, ic in facts)
    facts_html = f'\n <div class="facts rv">{fx}</div>' if fx else ''
    return f'''<section class="ph"><div class="wrap">
 {crumbs_html}
 <div class="g">
  <div><div class="kick">{kick_html}</div><h1>{e(h1)}</h1><p class="big {big_class(big)}" aria-hidden="true">{e(big)}</p><p class="lead">{e(lead)}</p><div class="ctas">{ctas_html}</div></div>
  <div class="art">{ART[art]()}{fl}</div>
 </div>{facts_html}
</div></section>
'''


def card(href, art, label_html, name, text, price_html, unit='', wide=False, tag='h2'):
    """Карточка услуги с изометрической сценой. label_html — строка над названием (уже HTML)."""
    unit_html = f'<small>{e(unit)}</small>' if unit else ''
    return (f'<a class="card rv{" wide" if wide else ""}" href="{href}"><div class="ilbox isogrid">{ART[art]()}</div>'
            f'<div class="b"><span class="mono">{label_html}</span><{tag}>{e(name)}</{tag}><p>{e(text)}</p>'
            f'<div class="r"><b>{price_html}{unit_html}</b><em>{ARR}</em></div></div></a>')


def includes(items, icons):
    return ''.join(f'<article class="rv"><span class="ic">{icon(icons[i % len(icons)])}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>'
                   for i, (t, d) in enumerate(items))


def who(items, icons):
    return ''.join(f'<article class="rv"><span class="ic">{icon(icons[i % len(icons)])}</span><h3>{e(t)}</h3><p>{e(d)}</p></article>'
                   for i, (t, d) in enumerate(items))


def flow(steps, arts):
    return ''.join(f'<li><span class="n">{i + 1}</span><span class="fi">{ART[arts[i % len(arts)]]()}</span><span class="mono d">{e(a)}</span><h3>{e(b)}</h3><p>{e(c)}</p></li>'
                   for i, (a, b, c) in enumerate(steps))


def path(items):
    """Полоса «путь товара» / «как услуги работают вместе»: [(сцена, подпись, текст, href|None)]."""
    li = ''
    for i, (art, name, text, href) in enumerate(items):
        link = f'<a href="{href}">Подробнее →</a>' if href else ''
        li += f'<li class="rv"><span class="fi">{ART[art]()}</span><span class="mono">{i + 1:02d}</span><h3>{e(name)}</h3><p>{e(text)}</p>{link}</li>'
    return f'<ol class="path">{li}</ol>'


def faq(items, faq_art=True):
    return ''.join(f'<details{"" if i else " open"}><summary><span class="num mono">0{i + 1}</span><span>{e(q)}</span><span class="pl"></span></summary><div class="a">{e(a)}</div></details>'
                   for i, (q, a) in enumerate(items))


def faq_art():
    return ART['faq_art']().replace('class="il"', 'class="il faqart"')


def formula(items):
    """Из чего складывается цена: [(иконка, заголовок, подпись)], между ними «+», перед последним «=»."""
    out = ''
    for i, (ic, t, d) in enumerate(items):
        if i:
            out += f'<span class="op" aria-hidden="true">{"=" if i == len(items) - 1 else "+"}</span>'
        out += f'<div class="f"><span class="ic">{icon(ic)}</span><b>{e(t)}</b><span>{e(d)}</span></div>'
    return f'<div class="formula rv">{out}</div>'
