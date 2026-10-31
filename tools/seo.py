#!/usr/bin/env python3
"""SEO фулфилмента «Товар в деле».

Запуск из корня репозитория:  python3 tools/seo.py
Все настройки — в data/seo.json (заголовки, описания, адрес, телефон, коды
Вебмастера и Search Console, Метрика). Скрипт:
  * пишет в <head> каждой страницы из списка pages блок между <!-- seo --> и <!-- /seo -->:
    title, description, canonical, Open Graph, иконки, гео-метки, коды подтверждения,
    разметку schema.org (JSON-LD) и счётчик Метрики;
  * на главной дублирует «Частые вопросы» статичным HTML (их видят роботы без JS);
  * пишет robots.txt, sitemap.xml и llms.txt в корень.
Запускать после правок data/seo.json, текстов главной и после генераторов
contacts_page.py / legal_pages.py (они вызывают его сами).
"""
import ast, datetime, html, json, os, re, subprocess, sys
from urllib.parse import urlsplit

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, 'data', 'seo.json')
START, END = '<!-- seo -->', '<!-- /seo -->'
OG_W, OG_H = 1200, 630

e = lambda s: html.escape(str(s), quote=True)


def read(p):
    with open(os.path.join(ROOT, p), encoding='utf-8') as f:
        return f.read()


def write(p, s):
    with open(os.path.join(ROOT, p), 'w', encoding='utf-8') as f:
        f.write(s)


def text(s):
    """HTML → обычный текст."""
    s = re.sub(r'<br\s*/?>', ' ', s)
    s = re.sub(r'<[^>]+>', '', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def lastmod(p):
    try:
        d = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', p], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        d = ''
    return d or datetime.date.today().isoformat()


# ---------- контент главной: услуги и вопросы ----------

def services(src):
    acc = src[src.index('id="acc"'):]
    acc = acc[:acc.index('</section>')]
    out = []
    for d in re.findall(r'<details.*?</details>', acc, re.S):
        name = re.search(r'<h3>(.*?)</h3>', d, re.S)
        desc = re.search(r'<p class="lead">(.*?)</p>', d, re.S)
        price = re.search(r'<div class="pr">(.*?)(?:<a |</div>)', d, re.S)
        if name:
            out.append({'name': text(name.group(1)), 'desc': text(desc.group(1)) if desc else '',
                        'price': text(price.group(1)) if price else ''})
    return out


def faq(src):
    m = re.search(r'const FAQ=(\[.*?\]);', src, re.S)
    return [(q, a) for q, a in ast.literal_eval(m.group(1))] if m else []


def faq_html(items):
    # Та же разметка, что строит скрипт главной: роботы без JS видят ответы, скрипт перерисует так же.
    return ''.join(f'<details{"" if i else " open"}><summary><span class="num mono">0{i + 1}</span><span>{q}</span>'
                   f'<span class="pl"></span></summary><div class="a">{a}</div></details>' for i, (q, a) in enumerate(items))


# ---------- schema.org ----------

def tel(s):
    return re.sub(r'[^\d+]', '', s)


def business(cfg, svc):
    site, org = cfg['site'], cfg['organization']
    base = site['base_url']
    a = org['address']
    b = {
        '@type': 'LocalBusiness', '@id': base + '#business', 'name': org['name'],
        'alternateName': org.get('alternate_name'), 'description': org.get('description'),
        'url': base, 'logo': base + org['logo'] if org.get('logo') else None,
        'image': base + site['og_image'] if site.get('og_image') else None,
        'telephone': tel(org['phone']) if org.get('phone') else None, 'email': org.get('email'),
        'legalName': org.get('legal_name'), 'taxID': org.get('inn'), 'priceRange': org.get('price_range'),
        'address': {'@type': 'PostalAddress', 'streetAddress': a.get('street'), 'addressLocality': a.get('locality'),
                    'addressRegion': a.get('region'), 'postalCode': a.get('postal_code'), 'addressCountry': a.get('country')},
        'areaServed': [{'@type': 'Country', 'name': n} for n in org.get('area_served', [])],
        'sameAs': org.get('same_as'),
    }
    g = org.get('geo') or {}
    if g.get('lat') and g.get('lon'):
        b['geo'] = {'@type': 'GeoCoordinates', 'latitude': g['lat'], 'longitude': g['lon']}
        b['hasMap'] = f'https://yandex.ru/maps/?pt={g["lon"]},{g["lat"]}&z=17&l=map'
    if org.get('opening_hours'):
        b['openingHoursSpecification'] = [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': h['days'],
                                           'opens': h['opens'], 'closes': h['closes']} for h in org['opening_hours']]
    if svc:
        b['hasOfferCatalog'] = {'@type': 'OfferCatalog', 'name': 'Услуги фулфилмента', 'itemListElement': [
            {'@type': 'Offer', 'description': s['price'] or None,
             'itemOffered': {'@type': 'Service', 'name': s['name'], 'description': s['desc'] or None}} for s in svc]}
    return b


