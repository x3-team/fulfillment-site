<?php

namespace App\Site;

use Illuminate\Support\Facades\Cache;

/**
 * Отдаёт HTML-страницы из public/ с подставленными настройками из админки.
 * Файлы в public/ — шаблоны: в них лежат значения «по умолчанию», которые видит и админка.
 */
class PageRenderer
{
    private const JSON = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG;

    public function __construct(private Settings $settings) {}

    /** Путь страницы ('' — главная, 'kontakty', 'dokumenty/politika') → файл или null. */
    public function file(string $path): ?string
    {
        $path = trim($path, '/');
        if (str_contains($path, '..')) {
            return null;
        }
        $file = public_path(($path === '' ? '' : $path.'/').'index.html');

        return is_file($file) ? $file : null;
    }

    public function render(string $path): ?string
    {
        $path = trim($path, '/');
        $file = $this->file($path);
        if (! $file) {
            return null;
        }

        return Cache::rememberForever(
            'site.page.'.$this->settings->version().'.'.md5($path.'|'.filemtime($file)),
            fn () => $this->apply(file_get_contents($file), $path),
        );
    }

    public function apply(string $html, string $path): string
    {
        $s = $this->settings;
        if ($path === '') {
            if ($calc = $s->get('calculator')) {
                $html = $this->applyCalculator($html, $calc);
            }
            if ($texts = $s->get('texts')) {
                $html = $this->applyTexts($html, $texts);
            }
            if ($faq = $s->get('faq')) {
                $html = $this->applyFaq($html, $faq);
            }
        }
        if (! str_starts_with($path, 'agency') && ($contacts = $s->get('contacts'))) {
            $html = $this->applyContacts($html, $contacts);
        }
        if ($seo = $s->get('seo')[$path] ?? null) {
            $html = $this->applySeo($html, $seo);
        }

        return $html;
    }

    // ---------- что сейчас в вёрстке (для админки) ----------

    public function defaults(): array
    {
        $home = file_get_contents(public_path('index.html'));
        preg_match('/const CALC_DEFAULT=(\{.*?\});\n/', $home, $calc);
        preg_match('/const FAQ=(\[.*?\]);\n/', $home, $faq);
        preg_match_all('/<!--t:(\w+)-->(.*?)<!--\/t-->/s', $home, $texts);
        $seo = [];
        foreach (array_keys(config('site.pages')) as $path) {
            if ($file = $this->file($path)) {
                $seo[$path] = $this->readSeo(file_get_contents($file));
            }
        }

        return [
            'calculator' => json_decode($calc[1] ?? 'null', true),
            'faq' => array_map(fn ($qa) => ['q' => $qa[0], 'a' => $qa[1]], json_decode($faq[1] ?? '[]', true)),
            'texts' => array_combine($texts[1], $texts[2]),
            'contacts' => array_map(fn ($f) => $f['default'], config('site.contacts')),
            'seo' => $seo,
        ];
    }

    // ---------- подстановки ----------

    private function applyCalculator(string $html, array $calc): string
    {
        $html = preg_replace_callback('/const CALC_DEFAULT=\{.*?\};\n/', fn () => 'const CALC_DEFAULT='.json_encode($calc, self::JSON).";\n", $html, 1);
        $num = fn ($v) => str_replace('.', ',', (string) (0 + $v));
        foreach (['cfg-disc' => $num($calc['discount'] ?? 0), 'cfg-rate' => $num($calc['storage']['rate'] ?? 0), 'cfg-free' => $num($calc['storage']['free_days'] ?? 0)] as $cls => $v) {
            $html = preg_replace('/(<span class="'.$cls.'">)[^<]*(<\/span>)/', '${1}'.e($v).'${2}', $html);
        }

        return $html;
    }

    private function applyTexts(string $html, array $texts): string
    {
        return preg_replace_callback('/<!--t:(\w+)-->(.*?)<!--\/t-->/s', function ($m) use ($texts) {
            $v = $texts[$m[1]] ?? null;

            return '<!--t:'.$m[1].'-->'.($v === null || $v === '' ? $m[2] : $v).'<!--/t-->';
        }, $html);
    }

