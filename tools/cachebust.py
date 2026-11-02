#!/usr/bin/env python3
"""Метки версий для CSS и JS: href="uslugi/uslugi.css" → href="uslugi/uslugi.css?v=<хэш файла>".

Хостинг reg.ru отдаёт .css и .js с Cache-Control max-age 45 дней, поэтому без метки браузер после
выкладки держит старые стили при новом HTML (вёрстка «разваливается»). Метка — первые 8 символов
SHA-256 содержимого файла: меняется только когда меняется файл.

Запуск из корня репозитория:  python3 tools/cachebust.py
Проходит все .html обоих сайтов (корень — tovarvdele.ru, agency/ — madrocks.agency), повторный запуск
ничего не меняет. Его же вызывает деплой (.github/workflows/deploy.yml) перед загрузкой, так что после
ручных правок или перезапуска генераторов метки обновятся сами.
"""
import hashlib, os, re

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SKIP = {'.git', '.github', 'tools', 'node_modules'}
REF = re.compile(r'((?:href|src)=")([^"?#]+\.(?:css|js))(?:\?v=[0-9a-f]*)?(")')
_hash = {}


def ver(path):
    if path not in _hash:
        with open(path, 'rb') as f:
            _hash[path] = hashlib.sha256(f.read()).hexdigest()[:8]
    return _hash[path]


def fix(html_path):
    site = os.path.join(ROOT, 'agency') if os.path.relpath(html_path, ROOT).startswith('agency' + os.sep) else ROOT
    base = os.path.dirname(html_path)

    def sub(m):
        url = m.group(2)
        if re.match(r'([a-z]+:|//)', url):
            return m.group(0)
        target = os.path.normpath(os.path.join(site, url.lstrip('/')) if url.startswith('/') else os.path.join(base, url))
        if not os.path.isfile(target):
            return m.group(0)
        return f'{m.group(1)}{url}?v={ver(target)}{m.group(3)}'

    with open(html_path, encoding='utf-8') as f:
        src = f.read()
    out = REF.sub(sub, src)
    if out != src:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(out)
        return True
    return False


def main():
    changed = 0
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP]
        for name in files:
            if name.endswith('.html') and fix(os.path.join(d, name)):
                changed += 1
    print(f'cachebust: обновлено файлов: {changed}')


if __name__ == '__main__':
    main()