def breadcrumbs(cfg, page):
    base = cfg['site']['base_url']
    by_path = {p['path']: p for p in cfg['pages']}
    items, acc = [('Главная', base)], ''
    for part in page['path'].strip('/').split('/'):
        acc += part + '/'
        p = by_path.get(acc)
        if p:
            items.append((p.get('breadcrumb') or p['title'], base + acc))
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}


def clean(o):
    """Убрать пустые поля, чтобы в разметке не было null и пустых строк."""
    if isinstance(o, dict):
        o = {k: clean(v) for k, v in o.items()}
        return {k: v for k, v in o.items() if v not in (None, '', [], {})}
    if isinstance(o, list):
        return [v for v in (clean(v) for v in o) if v not in (None, '', [], {})]
    return o


def ff_graph(cfg, page, kinds):
    """Разметка страниц услуг и цен (tools/ff_pages.py): Service, список услуг, прайс."""
    if not {'service', 'service_faq', 'services', 'prices'} & set(kinds):
        return []
    from ff_services import PRICES, SERVICES
    base = cfg['site']['base_url']
    biz = {'@id': base + '#business'}
    num = lambda p: re.sub(r'[^\d,]', '', p).replace(',', '.') or None
    g = []
    s = next((x for x in SERVICES if x['slug'] == page.get('service')), None)
    if s and 'service' in kinds:
        g.append({'@type': 'Service', 'name': s['name'], 'serviceType': s['name'], 'description': s['description'],
                  'url': base + page['path'], 'provider': biz, 'areaServed': {'@type': 'Country', 'name': 'Россия'},
                  'offers': {'@type': 'Offer', 'priceCurrency': 'RUB', 'description': f'{s["price"]} {s["unit"]}',
                             'priceSpecification': {'@type': 'UnitPriceSpecification', 'price': num(s['price']),
                                                    'priceCurrency': 'RUB', 'unitText': s['unit']}}})
    if s and 'service_faq' in kinds:
        g.append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in s['faq']]})
    if 'services' in kinds:
        g.append({'@type': 'ItemList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': x['name'], 'url': f'{base}uslugi/{x["slug"]}/'} for i, x in enumerate(SERVICES)]})
    if 'prices' in kinds:
        g.append({'@type': 'OfferCatalog', 'name': 'Цены на фулфилмент', 'url': base + page['path'], 'itemListElement': [
            {'@type': 'OfferCatalog', 'name': grp['name'], 'itemListElement': [
                {'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': n, 'provider': biz}, 'priceCurrency': 'RUB',
                 'priceSpecification': {'@type': 'UnitPriceSpecification', 'price': num(pr), 'priceCurrency': 'RUB', 'unitText': u}}
                for n, pr, u, _ in grp['rows'] if num(pr)]} for grp in PRICES]})
    return g