    private function applyFaq(string $html, array $faq): string
    {
        $faq = array_values(array_filter($faq, fn ($f) => trim($f['q'] ?? '') !== ''));
        $pairs = array_map(fn ($f) => [$f['q'], $f['a'] ?? ''], $faq);
        $html = preg_replace_callback('/const FAQ=\[.*?\];\n/', fn () => 'const FAQ='.json_encode($pairs, self::JSON).";\n", $html, 1);

        // Та же разметка, что строит скрипт главной (и tools/seo.py): роботы без JS видят ответы
        $list = '';
        foreach ($pairs as $i => [$q, $a]) {
            $list .= '<details'.($i ? '' : ' open').'><summary><span class="num mono">0'.($i + 1).'</span><span>'.$q.'</span><span class="pl"></span></summary><div class="a">'.$a.'</div></details>';
        }
        $html = preg_replace_callback('/(<div id="faqList">).*?(<\/div>\n<\/div><\/section>)/s', fn ($m) => $m[1].$list.$m[2], $html, 1);

        return $this->mapJsonLd($html, function (array $node) use ($pairs) {
            if (($node['@type'] ?? null) === 'FAQPage') {
                $node['mainEntity'] = array_map(fn ($p) => ['@type' => 'Question', 'name' => $this->text($p[0]), 'acceptedAnswer' => ['@type' => 'Answer', 'text' => $this->text($p[1])]], $pairs);
            }

            return $node;
        });
    }

    private function applyContacts(string $html, array $c): string
    {
        $d = array_map(fn ($f) => $f['default'], config('site.contacts'));
        $map = [];
        if (($c['phone'] ?? '') !== '' && $c['phone'] !== $d['phone']) {
            $map[$d['phone']] = $c['phone'];
            $map['tel:'.$this->tel($d['phone'])] = 'tel:'.$this->tel($c['phone']);
            $map['"'.$this->tel($d['phone']).'"'] = '"'.$this->tel($c['phone']).'"';
        }
        if (($c['telegram'] ?? '') !== '' && $c['telegram'] !== $d['telegram']) {
            $map['href="'.$d['telegram'].'"'] = 'href="'.e($c['telegram']).'"';
        }
        if (($c['address'] ?? '') !== '' && $c['address'] !== $d['address']) {
            $map[$d['address']] = $c['address'];
        }

        return strtr($html, $map);
    }

    private function applySeo(string $html, array $seo): string
    {
        $title = trim($seo['title'] ?? '');
        $desc = trim($seo['description'] ?? '');
        if ($title !== '') {
            $html = preg_replace_callback('/<title>.*?<\/title>/s', fn () => '<title>'.e($title).'</title>', $html, 1);
            $html = $this->meta($html, 'property="og:title"', $title);
        }
        if ($desc !== '') {
            $html = $this->meta($html, 'name="description"', $desc);
            $html = $this->meta($html, 'property="og:description"', $desc);
        }

        return $html;
    }

    // ---------- помощники ----------

    private function readSeo(string $html): array
    {
        preg_match('/<title>(.*?)<\/title>/s', $html, $t);
        preg_match('/<meta name="description" content="([^"]*)">/', $html, $d);

        return ['title' => html_entity_decode($t[1] ?? ''), 'description' => html_entity_decode($d[1] ?? '')];
    }

    private function meta(string $html, string $attr, string $value): string
    {
        return preg_replace_callback('/(<meta '.preg_quote($attr, '/').' content=")[^"]*(">)/', fn ($m) => $m[1].e($value).$m[2], $html, 1);
    }

    private function mapJsonLd(string $html, callable $fn): string
    {
        return preg_replace_callback('/(<script type="application\/ld\+json">)(.*?)(<\/script>)/s', function ($m) use ($fn) {
            $ld = json_decode(str_replace('<\/', '</', $m[2]), true);
            if (! is_array($ld)) {
                return $m[0];
            }
            if (isset($ld['@graph'])) {
                $ld['@graph'] = array_map($fn, $ld['@graph']);
            } else {
                $ld = $fn($ld);
            }

            return $m[1].str_replace('</', '<\/', json_encode($ld, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)).$m[3];
        }, $html);
    }

    private function text(string $html): string
    {
        return trim(preg_replace('/\s+/u', ' ', html_entity_decode(strip_tags($html))));
    }

    private function tel(string $phone): string
    {
        $d = preg_replace('/\D/', '', $phone);
        if (strlen($d) === 11 && $d[0] === '8') {
            $d = '7'.substr($d, 1);
        }

        return '+'.$d;
    }
}