def graph(cfg, page, svc, qa):
    site, base = cfg['site'], cfg['site']['base_url']
    kinds, g = page.get('schema', []), []
    if 'website' in kinds:
        g.append({'@type': 'WebSite', '@id': base + '#website', 'url': base, 'name': site['name'],
                  'inLanguage': 'ru-RU', 'publisher': {'@id': base + '#business'}})
    if 'business' in kinds:
        g.append(business(cfg, svc))
    if 'faq' in kinds and qa:
        g.append({'@type': 'FAQPage', '@id': base + page['path'] + '#faq', 'mainEntity': [
            {'@type': 'Question', 'name': text(q), 'acceptedAnswer': {'@type': 'Answer', 'text': text(a)}} for q, a in qa]})
    if 'breadcrumbs' in kinds:
        g.append(breadcrumbs(cfg, page))
    g += ff_graph(cfg, page, kinds)
    return clean({'@context': 'https://schema.org', '@graph': g}) if g else None


# ---------- <head> ----------

def head_block(cfg, page, svc, qa):
    site, org = cfg['site'], cfg['organization']
    base, url = site['base_url'], site['base_url'] + page['path']
    up = '../' * page['path'].count('/')
    title = page['title']
    L = [f'<title>{e(title)}</title>',
         f'<meta name="description" content="{e(page["description"])}">',
         f'<link rel="canonical" href="{e(url)}">',
         '<meta name="robots" content="index, follow, max-image-preview:large">']
    v = cfg.get('verification', {})
    if v.get('yandex'):
        L.append(f'<meta name="yandex-verification" content="{e(v["yandex"])}">')
    if v.get('google'):
        L.append(f'<meta name="google-site-verification" content="{e(v["google"])}">')
    L += [f'<meta name="theme-color" content="{e(site["theme_color"])}">',
          f'<link rel="icon" href="{up}favicon.ico" sizes="32x32">',
          f'<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">',
          f'<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">',
          '<meta property="og:type" content="website">',
          f'<meta property="og:site_name" content="{e(site["name"])}">',
          f'<meta property="og:locale" content="{e(site["locale"])}">',
          f'<meta property="og:title" content="{e(page.get("og_title") or title)}">',
          f'<meta property="og:description" content="{e(page["description"])}">',
          f'<meta property="og:url" content="{e(url)}">']
    if site.get('og_image'):
        L += [f'<meta property="og:image" content="{e(base + site["og_image"])}">',
              f'<meta property="og:image:width" content="{OG_W}">',
              f'<meta property="og:image:height" content="{OG_H}">',
              f'<meta property="og:image:alt" content="{e(site.get("og_image_alt", ""))}">',
              '<meta name="twitter:card" content="summary_large_image">']
    if 'business' in page.get('schema', []):
        a, g = org['address'], org.get('geo') or {}
        if a.get('region_code'):
            L.append(f'<meta name="geo.region" content="{e(a["region_code"])}">')
        if a.get('locality'):
            L.append(f'<meta name="geo.placename" content="{e(a["locality"])}">')
        if g.get('lat') and g.get('lon'):
            L += [f'<meta name="geo.position" content="{g["lat"]};{g["lon"]}">',
                  f'<meta name="ICBM" content="{g["lat"]}, {g["lon"]}">']
    ld = graph(cfg, page, svc, qa)
    if ld:
        L.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace('</', '<\\/') + '</script>')
    m = cfg.get('analytics', {}).get('yandex_metrika')
    if m:
        L.append(METRIKA.replace('{ID}', e(m)))
    return START + '\n' + '\n'.join(L) + '\n' + END


METRIKA = ('<script>(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();'
           'for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}'
           'k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})'
           '(window,document,"script","https://mc.yandex.ru/metrika/tag.js?id={ID}","ym");'
           'ym({ID},"init",{ssr:true,webvisor:true,clickmap:true,ecommerce:"dataLayer",referrer:document.referrer,url:location.href,accurateTrackBounce:true,trackLinks:true});</script>'
           '<noscript><div><img src="https://mc.yandex.ru/watch/{ID}" style="position:absolute;left:-9999px" alt=""></div></noscript>')


def apply_head(src, block):
    if START in src:
        i, j = src.index(START), src.index(END) + len(END)
        return src[:i] + block + src[j:]
    # Первый запуск: убрать то, что теперь живёт в блоке, и вставить блок после viewport.
    h = src.index('</head>')
    head, rest = src[:h], src[h:]
    head = re.sub(r'\n?<title>.*?</title>', '', head, flags=re.S)
    head = re.sub(r'\n?<meta name="description"[^>]*>', '', head)
    head = re.sub(r'\n?<link rel="canonical"[^>]*>', '', head)
    head = re.sub(r'\n?<script type="application/ld\+json">.*?</script>', '', head, flags=re.S)
    vp = re.search(r'<meta name="viewport"[^>]*>', head)
    return head[:vp.end()] + '\n' + block + head[vp.end():] + rest


# ---------- robots, sitemap, llms ----------

def robots(cfg):
    base = cfg['site']['base_url']
    pre = urlsplit(base).path or '/'
    r = cfg.get('robots', {})
    L = ['User-agent: *', f'Allow: {pre}'] + [f'Disallow: {pre}{d}' for d in r.get('disallow', [])]
    L += ['', f'Sitemap: {base}sitemap.xml'] + [f'Sitemap: {base}{s}' for s in r.get('extra_sitemaps', [])]
    return '\n'.join(L) + '\n'


def sitemap(cfg):
    base = cfg['site']['base_url']
    rows = ''.join(f'  <url><loc>{e(base + p["path"])}</loc><lastmod>{lastmod(p["file"])}</lastmod>'
                   f'<changefreq>{p.get("changefreq", "monthly")}</changefreq><priority>{p.get("priority", 0.5):.1f}</priority></url>\n'
                   for p in cfg['pages'])
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{rows}</urlset>\n'


def llms(cfg, svc, qa):
    site, org, ll = cfg['site'], cfg['organization'], cfg.get('llms', {})
    base, a = site['base_url'], org['address']
    addr = ', '.join(x for x in (a.get('postal_code'), a.get('region'), a.get('locality'), a.get('street')) if x)
    L = [f'# {site["name"]}', '', f'> {ll.get("summary", org.get("description", ""))}', '']
    L += [f'- {f}' for f in ll.get('facts', [])]
    L += ['', '## Услуги и цены', '']
    L += [f'- {s["name"]}: {s["desc"]}' + (f' Цена: {s["price"]}.' if s['price'] else '') for s in svc]
    L += ['', '## Контакты', '', f'- Сайт: {base}']
    if org.get('phone'):
        L.append(f'- Телефон: {org["phone"]}')
    if org.get('email'):
        L.append(f'- Почта: {org["email"]}')
    if addr:
        L.append(f'- Склад: {addr}')
    if org.get('legal_name'):
        L.append(f'- Исполнитель: {org["legal_name"]}' + (f', ИНН {org["inn"]}' if org.get('inn') else ''))
    if qa:
        L += ['', '## Частые вопросы', '']
        L += [f'- {text(q)} {text(a)}' for q, a in qa]
    L += ['', '## Страницы', '']
    L += [f'- [{p.get("breadcrumb") or "Главная"}]({base + p["path"]}): {p["description"]}' for p in cfg['pages']]
    return '\n'.join(L) + '\n'


def main():
    with open(CFG, encoding='utf-8') as f:
        cfg = json.load(f)
    home = read('index.html')
    svc, qa = services(home), faq(home)
    for page in cfg['pages']:
        src = read(page['file'])
        src = apply_head(src, head_block(cfg, page, svc, qa))
        if 'faq' in page.get('schema', []) and qa:
            src = re.sub(r'(<div id="faqList">).*?(</div>\n</div></section>)', lambda m: m.group(1) + faq_html(qa) + m.group(2), src, count=1, flags=re.S)
        write(page['file'], src)
    write('robots.txt', robots(cfg))
    write('sitemap.xml', sitemap(cfg))
    write('llms.txt', llms(cfg, svc, qa))
    print(f'SEO: {len(cfg["pages"])} стр., услуг {len(svc)}, вопросов {len(qa)}; robots.txt, sitemap.xml, llms.txt')


if __name__ == '__main__':
    main()
